"""작업 조건에 따른 위험성평가 참고용 초안을 만든다."""

import re

from app.schemas import UNKNOWN, Conditions, RiskItem


def build_risk_assessment(c: Conditions) -> list[RiskItem]:
    """조건이 미상이면 가능성을 높게 잡은 위험 네 가지를 반환한다."""
    number = re.search(r'\d+', c.height)
    if c.height == UNKNOWN:
        fall_likelihood = '상'
    elif number and int(number.group(0)) >= 2:
        fall_likelihood = '중'
    else:
        fall_likelihood = '하'
    return [
        RiskItem(
            code='fire', hazard='용접 불티에 의한 화재',
            likelihood='하' if c.flammable == '없음' else '상', severity='상',
            measure='가연물 제거·방호, 화재감시자 배치, 소화기 비치',
        ),
        RiskItem(
            code='burn', hazard='불티·고온 접촉에 의한 화상', likelihood='중', severity='중',
            measure='보호구(용접면·장갑·앞치마) 착용, 불티 비산 방지포 설치',
        ),
        RiskItem(
            code='ventilation', hazard='흄·가스 흡입',
            likelihood='하' if c.ventilation == '양호' else '상', severity='중',
            measure='국소배기 또는 환기 확보, 필요 시 방진마스크 착용',
        ),
        RiskItem(
            code='fall', hazard='고소 작업 중 추락·낙하물', likelihood=fall_likelihood, severity='상',
            measure='작업 발판·안전난간 확인, 하부 통제',
        ),
    ]
