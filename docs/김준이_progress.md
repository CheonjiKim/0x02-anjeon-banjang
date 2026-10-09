# 김준이 작업 현황

2026-10-09 기준. 담당: 수칙 데이터·점수·연속 기록. **K1·K2·K4는 로컬 `main`에 반영했고, K3는 김천지 C4 API 병합을 기다린다.**

기준: [김준이 담당 노션](https://app.notion.com/p/3f3b00a36e9b81da8f82e5dfc972fadc). 선행 조건은 사용자 지시에 따라 원격이 아닌 로컬 `main`에서 확인한다. 이 문서는 진행 현황 기록이다.

| 단계 | 브랜치 | 현재 상태 | 로컬 `main` 병합 커밋 |
| --- | --- | --- | --- |
| K1 수칙 데이터 | `feature/jun-rules-data` | 완료 | `e7d32b1` |
| K2 점수·연속 기록·집계 | `feature/jun-scoring` | 완료 | `47433c5` |
| K3 사고·참여 기록 API 테스트 | `feature/jun-scoring-api-tests` | 김천지 C4 API 병합 대기 | 미반영 |
| K4 `rules/`·`scoring/` README | `feature/jun-docs` | 완료 | `d89847a` |

## 완료한 작업

K1 수칙 데이터는 네 가지 PoC 작업으로 정리했다. [용접·용단](../rules/welding.json), [절단·원형톱](../rules/circular_saw.json), [도장·방수](../rules/painting_waterproofing.json), [사다리·말비계](../rules/ladder_horse_scaffold.json)의 시나리오와 조건 매핑은 [PoC 대응표](../rules/poc_scenarios.json)에 기록했다. 그라인더는 PoC 범위에서 제외했다. 법적 근거가 검수되지 않은 항목은 `needs_check` 상태를 유지한다.

K2는 다음 담당 파일만 추가했다.

| 파일 | 구현 내용 |
| --- | --- |
| [scoring/__init__.py](../scoring/__init__.py) | 확정 규칙 설명과 공개 함수 내보내기 |
| [scoring/points.py](../scoring/points.py) | 확인된 사진 항목당 10점 1회, 제보마다 5점, 작업당 TBM 3점 1회 |
| [scoring/streaks.py](../scoring/streaks.py) | 참여 연속 기록, 최근 14일 기록, 보고·후속 조치 완료 시 유지되는 무사고 기록, 현장 나이 상한 |
| [scoring/aggregate.py](../scoring/aggregate.py) | 적립 당시 팀 스냅샷 순위, 개인 누적 순위, 개인 스탬프 |
| [tests/test_scoring.py](../tests/test_scoring.py) | 노션에 지정된 단위 테스트 14개. K2에서는 `app.main`을 import하지 않음 |

확인되지 않은 사진은 점수를 저장하지 않는다. 팀을 옮겨도 과거 점수는 적립 당시 팀에 남고 개인 누적은 작업자를 따라간다. 참여 기록과 무사고 기록은 별도로 계산한다. 무사고 기록을 깨는 사고는 미보고 또는 후속 조치 미완료 사고뿐이며, 해당 사고가 없으면 현장 나이를 반환한다.

## 검증과 커밋

각 구현 전에 pytest 실패를 확인했다. 무사고 기록 상한 테스트에서는 현장 나이 11일에 대해 90일이 반환되는 실패를 확인한 뒤 상한을 적용했다. K2 커밋은 노션의 순서를 따랐다.

| 커밋 | 구현 단위 |
| --- | --- |
| `76f5597` | 확인된 사진·제보·TBM 적립 |
| `3f42c56` | 참여 연속 기록·14일 기록 |
| `8c5661f` | 보고·후속 조치에 따른 무사고 기록 |
| `be88d44` | 무사고 일수의 현장 나이 상한 |
| `6e3e388` | 팀·개인 순위와 스탬프 |

K2 완료 명령의 실제 결과:

```text
uv run pytest tests/test_scoring.py -q
14 passed in 0.83s

uv run pytest -q
24 passed in 0.90s
```

TBM 중복 적립, 빈 현장·미래 날짜, TBM 로그 참여일, 14일 기록의 날짜 경계는 임시 테스트 한 개의 여러 단언으로 추가 확인했다(`1 passed`). 임시 테스트는 저장소에 추가하지 않았다. K1 JSON 원본 비교는 출력이 없었고, K1에서 웹 빌드도 통과했다. 위 결과는 각 단계 검증 시점의 기록이며, 이후 다른 담당자의 작업이 병합되면 전체 테스트 수는 달라질 수 있다.

## 김천지에게 필요한 다음 작업

김천지 C4 `feature/cheonji-api`를 구현·검증하고 로컬 `main`에 병합해 주세요. K3는 다음 계약을 사용한다.

- `create_app(db_path, upload_dir)`
- `POST /api/tasks`, `POST /api/evidence`
- `POST /api/incidents`, `POST /api/incidents/{id}/follow-up`
- `GET /api/scores`

병합 후 김준이는 `tests/test_scoring.py`에 사고 후속 조치의 기록 복원과 사고·참여 기록 독립성을 확인하는 API 테스트 2개를 추가한다. 테스트가 실패하면 라우터를 수정하지 않고 김천지에게 결과를 알린다. K4는 K3가 로컬 `main`에 병합된 뒤 진행한다.

## 공동 작업 방식

별도 worktree에서 김준이 담당 파일만 수정한다. 완료 브랜치는 `/home/cjkim/anjeon-banjang-jaeeun-main`의 로컬 `main`에 병합한다. 병합 직전 HEAD와 미커밋 작업을 재확인하고 공용 `.git/main-merge.lock`으로 병합을 조율한다. 타인의 체크아웃·staged 파일은 건드리지 않는다.

원격 `main` push와 GitHub PR merge는 수행하지 않았다. K1 [PR #4](https://github.com/CheonjiKim/anjeon-banjang/pull/4)를 생성했으며, K2는 로컬 브랜치와 로컬 `main`에 반영했다.
