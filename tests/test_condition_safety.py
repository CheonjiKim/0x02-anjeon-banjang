import pytest
from fastapi.testclient import TestClient
from app.main import create_app

from app.pipeline.extract import extract_with_spans
from app.pipeline.normalize import normalize
from app.schemas import UNKNOWN, Conditions
from app.workflows import run_task


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(str(tmp_path / 'safety.db'), str(tmp_path / 'uploads'))) as test_client:
        yield test_client


@pytest.mark.parametrize(('text', 'flammable', 'ventilation', 'people'), [
    ('5층 용접, 환기 상태 불량', UNKNOWN, '불량', UNKNOWN),
    ('5층 용접, 주변 사람 없음', UNKNOWN, UNKNOWN, '없음'),
    ('용접, 주변에 사람 많고 환기 미흡', UNKNOWN, '불량', '있음'),
    ('용접, 환기 안 됨, 가연물 없음', '없음', '불량', UNKNOWN),
    ('용접, 환기 양호, 주변 가연물 없음', '없음', '양호', UNKNOWN),
    ('용접, 환기 확인 필요, 가연물 확인 필요', UNKNOWN, UNKNOWN, UNKNOWN),
    ('용접, 환기 없음, 주변 작업자 없음', UNKNOWN, '불량', '없음'),
])
def test_condition_context(text, flammable, ventilation, people):
    result = run_task(text)
    assert result.conditions.flammable == flammable
    assert result.conditions.ventilation == ventilation
    assert result.conditions.nearby_people == people
    if flammable == UNKNOWN:
        assert next(item for item in result.checklist if item.code == 'fire-watch').level == 'required'


def test_floor_is_not_work_height_or_indoor_place():
    conditions = run_task('5층 용접').conditions
    assert conditions.floor == '5층'
    assert conditions.height == conditions.place == UNKNOWN


def test_fabricated_lowering_span_cannot_borrow_unrelated_no():
    text = '용접, 주변 사람 없음'
    candidate = Conditions(work='용접·용단', flammable='없음')
    normalized, dropped = normalize(candidate, {'flammable': '없음'}, text)
    assert normalized.flammable == UNKNOWN
    assert 'flammable' in dropped


def test_welding_contextual_risks_and_post_work_rule():
    result = run_task('5층 용접, 주변에 사람 많고')
    assert 'welding-fall' not in {risk.code for risk in result.risks}
    assert 'welding-bystander' in {risk.code for risk in result.risks}
    assert 'work-height-check' in {item.code for item in result.checklist}
    assert next(item for item in result.checklist if item.code == 'post-work-fire-check').level == 'recommended'

    elevated = run_task('용접, 작업 높이 3m, 주변 작업자 있음')
    assert 'welding-fall' in {risk.code for risk in elevated.risks}


def test_lowering_patch_requires_evidence(client):
    task = client.post('/api/tasks', json={'text': '용접, 합판 주변에 있음'}).json()
    url = f"/api/tasks/{task['id']}/conditions"
    assert client.patch(url, json={'flammable': '없음'}).status_code == 422
    updated = client.patch(url, json={'flammable': '없음', 'review_evidence': '현장 가연물 제거 확인'}).json()
    assert updated['condition_changes'][-1]['before_value'] == '합판'
    assert updated['condition_changes'][-1]['after_value'] == '없음'
    assert updated['condition_changes'][-1]['evidence'] == '현장 가연물 제거 확인'


@pytest.mark.parametrize(('field', 'value'), [
    ('height', '10층 건물'), ('floor', '10층 건물'), ('place', '건물'),
    ('ventilation', '좋음'), ('flammable', '모르겠음'),
])
def test_manager_cannot_store_ambiguous_condition_as_confirmed(client, field, value):
    task = client.post('/api/tasks', json={'text': '용접'}).json()
    response = client.patch(f"/api/tasks/{task['id']}/conditions", json={field: value, 'review_evidence': '현장 확인'})
    assert response.status_code == 422
    assert client.get(f"/api/tasks/{task['id']}").json()['conditions'][field] == UNKNOWN


def test_manager_nearby_people_count_is_normalized(client):
    task = client.post('/api/tasks', json={'text': '용접'}).json()
    response = client.patch(f"/api/tasks/{task['id']}/conditions", json={'nearby_people': '일반인 10명'})
    assert response.status_code == 200
    assert response.json()['conditions']['nearby_people'] == '10명'
