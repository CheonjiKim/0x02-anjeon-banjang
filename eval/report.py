"""평가 결과를 사람이 읽는 텍스트로 렌더링한다."""

SAMPLE_BANNER = ['#' * 64, '##  뼈대 점검용 샘플 — 성능 수치 아님', '##  라벨이 샘플이라 아래 숫자는 평가 틀이 도는지만 보여 준다.', '#' * 64]


def _number(value):
    if value is None: return '-'
    return f'{value:,}' if isinstance(value, int) else str(value)


def render_one(result):
    counts = result['counts']
    false = result['false_approvals']
    lines = [f"== [{result['variant']}] {result['variant_label']}  작업 {counts['tasks']}건 · 사진 {counts['photos']}장 · TBM {counts['tbm']}건",
             f"① 오승인 건수: {false['total']}건   ← 가장 먼저 보는 숫자 (낮을수록 좋음)",
             f"  사진 {false['photo']['count']}건 / 필수→권장 {false['checklist_downgrade']['count']}건",
             '실패 유형']
    lines.extend(f"  {value['label']}: {value['count']}" for value in result['failures'].values())
    lines.extend(['② 작업·조건 추출 정확도', f"  전체: {_number(result['extraction']['overall_accuracy_pct'])}%",
                  '③ 사진 분류 정확도', f"  전체: {_number(result['photo']['accuracy_pct'])}%",
                  '④ TBM 누락 항목 탐지율', f"  재현율: {_number(result['tbm']['recall_pct'])}%", '⑤ 흐름별 건당 비용·응답 시간'])
    for kind, flow in result['flows'].items():
        cost = '미산정(단가·사용량 확인 필요)' if flow['cost_usd_per_run'] is None else f"${flow['cost_usd_per_run']} (추정)"
        lines.append(f"  {kind}: 비용 {cost}, p50 {flow['latency_ms_p50']}ms, LLM {flow['llm_calls_per_run']}회")
    return lines


def render(dataset, results, comparison=None):
    lines = SAMPLE_BANNER.copy() if dataset.get('is_sample') else []
    lines += [f"데이터 출처: {dataset.get('source', '-')}", f"사진 판정: {dataset.get('photo_judge', '-')}"]
    for result in results.values(): lines += [''] + render_one(result)
    if comparison:
        lines += ['', '== 변형 비교 (verify = 지금 구조)']
        for row in comparison['rows']:
            lines.append(f"{row['metric']} [{row['direction']}] " + ' | '.join(f"{name}: {_number(value)}" for name, value in row['values'].items()))
    if dataset.get('is_sample'): lines += ['', SAMPLE_BANNER[1]]
    return '\n'.join(lines)
