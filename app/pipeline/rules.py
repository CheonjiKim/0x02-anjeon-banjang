"""Load PoC rule details from rules/*.json and build conservative checklists."""

from functools import lru_cache
import json
from pathlib import Path
import re

from app.schemas import UNKNOWN, ChecklistItem, Conditions

ROOT = Path(__file__).resolve().parents[2]
RULES_DIR = ROOT / 'rules'
POC_SOURCE = 'PoC 점검 안내(법적 근거 검수 전)'

# The binding file connects stable UI/evidence codes to source rule IDs. Rule
# wording, source status and unknown-condition policy remain in the source JSON.
WORK_FILES = {
    '용접·용단': 'welding.json',
    '절단·원형톱': 'circular_saw.json',
    '도장·방수': 'painting_waterproofing.json',
    '사다리·말비계': 'ladder_horse_scaffold.json',
}
WORK_TYPES = {
    '용접·용단': 'welding',
    '절단·원형톱': 'circular_saw',
    '도장·방수': 'painting_waterproofing',
    '사다리·말비계': 'ladder_horse_scaffold',
}

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
        ('fire-watch', '화재감시자 배치'), ('spark-cover', '불티 비산 방지포 설치'),
        ('extinguisher', '소화기 비치'), ('ventilation', '환기 확인'),
        ('hot-work-posting', '화기 작업 구역 표지'),
    ],
    '절단·원형톱': [
        ('saw-guard', '원형톱 안전 덮개 확인'), ('saw-kickback', '절단물 고정 및 반발 방지'),
        ('cutting-ppe', '보안경·청력 보호구 착용'), ('power-tool-electric', '전동공구 전선·누전 차단 확인'),
        ('cutting-fire', '절단 불티 화재 예방'),
    ],
    '도장·방수': [
        ('paint-ventilation', '환풍기 또는 자연환기 확보'), ('confined-space', '밀폐 공간 작업 관리'),
        ('paint-respirator', '유기용제용 방독마스크 착용'), ('no-ignition', '점화원 제거 및 화기 금지'),
        ('msds-posting', '도료·방수재 MSDS 비치'), ('flammable-containers', '인화성 용기 밀폐 보관'),
    ],
    '사다리·말비계': [
        ('fall-height-check', '작업 높이·추락 방지 확인'), ('ladder-use', '사다리 설치·사용 상태 확인'),
        ('horse-scaffold', '말비계 발판·잠금 상태 확인'), ('helmet-chinstrap', '안전모·턱끈 착용'),
        ('ladder-buddy', '사다리 보조 작업자 배치'), ('scaffold-clear-deck', '작업 발판 정리 상태 확인'),
    ],
}


@lru_cache(maxsize=1)
def _rule_catalog() -> tuple[dict, dict]:
    """Read the rule JSON files and bindings; invalid/missing rules fail closed."""
    binding_data = json.loads((RULES_DIR / 'runtime_bindings.json').read_text(encoding='utf-8'))
    bindings = binding_data['bindings']
    catalog = {}
    for work, filename in WORK_FILES.items():
        data = json.loads((RULES_DIR / filename).read_text(encoding='utf-8'))
        if data.get('schema_version') is None or data.get('work_type') != WORK_TYPES[work]:
            raise ValueError(f'수칙 파일의 버전/작업 유형이 올바르지 않습니다: {filename}')
        for rule in data.get('rules', []):
            rule_id = rule.get('id')
            if not rule_id or rule_id in catalog:
                raise ValueError(f'수칙 ID가 없거나 중복되었습니다: {rule_id}')
            catalog[rule_id] = (work, filename, rule)
    for work_type, rules in bindings.items():
        for rule_id in rules:
            if rule_id not in catalog or catalog[rule_id][0] not in WORK_TYPES or WORK_TYPES[catalog[rule_id][0]] != work_type:
                raise ValueError(f'실행 연결에 존재하지 않는 수칙이 지정되었습니다: {work_type}/{rule_id}')
    return catalog, bindings


def _is_high_or_unknown(height: str) -> bool:
    if height == UNKNOWN or '층' in height:
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


