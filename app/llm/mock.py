"""네트워크 없이 결정적으로 실행하는 테스트·시연용 클라이언트다."""

from app.llm.base import ExtractOut, JudgeOut, LLMError, VerifyOut
from app.pipeline.extract import evidence_spans, extract_conditions
from app.pipeline.judge import judge_evidence

SCENARIOS = ('verify_reject', 'judge_fail', 'unsupported_none', 'extract_fail', 'extract_empty',
             'judge_timeout', 'verify_empty', 'judge_invalid')


class MockClient:
    name = 'mock'

    def __init__(self, forced: str | None = None, scenario: str | None = None):
        if scenario is not None and scenario not in SCENARIOS:
            raise ValueError(f'모르는 시나리오: {scenario}')
        self.forced = forced
        self.scenario = scenario

    def extract(self, text, *, step=None) -> ExtractOut:
        if self.scenario == 'extract_fail':
            raise LLMError('mock: extraction unavailable')
        if self.scenario == 'extract_empty':
            raise LLMError('mock: empty extraction response')
        conditions = extract_conditions(text)
        evidence = evidence_spans(text, conditions)
        if self.scenario == 'unsupported_none':
            conditions.flammable = '없음'
            evidence.pop('flammable', None)
        return ExtractOut(conditions=conditions, evidence=evidence)

    def judge(self, item, photo_hint, photo: bytes, *, step=None) -> JudgeOut:
        if self.scenario in {'judge_fail', 'judge_timeout', 'judge_invalid'}:
            raise LLMError('mock: 판정 응답을 해석하지 못함')
        return JudgeOut(**judge_evidence(item, photo, self.forced).model_dump())

    def verify(self, item, photo_hint, photo: bytes, first: JudgeOut, *, step=None) -> VerifyOut:
        if self.scenario in {'verify_reject', 'verify_empty'}:
            return VerifyOut(agrees=False, evidence='')
        return VerifyOut(agrees=True, evidence=first.observed)
