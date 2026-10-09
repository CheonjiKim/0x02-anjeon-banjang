"""현장의 참여 연속 기록과 무사고 기록을 별도로 계산한다."""

from datetime import date, timedelta
import sqlite3

from app.schemas import StreakOut

HISTORY_DAYS = 14


def _d(value: str) -> date:
    """현지 시각 문자열의 앞 열 글자를 날짜로 읽는다."""
    return date.fromisoformat(value[:10])


def active_dates(conn: sqlite3.Connection, site_id: int = 1, worker_id: int | None = None) -> set[date]:
    """해당 현장에서 점수 이벤트나 TBM 일지가 있는 날짜를 모은다."""
    if worker_id is not None:
        rows = conn.execute(
            'SELECT created_at FROM score_events WHERE site_id = ? AND worker_id = ?',
            (site_id, worker_id),
        ).fetchall()
        return {_d(row['created_at']) for row in rows}
    rows = conn.execute(
        'SELECT created_at FROM score_events WHERE site_id = ? '
        'UNION SELECT tbm_logs.created_at FROM tbm_logs '
        'JOIN tasks ON tasks.id = tbm_logs.task_id WHERE tasks.site_id = ?',
        (site_id, site_id),
    ).fetchall()
    return {_d(row['created_at']) for row in rows}


def participation_days(
    conn: sqlite3.Connection, site_id: int = 1, today: date | None = None,
    *, worker_id: int | None = None,
) -> int:
    """오늘 또는 어제부터 거꾸로 이어진 참여 날짜 수를 센다."""
    today = today if today is not None else date.today()
    recorded = active_dates(conn, site_id, worker_id)
    current = today if today in recorded else today - timedelta(days=1)
    days = 0
    while current in recorded:
        days += 1
        current -= timedelta(days=1)
    return days


def streaks(
    conn: sqlite3.Connection, site_id: int = 1, today: date | None = None,
    *, worker_id: int | None = None,
) -> list[StreakOut]:
    """참여 연속 기록과 무사고 기록을 화면용 모델로 반환한다."""
    return [
        StreakOut(
            kind='participation', days=participation_days(conn, site_id, today, worker_id=worker_id),
            label='연속 점검 기록',
        ),
        StreakOut(
            kind='incident_free', days=incident_free_days(conn, site_id, today),
            label='무사고 기록',
        ),
    ]


def breaking_incidents(conn: sqlite3.Connection, site_id: int = 1) -> list[date]:
    """보고와 후속 조치가 모두 끝나지 않은 사고 날짜를 최신순으로 읽는다."""
    rows = conn.execute(
        'SELECT occurred_on FROM incidents WHERE site_id = ? '
        'AND NOT (reported = 1 AND follow_up_done = 1) ORDER BY occurred_on DESC',
        (site_id,),
    ).fetchall()
    return [_d(row['occurred_on']) for row in rows]


def site_age_days(
    conn: sqlite3.Connection, site_id: int = 1, today: date | None = None,
) -> int:
    """현장의 첫 작업 날짜부터 오늘까지의 일수를 센다."""
    today = today if today is not None else date.today()
    row = conn.execute(
        'SELECT MIN(created_at) AS first_created_at FROM tasks WHERE site_id = ?',
        (site_id,),
    ).fetchone()
    if row['first_created_at'] is None:
        return 0
    return max((today - _d(row['first_created_at'])).days + 1, 0)


def incident_free_days(
    conn: sqlite3.Connection, site_id: int = 1, today: date | None = None,
) -> int:
    """보고·후속 조치를 마친 사고는 기록을 유지하고 현장 나이를 넘지 않는다."""
    today = today if today is not None else date.today()
    incidents = breaking_incidents(conn, site_id)
    if incidents:
        return min(max((today - incidents[0]).days, 0), site_age_days(conn, site_id, today))
    return site_age_days(conn, site_id, today)


def history(
    conn: sqlite3.Connection, site_id: int = 1, today: date | None = None,
    *, worker_id: int | None = None,
) -> list[dict]:
    """최근 14일의 실제 참여 여부를 오래된 날부터 반환한다."""
    today = today if today is not None else date.today()
    recorded = active_dates(conn, site_id, worker_id)
    return [
        {'date': day.isoformat(), 'recorded': day in recorded, 'today': day == today}
        for offset in range(HISTORY_DAYS - 1, -1, -1)
        for day in [today - timedelta(days=offset)]
    ]
