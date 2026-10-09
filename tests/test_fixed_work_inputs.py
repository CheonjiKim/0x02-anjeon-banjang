import pytest

from app.workflows import run_task


@pytest.mark.parametrize(('text', 'conditions', 'codes'), [
    ('각파이프로 카페 벽체 프레임 용접, 2m 옆에 합판 쌓여 있음',
     {'work': '용접·용단', 'height': '2m', 'flammable': '합판'},
     {'fire-watch', 'spark-cover', 'extinguisher', 'ventilation', 'hot-work-posting',
      'post-work-fire-check', 'work-height-check', 'bystander-control'}),
    ('원형톱으로 각재 재단, 주변에 톱밥 많고 2명 같이 작업 중',
     {'work': '절단·원형톱', 'flammable': '톱밥', 'nearby_people': '2명'},
     {'saw-guard', 'saw-kickback', 'cutting-ppe', 'power-tool-electric',
      'cutting-fire', 'cutting-bystander'}),
    ('욕실 바닥 우레탄 방수, 창문 없고 환풍기 아직 미설치',
     {'work': '도장·방수', 'ventilation': '불량', 'place': '밀폐 공간'},
     {'paint-ventilation', 'confined-space', 'paint-respirator', 'no-ignition',
      'msds-posting', 'flammable-containers'}),
    ('A형 사다리로 천장 조명 교체, 높이 3m, 잡아줄 사람 없음',
     {'work': '사다리·말비계', 'height': '3m', 'nearby_people': '없음'},
     {'fall-height-check', 'ladder-use', 'horse-scaffold', 'helmet-chinstrap',
      'ladder-buddy', 'scaffold-clear-deck'}),
])
def test_fixed_input_extracts_only_related_checklist(text, conditions, codes):
    result = run_task(text)
    for key, expected in conditions.items():
        assert getattr(result.conditions, key) == expected
    assert {item.code for item in result.checklist} == codes


def test_fixed_inputs_include_requested_required_actions():
    welding = run_task('각파이프로 카페 벽체 프레임 용접, 2m 옆에 합판 쌓여 있음')
    assert {'fire-watch', 'extinguisher'} <= {item.code for item in welding.checklist if item.level == 'required'}
    cutting = run_task('원형톱으로 각재 재단, 주변에 톱밥 많고 2명 같이 작업 중')
    assert next(item for item in cutting.checklist if item.code == 'cutting-bystander').level == 'required'
    painting = run_task('욕실 바닥 우레탄 방수, 창문 없고 환풍기 아직 미설치')
    assert next(item for item in painting.checklist if item.code == 'paint-ventilation').level == 'required'
    ladder = run_task('A형 사다리로 천장 조명 교체, 높이 3m, 잡아줄 사람 없음')
    titles = {item.title for item in ladder.checklist if item.level == 'required'}
    assert '아웃트리거 설치 또는 사다리 지지자 배치' in titles
    assert '사다리 최상단 작업 금지·설치 상태 확인' in titles
