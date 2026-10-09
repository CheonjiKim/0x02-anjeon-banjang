"""네 가지 PoC 작업 조건에 따른 위험성평가 참고용 초안을 만든다."""

import re

from app.schemas import UNKNOWN, Conditions, RiskItem


def _high_or_unknown(height: str) -> bool:
    if height == UNKNOWN:
        return True
    if '층' in height:
        return True
    number = re.search(r'\d+', height)
    return number is None or int(number.group(0)) >= 2


def _welding_risks(c: Conditions) -> list[RiskItem]:
    risks = [
        RiskItem(
            code='fire', hazard='용접 불티에 의한 화재',
            likelihood='하' if c.flammable == '없음' else '상', severity='상',
            measure='가연물 제거·방호와 소화기 확인. 화재감시자 법정 배치 요건은 장소·예외를 별도로 확인',
        ),
        RiskItem(
            code='welding-fume', hazard='용접 흄·가스 흡입',
            likelihood='하' if c.ventilation == '양호' else '상', severity='중',
            measure='국소배기 또는 환기 확보, 필요 시 호흡 보호구 착용',
        ),
    ]
    if c.height != UNKNOWN and c.height != '지상' and _high_or_unknown(c.height):
        risks.append(RiskItem(code='welding-fall', hazard='작업 위치에서 추락',
            likelihood='상' if _high_or_unknown(c.height) else '중', severity='상',
            measure='실제 발판 높이와 추락 방지 조치를 현장에서 확인'))
    if c.nearby_people != UNKNOWN and c.nearby_people != '없음':
        risks.append(RiskItem(code='welding-bystander', hazard='주변 인원에 불티·낙하물 노출',
            likelihood='상' if c.nearby_people != UNKNOWN else '중', severity='중',
            measure='주변 작업자 유무와 불티 비산 범위를 확인하고 출입을 통제'))
    return risks


def _saw_risks(c: Conditions) -> list[RiskItem]:
    return [
        RiskItem(
            code='cutting', hazard='원형톱 날 접촉·반발에 의한 절단상',
            likelihood='중', severity='상',
            measure='안전 덮개·절단물 고정 상태를 확인하고 보안경을 착용',
        ),
        RiskItem(
            code='cutting-fire', hazard='절단 불티에 의한 화재',
            likelihood='하' if c.flammable == '없음' else '상', severity='상',
            measure='가연물 제거·방호, 소화기 비치와 불티 비산 방지',
        ),
    ]


def _painting_risks(c: Conditions) -> list[RiskItem]:
    return [
        RiskItem(
            code='chemical', hazard='도료·방수재 증기 흡입 및 피부 노출',
            likelihood='하' if c.ventilation == '양호' else '상', severity='중',
            measure='환기·방독마스크·보호장갑을 확인하고 MSDS를 비치',
        ),
        RiskItem(
            code='ignition', hazard='인화성 증기 점화에 의한 화재·폭발',
            likelihood='중', severity='상',
            measure='화기·스파크를 제거하고 인화성 용기를 밀폐 보관',
        ),
    ]


def _ladder_risks(c: Conditions) -> list[RiskItem]:
    return [
        RiskItem(
            code='ladder-fall', hazard='사다리·말비계 사용 중 추락',
            likelihood='상' if _high_or_unknown(c.height) else '중', severity='상',
            measure='평탄한 바닥·발판 잠금·3점 지지와 보조 작업자를 확인',
        ),
        RiskItem(
            code='falling-object', hazard='상부 공구·자재 낙하',
            likelihood='중', severity='중',
            measure='작업 발판을 정리하고 안전모·턱끈을 착용',
        ),
    ]


_RISK_BUILDERS = {
    '용접·용단': _welding_risks,
    '절단·원형톱': _saw_risks,
    '도장·방수': _painting_risks,
    '사다리·말비계': _ladder_risks,
}


def build_risk_assessment(c: Conditions) -> list[RiskItem]:
    """작업이 미상이면 네 작업의 위험을 모두 높게 잡아 안내한다."""
    if c.work == UNKNOWN:
        return [item for builder in _RISK_BUILDERS.values() for item in builder(c)]
    return _RISK_BUILDERS[c.work](c)
