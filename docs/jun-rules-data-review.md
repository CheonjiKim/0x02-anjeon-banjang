# 김준이 확인 요청: 수칙 원본과 개발 문서의 차이

담당: 김준이. 범위: K1 `feature/jun-rules-data`.

작업은 원본 수칙을 그대로 저장하고 문서와의 차이를 담당자에게 남기는 것으로 이해했다. 사용자 지시에 따라 아래 차이를 유지한 채 진행했다. 조문·수칙·예외·필드·검증 상태는 수정하지 않았다.

기준 문서: [김준이 — 수칙 데이터·점수·연속 기록](https://app.notion.com/p/3f3b00a36e9b81da8f82e5dfc972fadc). 복사 출처: `~/safe-banjang-playground/rules/`. 저장 파일: [welding.json](../rules/welding.json), [grinding_cutting.json](../rules/grinding_cutting.json).

## 담당자가 확인할 차이

개발 문서의 필드 목록에 열거되지 않은 원본 필드가 있다. 아래 필드는 Codex가 추가한 것이 아니라 원본에 들어 있는 값을 그대로 복사한 것이다.

| 위치 | 원본의 추가 필드 |
| --- | --- |
| V2·V3·R5 | `source.secondary` |
| V4·R4 | `source.guideline` |
| V4·V5 | `design_note` |
| V5·R2 | `evidence.timer_minutes` (V5는 숫자, R2는 객체) |
| R1 | `assumption` |
| R4 | `item_levels`, `open_issue` |
| R6 | `mixed_with_welding` |

문서는 조문 인용 상태를 `verified_via_guide`로 설명하지만, 원본 `source.status`에는 다음 세 값이 있다. 이 표는 JSON 값의 기록이며 법률 원문을 대조했다는 뜻이 아니다. 이번 작업에서 법률 원문 대조는 수행하지 않았다.

| 항목 | 원본 `source.status` |
| --- | --- |
| V1·V2·V4·V5·V6·R4·R6 | `verified_via_guide` |
| V3·R5 | `needs_check` |
| R1·R2·R3 | `verified` |

김준이 확인 요청: 위 원본에만 명시된 필드를 데이터 계약에 포함할지, 항목별 검증 상태가 실제 검수 근거와 일치하는지 확인해 주세요. 확인 결과와 근거는 이 문서에 남기고, 개발 문서 또는 원본을 정리해 주세요. 확인 전에는 상태를 통일하거나 법률 검증 완료로 해석하지 않습니다.

조건 키와 서버 모델의 매핑, 규칙 평가 엔진은 이번 작업에서 구현하지 않았다.

## 확인한 결과

- K1 선행 PR [#1](https://github.com/CheonjiKim/anjeon-banjang/pull/1)의 병합 커밋 `1e63ac2`를 `git log origin/main`에서 확인했다.
- 임시 pytest로 원본과 바이트 동일성, 최상위 키·작업 유형·라벨·항목 ID·필수 키·`when_unknown`을 검사했다. 복사 전 파일 부재로 `2 failed`, 복사 후 `2 passed`. 임시 테스트는 저장소에 추가하지 않았다.
- `uv run pytest -q`: `2 passed in 0.06s`.
- 개발 문서의 JSON 확인 명령 결과:

```text
rules/welding.json welding ['V1', 'V2', 'V3', 'V4', 'V5', 'V6']
rules/grinding_cutting.json grinding_cutting ['R1', 'R2', 'R3', 'R4', 'R5', 'R6']
```

- `diff -r rules ~/safe-banjang-playground/rules | grep -v README`: 출력 없음. 두 JSON은 원본과 동일하다.

작업은 별도 worktree에서 수행했다. 사용자 지시에 따라 작업 브랜치를 로컬 `main`에 병합하며, 원격 `main` push 및 GitHub PR merge는 하지 않는다. 타인의 체크아웃·staged 파일·담당 파일은 수정하지 않는다.

## 다음 작업의 선행 조건

K2 `feature/jun-scoring`은 `feature/cheonji-db-pipeline`이 main에 있어야 시작한다. K1 검증 시 `git log origin/main`과 로컬 `main`의 `app/db.py` 이력을 확인했으나 해당 DB 구현은 없었고, 그 브랜치의 PR 조회도 빈 목록이었다. 선행 작업이 들어오기 전에는 K2 파일을 만들지 않는다.
