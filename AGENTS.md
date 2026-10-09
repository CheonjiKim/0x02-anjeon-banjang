# 작업 규칙 (Codex)

프로젝트 개요는 [README.md](README.md), 역할 분담은 [docs/dev-outline.md](docs/dev-outline.md)를 참고한다. 두 문서는 문서 브랜치에서 추가한다.

## Git 워크플로우

- 브랜치와 Pull Request로 작업한다. `main`에 직접 commit/push하지 않는다. `main`은 팀장이 PR로만 merge한다.
- 김천지(`@CheonjiKim`)는 GitHub 코드 관리자이자 형상관리 담당이다. 팀장은 별도 인물이다.
- 시작 전 `git switch main && git pull origin main`을 실행한다.
- 브랜치는 `feature/<이름>-<작업>`, 버그 수정은 `fix/<이름>-<작업>`을 쓴다.
- 커밋은 `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `data:`, `chore:` 접두어를 쓴다.
- 테스트 후 push하고 `gh pr create --base main`으로 PR을 만든다. PR 템플릿을 채운다.
- `main`이 앞서면 fetch 후 rebase 또는 merge로 따라잡는다. 충돌은 PR을 올린 사람이 해결한다.
- 다른 사람 브랜치와 `main`을 force push하지 않는다.
- **PR merge는 팀장만 한다. 에이전트는 PR을 merge하지 않는다.**

## 검증

- 백엔드는 `uv run pytest`, 프런트엔드는 `cd web && npm run build`로 검증한다.
- PR 전에 둘 다 통과시킨다. 실행하지 못했으면 PR 본문에 이유를 적는다.

## 주의

- `.env`, `.personal/`, `data/*.db`, `data/uploads/`는 커밋하지 않는다.
- 파이썬은 uv만 쓴다.
- 기본은 `BANJANG_LLM=mock`이다. 실제 API 호출은 사람 승인 후에만 한다.
- LangGraph를 도입하지 않는다.
