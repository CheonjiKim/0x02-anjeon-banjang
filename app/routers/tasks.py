"""작업 입력, 조건 보정, 체크리스트 API다."""

import json
import re
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.db import get_db
from app.pipeline.risk import build_risk_assessment
from app.pipeline.rules import WORK_TYPES
from app.pipeline.normalize import FLAMMABLES, PLACES
from app.schemas import UNKNOWN, ChecklistItem, Conditions, ConditionsPatch, QuestionOut, TaskIn, TaskOut
from app.workflows import CONDITION_QUESTIONS, QUESTION_OPTIONS, run_task


router = APIRouter(prefix='/api/tasks', tags=['tasks'])


class TaskReviewIn(BaseModel):
    action: str
    reason: str = Field(min_length=3)


def _task_state(conditions: Conditions) -> tuple[str, str | None]:
    # The work type selects the rule set. Missing other details remain unknown,
    # so the rules keep conservative required items without blocking the flow.
    if conditions.work == UNKNOWN:
        return 'pending', '작업 종류를 확인해 주세요.'
    return 'ready', None


def _checklist(conn: sqlite3.Connection, task_id: int) -> list[ChecklistItem]:
    rows = conn.execute('SELECT * FROM checklist_items WHERE task_id = ? ORDER BY id', (task_id,)).fetchall()
    return [ChecklistItem(code=row['code'], title=row['title'], source=row['source'], level=row['level'],
                          note=row['note'], resolved=bool(row['resolved']), attached=bool(conn.execute(
                              'SELECT 1 FROM evidence_photos WHERE task_id = ? AND item_code = ? LIMIT 1',
                              (task_id, row['code'])).fetchone())) for row in rows]


def load_task(conn: sqlite3.Connection, task_id: int) -> TaskOut:
    row = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail='작업을 찾을 수 없어요')
    worker = conn.execute('SELECT name FROM workers WHERE id = ?', (row['worker_id'],)).fetchone()
    return TaskOut(worker_id=row['worker_id'], worker_name=worker['name'] if worker else '', created_at=row['created_at'], id=row['id'], text=row['text'], conditions=Conditions(**json.loads(row['conditions'])),
                   checklist=_checklist(conn, task_id), run_id=row['run_id'],
                   close_requested=bool(row['close_requested']), review_status=row['review_status'],
                   review_reason=row['review_reason'], review_action=row['review_action'],
                   review_note=row['review_note'], reviewed_at=row['reviewed_at'],
                   extraction_method=row['extraction_method'], rule_version=row['rule_version'],
                   condition_changes=[dict(change) for change in conn.execute(
                       'SELECT field, before_value, after_value, evidence, created_at FROM condition_changes WHERE task_id = ? ORDER BY id', (task_id,))])


def _pinned(conn: sqlite3.Connection, task_id: int) -> dict[str, str]:
    row = conn.execute('SELECT pinned FROM tasks WHERE id = ?', (task_id,)).fetchone()
    return json.loads(row['pinned'] or '{}') if row else {}


def _store_checklist(conn: sqlite3.Connection, task_id: int, items: list[ChecklistItem]) -> None:
    resolved = {row['code']: row['resolved'] for row in conn.execute(
        'SELECT code, resolved FROM checklist_items WHERE task_id = ?', (task_id,)
    )}
    conn.execute('DELETE FROM checklist_items WHERE task_id = ?', (task_id,))
    conn.executemany(
        'INSERT INTO checklist_items(task_id, code, title, source, level, note, resolved) VALUES (?, ?, ?, ?, ?, ?, ?)',
        [(task_id, item.code, item.title, item.source, item.level, item.note, resolved.get(item.code, 0)) for item in items],
    )


@router.post('', response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskIn, conn: sqlite3.Connection = Depends(get_db)):
    result = run_task(payload.text, site_id=payload.site_id, worker_id=payload.worker_id,
                      scenario=payload.scenario)
    review_status, review_reason = _task_state(result.conditions)
    cursor = conn.execute(
        'INSERT INTO tasks(site_id, worker_id, text, conditions, pinned, run_id, close_requested, review_status, review_reason, extraction_method) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (payload.site_id, payload.worker_id, payload.text, result.conditions.model_dump_json(), '{}', result.run_id, payload.close_requested, review_status, review_reason, result.extraction_method),
    )
    _store_checklist(conn, cursor.lastrowid, result.checklist)
    return load_task(conn, cursor.lastrowid)


