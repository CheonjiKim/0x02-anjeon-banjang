"""사진 판정은 확인됨일 때만 한 번 더 검증한다."""

from app.llm import JudgeOut, MockClient, VerifyOut, get_vision_client, vision_mode
from app.pipeline.rules import photo_hint
from app.schemas import ChecklistItem, EvidenceResult, Judgement, TodoCard
from app.tracing import trace_run

FAILED_OBSERVED = 'AI가 판단하지 못했어요, 관리자 검토가 필요합니다.'
FAILED = Judgement(result='uncertain', observed=FAILED_OBSERVED,
                   retake_hint='사진을 다시 촬영하거나 관리자가 직접 확인해 주세요')
REJECTED_HINT = 'AI가 확실히 확인하지 못했어요. 조치가 잘 보이게 다시 찍거나 반장님이 직접 확인해 주세요'


def run_evidence(item: ChecklistItem, photo: bytes, *, forced: str | None = None,
                 scenario: str | None = None, verify: bool = True,
                 task_id: int | None = None) -> EvidenceResult:
    """판정 또는 검증이 실패하면 판단불가로 내려 사람에게 넘긴다."""
    hint = photo_hint(item.code, item.title)
    mode = 'mock' if forced is not None or scenario is not None else vision_mode()
    with trace_run('evidence', item_code=item.code, task_id=task_id) as trace:
        with trace.step('judge', item_code=item.code, photo=photo, forced=forced, scenario=scenario) as step:
            try:
                client = MockClient(forced=forced, scenario=scenario) if forced is not None or scenario is not None else get_vision_client()
                step.meta['llm'] = client.name
                first = Judgement(**client.judge(item.title, hint, photo, step=step).model_dump())
            except Exception as exc:
                step.meta['failure'] = f'{type(exc).__name__}: {exc}'
                client = None
                first = FAILED
            step.output = first.model_dump()
        final = first
        verified = None
        if first.result == 'confirmed' and verify:
            with trace.step('verify', item_code=item.code, first=first) as step:
                try:
                    checked = client.verify(item.title, hint, photo, first, step=step)
                except Exception as exc:
                    step.meta['failure'] = f'{type(exc).__name__}: {exc}'
                    checked = VerifyOut(agrees=False, evidence='')
                verified = checked.agrees and bool(checked.evidence.strip())
                if not verified:
                    observed = '검증에서 승인 근거를 찾지 못했어요'
                    if checked.evidence:
                        observed += f' — {checked.evidence}'
                    final = Judgement(result='uncertain', observed=observed, retake_hint=REJECTED_HINT)
                step.output = checked.model_dump()
        todo = None if final.result == 'confirmed' else TodoCard(
            kind=final.result, item_code=item.code, title=item.title,
            observed=final.observed, detail=final.retake_hint,
        )
        with trace.step('decide', result=final.result) as step:
            step.output = {'result': final.result, 'todo': todo.model_dump() if todo else None}
    return EvidenceResult(mode=mode, run_id=trace.run_id, judgement=final, first=first,
                          verified=verified, todo=todo)
