"""확인된 사진, 제보, TBM 일지의 점수를 적립한다."""

import sqlite3

from app.db import team_of

POINTS_CONFIRMED = 10
POINTS_REPORT = 5
POINTS_TBM = 3


def _insert(
    conn: sqlite3.Connection, site_id: int, kind: str, points: int,
    task_id: int | None = None, worker_id: int | None = None,
    item_code: str | None = None,
) -> int:
    """적립 시점의 소속 팀과 작업자를 함께 기록한다."""
    cursor = conn.execute(
        'INSERT INTO score_events '
        '(site_id, task_id, worker_id, team_snapshot, kind, item_code, points) '
        'VALUES (?, ?, ?, ?, ?, ?, ?)',
        (site_id, task_id, worker_id, team_of(conn, worker_id), kind, item_code, points),
    )
    return cursor.lastrowid


def award_evidence(
    conn: sqlite3.Connection, *, site_id: int, task_id: int,
    item_code: str, result: str, worker_id: int | None = None,
) -> int:
    """확인된 사진 증빙을 작업의 항목당 한 번만 적립한다."""
    if result != 'confirmed':
        return 0
    exists = conn.execute(
        "SELECT 1 FROM score_events WHERE kind = 'evidence' "
        'AND task_id = ? AND item_code = ?',
        (task_id, item_code),
    ).fetchone()
    if exists:
        return 0
    _insert(conn, site_id, 'evidence', POINTS_CONFIRMED, task_id, worker_id, item_code)
    return POINTS_CONFIRMED


def award_report(
    conn: sqlite3.Connection, *, site_id: int, worker_id: int | None = None,
) -> int:
    """위험·아차사고 제보는 횟수 제한 없이 항상 적립한다."""
    _insert(conn, site_id, 'report', POINTS_REPORT, worker_id=worker_id)
    return POINTS_REPORT


def award_tbm(
    conn: sqlite3.Connection, *, site_id: int, task_id: int,
    worker_id: int | None = None,
) -> int:
    """TBM 일지 점수는 작업당 한 번만 적립한다."""
    exists = conn.execute(
        "SELECT 1 FROM score_events WHERE kind = 'tbm' AND task_id = ?",
        (task_id,),
    ).fetchone()
    if exists:
        return 0
    _insert(conn, site_id, 'tbm', POINTS_TBM, task_id, worker_id)
    return POINTS_TBM