class AssignmentIn(BaseModel):
    worker_id: int


@router.get('')
def list_tasks(worker_id: int | None = None, conn: sqlite3.Connection = Depends(get_db)):
    query = 'SELECT id FROM tasks'
    params = ()
    if worker_id is not None:
        query += ' WHERE worker_id = ?'
        params = (worker_id,)
    return [load_task(conn, row['id']) for row in conn.execute(query + ' ORDER BY id DESC', params)]


@router.get('/workers')
def list_workers(conn: sqlite3.Connection = Depends(get_db)):
    return [dict(row) for row in conn.execute('SELECT id, name, team FROM workers WHERE is_foreman = 0 ORDER BY name, id')]


@router.patch('/{task_id}/assignment', response_model=TaskOut)
def assign_worker(task_id: int, payload: AssignmentIn, conn: sqlite3.Connection = Depends(get_db)):
    load_task(conn, task_id)
    worker = conn.execute('SELECT id FROM workers WHERE id = ? AND is_foreman = 0 AND site_id = (SELECT site_id FROM tasks WHERE id = ?)', (payload.worker_id, task_id)).fetchone()
    if worker is None:
        raise HTTPException(status_code=422, detail='현장에 등록된 작업자를 선택해 주세요.')
    conn.execute('UPDATE tasks SET worker_id = ? WHERE id = ?', (payload.worker_id, task_id))
    return load_task(conn, task_id)


@router.get('/review-queue')
def task_review_queue(conn: sqlite3.Connection = Depends(get_db)):
    ids = [row['id'] for row in conn.execute("SELECT id FROM tasks WHERE review_status = 'pending' ORDER BY id DESC")]
    return [load_task(conn, task_id).model_dump() for task_id in ids]


@router.get('/{task_id}', response_model=TaskOut)
def get_task(task_id: int, conn: sqlite3.Connection = Depends(get_db)):
    return load_task(conn, task_id)


@router.get('/{task_id}/checklist', response_model=list[ChecklistItem])
def checklist(task_id: int, conn: sqlite3.Connection = Depends(get_db)):
    load_task(conn, task_id)
    return _checklist(conn, task_id)


@router.get('/{task_id}/risk')
def risk(task_id: int, conn: sqlite3.Connection = Depends(get_db)):
    return build_risk_assessment(load_task(conn, task_id).conditions)


@router.get('/{task_id}/questions', response_model=list[QuestionOut])
def questions(task_id: int, conn: sqlite3.Connection = Depends(get_db)):
    task = load_task(conn, task_id)
    result = run_task(task.text, pinned=_pinned(conn, task_id))
    return [QuestionOut(key=key, text=CONDITION_QUESTIONS[key], options=QUESTION_OPTIONS.get(key, []))
            for key in result.assumed_required]


