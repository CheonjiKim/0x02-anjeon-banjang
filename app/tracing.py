"""워크플로우 실행과 단계별 입력·출력·지연·비용을 JSONL로 기록한다."""

from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from time import perf_counter
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]


def price_file() -> Path:
    return Path(os.environ.get('BANJANG_PRICES', ROOT / 'config/model_prices.json'))


def prices() -> dict[str, tuple[float, float]]:
    try:
        data = json.loads(price_file().read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {
        model: (value.get('input_per_1m', 0), value.get('output_per_1m', 0))
        for model, value in data.items()
        if isinstance(value, dict)
    }


def trace_dir() -> Path:
    return Path(os.environ.get('BANJANG_TRACE_DIR', ROOT / 'data/traces'))


def _jsonable(value, limit=2000):
    if isinstance(value, (bytes, bytearray)):
        return {'bytes': len(value)}
    if hasattr(value, 'model_dump'):
        return _jsonable(value.model_dump(), limit)
    if isinstance(value, dict):
        return {key: _jsonable(item, limit) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item, limit) for item in value]
    if isinstance(value, str):
        if len(value) > limit:
            return value[:limit] + f'…(+{len(value) - limit}자)'
        return value
    if value is None or isinstance(value, (int, float, bool)):
        return value
    return repr(value)[:limit]


class Step:
    def __init__(self, name):
        self.name = name
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.latency_ms = 0
        self.input = None
        self.output = None
        self.error = None
        self.model = None
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.cost_usd = 0
        self.meta = {}

    def record_usage(self, model, prompt_tokens=0, completion_tokens=0):
        self.model = model
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        table = prices()
        if model not in table:
            self.meta['price_missing'] = model
        input_price, output_price = table.get(model, (0, 0))
        self.cost_usd += (prompt_tokens * input_price + completion_tokens * output_price) / 1_000_000

    def as_dict(self):
        result = {
            'name': self.name,
            'started_at': self.started_at,
            'latency_ms': round(self.latency_ms, 2),
            'input': _jsonable(self.input),
            'output': _jsonable(self.output),
            'error': self.error,
            'model': self.model,
            'prompt_tokens': self.prompt_tokens,
            'completion_tokens': self.completion_tokens,
            'cost_usd': self.cost_usd,
        }
        if self.meta:
            result['meta'] = _jsonable(self.meta)
        return result


class Trace:
    def __init__(self, kind, run_id=None, **meta):
        self.run_id = run_id if run_id is not None else uuid4().hex
        self.kind = kind
        self.meta = meta
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.steps: list[Step] = []
        self.error = None
        self._started = perf_counter()

    @contextmanager
    def step(self, name, **inputs):
        step = Step(name)
        step.input = _jsonable(inputs) if inputs else None
        self.steps.append(step)
        started = perf_counter()
        try:
            yield step
        except Exception as exc:
            step.error = self.error = f'{type(exc).__name__}: {exc}'
            raise
        finally:
            step.latency_ms = (perf_counter() - started) * 1000

    @property
    def latency_ms(self):
        return (perf_counter() - self._started) * 1000

    @property
    def cost_usd(self):
        return sum(step.cost_usd for step in self.steps)

    def as_dict(self):
        return {
            'run_id': self.run_id,
            'kind': self.kind,
            'started_at': self.started_at,
            'latency_ms': round(self.latency_ms, 2),
            'cost_usd': self.cost_usd,
            'error': self.error,
            'meta': _jsonable(self.meta),
            'steps': [step.as_dict() for step in self.steps],
        }

    def write(self):
        directory = trace_dir()
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f'{datetime.now(timezone.utc).date().isoformat()}.jsonl'
        with path.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(self.as_dict(), ensure_ascii=False) + '\n')


@contextmanager
def trace_run(kind, run_id=None, **meta):
    trace = Trace(kind, run_id, **meta)
    try:
        yield trace
    except Exception as exc:
        trace.error = f'{type(exc).__name__}: {exc}'
        raise
    finally:
        try:
            trace.write()
        except OSError:
            pass


def read_traces(path=None) -> list[dict]:
    path = Path(path) if path is not None else trace_dir()
    paths = sorted(path.glob('*.jsonl')) if path.is_dir() else [path]
    runs = []
    for file in paths:
        try:
            lines = file.read_text(encoding='utf-8').splitlines()
        except FileNotFoundError:
            continue
        runs.extend(json.loads(line) for line in lines if line.strip())
    return runs
