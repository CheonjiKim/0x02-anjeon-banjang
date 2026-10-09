import pytest
from pydantic import ValidationError

from app import schemas as s


def test_conditions_contract():
    keys = ['work', 'height', 'flammable', 'ventilation', 'nearby_people', 'place']
    assert list(s.Conditions.model_fields) == keys
    assert s.Conditions().model_dump() == dict.fromkeys(keys, '알 수 없음')
    assert s.Conditions(work='용접·용단').unknown_keys() == keys[1:]
    assert s.ConditionsPatch().model_dump() == dict.fromkeys(keys)
    assert s.TaskIn(text='용접').model_dump() == {'text': '용접', 'site_id': 1, 'worker_id': 1}


def test_rule_and_photo_contract():
    rule = s.RuleItem(code='a', title='수칙')
    assert rule.base_level == 'recommended'
    assert rule.works == rule.required_when == []
    condition = s.RuleCondition(key='height')
    assert condition.values == [] and condition.unknown_is_required is True
    rule.works.append('용접')
    assert s.RuleItem(code='b', title='수칙').works == []
    item = s.ChecklistItem(code='a', title='수칙', level='required')
    assert item.resolved is False and item.note is None
    task = s.TaskOut(id=1, text='용접', conditions=s.Conditions(), checklist=[item])
    assert task.run_id is None
    for result in ['confirmed', 'not_visible', 'uncertain']:
        evidence = s.EvidenceOut(result=result, observed='관찰', id=1, task_id=1, item_code='a')
        assert isinstance(evidence, s.Judgement)
        assert evidence.points == 0 and evidence.first_result is None and evidence.verified is None
    with pytest.raises(ValidationError):
        s.Judgement(result='approved', observed='관찰')
    with pytest.raises(ValidationError):
        s.ChecklistItem(code='a', title='수칙', level='optional')


def test_score_contract():
    event = s.ScoreEvent(kind='evidence', points=5, worker_id=2, team_snapshot='팀')
    assert event.site_id == 1 and event.id is None and event.task_id is None
    assert event.worker_id == 2 and event.team_snapshot == '팀'
    assert event.item_code is None and event.created_at is None
    for kind in ['participation', 'incident_free']:
        assert s.StreakOut(kind=kind, days=1, label='기록').kind == kind
    assert s.RankRow(name='팀', score=5).me is False
    assert s.StampOut(code='a', title='스탬프', earned=False).count == 0
    scores = s.ScoresOut(total=0, streaks=[], events=[], team_ranking=[], worker_ranking=[], stamps=[], history=[])
    assert scores.total == 0
    assert s.IncidentIn().model_dump() == {'site_id': 1, 'worker_id': 1, 'note': '', 'occurred_on': None}
    with pytest.raises(ValidationError):
        s.ScoreEvent(kind='other', points=1)


def test_api_contract():
    assert s.TodoOut(id='a', kind='condition', title='조건').cond_key is None
    assert s.TbmIn(task_id=1).model_dump() == {'task_id': 1, 'points': [], 'attendees': '', 'memo': ''}
    assert s.TbmOut(id=1).missing == []
    assert s.WorkerFormIn(task_id=1, understood=True, ppe_worn=False).risk_note == ''
    assert s.RiskItem(code='a', hazard='화재', likelihood='상', severity='중', measure='조치').severity == '중'
    with pytest.raises(ValidationError):
        s.WorkerFormIn(task_id=1, understood=True)
    with pytest.raises(ValidationError):
        s.RiskItem(code='a', hazard='화재', likelihood='높음', severity='중', measure='조치')


def test_workflow_contract():
    task = s.TaskResult(run_id='run', conditions=s.Conditions())
    assert task.questions == task.assumed_required == task.checklist == task.risks == []
    task.questions.append('높이?')
    assert s.TaskResult(run_id='other', conditions=s.Conditions()).questions == []
    first = s.Judgement(result='confirmed', observed='관찰')
    final = s.Judgement(result='uncertain', observed='재확인')
    result = s.EvidenceResult(run_id='run', judgement=final, first=first, verified=False)
    assert result.judgement.result == 'uncertain' and result.first.result == 'confirmed'
    assert result.todo is None
    assert s.TodoCard(kind='uncertain', item_code='a', title='확인').detail is None
    assert s.QuestionOut(key='height', text='높이?').options == []
    assert s.TbmResult(run_id='run').missing == []
    with pytest.raises(ValidationError):
        s.TodoCard(kind='condition', item_code='a', title='조건')
