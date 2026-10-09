"""오승인을 첫 지표로 두는 평가 지표 계산기다."""

from collections import Counter, defaultdict
from statistics import median

from app.schemas import UNKNOWN


def _pct(n, d):
    return None if not d else round(n / d * 100, 1)


def false_approvals(photo_rows, task_rows):
    photo_cases = [{'id': row['id'], 'item_code': row['item_code'], 'label': row['label']}
                   for row in photo_rows if row['label'] != 'confirmed' and row['predicted'] == 'confirmed']
    downgrade_cases = [{'id': row['id'], 'code': code}
                       for row in task_rows for code in row['missed_required']]
    return {'total': len(photo_cases) + len(downgrade_cases),
            'photo': {'count': len(photo_cases), 'rate_pct': _pct(len(photo_cases), sum(r['label'] != 'confirmed' for r in photo_rows)), 'cases': photo_cases},
            'checklist_downgrade': {'count': len(downgrade_cases), 'cases': downgrade_cases}}


def extraction_accuracy(task_rows):
    fields = {}
    correct_total = total = 0
    for key in ('work', 'height', 'flammable', 'ventilation', 'nearby_people', 'place'):
        rows = [row['fields'][key] for row in task_rows]
        correct = sum(row['correct'] for row in rows)
        fields[key] = {'n': len(rows), 'accuracy_pct': _pct(correct, len(rows)),
                       'wrong_value': sum(not row['correct'] and row['predicted'] != UNKNOWN for row in rows)}
        correct_total += correct
        total += len(rows)
    return {'n_tasks': len(task_rows), 'overall_accuracy_pct': _pct(correct_total, total), 'per_field': fields}


def photo_accuracy(photo_rows):
    classes = ('confirmed', 'not_visible', 'uncertain')
    confusion = {actual: {predicted: 0 for predicted in classes} for actual in classes}
    for row in photo_rows:
        confusion[row['label']][row['predicted']] += 1
    return {'n': len(photo_rows), 'accuracy_pct': _pct(sum(r['label'] == r['predicted'] for r in photo_rows), len(photo_rows)),
            'per_class': {kind: {'n': sum(r['label'] == kind for r in photo_rows),
                                 'recall_pct': _pct(confusion[kind][kind], sum(confusion[kind].values()))} for kind in classes},
            'confusion': confusion}


def tbm_detection(rows):
    expected = {(row['id'], code) for row in rows for code in row['missing']}
    predicted = {(row['id'], code) for row in rows for code in row['predicted']}
    matched = expected & predicted
    return {'n': len(rows), 'recall_pct': _pct(len(matched), len(expected)), 'precision_pct': _pct(len(matched), len(predicted)),
            'missed': len(expected - predicted), 'false_alarms': len(predicted - expected)}


def _summary(values):
    values = sorted(values)
    return {'p50': round(median(values), 2), 'p95': round(values[min(int(len(values) * .95), len(values) - 1)], 2), 'max': round(max(values), 2)} if values else None


def cost_and_latency(traces):
    if not traces:
        return {'n_runs': 0}
    by_step = defaultdict(list)
    for trace in traces:
        for step in trace['steps']:
            by_step[step['name']].append(step)
    return {'n_runs': len(traces), 'latency_ms': _summary([t['latency_ms'] for t in traces]),
            'cost_usd': {'total': round(sum(t['cost_usd'] for t in traces), 8), 'per_run': round(sum(t['cost_usd'] for t in traces) / len(traces), 8)},
            'per_step': {name: {'n': len(steps), 'latency_ms_p50': round(median([s['latency_ms'] for s in steps]), 2), 'cost_usd': round(sum(s['cost_usd'] for s in steps), 8)} for name, steps in by_step.items()},
            'errors': sum(bool(t.get('error')) for t in traces)}


LLM_STEPS = {'extract', 'judge', 'verify'}


def per_flow(traces):
    grouped = defaultdict(list)
    for trace in traces:
        grouped[trace['kind']].append(trace)
    return {kind: {'n': len(rows), 'cost_usd_per_run': round(sum(r['cost_usd'] for r in rows) / len(rows), 8),
                   'latency_ms_p50': round(median([r['latency_ms'] for r in rows]), 2),
                   'latency_ms_p95': _summary([r['latency_ms'] for r in rows])['p95'],
                   'llm_calls_per_run': round(sum(sum(s['name'] in LLM_STEPS for s in r['steps']) for r in rows) / len(rows), 2),
                   'llm_calls_max': max(sum(s['name'] in LLM_STEPS for s in r['steps']) for r in rows)} for kind, rows in grouped.items()}


FAILURE_TYPES = {'false_approval': '오승인: 안전하지 않은데 넘김', 'extract_wrong_value': '틀린 값을 자신 있게 넣음',
                 'extract_missing': '알아야 할 것을 모름(→ 필수로 처리됨)', 'over_abstain': '확인됨인데 판단불가로 넘김',
                 'system_error': '실행 중 실패·대체 경로'}


def failure_types(task_rows, photo_rows, traces):
    cases = {key: [] for key in FAILURE_TYPES}
    for row in task_rows:
        for key, field in row['fields'].items():
            if not field['correct']:
                cases['extract_missing' if field['predicted'] == UNKNOWN else 'extract_wrong_value'].append(f"{row['id']}:{key}")
        cases['false_approval'].extend(f"{row['id']}:{code}" for code in row['missed_required'])
    for row in photo_rows:
        if row['label'] != 'confirmed' and row['predicted'] == 'confirmed': cases['false_approval'].append(row['id'])
        if row['label'] == 'confirmed' and row['predicted'] != 'confirmed': cases['over_abstain'].append(row['id'])
    for trace in traces:
        if trace.get('error') or any(step.get('error') or step.get('meta', {}).get('failure') or step.get('meta', {}).get('fallback') for step in trace['steps']): cases['system_error'].append(f"run:{trace['run_id'][:8]}")
    return {key: {'label': FAILURE_TYPES[key], 'count': len(value), 'cases': value} for key, value in cases.items()}


COMPARE_ROWS = [('오승인 건수', '낮을수록 좋음', ('false_approvals', 'total')), ('  사진 오승인', '낮을수록 좋음', ('false_approvals', 'photo', 'count')), ('  필수→권장 오판', '낮을수록 좋음', ('false_approvals', 'checklist_downgrade', 'count')), ('헛수고(확인됨→판단불가)', '낮을수록 좋음', ('failures', 'over_abstain', 'count')), ('조건 추출 정확도(%)', '높을수록 좋음', ('extraction', 'overall_accuracy_pct')), ('사진 분류 정확도(%)', '높을수록 좋음', ('photo', 'accuracy_pct')), ('TBM 누락 탐지율(%)', '높을수록 좋음', ('tbm', 'recall_pct')), ('사진 1장 LLM 호출 수', '낮을수록 좋음', ('flows', 'evidence', 'llm_calls_per_run')), ('사진 1장 비용(USD)', '낮을수록 좋음', ('flows', 'evidence', 'cost_usd_per_run')), ('작업 1건 비용(USD)', '낮을수록 좋음', ('flows', 'task', 'cost_usd_per_run')), ('사진 1장 응답 p50(ms)', '낮을수록 좋음', ('flows', 'evidence', 'latency_ms_p50'))]


def compare(results):
    def get(value, path):
        for key in path:
            if not isinstance(value, dict) or key not in value: return None
            value = value[key]
        return value
    return {'variants': list(results), 'rows': [{'metric': metric, 'direction': direction, 'values': {name: get(result, path) for name, result in results.items()}} for metric, direction, path in COMPARE_ROWS]}
