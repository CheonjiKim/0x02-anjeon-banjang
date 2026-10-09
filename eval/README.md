# 평가 도구

담당: 남재은. 화면과 같은 워크플로우를 라벨로 실행해 오승인, 조건 추출, 사진 분류, TBM 누락, 비용·응답 시간을 계산한다. 오승인을 맨 앞에 두는 이유는 정확도가 높아도 안전하지 않은 상태를 승인하면 실패이기 때문이다.

```bash
uv run python -m eval.run
uv run python -m eval.run --compare
uv run python -m eval.run --simulate
uv run python -m eval.run --compare --json
```

기본 데이터는 작업 31건, 사진 7건, TBM 10건이다. AI-Hub 사진 후보 88건은 천지 검수 전 후보이므로 `--photos eval/data/photos_aihub.jsonl`로 명시할 때만 쓴다. 기본 사진 7건도 뼈대 점검 목적의 라벨을 포함한다. 결과의 `is_sample`이 참일 때만 경고가 출력된다.

`eval/labels.py`가 라벨 계약이다. 작업·TBM 라벨은 김준이, 사진 라벨은 김천지가 담당한다. 프롬프트를 쓴 사람이 라벨을 만들면 평가가 오염될 수 있다.

`verify`는 확인됨 사진만 재검증하는 현재 구조, `no_verify`는 그 검증을 뺀 변형, `single_call`은 모르는 조건을 문제없다고 가정하는 ablation이다. 실행 기록은 흐름별 LLM 호출 수·비용·응답 시간을 계산하는 데 사용한다.
