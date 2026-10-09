"""점수와 연속 기록의 확정 규칙을 지킨다.

확인된 활동에만 점수를 주고 사진 증빙은 항목당 한 번만 적립한다.
제보는 횟수 제한 없이 항상 가점한다.
이벤트에 worker_id와 team_snapshot을 함께 기록해 개인과 팀으로 집계한다.
참여 연속 기록과 무사고 기록을 분리한다.
"""

from .points import (
    POINTS_CONFIRMED,
    POINTS_REPORT,
    POINTS_TBM,
    award_evidence,
    award_report,
    award_tbm,
)
from .streaks import history, incident_free_days, participation_days, site_age_days, streaks
from .aggregate import stamps_for, team_ranking, worker_ranking
