# TASK-056b. ProjectDetail에 삭제(Delete) 버튼 추가

## 상태
완료

## 날짜
2026-11-10

## 작업 요약
T056a(수정 UI)와 같은 성격의 공백이었습니다 — T060 보고서에서 "Dashboard/ProjectCard에 삭제 버튼이 없다"고 기록되어 있었는데, 백엔드 `DELETE /api/v1/projects/{id}`(T050, 소프트 삭제)는 이미 완성돼 있었지만 그걸 호출할 화면이 어디에도 없었습니다. `ProjectDetail` 페이지에 "Delete" 버튼을 추가해 이 공백을 메꿨습니다.

동작:
- "Delete" 클릭 → 즉시 삭제하지 않고 "정말 삭제하시겠습니까?" + "확인"/"취소" 인라인 확인 단계로 전환 (네이티브 `window.confirm()` 사용 안 함 — 테스트 가능성 유지를 위해 TrashedProjectCard의 영구삭제 확인 패턴과 동일하게 설계)
- "확인" → `removeProject(projectId)`(T053에서 이미 구현된 기존 함수) 호출 → 성공 시 `['projects']` 쿼리 무효화 후 `navigate('/')`로 대시보드 복귀
- "취소" → API 호출 없이 보기 모드로 복귀
- 실패 시 `role="alert"`로 에러 표시, 페이지에 그대로 머무름

백엔드/DB 변경 없음 — 기존 `ProjectService.soft_delete()`/`DELETE /projects/{id}`/`removeProject()`를 그대로 호출만 합니다.

## 변경 파일
- `frontend/src/pages/ProjectDetail.tsx` (수정 — Delete 버튼 + 확인 단계 + navigate 추가)
- `frontend/tests/integration/pages/ProjectDetail.test.tsx` (수정 — "deleting the project" describe 블록에 5개 테스트 추가)

## TDD 결과
- RED: 신규 테스트 5개 작성 → "Delete 버튼이 없음"이라는 올바른 이유로 실패 확인
- GREEN: 구현 후 5개 포함 ProjectDetail 17/17 통과, 프론트엔드 전체 스위트 112/112 통과(회귀 없음)
- `eslint`, `tsc --noEmit` 클린
- 실브라우저(Playwright MCP) 재검증: 프로젝트 생성 → Delete 클릭 → 확인 단계 노출 확인 → "확인" 클릭 → 대시보드(`/`)로 정상 이동 → 목록에서 제외 확인
- Git 저장소가 아직 초기화되지 않아 커밋은 생략했습니다.

## 기술 결정
영구 삭제가 아닌 소프트 삭제(휴지통 이동)임에도 확인 단계를 넣었습니다. 되돌릴 수는 있지만(T170 복원), 실수로 누르면 Trash 페이지까지 가서 복원해야 하는 불편이 생기므로 한 번의 추가 확인이 사용자 경험상 더 안전하다고 판단했습니다.

## 비고
tasks.md에 T056b로 신규 등록(T056a 바로 다음), Total Task Count 217 → 218, Projects 섹션 19 → 20 tasks로 갱신했습니다.
