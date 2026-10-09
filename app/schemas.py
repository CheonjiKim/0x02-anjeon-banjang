"""계약의 단일 출처다.

주요 스키마는 작업 추출 출력 Conditions, 수칙 DB 항목 RuleItem,
사진 판정 출력 Judgement, 점수 이벤트 ScoreEvent다.
점수 이벤트에 worker_id와 team_snapshot을 함께 기록한다.
순위는 team_snapshot, 스탬프는 worker_id를 쓴다.
참여 streak과 무사고 기록은 분리하고 무사고 기록은 보고 + 후속 조치 완료면 유지한다.
"""

from typing import Literal

from pydantic import BaseModel, Field

UNKNOWN = '알 수 없음'
Level = Literal['required', 'recommended']
Result = Literal['confirmed', 'not_visible', 'uncertain']
ScoreKind = Literal['evidence', 'report', 'tbm']
StreakKind = Literal['participation', 'incident_free']


class Conditions(BaseModel):
    # 조건이 '알 수 없음'이면 규칙 엔진이 안전한 쪽으로 처리
    work: str = UNKNOWN
    height: str = UNKNOWN
    flammable: str = UNKNOWN
    ventilation: str = UNKNOWN
    nearby_people: str = UNKNOWN
    place: str = UNKNOWN

    def unknown_keys(self) -> list[str]:
        return [key for key, value in self.model_dump().items() if value == UNKNOWN]


class ConditionsPatch(BaseModel):
    work: str | None = None
    height: str | None = None
    flammable: str | None = None
    ventilation: str | None = None
    nearby_people: str | None = None
    place: str | None = None


class TaskIn(BaseModel):
    text: str
    site_id: int = 1
    worker_id: int = 1
    close_requested: bool = Field(True, exclude=True)
    scenario: str | None = Field(None, exclude=True)


class RuleCondition(BaseModel):
    key: str
    values: list[str] = Field(default_factory=list)
    # unknown_is_required=True면 조건을 모를 때도 필수
    unknown_is_required: bool = True


class RuleItem(BaseModel):
    code: str
    title: str
    # RuleItem.works가 빈 리스트면 모든 작업에 적용
    works: list[str] = Field(default_factory=list)
    source: str | None = None
    base_level: Level = 'recommended'
    required_when: list[RuleCondition] = Field(default_factory=list)
    photo_hint: str | None = None


class ChecklistItem(BaseModel):
    code: str
    title: str
    source: str | None = None
    level: Level
    note: str | None = None
    resolved: bool = False


class TaskOut(BaseModel):
    id: int
    text: str
    conditions: Conditions
    checklist: list[ChecklistItem]
    run_id: str | None = None
    close_requested: bool = False
    review_status: str = 'ready'
    review_reason: str | None = None
    review_action: str | None = None
    review_note: str | None = None
    reviewed_at: str | None = None


class Judgement(BaseModel):
    result: Result
    observed: str
    retake_hint: str | None = None


class EvidenceOut(Judgement):
    id: int
    task_id: int
    item_code: str
    points: int = 0
    run_id: str | None = None
    first_result: Result | None = None  # 검증 전 1차 판정
    verified: bool | None = None  # None은 검증 안 함, False는 승인 거부


class EvidenceReviewIn(BaseModel):
    action: Literal['retake_requested', 'confirmed_by_manager', 'not_confirmed']
    reason: str
    reviewer: str = '관리자'


class EvidenceReviewOut(BaseModel):
    id: int
    evidence_id: int
    action: str
    reason: str
    reviewer: str
    created_at: str


class ScoreEvent(BaseModel):
    id: int | None = None
    site_id: int = 1
    task_id: int | None = None
    worker_id: int | None = None
    team_snapshot: str | None = None
    kind: ScoreKind
    item_code: str | None = None
    points: int
    created_at: str | None = None


class StreakOut(BaseModel):
    kind: StreakKind
    days: int
    label: str


class RankRow(BaseModel):
    name: str
    score: int
    me: bool = False


class StampOut(BaseModel):
    code: str
    title: str
    earned: bool
    count: int = 0


class ScoresOut(BaseModel):
    total: int
    streaks: list[StreakOut]
    events: list[ScoreEvent]
    team_ranking: list[RankRow]
    worker_ranking: list[RankRow]
    stamps: list[StampOut]
    history: list[dict]


class IncidentIn(BaseModel):
    site_id: int = 1
    worker_id: int = 1
    note: str = ''
    occurred_on: str | None = None  # YYYY-MM-DD, 비우면 오늘


class TodoOut(BaseModel):
    id: str
    kind: Literal['uncertain', 'not_visible', 'condition']
    title: str
    detail: str | None = None
    observed: str | None = None
    level: Level | None = None
    photo_url: str | None = None
    item_code: str | None = None
    cond_key: str | None = None


class TbmIn(BaseModel):
    task_id: int
    points: list[str] = Field(default_factory=list)
    attendees: str = ''
    memo: str = ''
    transcript: str = Field('', exclude=True)


class TbmOut(BaseModel):
    id: int
    missing: list[ChecklistItem] = Field(default_factory=list)
    run_id: str | None = None


class WorkerFormIn(BaseModel):
    task_id: int
    understood: bool = True
    risk_note: str = ''
    ppe_worn: bool
    report_text: str = ''


class WorkerFormOut(BaseModel):
    id: int
    task_id: int
    report_text: str = ''
    risk_note: str = ''
    photo_url: str | None = None
    created_at: str | None = None


class TranscriptionOut(BaseModel):
    text: str


class RiskItem(BaseModel):
    code: str
    hazard: str
    likelihood: Literal['상', '중', '하']
    severity: Literal['상', '중', '하']
    measure: str


class TodoCard(BaseModel):
    kind: Literal['uncertain', 'not_visible']
    item_code: str
    title: str
    observed: str | None = None
    detail: str | None = None  # 재촬영 안내 또는 반장 확인 요청


class TaskResult(BaseModel):
    run_id: str
    conditions: Conditions
    questions: list[str] = Field(default_factory=list)
    assumed_required: list[str] = Field(default_factory=list)
    checklist: list[ChecklistItem] = Field(default_factory=list)
    risks: list[RiskItem] = Field(default_factory=list)


class EvidenceResult(BaseModel):
    run_id: str
    judgement: Judgement  # 최종 판정
    first: Judgement  # 1차 판정
    verified: bool | None = None
    todo: TodoCard | None = None


class QuestionOut(BaseModel):
    key: str
    text: str
    options: list[str] = Field(default_factory=list)


class TbmResult(BaseModel):
    run_id: str
    missing: list[ChecklistItem] = Field(default_factory=list)
