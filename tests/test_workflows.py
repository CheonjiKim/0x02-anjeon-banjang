import pytest

from app.schemas import ChecklistItem
from app.tracing import read_traces
from app.workflows import QUESTION_OPTIONS, run_evidence, run_task, run_tbm

DEMO = '2층 각파이프 용접, 옆에 합판'
FULL = '외부 지상에서 용접, 환기 양호, 가연물 없음, 혼자 작업'
ITEM = ChecklistItem(code='extinguisher', title='소화기 비치', level='required')


def steps():
    return [step['name'] for step in read_traces()[-1]['steps']]


def test_task_steps_in_order():
    result = run_task(DEMO)
    assert steps() == ['extract', 'normalize', 'questions', 'rules', 'risk']
    assert result.run_id == read_traces()[-1]['run_id']


def test_unknown_conditions_become_questions_and_required():
    result = run_task(DEMO)
    assert set(result.assumed_required) == {'ventilation', 'nearby_people', 'place'}
    assert len(result.questions) == 3
    assert next(item for item in result.checklist if item.code == 'ventilation').level == 'required'


def test_all_known_conditions_ask_nothing():
    result = run_task(FULL)
    assert result.questions == result.assumed_required == []


def test_pinned_condition_beats_extraction():
    result = run_task(DEMO, pinned={'flammable': '없음', 'ventilation': '양호'})
    assert result.conditions.flammable == '없음'
    assert 'ventilation' not in result.assumed_required
    assert next(item for item in result.checklist if item.code == 'fire-watch').level == 'recommended'
    assert steps() == ['extract', 'normalize', 'pin', 'questions', 'rules', 'risk']


def test_confirmed_is_verified_then_decided():
    result = run_evidence(ITEM, b'photo', forced='confirmed')
    assert result.judgement.result == 'confirmed' and result.verified is True and result.todo is None
    assert steps() == ['judge', 'verify', 'decide']


def test_unconfirmed_skips_verify_and_makes_todo():
    for forced in ['not_visible', 'uncertain']:
        result = run_evidence(ITEM, b'photo', forced=forced)
        assert result.verified is None and result.todo.kind == forced
        assert steps() == ['judge', 'decide']


def test_verify_rejection_downgrades_to_uncertain():
    result = run_evidence(ITEM, b'photo', forced='confirmed', scenario='verify_reject')
    assert result.first.result == 'confirmed' and result.judgement.result == 'uncertain'
    assert result.verified is False and '찾지 못했어요' in result.todo.observed


def test_tbm_flags_missing_required_items():
    task = run_task(DEMO)
    result = run_tbm(['소화기 비치'], task.checklist)
    assert 'extinguisher' not in [item.code for item in result.missing]
    assert 'fire-watch' in [item.code for item in result.missing]
    assert all(item.level == 'required' for item in result.missing)
    assert steps() == ['tbm_review']


def test_tbm_clean_when_all_said():
    task = run_task(DEMO)
    points = [item.title for item in task.checklist if item.level == 'required']
    assert run_tbm(points, task.checklist).missing == []


def test_extract_falls_back_to_keywords_when_llm_unavailable(monkeypatch):
    monkeypatch.setenv('BANJANG_LLM', 'openai')
    for key in ['OPENAI_API_KEY', 'BANJANG_MODEL_EXTRACT', 'BANJANG_MODEL_JUDGE']:
        monkeypatch.delenv(key, raising=False)
    assert run_task(DEMO).conditions.flammable == '합판'
    assert read_traces()[-1]['steps'][0]['meta']['fallback'].startswith('keyword')


def test_question_options_match_the_foreman_patch_contract():
    assert QUESTION_OPTIONS['work'] == ['용접·용단', '절단·원형톱', '도장·방수', '사다리·말비계']
    assert QUESTION_OPTIONS['flammable'] == ['합판', '스티로폼', '없음']


@pytest.mark.parametrize(
    ('text', 'work', 'required'),
    [
        ('2층 각파이프 용접, 옆에 합판', '용접·용단', {'fire-watch', 'spark-cover', 'extinguisher', 'ventilation', 'hot-work-posting'}),
        ('원형톱으로 합판 절단', '절단·원형톱', {'saw-guard', 'saw-kickback', 'cutting-ppe', 'power-tool-electric', 'cutting-fire'}),
        ('지하 주차장 바닥 우레탄 방수, 환기 불량', '도장·방수', {'paint-ventilation', 'paint-respirator', 'no-ignition', 'msds-posting', 'flammable-containers'}),
        ('사다리 3m 올라가서 조명 교체', '사다리·말비계', {'fall-height-check', 'ladder-use', 'horse-scaffold', 'helmet-chinstrap', 'ladder-buddy', 'scaffold-clear-deck'}),
    ],
)
def test_four_poc_work_types_make_their_own_required_checklist(text, work, required):
    result = run_task(text)
    assert result.conditions.work == work
    assert required <= {item.code for item in result.checklist if item.level == 'required'}


def test_unknown_work_keeps_all_four_poc_checklists_required():
    result = run_task('배관 작업 합니다')
    codes = {item.code for item in result.checklist if item.level == 'required'}
    assert {'cutting-fire', 'paint-ventilation', 'ladder-use', 'fire-watch'} <= codes


def test_painting_mixed_with_welding_warns_the_foreman():
    result = run_task('용접과 같은 층에서 우레탄 방수 페인트 작업, 환기 불량')
    assert 'mixed-work-warning' in {item.code for item in result.checklist if item.level == 'required'}


@pytest.mark.parametrize(
    ('text', 'risk_code'),
    [
        ('원형톱으로 합판 절단', 'cutting'),
        ('지하 주차장 바닥 우레탄 방수, 환기 불량', 'chemical'),
        ('사다리 3m 올라가서 조명 교체', 'ladder-fall'),
    ],
)
def test_poc_work_type_changes_risk_assessment(text, risk_code):
    assert risk_code in {item.code for item in run_task(text).risks}
