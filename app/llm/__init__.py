"""환경변수로 선택하는 텍스트/비전 LLM 클라이언트다."""

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


def get_vision_client() -> LLMClient:
    """사진 판정 전용 클라이언트. 기본은 기존 mock/LLM 설정을 따른다.

    BANJANG_VISION=openai를 지정하면 텍스트 추출은 mock으로 두고 사진만
    OpenAI 비전 모델로 보낼 수 있다. 외부 호출은 명시 설정을 해야 발생한다.
    """
    kind = os.environ.get('BANJANG_VISION', '').strip().lower()
    if not kind or kind == 'default':
        return get_client()
    if kind == 'mock':
        return MockClient()
    if kind == 'openai':
        from app.llm.openai_client import OpenAIClient
        return OpenAIClient(require_extract=False)
    raise LLMError(f"BANJANG_VISION 값을 모르겠어요: '{kind}' (mock 또는 openai)")
