"""TBM에서 언급하지 않은 필수 점검 항목을 찾는다."""

from app.schemas import ChecklistItem, TbmResult
from app.tracing import trace_run


# Curated phrases are intentional: reporting a required item absent or broken
# must not satisfy TBM merely because the noun was spoken.
_ALIASES = {
    'fire-watch': ('화재감시자', '화재 감시자', '감시자 배치', '불티 감시'),
    'spark-cover': ('불티 비산 방지포', '불티 방지포', '방화포', '불티 방지 커버', '가연물 방호'),
    'extinguisher': ('소화기', '소화 설비', '소화기구'),
    'ventilation': ('환기', '송풍기', '환풍기'),
    'paint-ventilation': ('환풍기', '자연환기', '송풍기', '환기'),
    'hot-work-posting': ('화기 작업 구역 표지', '화기 작업 표지', '출입 통제선'),
    'cutting-fire': ('불티 방지', '소화기', '방화 조치', '불티방지커버'),
    'saw-guard': ('톱날 덮개', '안전 덮개', '보호 덮개'),
    'saw-kickback': ('절단물 고정', '반발 방지', '킥백 방지'),
    'cutting-ppe': ('보안경', '청력 보호구', '귀마개'),
    'power-tool-electric': ('누전 차단기', '전선 점검', '전동공구 점검'),
    'flammable-containers': ('인화성 용기', '시너 용기', '페인트 용기'),
    'ladder-use': ('사다리 설치', '사다리 고정', '삼점 지지', '3점 지지'),
    'horse-scaffold': ('말비계 잠금', '말비계 지주', '말비계 바닥'),
    'scaffold-clear-deck': ('발판 정리', '발판 위 자재', '작업 발판 정리'),
    'helmet-chinstrap': ('안전모 턱끈', '턱끈'),
    'ladder-buddy': ('사다리 보조자', '사다리 잡아'),
    'fall-height-check': ('추락 방지', '작업 높이'),
}
_NEGATION = ('없', '미설치', '미배치', '불량', '미착용', '착용 안', '설치 안', '확인 안', '않', '못')


def _normalized(value: str) -> str:
    return ''.join(char for char in value.lower() if char.isalnum() or '가' <= char <= '힣')


def _mentioned(item: ChecklistItem, text: str) -> bool:
    normalized = _normalized(text)
    aliases = _ALIASES.get(item.code, (item.title,)) + (item.title,)
    for alias in aliases:
        key = _normalized(alias)
        if not key:
            continue
        position = 0
        while (position := normalized.find(key, position)) >= 0:
            after = normalized[position + len(key):position + len(key) + 24]
            if not any(_normalized(negative) in after for negative in _NEGATION):
                return True
            position += 1
    return False


def run_tbm(points: list[str], checklist: list[ChecklistItem], *, task_id: int | None = None) -> TbmResult:
    """문자열 포함 관계로 필수 항목의 언급 여부를 비교한다."""
    said = [point.strip() for point in points if point.strip()]
    with trace_run('tbm', task_id=task_id) as trace:
        with trace.step('tbm_review', said=said, checklist=[item.code for item in checklist]) as step:
            missing = [item for item in checklist
                       if item.level == 'required' and not any(_mentioned(item, point) for point in said)]
            step.output = [item.code for item in missing]
    return TbmResult(run_id=trace.run_id, missing=missing)
