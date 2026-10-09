"""OpenAI speech-to-text client, kept separate from the mock safety workflow."""

import os

import httpx

from app.llm.base import LLMError


API_URL = 'https://api.openai.com/v1/audio/transcriptions'


def transcribe_audio(filename: str, content: bytes, content_type: str | None = None, *, http: httpx.Client | None = None) -> str:
    api_key = os.environ.get('OPENAI_API_KEY', '').strip()
    model = os.environ.get('BANJANG_TRANSCRIPTION_MODEL', 'gpt-transcribe').strip()
    if not api_key:
        raise LLMError('OPENAI_API_KEY 설정이 필요합니다.')
    if not model:
        raise LLMError('BANJANG_TRANSCRIPTION_MODEL 설정이 필요합니다.')
    files = {'file': (filename or 'recording.webm', content, content_type or 'audio/webm')}
    data = {'model': model, 'response_format': 'json'}
    if model == 'gpt-transcribe':
        data['languages[]'] = 'ko'
    else:
        data['language'] = 'ko'
    headers = {'Authorization': f'Bearer {api_key}'}
    try:
        if http is not None:
            response = http.post(API_URL, data=data, files=files, headers=headers, timeout=45.0)
        else:
            with httpx.Client(timeout=45.0) as client:
                response = client.post(API_URL, data=data, files=files, headers=headers)
    except httpx.HTTPError as exc:
        raise LLMError(f'음성 전사 통신 오류: {exc}') from exc
    if response.status_code != 200:
        raise LLMError(f'음성 전사 HTTP {response.status_code}: {response.text[:200]}')
    try:
        text = response.json()['text'].strip()
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        raise LLMError(f'음성 전사 응답을 읽을 수 없습니다: {exc}') from exc
    if not text:
        raise LLMError('음성에서 텍스트를 찾지 못했습니다.')
    return text
