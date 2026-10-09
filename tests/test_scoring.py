"""점수 규칙과 연속 기록 2종. 제품의 핵심 주장을 지키는 테스트."""

from contextlib import closing
from datetime import date, timedelta

import pytest

from app.db import connect, init_db
from scoring import award_evidence, award_report
from scoring import incident_free_days, participation_days
from scoring import stamps_for, team_ranking, worker_ranking


@pytest.fixture
def conn(tmp_path):
    db_path = tmp_path / 't.db'
    init_db(db_path)
    with closing(connect(db_path)) as connection:
        started_on = date.today() - timedelta(days=10)
        connection.execute(
            'INSERT INTO tasks(site_id, worker_id, text, conditions, created_at) '
            'VALUES (?, ?, ?, ?, ?)',
            (1, 1, '용접', '{}', f'{started_on.isoformat()} 08:00:00'),
        )
        connection.commit()
        yield connection


@pytest.mark.parametrize('result', ['not_visible', 'uncertain'])
def test_only_confirmed_scores(conn, result):
    assert award_evidence(
        conn, site_id=1, task_id=1, item_code='fire-watch', result=result,
    ) == 0
    assert conn.execute('SELECT COUNT(*) FROM score_events').fetchone()[0] == 0


def test_confirmed_scores_once_per_item(conn):
    points = [
        award_evidence(
            conn, site_id=1, task_id=1, item_code='fire-watch', result='confirmed',
        )
        for _ in range(2)
    ]
    assert points == [10, 0]
    assert conn.execute('SELECT COUNT(*) FROM score_events').fetchone()[0] == 1


def test_report_always_scores_even_repeatedly(conn):
    assert [award_report(conn, site_id=1) for _ in range(3)] == [5, 5, 5]
    assert conn.execute('SELECT COUNT(*) FROM score_events').fetchone()[0] == 3


def test_event_records_both_worker_and_team_snapshot(conn):
    award_evidence(
        conn, site_id=1, task_id=1, item_code='fire-watch',
        result='confirmed', worker_id=3,
    )
    row = conn.execute('SELECT worker_id, team_snapshot FROM score_events').fetchone()
    assert row['worker_id'] == 3
    assert row['team_snapshot'] == '철골 1팀'


def test_participation_streak_counts_recorded_days(conn):
    today = date.today()
    for offset in (0, 1, 2):
        recorded_on = today - timedelta(days=offset)
        conn.execute(
            'INSERT INTO score_events(site_id, kind, points, created_at) VALUES (?, ?, ?, ?)',
            (1, 'report', 5, f'{recorded_on.isoformat()} 09:00:00'),
        )
    assert participation_days(conn, today=today) == 3


def test_participation_streak_survives_today_not_done_yet(conn):
    today = date.today()
    yesterday = today - timedelta(days=1)
    conn.execute(
        'INSERT INTO score_events(site_id, kind, points, created_at) VALUES (?, ?, ?, ?)',
        (1, 'report', 5, f'{yesterday.isoformat()} 09:00:00'),
    )
    assert participation_days(conn, today=today) == 1


def test_participation_streak_breaks_on_gap(conn):
    today = date.today()
    for offset in (1, 3):
        recorded_on = today - timedelta(days=offset)
        conn.execute(
            'INSERT INTO score_events(site_id, kind, points, created_at) VALUES (?, ?, ?, ?)',
            (1, 'report', 5, f'{recorded_on.isoformat()} 09:00:00'),
        )
    assert participation_days(conn, today=today) == 1


def test_unreported_incident_breaks_incident_free_record(conn):
    today = date.today()
    occurred_on = today - timedelta(days=2)
    conn.execute(
        'INSERT INTO incidents(site_id, occurred_on, reported, follow_up_done) '
        'VALUES (?, ?, ?, ?)',
        (1, occurred_on.isoformat(), 0, 0),
    )
    assert incident_free_days(conn, today=today) == 2


def test_reported_incident_with_follow_up_keeps_record(conn):
    today = date.today()
    assert incident_free_days(conn, today=today) == 11
    occurred_on = today - timedelta(days=2)
    conn.execute(
        'INSERT INTO incidents(site_id, occurred_on, reported, follow_up_done) '
        'VALUES (?, ?, ?, ?)',
        (1, occurred_on.isoformat(), 1, 1),
    )
    assert incident_free_days(conn, today=today) == 11


def test_reported_incident_without_follow_up_still_breaks(conn):
    today = date.today()
    occurred_on = today - timedelta(days=2)
    conn.execute(
        'INSERT INTO incidents(site_id, occurred_on, reported, follow_up_done) '
        'VALUES (?, ?, ?, ?)',
        (1, occurred_on.isoformat(), 1, 0),
    )
    assert incident_free_days(conn, today=today) == 2


def test_incident_free_days_never_exceeds_site_age(conn):
    today = date.today()
    occurred_on = today - timedelta(days=90)
    conn.execute(
        'INSERT INTO incidents(site_id, occurred_on, reported, follow_up_done) '
        'VALUES (?, ?, ?, ?)',
        (1, occurred_on.isoformat(), 0, 0),
    )
    assert incident_free_days(conn, today=today) == 11


def test_team_snapshot_survives_team_change(conn):
    award_evidence(
        conn, site_id=1, task_id=1, item_code='fire-watch',
        result='confirmed', worker_id=3,
    )
    conn.execute("UPDATE workers SET team = '마감 3팀' WHERE id = 3")
    award_evidence(
        conn, site_id=1, task_id=1, item_code='extinguisher',
        result='confirmed', worker_id=3,
    )
    assert {row.name: row.score for row in team_ranking(conn)} == {
        '철골 1팀': 10, '마감 3팀': 10,
    }
    assert [row.score for row in worker_ranking(conn)] == [20]


def test_stamps_count_personal_activity(conn):
    for code in 'abcde':
        award_evidence(
            conn, site_id=1, task_id=1, item_code=code,
            result='confirmed', worker_id=1,
        )
    stamps = {stamp.code: stamp for stamp in stamps_for(conn, worker_id=1)}
    assert stamps['first-photo'].earned
    assert stamps['first-photo'].count == 1
    assert stamps['photo-5'].earned
    assert stamps['photo-5'].count == 5
    assert not stamps['photo-20'].earned
    assert stamps['photo-20'].count == 5
