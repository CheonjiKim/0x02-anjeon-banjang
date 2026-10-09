"""네 가지 PoC 작업의 조건별 점검 항목과 사진 판정 안내를 제공한다."""

import re

from app.schemas import UNKNOWN, ChecklistItem, Conditions

POC_SOURCE = 'PoC 점검 안내(법적 근거 검수 전)'

PHOTO_HINTS = {
    'fire-watch': '용접 지점 근처에서 감시만 하는 사람과 소화기',
    'extinguisher': '작업 지점 가까이 놓인 소화기',
    'spark-cover': '가연물을 덮은 방화포 또는 불티 비산 방지포',
    'hot-work-posting': '화기 작업 구역 표지와 출입 통제선',
    'saw-guard': '원형톱 날을 덮는 안전 덮개',
    'saw-kickback': '절단물을 고정한 상태와 반발 방지 조치',
    'cutting-ppe': '보안경과 청력 보호구를 착용한 작업자',
    'power-tool-electric': '손상 없는 전선과 누전 차단 장치',
    'cutting-fire': '절단 불티 주변의 소화기와 방화 조치',
    'paint-ventilation': '작동 중인 환풍기·송풍기 또는 열린 개구부',
    'confined-space': '밀폐 공간 출입 관리와 환기 장치',
    'paint-respirator': '유기용제용 방독마스크를 착용한 작업자',
    'no-ignition': '점화원 제거·화기 금지 표지',
    'msds-posting': '도료·방수재의 물질안전보건자료(MSDS)',
    'flammable-containers': '밀폐 보관한 도료·시너 용기',
    'fall-height-check': '작업 높이와 추락 방지 조치를 확인하는 모습',
    'ladder-use': '평탄한 바닥에 고정하고 3점 지지로 사용하는 사다리',
    'horse-scaffold': '수평 발판과 잠금 상태가 보이는 말비계',
    'helmet-chinstrap': '턱끈을 조인 안전모',
    'ladder-buddy': '사다리를 잡아 주는 보조 작업자',
    'scaffold-clear-deck': '물건을 치우고 틈 없이 정리한 작업 발판',
    'mixed-work-warning': '도장·방수 작업 구역과 화기 작업 구역을 분리한 모습',
}

_WORK_ITEMS = {
    '용접·용단': [
        ('fire-watch', '화재감시자 배치'),
        ('spark-cover', '불티 비산 방지포 설치'),
        ('extinguisher', '소화기 비치'),
        ('ventilation', '환기 확인'),
        ('hot-work-posting', '화기 작업 구역 표지'),
    ],
    '절단·원형톱': [
        ('saw-guard', '원형톱 안전 덮개 확인'),
        ('saw-kickback', '절단물 고정 및 반발 방지'),
        ('cutting-ppe', '보안경·청력 보호구 착용'),
        ('power-tool-electric', '전동공구 전선·누전 차단 확인'),
        ('cutting-fire', '절단 불티 화재 예방'),
    ],
    '도장·방수': [
        ('paint-ventilation', '환풍기 또는 자연환기 확보'),
        ('confined-space', '밀폐 공간 작업 관리'),
        ('paint-respirator', '유기용제용 방독마스크 착용'),
        ('no-ignition', '점화원 제거 및 화기 금지'),
        ('msds-posting', '도료·방수재 MSDS 비치'),
        ('flammable-containers', '인화성 용기 밀폐 보관'),
    ],
    '사다리·말비계': [
        ('fall-height-check', '작업 높이·추락 방지 확인'),
        ('ladder-use', '사다리 설치·사용 상태 확인'),
        ('horse-scaffold', '말비계 발판·잠금 상태 확인'),
        ('helmet-chinstrap', '안전모·턱끈 착용'),
        ('ladder-buddy', '사다리 보조 작업자 배치'),
        ('scaffold-clear-deck', '작업 발판 정리 상태 확인'),
    ],
}


def _is_high_or_unknown(height: str) -> bool:
    if height == UNKNOWN:
        return True
    if '층' in height:
        return True
    number = re.search(r'\d+', height)
    return number is None or int(number.group(0)) >= 2


def _required(code: str, c: Conditions, *, force: bool) -> bool:
    if force:
        return True
    if code in {'fire-watch', 'spark-cover', 'hot-work-posting', 'cutting-fire'}:
        return c.flammable != '없음'
    if code in {'ventilation', 'paint-ventilation'}:
        return c.ventilation != '양호'
    if code == 'confined-space':
        return c.ventilation != '양호' and c.place != '지하 주차장'
    if code in {'fall-height-check', 'ladder-buddy'}:
        return _is_high_or_unknown(c.height)
    return True


def _items_for(work: str, c: Conditions, *, force: bool) -> list[ChecklistItem]:
    return [
        ChecklistItem(
            code=code,
            title=title,
            source=POC_SOURCE,
            level='required' if _required(code, c, force=force) else 'recommended',
            note='조건이 확인되지 않아 필수로 안내해요' if force else None,
        )
        for code, title in _WORK_ITEMS[work]
    ]


def build_checklist(c: Conditions, *, task_text: str = '') -> list[ChecklistItem]:
    """조건 미상은 안전한 쪽으로 필수 처리하고, 혼재작업은 별도로 경고한다."""
    force = c.work == UNKNOWN
    works = list(_WORK_ITEMS) if force else [c.work]
    checklist = [item for work in works for item in _items_for(work, c, force=force)]
    welding_and_painting = (
        bool(re.search(r'용접|용단', task_text))
        and bool(re.search(r'도장|페인트|방수|우레탄', task_text))
    )
    if welding_and_painting:
        if not force:
            companion = '도장·방수' if c.work == '용접·용단' else '용접·용단'
            checklist.extend(_items_for(companion, c, force=False))
        checklist.append(ChecklistItem(
            code='mixed-work-warning', title='도장·방수와 화기 작업 혼재 금지',
            source=POC_SOURCE, level='required',
            note='인화성 증기와 불티가 만날 수 있어 작업 구역·시간을 분리하세요',
        ))
    return checklist


def photo_hint(code: str, title: str) -> str:
    """등록된 사진 안내가 없으면 항목 제목을 사용한다."""
    return PHOTO_HINTS.get(code, title)
