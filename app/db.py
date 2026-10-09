"""SQLite 연결과 기본 현장·작업자 데이터를 준비한다.

점수 이벤트는 worker_id(개인)와 team_snapshot(그 시점 소속 팀)을 함께 들고 있다.
순위는 team_snapshot으로, 스탬프·개인 기록은 worker_id로 집계한다.
"""

from contextlib import closing
from pathlib import Path
import sqlite3

from fastapi import Request

SCHEMA = """
CREATE TABLE IF NOT EXISTS sites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS workers (
    id INTEGER PRIMARY KEY,
    site_id INTEGER NOT NULL REFERENCES sites(id),
    name TEXT NOT NULL,
    team TEXT,
    is_foreman INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    login_id TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'worker')),
    name TEXT NOT NULL,
    team TEXT
);
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY,
    site_id INTEGER NOT NULL REFERENCES sites(id),
    worker_id INTEGER REFERENCES workers(id),
    text TEXT NOT NULL,
    conditions TEXT NOT NULL,
    pinned TEXT,
    run_id TEXT,
    review_status TEXT NOT NULL DEFAULT 'ready',
    review_reason TEXT,
    review_action TEXT,
    review_note TEXT,
    reviewed_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS checklist_items (
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id),
    code TEXT NOT NULL,
    title TEXT NOT NULL,
    source TEXT,
    level TEXT NOT NULL,
    note TEXT,
    resolved INTEGER NOT NULL DEFAULT 0,
    UNIQUE(task_id, code)
);
CREATE TABLE IF NOT EXISTS evidence_photos (
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id),
    item_code TEXT NOT NULL,
    path TEXT NOT NULL,
    result TEXT NOT NULL,
    observed TEXT,
    retake_hint TEXT,
    run_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS evidence_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evidence_id INTEGER NOT NULL REFERENCES evidence_photos(id),
    action TEXT NOT NULL CHECK(action IN ('retake_requested', 'confirmed_by_manager', 'not_confirmed')),
    reason TEXT NOT NULL,
    reviewer TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS score_events (
    id INTEGER PRIMARY KEY,
    site_id INTEGER NOT NULL REFERENCES sites(id),
    task_id INTEGER,
    worker_id INTEGER REFERENCES workers(id),
    team_snapshot TEXT,
    kind TEXT NOT NULL,
    item_code TEXT,
    points INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS tbm_logs (
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id),
    points TEXT NOT NULL,
    attendees TEXT,
    memo TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS worker_forms (
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id),
    understood INTEGER NOT NULL,
    risk_note TEXT,
    ppe_worn INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS incidents (
    id INTEGER PRIMARY KEY,
    site_id INTEGER NOT NULL REFERENCES sites(id),
    worker_id INTEGER REFERENCES workers(id),
    note TEXT,
    occurred_on TEXT NOT NULL,
    reported INTEGER NOT NULL DEFAULT 1,
    follow_up_done INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
"""


def connect(path: str | Path) -> sqlite3.Connection:
    """행 데이터를 이름으로 읽고 외래키를 검사하는 연결을 연다."""
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def init_db(path: str | Path) -> None:
    """테이블을 준비하고 현장이 비어 있을 때만 기본 데이터를 넣는다."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with closing(connect(path)) as conn:
        conn.executescript(SCHEMA)
        # Existing local demo databases predate these columns. SQLite has no
        # portable ADD COLUMN IF NOT EXISTS, so inspect before each migration.
        _add_column(conn, 'tasks', 'close_requested INTEGER NOT NULL DEFAULT 0')
        _add_column(conn, 'tasks', "review_status TEXT NOT NULL DEFAULT 'ready'")
        _add_column(conn, 'tasks', 'review_reason TEXT')
        _add_column(conn, 'tasks', 'review_action TEXT')
        _add_column(conn, 'tasks', 'review_note TEXT')
        _add_column(conn, 'tasks', 'reviewed_at TEXT')
        _add_column(conn, 'tbm_logs', "transcript TEXT NOT NULL DEFAULT ''")
        _add_column(conn, 'worker_forms', "report_text TEXT NOT NULL DEFAULT ''")
        _add_column(conn, 'worker_forms', 'photo_path TEXT')
        if conn.execute('SELECT COUNT(*) FROM sites').fetchone()[0] == 0:
            conn.execute("INSERT INTO sites(id, name) VALUES (1, '기본 현장')")
            conn.executemany(
                'INSERT INTO workers(site_id, name, team, is_foreman) VALUES (?, ?, ?, ?)',
                [(1, '반장', '우리 팀', 1), (1, '김OO', '우리 팀', 0), (1, '박OO', '철골 1팀', 0)],
            )
        if conn.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 0:
            conn.executemany(
                'INSERT INTO users(login_id, password, role, name, team) VALUES (?, ?, ?, ?, ?)',
                [('admin', '1234', 'admin', '김반장', '우리 팀'), ('worker', '1234', 'worker', '김작업', '우리 팀')],
            )
        conn.commit()


def _add_column(conn: sqlite3.Connection, table: str, definition: str) -> None:
    column = definition.split()[0]
    columns = {row['name'] for row in conn.execute(f'PRAGMA table_info({table})')}
    if column not in columns:
        conn.execute(f'ALTER TABLE {table} ADD COLUMN {definition}')


def team_of(conn: sqlite3.Connection, worker_id: int | None) -> str | None:
    """점수를 적립할 시점의 소속 팀을 조회한다."""
    if worker_id is None:
        return None
    row = conn.execute('SELECT team FROM workers WHERE id = ?', (worker_id,)).fetchone()
    return row['team'] if row else None


def get_db(request: Request):
    """정상 요청의 변경을 저장하고 연결을 항상 닫는다."""
    conn = connect(request.app.state.db_path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
