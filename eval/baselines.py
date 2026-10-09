"""안전한 쪽 처리만 제거한 ablation 기준선이다."""

from app.pipeline.extract import extract_conditions
from app.pipeline.rules import build_checklist
from app.schemas import UNKNOWN, Conditions

BENIGN = {'flammable': '없음', 'ventilation': '양호', 'height': '지상', 'nearby_people': '없음', 'place': '외부'}


def single_call(text: str):
    """되묻기 없이 미상 조건을 문제없는 값으로 가정하는 기준선이다."""
    extracted = extract_conditions(text)
    values = extracted.model_dump()
    for key, value in BENIGN.items():
        if values[key] == UNKNOWN:
            values[key] = value
    return extracted, build_checklist(Conditions(**values))
