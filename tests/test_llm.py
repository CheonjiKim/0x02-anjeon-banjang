import json

import httpx
import pytest

from app.llm import LLMError, MockClient, get_client
from app.llm.openai_client import OpenAIClient, load_prompt, prompt_dir
from app.schemas import Conditions
from app.tracing import Step


def completion(content, usage=(120, 30), refusal=None):
    return httpx.Response(200, json={
        'choices': [{'message': {'content': json.dumps(content, ensure_ascii=False), 'refusal': refusal}}],
        'usage': {'prompt_tokens': usage[0], 'completion_tokens': usage[1]},
    })


def client_with(handler):
    requests = []

    def record(request):
        requests.append(json.loads(request.content))
        assert request.headers['Authorization'] == 'Bearer k'
        return handler(request)

    http = httpx.Client(transport=httpx.MockTransport(record))
    return OpenAIClient(api_key='k', model_extract='m-extract', model_judge='m-judge', http=http), requests


def test_default_client_is_mock(monkeypatch):
    monkeypatch.delenv('BANJANG_LLM', raising=False)
    assert isinstance(get_client(), MockClient)


def test_unknown_llm_kind_is_error(monkeypatch):
    monkeypatch.setenv('BANJANG_LLM', 'gpt')
    with pytest.raises(LLMError):
        get_client()


def test_openai_without_settings_is_config_error(monkeypatch):
    monkeypatch.setenv('BANJANG_LLM', 'openai')
    for key in ['OPENAI_API_KEY', 'BANJANG_MODEL_EXTRACT', 'BANJANG_MODEL_JUDGE']:
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(LLMError, match='BANJANG_MODEL_EXTRACT'):
        get_client()


def test_extract_parses_and_records_usage(tmp_path, monkeypatch):
    path = tmp_path / 'prices.json'
    path.write_text(json.dumps({'m-extract': {'input_per_1m': 1.0, 'output_per_1m': 4.0}}))
    monkeypatch.setenv('BANJANG_PRICES', str(path))
    conditions = Conditions(flammable='합판').model_dump()
    evidence = dict.fromkeys(conditions, '')
    evidence['flammable'] = '합판'
    client, sent = client_with(lambda _: completion({'conditions': conditions, 'evidence': evidence}))
    step = Step('extract')
    got = client.extract('옆에 합판', step=step)
    assert got.conditions.flammable == '합판'
    assert got.evidence == {'flammable': '합판'}
    assert sent[0]['model'] == 'm-extract'
    assert sent[0]['response_format']['json_schema']['strict'] is True
    assert '옆에 합판' in sent[0]['messages'][0]['content']
    schema = sent[0]['response_format']['json_schema']['schema']
    for obj in [schema, *schema['properties'].values()]:
        assert obj['type'] == 'object'
        assert set(obj['required']) == set(obj['properties'])
        assert obj['additionalProperties'] is False
    assert (step.model, step.prompt_tokens, step.completion_tokens) == ('m-extract', 120, 30)
    assert step.cost_usd == pytest.approx((120 + 30 * 4) / 1_000_000)


def test_judge_sends_image_and_uses_judge_model():
    client, sent = client_with(lambda _: completion({'result': 'not_visible', 'observed': '안 보임', 'retake_hint': ''}))
    got = client.judge('소화기 비치', '소화기', b'\x89PNG...')
    assert got.result == 'not_visible' and got.retake_hint is None
    assert sent[0]['model'] == 'm-judge'
    assert sent[0]['messages'][0]['content'][1]['image_url']['url'].startswith('data:image/png;base64,')


def test_verify_parses():
    client, sent = client_with(lambda _: completion({'agrees': True, 'evidence': '왼쪽 소화기'}))
    from app.llm import JudgeOut
    got = client.verify('소화기', '소화기', b'photo', JudgeOut(result='confirmed', observed='소화기'))
    assert got.agrees is True and '소화기' in got.evidence
    assert len(sent[0]['messages'][0]['content']) == 2


def test_unpriced_model_is_flagged_not_hidden(tmp_path, monkeypatch):
    monkeypatch.setenv('BANJANG_PRICES', str(tmp_path / 'missing.json'))
    client, _ = client_with(lambda _: completion({'result': 'confirmed', 'observed': '소화기', 'retake_hint': ''}))
    step = Step('judge')
    client.judge('소화기', '소화기', b'photo', step=step)
    assert step.cost_usd is None and step.meta['price_missing'] == 'm-judge'


@pytest.mark.parametrize('case', ['http', 'body', 'choices', 'content', 'array', 'result', 'missing', 'refusal'])
def test_judge_failures_raise_llm_error(case):
    responses = {
        'http': httpx.Response(500, text='실패'),
        'body': httpx.Response(200, text='JSON 아님'),
        'choices': httpx.Response(200, json={'choices': []}),
        'content': httpx.Response(200, json={'choices': [{'message': {'content': 'JSON 아님'}}]}),
        'array': completion([]),
        'result': completion({'result': 'maybe', 'observed': '관찰', 'retake_hint': ''}),
        'missing': completion({'observed': '관찰', 'retake_hint': ''}),
        'refusal': completion({}, refusal='거절'),
    }
    client, _ = client_with(lambda _: responses[case])
    step = Step('judge')
    with pytest.raises(LLMError):
        client.judge('소화기', '소화기', b'photo', step=step)
    if case in ['array', 'result', 'missing', 'refusal']:
        assert step.prompt_tokens == 120


def test_timeout_raises_llm_error():
    def timeout(request):
        raise httpx.ReadTimeout('응답 없음', request=request)
    client, _ = client_with(timeout)
    with pytest.raises(LLMError, match='시간 초과'):
        client.judge('소화기', '소화기', b'photo')


def test_extract_bad_shape_raises():
    client, _ = client_with(lambda _: completion({'conditions': '조건', 'evidence': {}}))
    with pytest.raises(LLMError, match='추출 출력 형식'):
        client.extract('용접')


def test_active_prompts_are_v1_and_baseline_v0_is_preserved(monkeypatch):
    monkeypatch.delenv('BANJANG_PROMPTS', raising=False)
    for name in ['extract', 'judge', 'verify']:
        assert (prompt_dir() / f'{name}.md').read_text(encoding='utf-8').startswith('<!-- v1:')
        assert (prompt_dir().parent / 'v0' / f'{name}.md').exists()
    text = load_prompt('judge', item='소화기 비치', photo_hint='소화기')
    assert '소화기 비치' in text and '점검 완료' in text
    assert '{item}' not in text and '<!--' not in text


def test_cached_tokens_are_priced_at_cached_rate():
    step = Step('extract')
    step.record_usage('gpt-4.1-mini', 2000, 100, cached_tokens=1000)
    assert step.cached_tokens == 1000
    assert step.cost_usd == pytest.approx((1000 * .4 + 1000 * .1 + 100 * 1.6) / 1_000_000)
