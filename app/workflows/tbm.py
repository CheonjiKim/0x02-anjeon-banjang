"""TBM에서 언급하지 않은 필수 점검 항목을 찾는다."""

from app.schemas import ChecklistItem, TbmResult
from app.tracing import trace_run


def run_tbm(points: list[str], checklist: list[ChecklistItem], *, task_id: int | None = None) -> TbmResult:
    """문자열 포함 관계로 필수 항목의 언급 여부를 비교한다."""
    said = [point.strip() for point in points if point.strip()]
    with trace_run('tbm', task_id=task_id) as trace:
        with trace.step('tbm_review', said=said, checklist=[item.code for item in checklist]) as step:
            missing = [
                item for item in checklist
                if item.level == 'required'
                and not any(item.title in point or point in item.title for point in said)
            ]
            step.output = [item.code for item in missing]
    return TbmResult(run_id=trace.run_id, missing=missing)
