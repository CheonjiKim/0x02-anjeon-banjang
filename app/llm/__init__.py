"""환경변수로 선택하는 LLM 클라이언트이며 기본은 네트워크 없는 mock이다."""

import os

from app.llm.base import ExtractOut, JudgeOut, LLMClient, LLMError, VerifyOut
from app.llm.mock import MockClient

__all__ = ['get_client', 'LLMClient', 'LLMError', 'MockClient', 'ExtractOut', 'JudgeOut', 'VerifyOut']


def get_client() -> LLMClient:
    kind = os.environ.get('BANJANG_LLM', 'mock').strip().lower() or 'mock'
    if kind == 'mock':
        return MockClient()
    if kind == 'openai':
        from app.llm.openai_client import OpenAIClient
        return OpenAIClient()
    raise LLMError(f"BANJANG_LLM 값을 모르겠어요: '{kind}' (mock 또는 openai)")
