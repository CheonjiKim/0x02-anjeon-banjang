# rules/ — PoC 수칙 데이터와 사진 시나리오

담당: 김준이. 이 폴더에는 안전반장 PoC의 수칙 데이터와 사진 평가 시나리오 대응표가 있다. 수칙 데이터는 안전 안내를 위한 참고 정보이며 법률 자문이나 작업 승인 근거가 아니다.

## PoC 작업 네 가지

| 작업 | 수칙 파일 | 데이터 시나리오 | 보여 주는 조건 |
| --- | --- | --- | --- |
| 용접 | `welding.json` | 33, 34 | 가연물 |
| 절단·원형톱 | `circular_saw.json` | 39, 40 | 가연물 |
| 실내 도장·방수 | `painting_waterproofing.json` | 31, 32, C-04 | 환기 |
| 사다리·말비계 | `ladder_horse_scaffold.json` | 09, 10, 43, 44 | 작업 높이 |

그라인더는 PoC 범위에 포함하지 않는다. 기존 그라인더·절단 데이터는 원형톱 수칙으로 바꿔 쓰지 않고 제거했다.

`poc_scenarios.json`은 작업·시나리오·수칙 ID·화면 판정 항목의 대응표다. AI-Hub 사진 데이터는 평가에만 사용하며 모델 학습에는 사용하지 않는다.

## 사진 판정 항목

| 수칙 ID | 판정 항목 | 시나리오 | PoC 판정 기준 |
| --- | --- | --- | --- |
| V1 | `fire-watch` | 34 | 가연물이 있으면 필수, 없으면 권장 |
| V2 | `spark-cover` | 34 | 가연물 방호 조건 |
| V3 | `extinguisher` | 33 | 소화기 확인 |
| C5 | `cutting-fire` | 39, 40 | 소화기와 불티방지커버를 함께 확인 |
| P1 | `paint-ventilation` | 31 | 밀폐 공간에서는 환풍기 확인 |
| P7 | `flammable-containers` | 32 | 인화성 용기 정리 확인 |
| L2 | `ladder-use` | 09, 10 | 사다리 다리 바닥·최상부 발판 작업 확인 |
| L6 | `scaffold-clear-deck` | 43 | 말비계 발판 위 자재 적치 확인 |
| L3 | `horse-scaffold` | 44 | 말비계 지주 하단·바닥 확인 |

사람이 없는 정상 사다리 사진(시나리오 09)은 최상부 작업 여부를 알 수 없으므로 `판단불가`다. C-04는 정상·비정상 사진 판정 없이 조건 추출과 판단불가 후보로만 쓴다.

## JSON 형식

각 작업 수칙 파일은 `schema_version`, `work_type`, `label`, `rules`를 가진다. 각 수칙에는 `id`, `title`, `hazard`, `protections`, `applies_when`, `exceptions`, `level`, `evidence`, `source`가 들어간다.

`level.when_unknown`은 조건을 알 수 없을 때 안전한 쪽으로 안내하기 위한 값이다. 새 PoC 항목 C5·P1·P7·L2·L3·L6의 `source.status`는 `needs_check`다. 제공된 사진 시나리오가 판정 기준을 정한 것이며, 법령 원문 검증을 뜻하지 않는다.

## 서버와 만나는 지점

현재 작업 워크플로우는 `app/workflows/task.py`에서 `app/pipeline/rules.py`의 `build_checklist(Conditions)`를 호출한다. 이 함수는 아직 하드코딩된 다섯 항목(`fire-watch`, `extinguisher`, `spark-cover`, `ventilation`, `area-sign`)만 반환하며, 이 폴더의 JSON을 읽지 않는다.

따라서 4개 PoC 작업을 실제 체크리스트에 반영하려면, 후속 규칙 엔진이 `build_checklist(Conditions) -> list[ChecklistItem]` 인터페이스를 유지한 채 JSON과 조건을 연결해야 한다. 이때 필요한 미결정 사항은 다음과 같다.

- JSON 조건 키와 서버 `Conditions` 여섯 필드의 매핑
- 수칙 ID와 화면 판정 항목 코드의 매핑
- 도장·방수와 용접의 혼재작업 표현 방법
- 사진만으로 알 수 없는 작업 높이·사다리 사용 상태의 관리자 질문 흐름
