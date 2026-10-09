"""평가 실행 결과를 화면에 전달하는 읽기 전용 API다."""

import json
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException


ROOT = Path(__file__).resolve().parents[2]
router = APIRouter(prefix='/api/eval', tags=['eval'])


def eval_out_dir() -> Path:
    """환경 설정이 없으면 저장소의 평가 결과 폴더를 사용한다."""
    return Path(os.getenv('BANJANG_EVAL_OUT', ROOT / 'eval' / 'out'))


@router.get('/latest')
def latest():
    """가장 최근 JSON 보고서에서 화면에 필요한 요약만 반환한다."""
    reports = list(eval_out_dir().glob('*.json'))
    if not reports:
        raise HTTPException(status_code=404, detail='평가 결과가 없어요. python -m eval.run --compare --json 을 먼저 돌려 주세요')
    report = max(reports, key=lambda path: path.stat().st_mtime)
    payload = json.loads(report.read_text(encoding='utf-8'))
    for result in payload.get('results', {}).values():
        result.pop('rows', None)
        result.pop('trace_dir', None)
    payload['file'] = report.name
    return payload
