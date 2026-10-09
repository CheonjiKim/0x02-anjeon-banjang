"""하드코딩한 다섯 점검 항목과 사진 판정 안내를 제공한다."""

from app.schemas import UNKNOWN, ChecklistItem, Conditions

PHOTO_HINTS = {
    'fire-watch': '용접 지점 근처에서 감시만 하는 사람(소화기·조명 등 장비를 든)',
    'extinguisher': '작업 지점 가까이 놓인 소화기',
    'spark-cover': '용접 지점 아래·주변 가연물을 덮은 방화포·불티 비산 방지포',
    'ventilation': '작동 중인 국소배기·송풍기 또는 열린 개구부',
    'area-sign': '작업 구역을 알리는 표지와 출입 통제선',
}


def build_checklist(c: Conditions) -> list[ChecklistItem]:
    """조건이 미상이면 안전한 쪽으로 점검 항목을 필수 처리한다."""
    return [
        ChecklistItem(
            code='fire-watch', title='화재감시자 배치',
            source='산업안전보건기준에 관한 규칙(용접 작업 화재 예방)',
            level='recommended' if c.flammable == '없음' else 'required',
        ),
        ChecklistItem(code='extinguisher', title='소화기 비치', source='현장 관례', level='required'),
        ChecklistItem(code='spark-cover', title='불티 비산 방지포 설치', source='현장 관례', level='required'),
        ChecklistItem(
            code='ventilation', title='환기 확인', source='현장 관례',
            level='recommended' if c.ventilation == '양호' else 'required',
            note='환기 상태를 몰라 필수로 올렸어요' if c.ventilation == UNKNOWN else None,
        ),
        ChecklistItem(code='area-sign', title='작업 구역 표지', source='현장 관례', level='recommended'),
    ]


def photo_hint(code: str, title: str) -> str:
    """등록된 사진 안내가 없으면 항목 제목을 사용한다."""
    return PHOTO_HINTS.get(code, title)
