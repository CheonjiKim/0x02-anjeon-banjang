import pytest

from app.tracing import read_traces, trace_run
from eval.labels import PhotoLabel, TaskLabel, TbmLabel, _load, load_dataset_meta, load_photos, load_tasks, load_tbm
from eval.metrics import (compare, extraction_accuracy, false_approvals, photo_accuracy,
                          tbm_detection)
from eval.runner import evaluate
from eval.run import main
from app.schemas import Conditions


def test_trace_groups_steps_under_one_run_id():
    with trace_run('task', text='용접') as trace:
        with trace.step('extract', text='용접') as step:
            step.output = {'work': '용접'}
            step.record_usage('mock', 100, 20)
        with trace.step('rules') as step:
            step.output = []
    runs = read_traces()
    assert len(runs) == 1
    assert runs[0]['run_id'] == trace.run_id
    assert [step['name'] for step in runs[0]['steps']] == ['extract', 'rules']
    assert runs[0]['steps'][0]['prompt_tokens'] == 100
    assert runs[0]['steps'][0]['completion_tokens'] == 20
    assert runs[0]['latency_ms'] >= 0
    assert runs[0]['steps'][0]['latency_ms'] >= 0
    assert runs[0]['cost_usd'] == 0


def test_trace_records_failures():
    with pytest.raises(ValueError, match='실패'):
        with trace_run('task') as trace:
            with trace.step('extract'):
                raise ValueError('실패')
    run = read_traces()[0]
    assert 'ValueError' in run['error']
    assert 'ValueError' in run['steps'][0]['error']


def test_trace_does_not_store_photo_bytes():
    with trace_run('evidence') as trace:
        with trace.step('judge', photo=b'x' * 5000):
            pass
    assert read_traces()[0]['steps'][0]['input']['photo'] == {'bytes': 5000}


def test_false_approval_counts_both_sources():
    got = false_approvals([
        {'id': 'p1', 'item_code': 'a', 'label': 'not_visible', 'predicted': 'confirmed'},
        {'id': 'p2', 'item_code': 'a', 'label': 'uncertain', 'predicted': 'uncertain'},
        {'id': 'p3', 'item_code': 'a', 'label': 'confirmed', 'predicted': 'confirmed'},
    ], [{'id': 't1', 'missed_required': ['fire-watch']}])
    assert got['total'] == 2 and got['photo']['count'] == got['checklist_downgrade']['count'] == 1
    assert got['photo']['rate_pct'] == 50.0


def test_photo_accuracy_confusion_matrix():
    got = photo_accuracy([{'label': 'not_visible', 'predicted': 'confirmed'}, {'label': 'confirmed', 'predicted': 'confirmed'}])
    assert got['accuracy_pct'] == 50.0 and got['confusion']['not_visible']['confirmed'] == 1
    assert got['per_class']['not_visible']['recall_pct'] == 0.0


def test_tbm_detection_separates_misses_from_false_alarms():
    got = tbm_detection([{'id': 'm', 'missing': ['a', 'b'], 'predicted': ['a', 'c']}])
    assert (got['recall_pct'], got['missed'], got['false_alarms']) == (50.0, 1, 1)


def test_extraction_accuracy_flags_wrong_values_separately():
    row = {'id': 't', 'fields': {'work': {'correct': True, 'predicted': '용접'}, 'height': {'correct': True, 'predicted': '2층'},
           'flammable': {'correct': False, 'predicted': '없음'}, 'ventilation': {'correct': True, 'predicted': '양호'},
           'nearby_people': {'correct': True, 'predicted': '없음'}, 'place': {'correct': False, 'predicted': '알 수 없음'}}}
    got = extraction_accuracy([row])
    assert got['per_field']['flammable']['wrong_value'] == 1 and got['per_field']['place']['wrong_value'] == 0


def test_team_labels_load_and_meta():
    assert (len(load_tasks()), len(load_photos()), len(load_tbm())) == (31, 7, 10)
    assert load_dataset_meta()['is_sample'] is False
    assert len(load_photos('eval/data/photos_aihub.jsonl')) == 88


