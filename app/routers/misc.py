"""할 일, 점수, 제보와 현장 기록 API다."""

from datetime import date
import json
from pathlib import Path
import sqlite3

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status

from app.db import get_db, team_of
from app.routers.tasks import _checklist, load_task
from app.schemas import EvidenceOut, IncidentIn, ScoresOut, TbmIn, TbmLatestOut, TbmOut, TodoOut, WorkerFormIn, WorkerFormOut
from app.workflows import run_tbm
from scoring import award_report, award_tbm, history, stamps_for, streaks, team_ranking, worker_ranking


router = APIRouter(prefix='/api', tags=['misc'])
CONDITION_TODOS = {
    'work': '작업 종류 확인', 'height': '작업 높이 확인', 'flammable': '가연물 확인',
    'ventilation': '환기 확인', 'nearby_people': '주변 인원 확인', 'place': '작업 장소 확인',
}


@router.get('/todos', response_model=list[TodoOut])
def todos(task_id: int, conn: sqlite3.Connection = Depends(get_db)):
    task = load_task(conn, task_id)
    latest = {}
    for row in conn.execute('SELECT * FROM evidence_photos WHERE task_id = ? ORDER BY id', (task_id,)):
        latest[row['item_code']] = row
    out = []
    for item in task.checklist:
        photo = latest.get(item.code)
        if photo is not None and photo['result'] != 'confirmed' and not item.resolved:
            review = conn.execute('SELECT action, reason FROM evidence_reviews WHERE evidence_id = (SELECT id FROM evidence_photos WHERE task_id = ? AND item_code = ? ORDER BY id DESC LIMIT 1) ORDER BY id DESC LIMIT 1', (task_id, item.code)).fetchone()
            out.append(TodoOut(id=f'ev-{item.code}', kind=photo['result'], title=item.title,
                               detail=(f"관리자 조치: {review['action']} — {review['reason']}" if review else photo['retake_hint']), observed=photo['observed'], level=item.level,
                               photo_url=f"/api/uploads/{Path(photo['path']).name}", item_code=item.code))
    for key, title in CONDITION_TODOS.items():
        if getattr(task.conditions, key) == '알 수 없음':
            out.append(TodoOut(id=f'cond-{key}', kind='condition', title=title,
                               detail='조건을 알 수 없어 필수로 처리 중', level='required', cond_key=key))
    return out


@router.get('/evidence/review-queue')
def evidence_review_queue(conn: sqlite3.Connection = Depends(get_db)):
    rows = conn.execute("SELECT * FROM evidence_photos WHERE result <> 'confirmed' ORDER BY id DESC").fetchall()
    out = []
    seen = set()
    for row in rows:
        if row['id'] in seen:
            continue
        seen.add(row['id'])
        item = next((entry for entry in _checklist(conn, row['task_id']) if entry.code == row['item_code']), None)
        if item is None:
            continue
        reviews = [dict(review) for review in conn.execute('SELECT * FROM evidence_reviews WHERE evidence_id = ? ORDER BY id', (row['id'],))]
        out.append({'id': row['id'], 'task_id': row['task_id'], 'item_code': row['item_code'],
                    'title': item.title, 'result': row['result'], 'observed': row['observed'],
                    'retake_hint': row['retake_hint'], 'photo_url': f"/api/uploads/{Path(row['path']).name}",
                    'reviews': reviews})
    return out


@router.get('/scores', response_model=ScoresOut)
def scores(site_id: int = 1, worker_id: int = 1, conn: sqlite3.Connection = Depends(get_db)):
    rows = conn.execute('SELECT * FROM score_events WHERE site_id = ? ORDER BY id DESC', (site_id,)).fetchall()
    events = [dict(row) for row in rows]
    return ScoresOut(total=sum(row['points'] for row in rows), events=events, streaks=streaks(conn, site_id),
                     team_ranking=team_ranking(conn, site_id, team_of(conn, worker_id)),
                     worker_ranking=worker_ranking(conn, site_id, worker_id),
                     stamps=stamps_for(conn, worker_id, site_id), history=history(conn, site_id))


