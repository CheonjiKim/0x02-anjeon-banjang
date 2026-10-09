"""작업 문장을 고정된 순서로 조건·점검 항목·위험성평가로 바꾼다."""

from app.llm import ExtractOut, LLMError, MockClient, get_client
from app.pipeline.normalize import normalize
from app.pipeline.risk import build_risk_assessment
from app.pipeline.rules import build_checklist
from app.schemas import Conditions, TaskResult
from app.tracing import trace_run

CONDITION_QUESTIONS = {
    'work': '어떤 작업인가요? (예: 용접·용단, 절단·원형톱, 도장·방수, 사다리·말비계)',
    'height': '작업 높이는 어떻게 되나요? (예: 2층, 지상)',
    'flammable': '주변에 불에 타는 물건이 있나요? (예: 합판, 없음)',
    'ventilation': '환기는 되나요? (예: 양호, 밀폐)',
    'nearby_people': '주변에 다른 작업자가 있나요? (예: 2명, 없음)',
    'place': '어디에서 하나요? (예: 지하 주차장, 외부)',
}
QUESTION_OPTIONS = {
    'work': ['용접·용단', '절단·원형톱', '도장·방수', '사다리·말비계'],
    'height': ['지상', '2층', '3층'],
    'flammable': ['합판', '스티로폼', '없음'],
    'ventilation': ['양호', '불량'],
    'nearby_people': ['있음', '없음'],
    'place': ['실내', '외부', '지하'],
}


def run_task(text: str, *, site_id: int = 1, worker_id: int = 1,
             pinned: dict[str, str] | None = None, scenario: str | None = None) -> TaskResult:
    """추출부터 위험성평가까지 한 번씩만 실행한다."""
    with trace_run('task', text=text, site_id=site_id, worker_id=worker_id) as trace:
        with trace.step('extract', text=text) as step:
            try:
                client = MockClient(scenario=scenario) if scenario else get_client()
                step.meta['llm'] = client.name
                raw = client.extract(text, step=step)
            except LLMError as exc:
                step.meta['failure'] = str(exc)
                raw = ExtractOut(conditions=Conditions(), evidence={})
            except Exception as exc:
                step.meta['failure'] = f'{type(exc).__name__}: {exc}'
                raw = ExtractOut(conditions=Conditions(), evidence={})
            step.output = raw.model_dump()
        with trace.step('normalize', conditions=raw.conditions, evidence=raw.evidence) as step:
            conditions, dropped = normalize(raw.conditions, raw.evidence, text)
            step.output = {'conditions': conditions.model_dump(), 'dropped': dropped}
        if pinned:
            with trace.step('pin', pinned=pinned) as step:
                values = conditions.model_dump()
                for key, value in pinned.items():
                    if key in Conditions.model_fields:
                        values[key] = value
                conditions = Conditions(**values)
                step.output = conditions.model_dump()
        with trace.step('questions', unknown=conditions.unknown_keys()) as step:
            unknown = conditions.unknown_keys()
            questions = [CONDITION_QUESTIONS[key] for key in unknown]
            step.output = {'questions': questions, 'assumed_required': unknown}
        with trace.step('rules', conditions=conditions) as step:
            checklist = build_checklist(conditions, task_text=text)
            step.output = [item.model_dump() for item in checklist]
        with trace.step('risk', conditions=conditions) as step:
            risks = build_risk_assessment(conditions)
            step.output = [item.model_dump() for item in risks]
    return TaskResult(run_id=trace.run_id, conditions=conditions, questions=questions,
                      assumed_required=unknown, checklist=checklist, risks=risks)
