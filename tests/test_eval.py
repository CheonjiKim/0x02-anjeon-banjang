import pytest

from app.tracing import read_traces, trace_run


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
