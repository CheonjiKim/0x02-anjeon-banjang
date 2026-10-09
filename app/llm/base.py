"""조건 추출·사진 판정·검증의 LLM 호출 계약이다."""

from typing import Protocol

from pydantic import BaseModel, Field

from app.schemas import Conditions, Result
from app.tracing import Step


class LLMError(Exception):
    """호출이 쓸 수 있는 답을 내지 못했다.

    워크플로우는 추출 실패를 키워드 추출로, 판정 실패를 판단불가로 처리한다.
    """


class ExtractOut(BaseModel):
    conditions: Conditions
    evidence: dict[str, str] = Field(default_factory=dict)


class JudgeOut(BaseModel):
    result: Result
    observed: str
    retake_hint: str | None = None


class VerifyOut(BaseModel):
    agrees: bool
    evidence: str = ''


class LLMClient(Protocol):
    name: str

    def extract(self, text: str, *, step: Step | None = None) -> ExtractOut: ...

    def judge(self, item: str, photo_hint: str, photo: bytes, *, step: Step | None = None) -> JudgeOut: ...

    def verify(self, item: str, photo_hint: str, photo: bytes, first: JudgeOut, *, step: Step | None = None) -> VerifyOut: ...
