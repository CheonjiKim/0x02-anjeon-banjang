"""오판 처리. 오승인으로 이어질 수 있는 실패 경로마다 테스트가 하나씩 있다.

원칙: AI가 확신하지 못하면 승인하지 않고 사람에게 넘긴다. 승인 쪽에만 비용을 더 쓴다.
"""

import pytest

from app.llm import JudgeOut
from app.pipeline.normalize import normalize
from app.schemas import UNKNOWN, Conditions


def test_out_of_range_result_cannot_be_constructed():
    with pytest.raises(ValueError):
        JudgeOut(result='approved', observed='관찰')


def test_prompts_reject_text_in_image():
    from app.llm.openai_client import load_prompt
    for name in ['judge', 'verify']:
        assert '글자' in load_prompt(name, item='소화기', photo_hint='소화기', observed='관찰')


def test_values_outside_allowlist_become_unknown():
    conditions = Conditions(work='배관', height='높음', flammable='나무', ventilation='좋음', nearby_people='많음', place='어딘가')
    got, dropped = normalize(conditions, {}, '작업')
    assert all(value == UNKNOWN for value in got.model_dump().values())
    assert set(dropped) == set(Conditions.model_fields)


def test_allowed_values_pass():
    conditions = Conditions(work='용접·용단', height='2층', flammable='합판', ventilation='불량', nearby_people='2명', place='지하 주차장')
    got, dropped = normalize(conditions, {}, '지하 주차장 2층 용접 옆에 합판, 환기 불량, 2명')
    assert got == conditions and dropped == {}


def test_lowering_value_with_fabricated_span_is_rejected():
    got, dropped = normalize(Conditions(flammable='없음'), {'flammable': '가연물 없음'}, '2층 용접, 옆에 자재')
    assert got.flammable == UNKNOWN and '근거' in dropped['flammable']
