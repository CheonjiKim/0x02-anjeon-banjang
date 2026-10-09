"""사진 증빙 저장과 판정 API다."""

from pathlib import Path
import uuid
import sqlite3

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status

from app.db import get_db
from app.routers.tasks import load_task
from app.schemas import ChecklistItem, EvidenceOut, EvidenceReviewIn, EvidenceReviewOut
from app.workflows import run_evidence
from scoring import award_evidence


router = APIRouter(prefix='/api/evidence', tags=['evidence'])
RESULTS = {None, 'confirmed', 'not_visible', 'uncertain'}
SCENARIOS = {None, '', 'verify_reject', 'judge_fail', 'judge_timeout', 'verify_empty', 'judge_invalid'}


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
    scenario_alias = {'judge_timeout': 'judge_fail', 'judge_invalid': 'judge_fail', 'verify_empty': 'verify_reject'}
    scenario = scenario_alias.get(scenario, scenario)
    result = run_evidence(item, content, forced=forced_result, scenario=scenario or None, task_id=task_id)
    row = conn.execute('SELECT site_id, worker_id FROM tasks WHERE id = ?', (task_id,)).fetchone()
    owner_id = worker_id or row['worker_id'] or 1
    cursor = conn.execute(
        'INSERT INTO evidence_photos(task_id, item_code, path, result, observed, retake_hint, run_id, worker_id) '
        'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        (task_id, item_code, str(path), result.judgement.result, result.judgement.observed,
         result.judgement.retake_hint, result.run_id, owner_id),
    )
    points = award_evidence(conn, site_id=row['site_id'], task_id=task_id, item_code=item_code,
                            result=result.judgement.result, worker_id=owner_id)
    return EvidenceOut(mode=result.mode, id=cursor.lastrowid, task_id=task_id, item_code=item_code, points=points,
                       run_id=result.run_id, first_result=result.first.result, verified=result.verified,
                       **result.judgement.model_dump())


@router.get('/task/{task_id}')
def task_evidence(task_id: int, worker_id: int, conn: sqlite3.Connection = Depends(get_db)):
    task = load_task(conn, task_id)
    if task.worker_id != worker_id:
        raise HTTPException(status_code=403, detail='배정된 작업자만 사진을 확인할 수 있습니다.')
    rows = conn.execute(
        'SELECT e.* FROM evidence_photos e JOIN '
        '(SELECT item_code, MAX(id) AS latest_id FROM evidence_photos '
        'WHERE task_id = ? AND worker_id = ? GROUP BY item_code) latest ON latest.latest_id = e.id '
        'ORDER BY e.id', (task_id, worker_id),
    ).fetchall()
    return [{'id': row['id'], 'item_code': row['item_code'], 'result': row['result'],
             'photo_url': f"/api/uploads/{Path(row['path']).name}"} for row in rows]


@router.get('/{evidence_id}/reviews', response_model=list[EvidenceReviewOut])
def evidence_reviews(evidence_id: int, conn: sqlite3.Connection = Depends(get_db)):
    if conn.execute('SELECT 1 FROM evidence_photos WHERE id = ?', (evidence_id,)).fetchone() is None:
        raise HTTPException(status_code=404, detail='사진 증빙을 찾을 수 없습니다.')
    return [dict(row) for row in conn.execute('SELECT * FROM evidence_reviews WHERE evidence_id = ? ORDER BY id', (evidence_id,))]


@router.post('/{evidence_id}/reviews', response_model=EvidenceReviewOut, status_code=status.HTTP_201_CREATED)
def review_evidence(evidence_id: int, payload: EvidenceReviewIn, conn: sqlite3.Connection = Depends(get_db)):
    if not payload.reason.strip():
        raise HTTPException(status_code=422, detail='조치 사유를 입력해 주세요.')
    evidence = conn.execute('SELECT * FROM evidence_photos WHERE id = ?', (evidence_id,)).fetchone()
    if evidence is None:
        raise HTTPException(status_code=404, detail='사진 증빙을 찾을 수 없습니다.')
    if evidence['result'] == 'confirmed' and payload.action == 'confirmed_by_manager':
        raise HTTPException(status_code=409, detail='이미 자동 확인된 사진은 관리자 확인 점수를 중복 부여하지 않습니다.')
    if conn.execute('SELECT 1 FROM evidence_reviews WHERE evidence_id = ? AND action = ?',
                    (evidence_id, payload.action)).fetchone():
        raise HTTPException(status_code=409, detail='이미 저장된 동일 조치입니다.')
    conn.execute('INSERT INTO evidence_reviews(evidence_id, action, reason, reviewer) VALUES (?, ?, ?, ?)',
                 (evidence_id, payload.action, payload.reason.strip(), payload.reviewer.strip() or '관리자'))
    points = 0
    if payload.action == 'confirmed_by_manager':
        task = conn.execute('SELECT site_id, worker_id FROM tasks WHERE id = ?', (evidence['task_id'],)).fetchone()
        points = award_evidence(conn, site_id=task['site_id'], task_id=evidence['task_id'],
                                item_code=evidence['item_code'], result='confirmed', worker_id=evidence['worker_id'] or task['worker_id'] or 1)
        conn.execute('UPDATE evidence_photos SET result = \'confirmed\' WHERE id = ?', (evidence_id,))
    else:
        points = 0
    row = conn.execute('SELECT * FROM evidence_reviews WHERE evidence_id = ? ORDER BY id DESC LIMIT 1', (evidence_id,)).fetchone()
    return EvidenceReviewOut(**dict(row))
