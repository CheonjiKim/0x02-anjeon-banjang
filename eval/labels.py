"""평가 라벨을 만드는 사람과 구현을 분리하는 JSONL 계약이다."""

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, Field

from app.schemas import Conditions, Result

DATA = Path(__file__).parent / 'data'
T = TypeVar('T', bound=BaseModel)


class TaskLabel(BaseModel):
    id: str
    text: str
    conditions: Conditions
    required: list[str] = Field(default_factory=list)
    note: str | None = None


class PhotoLabel(BaseModel):
    id: str
    item_code: str
    item_title: str
    label: Result
    path: str | None = None
    simulate: Result | None = None
    simulate_verify: bool | None = None
    attack: str | None = None
    note: str | None = None


class TbmLabel(BaseModel):
    id: str
    task_text: str
    said: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    note: str | None = None


def _load(path: str | Path, model: type[T]) -> list[T]:
    path = Path(path)
    if not path.exists():
        return []
    rows = []
    for line_no, line in enumerate(path.read_text(encoding='utf-8').splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith('//'):
            continue
        try:
            rows.append(model.model_validate_json(stripped))
        except Exception as exc:
            raise ValueError(f'{path.name} {line_no}번째 줄을 읽을 수 없어요: {exc}') from exc
    return rows


def load_tasks(path: str | Path | None = None) -> list[TaskLabel]:
    return _load(path or DATA / 'tasks.jsonl', TaskLabel)


def load_photos(path: str | Path | None = None) -> list[PhotoLabel]:
    return _load(path or DATA / 'photos.jsonl', PhotoLabel)


def load_tbm(path: str | Path | None = None) -> list[TbmLabel]:
    return _load(path or DATA / 'tbm.jsonl', TbmLabel)


def load_dataset_meta(tasks_path=None, photos_path=None, tbm_path=None) -> dict:
    paths = {
        'tasks': str(Path(tasks_path or DATA / 'tasks.jsonl')),
        'photos': str(Path(photos_path or DATA / 'photos.jsonl')),
        'tbm': str(Path(tbm_path or DATA / 'tbm.jsonl')),
    }
    meta = {'is_sample': True, 'source': '사용자 지정 라벨 파일(출처 미기재)', 'files': paths}
    if tasks_path is None and photos_path is None and tbm_path is None:
        meta_path = DATA / 'dataset.json'
        if meta_path.exists():
            meta.update(json.loads(meta_path.read_text(encoding='utf-8')))
            meta['files'] = paths
    return meta