@router.post('/reports', status_code=status.HTTP_201_CREATED)
def report(site_id: int = 1, worker_id: int = 1, conn: sqlite3.Connection = Depends(get_db)):
    return {'points': award_report(conn, site_id=site_id, worker_id=worker_id)}


@router.post('/incidents', status_code=status.HTTP_201_CREATED)
def incident(payload: IncidentIn, conn: sqlite3.Connection = Depends(get_db)):
    occurred_on = payload.occurred_on or date.today().isoformat()
    cursor = conn.execute('INSERT INTO incidents(site_id, worker_id, note, occurred_on) VALUES (?, ?, ?, ?)',
                          (payload.site_id, payload.worker_id, payload.note, occurred_on))
    points = award_report(conn, site_id=payload.site_id, worker_id=payload.worker_id)
    return {'id': cursor.lastrowid, 'points': points, 'streaks': [item.model_dump() for item in streaks(conn, payload.site_id)]}


@router.get('/incidents')
def incidents(conn: sqlite3.Connection = Depends(get_db)):
    return [dict(row) for row in conn.execute('SELECT * FROM incidents ORDER BY id DESC')]


@router.post('/incidents/{incident_id}/follow-up')
def incident_follow_up(incident_id: int, conn: sqlite3.Connection = Depends(get_db)):
    row = conn.execute('SELECT site_id FROM incidents WHERE id = ?', (incident_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail='사고 기록을 찾을 수 없어요')
    conn.execute('UPDATE incidents SET follow_up_done = 1 WHERE id = ?', (incident_id,))
    return {'id': incident_id, 'streaks': [item.model_dump() for item in streaks(conn, row['site_id'])]}


@router.post('/tbm', response_model=TbmOut, status_code=status.HTTP_201_CREATED)
def tbm(payload: TbmIn, conn: sqlite3.Connection = Depends(get_db)):
    task = load_task(conn, payload.task_id)
    spoken = [payload.transcript] if payload.transcript.strip() else payload.points
    result = run_tbm(spoken, _checklist(conn, payload.task_id), task_id=payload.task_id)
    cursor = conn.execute('INSERT INTO tbm_logs(task_id, points, attendees, memo, transcript) VALUES (?, ?, ?, ?, ?)',
                          (payload.task_id, json.dumps(payload.points, ensure_ascii=False), payload.attendees, payload.memo, payload.transcript))
    row = conn.execute('SELECT site_id, worker_id FROM tasks WHERE id = ?', (payload.task_id,)).fetchone()
    award_tbm(conn, site_id=row['site_id'], task_id=payload.task_id, worker_id=row['worker_id'] or 1)
    return TbmOut(id=cursor.lastrowid, missing=result.missing, run_id=result.run_id)


@router.get('/tbm/latest', response_model=TbmLatestOut)
def latest_tbm(task_id: int, conn: sqlite3.Connection = Depends(get_db)):
    task = load_task(conn, task_id)
    row = conn.execute('SELECT * FROM tbm_logs WHERE task_id = ? ORDER BY id DESC LIMIT 1', (task_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail='저장된 TBM이 없습니다.')
    spoken = [row['transcript']] if row['transcript'].strip() else json.loads(row['points'])
    result = run_tbm(spoken, _checklist(conn, task_id), task_id=task.id)
    return TbmLatestOut(id=row['id'], task_id=task_id, transcript=row['transcript'], memo=row['memo'],
                        attendees=row['attendees'], missing=result.missing, created_at=row['created_at'])


@router.post('/worker-forms', status_code=status.HTTP_201_CREATED)
def worker_form(payload: WorkerFormIn, conn: sqlite3.Connection = Depends(get_db)):
    task = load_task(conn, payload.task_id)
    if not task.close_requested:
        raise HTTPException(status_code=409, detail='이 작업은 마감 보고를 요청하지 않았습니다.')
    cursor = conn.execute('INSERT INTO worker_forms(task_id, understood, risk_note, ppe_worn, report_text) VALUES (?, ?, ?, ?, ?)',
                          (payload.task_id, payload.understood, payload.risk_note, payload.ppe_worn, payload.report_text))
    return {'id': cursor.lastrowid}


@router.post('/worker-forms/{form_id}/photo', response_model=WorkerFormOut)
async def worker_form_photo(form_id: int, request: Request, photo: UploadFile = File(...), conn: sqlite3.Connection = Depends(get_db)):
    row = conn.execute('SELECT * FROM worker_forms WHERE id = ?', (form_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail='마감 보고를 찾을 수 없습니다.')
    content = await photo.read()
    if not content:
        raise HTTPException(status_code=422, detail='비어 있는 사진입니다.')
    suffix = Path(photo.filename or '').suffix or '.jpg'
    path = Path(request.app.state.upload_dir) / f'closeout-{form_id}{suffix}'
    path.write_bytes(content)
    conn.execute('UPDATE worker_forms SET photo_path = ? WHERE id = ?', (str(path), form_id))
    return _worker_form_out(conn, form_id)


@router.get('/worker-forms', response_model=list[WorkerFormOut])
def worker_forms(task_id: int | None = None, conn: sqlite3.Connection = Depends(get_db)):
    query = 'SELECT * FROM worker_forms'
    args = () if task_id is None else (task_id,)
    if task_id is not None:
        query += ' WHERE task_id = ?'
    query += ' ORDER BY id DESC'
    return [_worker_form_out(conn, row['id']) for row in conn.execute(query, args)]


@router.post('/worker-forms/{form_id}/evidence', response_model=EvidenceOut, status_code=status.HTTP_201_CREATED)
def review_closeout_photo(form_id: int, item_code: str = Form(...), conn: sqlite3.Connection = Depends(get_db)):
    row = conn.execute('SELECT * FROM worker_forms WHERE id = ?', (form_id,)).fetchone()
    if row is None or not row['photo_path']:
        raise HTTPException(status_code=404, detail='첨부 사진이 있는 마감 보고를 찾을 수 없습니다.')
    task = load_task(conn, row['task_id'])
    item = next((entry for entry in task.checklist if entry.code == item_code), None)
    if item is None:
        raise HTTPException(status_code=404, detail='체크리스트 항목을 찾을 수 없습니다.')
    from app.workflows import run_evidence
    from scoring import award_evidence
    content = Path(row['photo_path']).read_bytes()
    result = run_evidence(item, content, task_id=task.id)
    cursor = conn.execute('INSERT INTO evidence_photos(task_id, item_code, path, result, observed, retake_hint, run_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
                          (task.id, item_code, row['photo_path'], result.judgement.result, result.judgement.observed, result.judgement.retake_hint, result.run_id))
    task_row = conn.execute('SELECT site_id, worker_id FROM tasks WHERE id = ?', (task.id,)).fetchone()
    points = award_evidence(conn, site_id=task_row['site_id'], task_id=task.id, item_code=item_code, result=result.judgement.result, worker_id=task_row['worker_id'] or 1)
    return EvidenceOut(id=cursor.lastrowid, task_id=task.id, item_code=item_code, points=points, run_id=result.run_id,
                       first_result=result.first.result, verified=result.verified, **result.judgement.model_dump())


@router.get('/tbm-suggestions')
def tbm_suggestions(task_id: int | None = None, conn: sqlite3.Connection = Depends(get_db)):
    query = "SELECT risk_note FROM worker_forms WHERE trim(risk_note) <> ''"
    args = () if task_id is None else (task_id,)
    if task_id is not None:
        query += ' AND task_id = ?'
    return {'suggestions': [row['risk_note'] for row in conn.execute(query + ' ORDER BY id DESC', args)]}


def _worker_form_out(conn: sqlite3.Connection, form_id: int) -> WorkerFormOut:
    row = conn.execute('SELECT * FROM worker_forms WHERE id = ?', (form_id,)).fetchone()
    return WorkerFormOut(id=row['id'], task_id=row['task_id'], report_text=row['report_text'] or '', risk_note=row['risk_note'] or '',
                         photo_url=f"/api/uploads/{Path(row['photo_path']).name}" if row['photo_path'] else None,
                         created_at=row['created_at'])
