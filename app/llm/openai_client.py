"""HTTP로 구조화 출력을 요청하며 사용할 수 없는 응답은 LLMError로 전달한다."""

import base64
import json
import os
from pathlib import Path
import re

import httpx

from app.llm.base import ExtractOut, JudgeOut, LLMError, VerifyOut
from app.schemas import Conditions
from app.tracing import ROOT

API_URL = 'https://api.openai.com/v1/chat/completions'


def prompt_dir() -> Path:
    return Path(os.environ.get('BANJANG_PROMPTS', ROOT / 'prompts/v0'))


def load_prompt(name, **values) -> str:
    text = (prompt_dir() / f'{name}.md').read_text(encoding='utf-8')
    if text.startswith('<!--'):
        text = text.split('-->', 1)[1].lstrip()
    # 삽입된 원문 속 중괄호를 다음 치환의 대상으로 삼지 않는다.
    return re.sub(r'\{(\w+)\}', lambda match: str(values.get(match[1], match[0])), text)


EXTRACT_SCHEMA = {
    'type': 'object',
    'properties': {
        name: {
            'type': 'object',
            'properties': {key: {'type': 'string'} for key in Conditions.model_fields},
            'required': list(Conditions.model_fields),
            'additionalProperties': False,
        }
        for name in ['conditions', 'evidence']
    },
    'required': ['conditions', 'evidence'],
    'additionalProperties': False,
}
JUDGE_SCHEMA = {
    'type': 'object',
    'properties': {
        'result': {'type': 'string', 'enum': ['confirmed', 'not_visible', 'uncertain']},
        'observed': {'type': 'string'},
        'retake_hint': {'type': 'string'},
    },
    'required': ['result', 'observed', 'retake_hint'],
    'additionalProperties': False,
}
VERIFY_SCHEMA = {
    'type': 'object',
    'properties': {'agrees': {'type': 'boolean'}, 'evidence': {'type': 'string'}},
    'required': ['agrees', 'evidence'],
    'additionalProperties': False,
}


class OpenAIClient:
    name = 'openai'

    def __init__(self, *, api_key=None, model_extract=None, model_judge=None, timeout=20.0,
                 http: httpx.Client | None = None, require_extract: bool = True):
        self.api_key = api_key if api_key is not None else os.environ.get('OPENAI_API_KEY', '')
        self.model_extract = model_extract if model_extract is not None else os.environ.get('BANJANG_MODEL_EXTRACT', '')
        self.model_judge = model_judge if model_judge is not None else os.environ.get('BANJANG_MODEL_JUDGE', '')
        required = [('OPENAI_API_KEY', self.api_key), ('BANJANG_MODEL_JUDGE', self.model_judge)]
        if require_extract:
            required.append(('BANJANG_MODEL_EXTRACT', self.model_extract))
        missing = [key for key, value in required if not value.strip()]
        if missing:
            raise LLMError(f"설정이 비어 있어요: {', '.join(missing)}")
        self.timeout = timeout
        self.http = http

    def _call(self, model, content, schema_name, schema, step) -> dict:
        body = {
            'model': model,
            'messages': [{'role': 'user', 'content': content}],
            'response_format': {'type': 'json_schema', 'json_schema': {
                'name': schema_name, 'schema': schema, 'strict': True,
            }},
        }
        headers = {'Authorization': f'Bearer {self.api_key}'}
        try:
            if self.http is not None:
                response = self.http.post(API_URL, json=body, headers=headers, timeout=self.timeout)
            else:
                with httpx.Client(timeout=self.timeout) as http:
                    response = http.post(API_URL, json=body, headers=headers)
        except httpx.TimeoutException as exc:
            raise LLMError(f'시간 초과: {exc}') from exc
        except httpx.HTTPError as exc:
            raise LLMError(f'네트워크 오류: {exc}') from exc
        if response.status_code != 200:
            raise LLMError(f'HTTP {response.status_code}: {response.text[:200]}')
        try:
            data = response.json()
            usage = data.get('usage')
            if usage and step is not None:
                step.record_usage(model, usage.get('prompt_tokens', 0), usage.get('completion_tokens', 0))
            message = data['choices'][0]['message']
            if message.get('refusal'):
                raise LLMError(f"모델이 거절했어요: {message['refusal']}")
            output = json.loads(message['content'])
            if not isinstance(output, dict):
                raise LLMError('응답이 JSON 객체가 아니에요')
            return output
        except (ValueError, KeyError, IndexError, TypeError, AttributeError) as exc:
            raise LLMError(f'응답을 해석하지 못했어요: {exc}') from exc

    def extract(self, text, *, step=None) -> ExtractOut:
        try:
            output = self._call(self.model_extract, load_prompt('extract', text=text), 'extract', EXTRACT_SCHEMA, step)
            parsed = ExtractOut.model_validate(output, strict=True)
            parsed.evidence = {key: value for key, value in parsed.evidence.items() if value.strip()}
            return parsed
        except (ValueError, TypeError, OSError) as exc:
            raise LLMError(f'추출 출력 형식이 달라요: {exc}') from exc

    def _vision_content(self, text, photo):
        if photo.startswith(b'\x89PNG'):
            mime = 'image/png'
        elif photo.startswith(b'RIFF') and photo[8:12] == b'WEBP':
            mime = 'image/webp'
        else:
            mime = 'image/jpeg'
        encoded = base64.b64encode(photo).decode('ascii')
        return [
            {'type': 'text', 'text': text},
            {'type': 'image_url', 'image_url': {'url': f'data:{mime};base64,{encoded}'}},
        ]

    def judge(self, item, photo_hint, photo: bytes, *, step=None) -> JudgeOut:
        try:
            text = load_prompt('judge', item=item, photo_hint=photo_hint)
            output = self._call(self.model_judge, self._vision_content(text, photo), 'judge', JUDGE_SCHEMA, step)
            parsed = JudgeOut.model_validate(output, strict=True)
            if not parsed.retake_hint:
                parsed.retake_hint = None
            return parsed
        except (ValueError, TypeError, OSError) as exc:
            raise LLMError(f'판정 출력 형식이 달라요: {exc}') from exc

    def verify(self, item, photo_hint, photo: bytes, first: JudgeOut, *, step=None) -> VerifyOut:
        try:
            text = load_prompt('verify', item=item, photo_hint=photo_hint, observed=first.observed)
            output = self._call(self.model_judge, self._vision_content(text, photo), 'verify', VERIFY_SCHEMA, step)
            return VerifyOut.model_validate(output, strict=True)
        except (ValueError, TypeError, OSError) as exc:
            raise LLMError(f'검증 출력 형식이 달라요: {exc}') from exc
