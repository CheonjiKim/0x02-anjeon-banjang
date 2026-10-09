# 실제 앱 화면 캡처

2026-10-09, 현재 저장소의 웹 앱을 별도 로컬 서버에서 실행해 촬영했다.
모든 PNG는 390 × 844 px의 휴대폰 뷰포트 원본이며 긴 페이지를 연결하지 않았다.

| 파일 | 사용 목적 |
| --- | --- |
| 01-task-input.png | 작업 한 문장 입력과 체크리스트 생성 |
| 02-condition-review.png | 관리자 조건 검토와 작업자 배정 |
| 03-checklist-conditions.png | 추출 조건 및 정보 없음 표시 |
| 04-checklist-rules.png | 안전 수칙, 우선 확인 표시, 법령 참고 근거 |
| 05-tbm-missing.png | TBM 저장 후 누락 필수 수칙 6개 표시 |
| 06-photo-upload-mock.png | 사진 첨부와 모의 판정 모드 명시 |
| 07-photo-manager-review.png | 판단불가 사진의 재촬영 요청·관리자 직접 확인 선택 |
| 08-worker-today.png | 작업자에게 배정된 오늘 작업과 항목별 사진 첨부 |
| 09-worker-report.png | 마감 보고 및 위험 메모 작성 |
| 10-worker-submitted.png | 마감 보고 제출 완료 |
| 11-admin-report-review.png | 관리자에게 전달된 작업 보고·위험 메모 |
| 12-jsa-draft.png | 보고·위험 메모를 포함한 수정 가능한 JSA 초안 |
| 13-jsa-controls.png | JSA 모달 하단의 위험 요인·안전 조치·사진 판정 요약·저장 버튼 |

## 실행 조건과 시연 한계

- `BANJANG_LLM=mock`, 별도 DB `tmp/presentation-capture.db`, 별도 업로드 경로 `tmp/presentation-uploads`.
- 실제 외부 AI API를 호출하지 않았다. 모의 판정은 실제 사진을 분석한 결과가 아니다.
- 사진 파일은 저장소의 `Dataset/eval_photos/H-221014_D14_N-39_013_0109.jpg`를 예시로 업로드했다. 촬영 시나리오 현장을 직접 촬영한 자료가 아니다.
- 사진 검토는 개발용 `검증 불일치` 시나리오로 판단불가 흐름을 재현했다. 관리자의 직접 확인 버튼은 촬영 과정에서 누르지 않았다.
- 작업 문장: `2층 각파이프 용접, 옆에 합판`. 누락 사례를 보여주기 위해 TBM에는 소화기 준비와 용접 전 점검만 입력했다.
- 근로자 보고: 용접 완료 및 합판·통로 적치물 정리 요청. 보호구 착용과 수칙 이해는 미확인 상태를 유지했다.
- JSA는 자동 생성된 초안이며 현장 검토·작업 승인의 증거가 아니다.
- 재현 스크립트는 임시 폴더 `tmp/browser-check/presentation-capture.cjs`, 마지막 화면 보정은 `presentation-last.cjs`, TBM 스크롤 캡처는 `presentation-tbm.cjs`에 있다.