@router.patch('/{task_id}/conditions', response_model=TaskOut)
def patch_conditions(task_id: int, payload: ConditionsPatch, conn: sqlite3.Connection = Depends(get_db)):
    task = load_task(conn, task_id)
    pinned = _pinned(conn, task_id)
    patch = payload.model_dump(exclude_none=True, exclude={'review_evidence'})
    if not patch:
        return task
    patch = {key: value.strip() or UNKNOWN for key, value in patch.items()}
    if 'work' in patch:
        work = patch['work']
        work = {'용접': '용접·용단', '용단': '용접·용단'}.get(work, work)
        if work not in WORK_TYPES and work != UNKNOWN:
            raise HTTPException(status_code=422, detail='현재는 지원하지 않는 작업 종류입니다. 추후 지원될 예정입니다.')
        patch['work'] = work
    if patch.get('ventilation') == '없음':
        patch['ventilation'] = '불량'
    if 'nearby_people' in patch:
        patch['nearby_people'] = re.sub(r'^(\d+)\s*인$', r'\1명', patch['nearby_people'])
        patch['nearby_people'] = re.sub(r'^(?:일반인|작업자|사람|인원)\s*(\d+)\s*명$', r'\1명', patch['nearby_people'])
    allowed_values = {
        'height': lambda value: re.fullmatch(r'\d+(?:\.\d+)?m|지상', value) is not None,
        'floor': lambda value: re.fullmatch(r'\d+층', value) is not None,
        'flammable': lambda value: value in FLAMMABLES,
        'ventilation': lambda value: value in {'양호', '불량'},
        'nearby_people': lambda value: re.fullmatch(r'\d+명|있음|없음', value) is not None,
        'place': lambda value: value in PLACES,
    }
    hints = {
        'height': '실제 작업 높이는 2m처럼 입력해 주세요. 층수는 작업 층에 입력합니다.',
        'floor': '작업 층은 10층처럼 입력해 주세요.',
        'flammable': '가연물 종류 또는 없음으로 입력해 주세요.',
        'ventilation': '환기 상태는 양호 또는 불량으로 입력해 주세요.',
        'nearby_people': '주변 인원은 있음, 없음 또는 10명처럼 입력해 주세요.',
        'place': '장소 유형은 실내, 외부, 지하 등으로 입력해 주세요.',
    }
    for key, value in patch.items():
        if key in allowed_values and value != getattr(task.conditions, key) and value != UNKNOWN and not allowed_values[key](value):
            raise HTTPException(status_code=422, detail=hints[key])
    lowering = {'flammable': '없음', 'ventilation': '양호', 'nearby_people': '없음', 'height': '지상'}
    changed = [(key, getattr(task.conditions, key), value) for key, value in patch.items()
               if getattr(task.conditions, key) != value]
    if any(lowering.get(key) == after for key, _, after in changed) and not (payload.review_evidence or '').strip():
        raise HTTPException(status_code=422, detail='위험을 낮추는 조건은 현장 확인 근거를 입력해 주세요.')
    pinned.update(patch)
    result = run_task(task.text, site_id=conn.execute('SELECT site_id FROM tasks WHERE id = ?', (task_id,)).fetchone()['site_id'],
                      pinned=pinned)
    review_status, review_reason = _task_state(result.conditions)
    conn.execute('UPDATE tasks SET conditions = ?, pinned = ?, run_id = ?, extraction_method = ?, review_status = ?, review_reason = ?, review_action = NULL, review_note = NULL, reviewed_at = NULL WHERE id = ?',
                 (result.conditions.model_dump_json(), json.dumps(pinned, ensure_ascii=False), result.run_id, result.extraction_method, review_status, review_reason, task_id))
    _store_checklist(conn, task_id, result.checklist)
    for key, before, after in changed:
        conn.execute('INSERT INTO condition_changes(task_id, field, before_value, after_value, evidence) VALUES (?, ?, ?, ?, ?)',
                     (task_id, key, before, after, (payload.review_evidence or '관리자 수정: 확인 근거 미입력').strip()))
    return load_task(conn, task_id)


@router.post('/{task_id}/review', response_model=TaskOut)
def review_task(task_id: int, payload: TaskReviewIn, conn: sqlite3.Connection = Depends(get_db)):
    task = load_task(conn, task_id)
    if task.review_status not in {'pending', 'ready'}:
        raise HTTPException(status_code=409, detail='검토 대기 중인 작업이 아닙니다.')
    if payload.action not in {'conditions_corrected', 'cancelled'}:
        raise HTTPException(status_code=422, detail='지원하지 않는 관리자 조치입니다.')
    if payload.action == 'conditions_corrected' and task.conditions.work == UNKNOWN:
        raise HTTPException(status_code=409, detail='먼저 작업 종류를 확인해 주세요.')
    conn.execute("UPDATE tasks SET review_action = ?, review_note = ?, reviewed_at = datetime('now','localtime'), review_status = ? WHERE id = ?",
                 (payload.action, payload.reason, 'cancelled' if payload.action == 'cancelled' else 'reviewed', task_id))
    return load_task(conn, task_id)


@router.post('/{task_id}/items/{code}/resolve', response_model=TaskOut)
def resolve_item(task_id: int, code: str, conn: sqlite3.Connection = Depends(get_db)):
    load_task(conn, task_id)
    cursor = conn.execute('UPDATE checklist_items SET resolved = 1 WHERE task_id = ? AND code = ?', (task_id, code))
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail='작업 또는 항목을 찾을 수 없어요')
    return load_task(conn, task_id)
