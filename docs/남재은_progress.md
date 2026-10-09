# 남재은 작업 현황

작성일: 2026-10-09. 담당: 남재은. 구현: Codex.

기준 명세는 [남재은 — 계약·실행 기록·LLM·워크플로우·평가](https://app.notion.com/p/3f3b00a36e9b8153959fece703aed762)다. 이 문서는 현재 구현·검증·병합 상태를 기록한다.

## 현재 위치

| 단계 | 브랜치 | 구현 상태 | 로컬 main 상태 |
| --- | --- | --- | --- |
| J1 계약 모델 | `feature/jaeeun-schemas` | 완료, 계약 테스트 포함 | 병합됨 |
| J2 실행 기록 | `feature/jaeeun-tracing` | 완료 | 병합됨 |
| J3 LLM·정규화·프롬프트 | `feature/jaeeun-llm-guard` | 지정된 5개 구현 커밋 완료, 테스트·빌드 통과 | 미병합 |
| J4 워크플로우 | `feature/jaeeun-workflows` | J3 기반 브랜치만 생성, 코드·테스트 미작성 | 미병합 |
| J5 평가 | `feature/jaeeun-eval` | 미착수 | 해당 없음 |
| J6 문서 | `feature/jaeeun-docs` | 미착수 | 해당 없음 |

J3은 로컬 main `47433c5`에서 시작했다. J1·J2와 김천지 DB·파이프라인이 포함된 것을 확인했다. J3 마지막 구현 커밋은 `92b9a28`이다. J4는 현재 같은 커밋을 가리킨다. 이 현황 문서는 J3 구현 뒤에 추가한다.

## J3 구현 내용

- `app/llm/`: 호출 계약, 네트워크 없는 mock, 환경변수로 클라이언트 선택, OpenAI HTTP 클라이언트.
- `app/pipeline/normalize.py`: 조건 허용 목록, 안전을 낮추는 값의 원문 근거 검사, 지정된 지시 표현 차단.
- `prompts/v0/`: 노션의 추출·사진 판정·검증 프롬프트 본문을 그대로 추가.
- `.env.example`: LLM 선택·키·모델·프롬프트·단가 설정 예시. 모델 이름에 기본값 없음.
- `tests/test_llm.py`, `tests/test_misjudgment.py`: 지정 테스트 23개. 구현 전에 테스트 실패를 확인한 뒤 구현.

커밋 순서는 다음과 같다.

1. `85f82c9` LLM 호출 계약과 mock 클라이언트
2. `239bb2d` 프롬프트 v0 파일
3. `9f1fbb1` OpenAI 클라이언트·구조화 출력·오류 처리
4. `6719034` 조건 정규화
5. `92b9a28` 환경변수 예시

## 확인한 것과 아직 확인하지 않은 것

J3 worktree `/home/cjkim/anjeon-banjang-jaeeun-llm-guard`에서 실행했다.

| 명령 | 실제 결과 |
| --- | --- |
| `uv run pytest tests/test_llm.py tests/test_misjudgment.py -q` | `23 passed in 0.15s` |
| `uv run pytest -q` | `47 passed in 1.13s` |
| `cd web && npm run build` | `✓ built in 1.37s` |

전체 47개에는 로컬 main의 기존 테스트 24개가 포함된다. 노션의 전체 기대치 40개와 차이가 있지만 지정된 J3 테스트 23개는 일치한다.

실제 OpenAI API는 호출하지 않았다. HTTP 응답은 `httpx.MockTransport`로만 시험했다. 모델 성능·현장 사진 판정 정확도·실제 비용·지연은 검증하지 않았다. J3의 정규화는 지정된 허용 값·원문 부분 문자열·정규식 범위만 검사한다. 독립 코드 검토는 아직 수행하지 않았다.

## 인계와 다음 작업

J3 구현과 이 문서는 `feature/jaeeun-llm-guard` 브랜치로 push하고 GitHub PR을 생성해 인계한다. PR은 검토용이며, 요청된 병합 대상은 로컬 main이다.

김천지가 로컬 main에 직접 병합한다. Codex는 로컬 main 병합, 원격 main push, GitHub PR merge를 수행하지 않는다. 병합 직전 `/home/cjkim/anjeon-banjang-jaeeun-main`의 최신 커밋·미커밋 작업을 확인하고 다른 에이전트의 병합과 겹치지 않게 진행한다.

다음 구현 대상은 J4의 작업 입력 → 사진 판정·검증 → TBM 검토 순서다. 작업 경로는 `/home/cjkim/anjeon-banjang-jaeeun-workflows`이며 담당 파일 `app/workflows/`, `tests/test_workflows.py`, `tests/test_misjudgment.py`만 수정한다. J3 위에 이어서 구현할 때는 병합 순서도 J3 → J4로 유지한다. 이 문서 작성 시점에는 J4 구현을 시작하지 않았다.
