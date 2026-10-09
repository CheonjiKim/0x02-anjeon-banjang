"""할 일, 점수, 제보와 현장 기록 API다."""

from datetime import date
import json
from pathlib import Path
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from app.db import get_db, team_of
from app.routers.tasks import _checklist, load_task
from app.schemas import IncidentIn, ScoresOut, TbmIn, TbmOut, TodoOut, WorkerFormIn
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
            out.append(TodoOut(id=f'ev-{item.code}', kind=photo['result'], title=item.title,
                               detail=photo['retake_hint'], observed=photo['observed'], level=item.level,
                               photo_url=f"/api/uploads/{Path(photo['path']).name}", item_code=item.code))
    for key, title in CONDITION_TODOS.items():
        if getattr(task.conditions, key) == '알 수 없음':
            out.append(TodoOut(id=f'cond-{key}', kind='condition', title=title,
                               detail='조건을 알 수 없어 필수로 처리 중', level='required', cond_key=key))
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
    return {'id': cursor.lastrowid, 'streaks': [item.model_dump() for item in streaks(conn, payload.site_id)]}


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
    result = run_tbm(payload.points, _checklist(conn, payload.task_id), task_id=payload.task_id)
    cursor = conn.execute('INSERT INTO tbm_logs(task_id, points, attendees, memo) VALUES (?, ?, ?, ?)',
                          (payload.task_id, json.dumps(payload.points, ensure_ascii=False), payload.attendees, payload.memo))
    row = conn.execute('SELECT site_id, worker_id FROM tasks WHERE id = ?', (payload.task_id,)).fetchone()
    award_tbm(conn, site_id=row['site_id'], task_id=payload.task_id, worker_id=row['worker_id'] or 1)
    return TbmOut(id=cursor.lastrowid, missing=result.missing, run_id=result.run_id)


@router.post('/worker-forms', status_code=status.HTTP_201_CREATED)
def worker_form(payload: WorkerFormIn, conn: sqlite3.Connection = Depends(get_db)):
    load_task(conn, payload.task_id)
    cursor = conn.execute('INSERT INTO worker_forms(task_id, understood, risk_note, ppe_worn) VALUES (?, ?, ?, ?)',
                          (payload.task_id, payload.understood, payload.risk_note, payload.ppe_worn))
    return {'id': cursor.lastrowid}
