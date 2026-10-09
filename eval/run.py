"""python -m eval.run CLI."""

import argparse
from datetime import datetime
import json
import os
from pathlib import Path

from eval.labels import load_dataset_meta, load_photos, load_tasks, load_tbm
from eval.metrics import compare
from eval.report import render
from eval.runner import VARIANTS, evaluate


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--tasks'); parser.add_argument('--photos'); parser.add_argument('--tbm')
    parser.add_argument('--variant', choices=VARIANTS, default='verify'); parser.add_argument('--compare', action='store_true')
    parser.add_argument('--simulate', action='store_true'); parser.add_argument('--json', nargs='?', const='')
    args = parser.parse_args(argv)
    tasks, photos, tbms = load_tasks(args.tasks), load_photos(args.photos), load_tbm(args.tbm)
    if not any((tasks, photos, tbms)):
        print('라벨이 없어요. eval/data/tasks.jsonl, photos.jsonl, tbm.jsonl 을 채워 주세요.\n형식은 eval/labels.py 의 모델을 그대로 따릅니다.')
        return 1
    llm = os.environ.get('BANJANG_LLM', 'mock')
    simulate = args.simulate or llm == 'mock'
    dataset = load_dataset_meta(args.tasks, args.photos, args.tbm)
    dataset.update({'counts': {'tasks': len(tasks), 'photos': len(photos), 'tbm': len(tbms)}, 'llm': llm,
                    'photo_judge': '라벨의 simulate 값(모델 아님)' if simulate else f'{llm} 모델'})
    names = list(VARIANTS) if args.compare else [args.variant]
    results = {name: evaluate(tasks, photos, tbms, variant=name, use_simulate=simulate) for name in names}
    comparison = compare(results) if args.compare else None
    print(render(dataset, results, comparison))
    if args.json is not None:
        path = Path(args.json) if args.json else Path('eval/out') / f"{datetime.now():%Y%m%d-%H%M%S}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'created_at': datetime.now().isoformat(), 'dataset': dataset, 'results': results, 'comparison': comparison}, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'JSON 저장: {path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