def test_loader_reports_bad_line(tmp_path):
    path = tmp_path / 'bad.jsonl'; path.write_text('{"id": "x"}\n', encoding='utf-8')
    with pytest.raises(ValueError, match='1번째 줄'):
        _load(path, TaskLabel)


def test_evaluate_runs_end_to_end(tmp_path):
    tasks = [TaskLabel(id='t', text='2층 용접, 옆에 합판', conditions=Conditions(work='용접·용단', height='2층', flammable='합판'))]
    photos = [PhotoLabel(id='p', item_code='extinguisher', item_title='소화기 비치', label='not_visible', simulate='not_visible')]
    tbms = [TbmLabel(id='m', task_text='2층 용접, 옆에 합판', said=[])]
    got = evaluate(tasks, photos, tbms, trace_dir=tmp_path)
    assert got['counts'] == {'tasks': 1, 'photos': 1, 'tbm': 1}
    assert got['cost']['n_runs'] > 0 and got['false_approvals']['checklist_downgrade']['count'] == 0


def test_simulate_mode_uses_label_value(tmp_path):
    photos = [PhotoLabel(id='p', item_code='extinguisher', item_title='소화기 비치', label='not_visible', simulate='not_visible')]
    got = evaluate([], photos, [], use_simulate=True, trace_dir=tmp_path)
    assert got['photo']['accuracy_pct'] == 100.0 and got['false_approvals']['total'] == 0


def test_baseline_has_more_checklist_false_approvals(tmp_path):
    tasks = load_tasks()
    verify = evaluate(tasks, [], [], trace_dir=tmp_path / 'verify')
    baseline = evaluate(tasks, [], [], variant='single_call', trace_dir=tmp_path / 'baseline')
    assert verify['false_approvals']['checklist_downgrade']['count'] <= baseline['false_approvals']['checklist_downgrade']['count']
    assert compare({'verify': verify, 'single_call': baseline})['rows'][0]['direction'] == '낮을수록 좋음'


def test_verify_reduces_photo_false_approvals(tmp_path):
    photos = load_photos()
    verify = evaluate([], photos, [], use_simulate=True, trace_dir=tmp_path / 'verify')
    plain = evaluate([], photos, [], variant='no_verify', use_simulate=True, trace_dir=tmp_path / 'plain')
    assert verify['false_approvals']['total'] < plain['false_approvals']['total']
    assert verify['flows']['evidence']['llm_calls_max'] == 2 and plain['flows']['evidence']['llm_calls_max'] == 1


def test_failure_types_are_classified(tmp_path):
    got = evaluate([], load_photos(), [], use_simulate=True, trace_dir=tmp_path)['failures']
    assert set(got) == {'false_approval', 'extract_wrong_value', 'extract_missing', 'over_abstain', 'system_error'}
    assert all(value['count'] == len(value['cases']) for value in got.values())


def test_cli_writes_json_report(tmp_path, capsys):
    path = tmp_path / 'report.json'
    assert main(['--compare', '--json', str(path)]) == 0
    report = __import__('json').loads(path.read_text(encoding='utf-8'))
    assert report['dataset']['is_sample'] is False and set(report['results']) == {'verify', 'no_verify', 'single_call'}
    assert report['comparison']['rows'][0]['metric'] == '오승인 건수'
    assert '오승인 건수' in capsys.readouterr().out


def test_cli_without_labels_explains_what_to_do(tmp_path, capsys):
    for name in ['tasks', 'photos', 'tbm']:
        (tmp_path / f'{name}.jsonl').write_text('', encoding='utf-8')
    assert main(['--tasks', str(tmp_path / 'tasks.jsonl'), '--photos', str(tmp_path / 'photos.jsonl'), '--tbm', str(tmp_path / 'tbm.jsonl')]) == 1
    assert '라벨이 없어요' in capsys.readouterr().out
