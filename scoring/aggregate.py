"""적립 시점의 팀 순위와 개인 누적·스탬프를 집계한다."""

import sqlite3

from app.schemas import RankRow, StampOut

STAMP_CATALOG = (
    ('first-photo', '첫 사진 증빙', 'evidence', 1),
    ('photo-5', '사진 증빙 5개', 'evidence', 5),
    ('photo-20', '사진 증빙 20개', 'evidence', 20),
    ('first-report', '첫 제보', 'report', 1),
    ('report-5', '제보 5건', 'report', 5),
    ('tbm-7', 'TBM 일지 7회', 'tbm', 7),
)


def _rows(conn: sqlite3.Connection, column: str, site_id: int):
    """팀 스냅샷 또는 작업자가 있는 이벤트의 점수를 내림차순으로 모은다."""
    return conn.execute(
        f'SELECT {column}, SUM(points) AS score FROM score_events '
        f'WHERE site_id = ? AND {column} IS NOT NULL '
        f'GROUP BY {column} ORDER BY score DESC',
        (site_id,),
    ).fetchall()


def team_ranking(
    conn: sqlite3.Connection, site_id: int = 1, my_team: str | None = None,
) -> list[RankRow]:
    """팀을 옮겨도 과거 점수는 적립 당시 팀에 남긴다."""
    return [
        RankRow(name=row['team_snapshot'], score=row['score'], me=row['team_snapshot'] == my_team)
        for row in _rows(conn, 'team_snapshot', site_id)
    ]


def worker_ranking(
    conn: sqlite3.Connection, site_id: int = 1, my_worker_id: int | None = None,
) -> list[RankRow]:
    """작업자의 현재 이름과 소속 변경에 무관한 개인 점수를 반환한다."""
    ranking = []
    for row in _rows(conn, 'worker_id', site_id):
        worker_id = row['worker_id']
        worker = conn.execute('SELECT name FROM workers WHERE id = ?', (worker_id,)).fetchone()
        ranking.append(RankRow(
            name=worker['name'] if worker else f'#{worker_id}',
            score=row['score'], me=worker_id == my_worker_id,
        ))
    return ranking


def stamps_for(
    conn: sqlite3.Connection, worker_id: int = 1, site_id: int = 1,
) -> list[StampOut]:
    """개인의 이벤트 수로 스탬프 획득 여부와 목표까지의 횟수를 계산한다."""
    counts = {
        row['kind']: row['count']
        for row in conn.execute(
            'SELECT kind, COUNT(*) AS count FROM score_events '
            'WHERE worker_id = ? AND site_id = ? GROUP BY kind',
            (worker_id, site_id),
        )
    }
    return [
        StampOut(
            code=code, title=title, earned=counts.get(kind, 0) >= required,
            count=min(counts.get(kind, 0), required),
        )
        for code, title, kind, required in STAMP_CATALOG
    ]
