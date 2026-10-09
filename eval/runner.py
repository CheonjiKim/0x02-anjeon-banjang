"""라벨로 화면과 같은 워크플로우를 실행한다."""

import os
from pathlib import Path
import tempfile

from app.schemas import ChecklistItem, UNKNOWN
from app.tracing import read_traces
from app.workflows import run_evidence, run_task, run_tbm
from eval.baselines import single_call
from eval.metrics import (cost_and_latency, extraction_accuracy, failure_types,
                          false_approvals, per_flow, photo_accuracy, tbm_detection)

VARIANTS = {'verify': '지금 구조: 1차 판정 + 확인됨일 때만 검증',
            'no_verify': '검증 없음: 1차 판정을 그대로 씀',
            'single_call': "기준선: 검증 없음 + '모르면 필수' 처리도 뺌"}


def _conditions_row(label, got, checklist):
    fields = {key: {'expected': expected, 'predicted': getattr(got, key), 'correct': expected == getattr(got, key)}
              for key, expected in label.conditions.model_dump().items()}
    levels = {item.code: item.level for item in checklist}
    return {'id': label.id, 'text': label.text, 'fields': fields,
            'missed_required': [code for code in label.required if levels.get(code) == 'recommended' or code not in levels],
            'unknown_predicted': [key for key, value in got.model_dump().items() if value == UNKNOWN]}


def run_tasks(labels, *, baseline=False):
    rows = []
    for label in labels:
        got, checklist = single_call(label.text) if baseline else (lambda result: (result.conditions, result.checklist))(run_task(label.text))
        rows.append(_conditions_row(label, got, checklist))
    return rows


def run_photos(labels, *, use_simulate=False, verify=True):
    rows = []
    for label in labels:
        data = Path(label.path).read_bytes() if label.path and Path(label.path).exists() else b''
        forced = label.simulate if use_simulate else None
        scenario = 'verify_reject' if use_simulate and label.simulate_verify is False else None
        result = run_evidence(ChecklistItem(code=label.item_code, title=label.item_title, level='required'), data,
                              forced=forced, scenario=scenario, verify=verify)
        rows.append({'id': label.id, 'item_code': label.item_code, 'label': label.label,
                     'predicted': result.judgement.result, 'first': result.first.result,
                     'attack': label.attack, 'observed': result.judgement.observed, 'photo_missing': not bool(data)})
    return rows


def run_tbms(labels):
    rows = []
    for label in labels:
        task = run_task(label.task_text)
        result = run_tbm(label.said, task.checklist)
        rows.append({'id': label.id, 'missing': label.missing, 'predicted': [item.code for item in result.missing]})
    return rows


def evaluate(tasks, photos, tbms, *, variant='verify', use_simulate=False, trace_dir=None):
    if variant not in VARIANTS:
        raise ValueError(f'모르는 변형: {variant}')
    previous = os.environ.get('BANJANG_TRACE_DIR')
    directory = str(trace_dir or tempfile.mkdtemp(prefix='banjang-eval-'))
    os.environ['BANJANG_TRACE_DIR'] = directory
    try:
        task_rows = run_tasks(tasks, baseline=variant == 'single_call')
        photo_rows = run_photos(photos, use_simulate=use_simulate, verify=variant == 'verify')
        tbm_rows = run_tbms(tbms)
        traces = read_traces(directory)
    finally:
        if previous is None: os.environ.pop('BANJANG_TRACE_DIR', None)
        else: os.environ['BANJANG_TRACE_DIR'] = previous
    return {'variant': variant, 'variant_label': VARIANTS[variant], 'counts': {'tasks': len(tasks), 'photos': len(photos), 'tbm': len(tbms)},
            'false_approvals': false_approvals(photo_rows, task_rows), 'extraction': extraction_accuracy(task_rows),
            'photo': photo_accuracy(photo_rows), 'tbm': tbm_detection(tbm_rows), 'cost': cost_and_latency(traces),
            'flows': per_flow(traces), 'failures': failure_types(task_rows, photo_rows, traces),
            'rows': {'tasks': task_rows, 'photos': photo_rows, 'tbm': tbm_rows}, 'trace_dir': directory}
