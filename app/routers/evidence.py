"""사진 증빙 저장과 판정 API다."""

from pathlib import Path
import uuid
import sqlite3

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status

from app.db import get_db
from app.routers.tasks import load_task
from app.schemas import ChecklistItem, EvidenceOut
from app.workflows import run_evidence
from scoring import award_evidence


router = APIRouter(prefix='/api/evidence', tags=['evidence'])
RESULTS = {None, 'confirmed', 'not_visible', 'uncertain'}
SCENARIOS = {None, '', 'verify_reject', 'judge_fail'}


@router.post('', response_model=EvidenceOut, status_code=status.HTTP_201_CREATED)
async def create_evidence(
    request: Request,
    task_id: int = Form(...), item_code: str = Form(...), photo: UploadFile = File(...),
    worker_id: int = Form(1), forced_result: str | None = Form(None), scenario: str | None = Form(None),
    conn: sqlite3.Connection = Depends(get_db),
):
    task = load_task(conn, task_id)
    item = next((item for item in task.checklist if item.code == item_code), None)
    if item is None:
        raise HTTPException(status_code=404, detail='작업 또는 항목을 찾을 수 없어요')
    if forced_result not in RESULTS:
        raise HTTPException(status_code=422, detail='forced_result 값이 올바르지 않아요')
    if scenario not in SCENARIOS:
        raise HTTPException(status_code=422, detail='scenario 값이 올바르지 않아요')
    content = await photo.read()
    suffix = Path(photo.filename or '').suffix or '.jpg'
    path = Path(request.app.state.upload_dir) / f'{uuid.uuid4().hex}{suffix}'
    path.write_bytes(content)
    result = run_evidence(item, content, forced=forced_result, scenario=scenario or None, task_id=task_id)
    cursor = conn.execute(
        'INSERT INTO evidence_photos(task_id, item_code, path, result, observed, retake_hint, run_id) '
        'VALUES (?, ?, ?, ?, ?, ?, ?)',
        (task_id, item_code, str(path), result.judgement.result, result.judgement.observed,
         result.judgement.retake_hint, result.run_id),
    )
    row = conn.execute('SELECT site_id, worker_id FROM tasks WHERE id = ?', (task_id,)).fetchone()
    points = award_evidence(conn, site_id=row['site_id'], task_id=task_id, item_code=item_code,
                            result=result.judgement.result, worker_id=worker_id or row['worker_id'] or 1)
    return EvidenceOut(id=cursor.lastrowid, task_id=task_id, item_code=item_code, points=points,
                       run_id=result.run_id, first_result=result.first.result, verified=result.verified,
                       **result.judgement.model_dump())