def _condition_value(key: str, expected: str, c: Conditions, task_text: str):
    if key in {'combustibles_present', 'combustibles_nearby', 'combustibles_below_or_behind', 'flammable_containers_nearby'}:
        return None if c.flammable == UNKNOWN else (c.flammable != '없음') == (expected == 'yes')
    if key == 'ventilation':
        if c.ventilation == UNKNOWN:
            return None
        return (c.ventilation != '양호') == (expected == 'enclosed')
    if key == 'concurrent_flammable_work':
        mixed = bool(re.search(r'도장|페인트|방수|우레탄', task_text)) and bool(re.search(r'용접|용단', task_text))
        return mixed == (expected == 'yes')
    if key == 'work_height':
        return None if c.height == UNKNOWN else _is_high_or_unknown(c.height) == (expected == 'over_2m')
    if key == 'location':
        if c.place == UNKNOWN:
            return None
        outdoor = c.place in {'외부', '옥상'}
        return outdoor == (expected == 'outdoor')
    if key == 'always':
        return bool(expected)
    # Unknown condition keys must never make an item optional.
    return None


def _expression(expression, c: Conditions, task_text: str):
    if not isinstance(expression, dict):
        return None
    if 'any' in expression:
        values = [_expression(child, c, task_text) for child in expression['any']]
        return True if True in values else (None if None in values else False)
    if 'all' in expression:
        values = [_expression(child, c, task_text) for child in expression['all']]
        return False if False in values else (None if None in values else True)
    if 'always' in expression:
        return bool(expression['always'])
    values = [_condition_value(key, expected, c, task_text) for key, expected in expression.items()]
    return None if None in values else all(values)


def _rule_level(rule: dict, c: Conditions, task_text: str, *, force: bool) -> str:
    if force:
        return 'required'
    applicability = _expression(rule.get('applies_when'), c, task_text)
    levels = rule.get('level', {})
    value = levels.get('when_unknown') if applicability is None else levels.get('when_applies' if applicability else 'otherwise')
    return 'required' if value == 'required' else 'recommended'


def _source_text(filename: str, rule: dict) -> str:
    source = rule.get('source') or {}
    articles = source.get('articles') or source.get('guideline') or []
    basis = ', '.join(articles)
    status = source.get('status', 'status 미기재')
    return f'{filename} · {status}' + (f' · {basis}' if basis else '')


def _rule_for(work: str, code: str):
    catalog, bindings = _rule_catalog()
    work_type = WORK_TYPES[work]
    for rule_id, bound_code in bindings.get(work_type, {}).items():
        if bound_code == code:
            return catalog[rule_id][1], catalog[rule_id][2]
    return None


def _items_for(work: str, c: Conditions, *, force: bool, task_text: str = '') -> list[ChecklistItem]:
    out = []
    for code, title in _WORK_ITEMS[work]:
        matched = _rule_for(work, code)
        if matched:
            filename, rule = matched
            protections = rule.get('protections') or []
            level = _rule_level(rule, c, task_text, force=force)
            out.append(ChecklistItem(code=code, title=title, source=_source_text(filename, rule), level=level,
                                     note=' · '.join(protections) if protections else None))
        else:
            out.append(ChecklistItem(code=code, title=title, source=POC_SOURCE,
                                     level='required' if _required(code, c, force=force) else 'recommended',
                                     note='조건이 확인되지 않아 필수로 안내해요' if force else None))
    return out


def build_checklist(c: Conditions, *, task_text: str = '') -> list[ChecklistItem]:
    """JSON-backed PoC entries plus conservative runtime-only checklist entries."""
    force = c.work == UNKNOWN
    works = list(_WORK_ITEMS) if force else [c.work]
    checklist = [item for work in works for item in _items_for(work, c, force=force, task_text=task_text)]
    welding_and_painting = bool(re.search(r'용접|용단', task_text)) and bool(re.search(r'도장|페인트|방수|우레탄', task_text))
    if welding_and_painting:
        if not force:
            companion = '도장·방수' if c.work == '용접·용단' else '용접·용단'
            checklist.extend(_items_for(companion, c, force=False, task_text=task_text))
        checklist.append(ChecklistItem(code='mixed-work-warning', title='도장·방수와 화기 작업 혼재 금지',
                                       source=POC_SOURCE, level='required',
                                       note='인화성 증기와 불티가 만날 수 있어 작업 구역·시간을 분리하세요'))
    return checklist


def photo_hint(code: str, title: str) -> str:
    """Return the registered visual target; rule evidence names supplement it."""
    matched = next((entry for entries in _WORK_ITEMS.values() for entry in entries if entry[0] == code), None)
    if matched:
        work = next(work for work, entries in _WORK_ITEMS.items() if any(item[0] == code for item in entries))
        rule_match = _rule_for(work, code)
        if rule_match:
            _, rule = rule_match
            photo_items = (rule.get('evidence') or {}).get('photo_items') or []
            if photo_items:
                return f"{PHOTO_HINTS.get(code, title)}. 확인할 요소: {', '.join(photo_items)}"
    return PHOTO_HINTS.get(code, title)
