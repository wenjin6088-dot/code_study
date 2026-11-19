# TASK-056a. 프로젝트 제목/설명 수정 UI 추가

## 상태
완료

## 날짜
2026-11-10

## 작업 요약
`ProjectDetail` 페이지에 "Edit" 버튼과 인라인 수정 폼을 추가했습니다. T059(제목 수정 브라우저 테스트)와 Phase 4 완료 체크포인트("User can create, view, edit, delete projects", tasks.md:582)는 수정 가능을 전제했지만, 정작 Frontend: Project UI 섹션(T051~T056)에는 수정 UI를 만드는 태스크가 없어서 실제로는 버튼/폼이 존재하지 않았습니다(T059/T060 보고서에 "UI 공백"으로 기록되어 있던 부분). 이번 작업으로 그 공백을 메꿨습니다.

백엔드는 전혀 건드리지 않았습니다 — `PATCH /api/v1/projects/{id}`(T049)와 `ProjectService.update()`(T044)가 이미 완성·테스트되어 있어서, 프론트엔드에서 기존 `updateProject()`(T053, `frontend/src/services/project-service.ts`)를 호출하는 화면만 새로 만들면 되는 순수 프론트엔드 작업이었습니다. DB 스키마/마이그레이션 변경 없음.

동작 방식:
- "Edit" 버튼 클릭 → 현재 title/description 값으로 미리 채워진 인라인 폼(Title/Description input + Save/Cancel)으로 전환
- Title이 비어있거나 공백만 있으면 Save 비활성화 (CreateProjectModal과 동일한 패턴)
- Save: `updateProject(projectId, {title, description})`을 컴포넌트가 직접 호출(모달에 위임하지 않고 CreateProjectModal이 `createProject`를 직접 호출하는 것과 동일한 패턴) → 성공 시 `queryClient.setQueryData(['project', projectId], updated)`로 캐시 즉시 갱신 후 보기 모드로 복귀
- 실패 시 `role="alert"`로 에러 메시지 표시, 수정 모드 유지(입력값 보존)
- Cancel: 입력값 버리고 보기 모드로 복귀, API 호출 없음

## 변경 파일
- `frontend/src/pages/ProjectDetail.tsx` (수정 — Edit 버튼/인라인 폼 추가)
- `frontend/tests/integration/pages/ProjectDetail.test.tsx` (수정 — "editing the project" describe 블록에 7개 테스트 추가)

## TDD 결과
- RED: 새 테스트 7개 작성 → 전부 "Edit 버튼이 없음"이라는 올바른 이유로 실패 확인 (기존 5개는 그대로 통과)
- GREEN: `ProjectDetail.tsx`에 Edit 버튼 + 인라인 폼 구현 → 신규 7개 포함 12/12 통과
- 프론트엔드 전체 스위트 재실행: 12개 테스트 파일, 89/89 전체 통과 (회귀 없음)
- `eslint`, `tsc --noEmit` 모두 클린
- 실제 브라우저(Playwright MCP)로도 재검증: 프로젝트 생성 → Edit 클릭 → 제목/설명 수정 → Save → 화면 즉시 반영 → 새로고침 후에도 유지 확인 (`http://localhost:8000/api/v1/projects/{id}` PATCH가 실제로 호출되어 persist됨을 확인). 검증에 쓴 프로젝트는 테스트 후 소프트 삭제로 정리.
- Git 저장소가 아직 초기화되지 않아 커밋은 생략했습니다.

## 기술 결정
- 별도 모달이 아니라 `ProjectDetail` 내부 인라인 폼으로 구현했습니다. T056a 설명 자체가 "Edit 버튼 + 폼을 ProjectDetail 페이지에"라고 명시했고, CreateProjectModal처럼 별도 다이얼로그로 띄울 필요 없이 이미 보고 있는 화면에서 바로 고치는 편이 자연스럽다고 판단했습니다.
- 수정 성공 후 `invalidateQueries` 대신 `setQueryData`를 사용했습니다. PATCH 응답이 이미 최신 상태를 담고 있어 재조회(refetch) 없이 캐시를 바로 갱신하는 게 더 빠르고, 테스트에서도 추가 `getProject` 모크 설정 없이 결과를 바로 검증할 수 있습니다.
- 타이틀 공백 검증(trim 후 길이 체크)은 `CreateProjectModal`과 동일한 규칙을 그대로 재사용했습니다. 백엔드 `InvalidProjectTitleError`와 동일한 제약이라 프론트/백엔드 검증 기준을 맞췄습니다.

## 비고
tasks.md의 `Total Task Count`를 216 → 217, `Projects` 섹션을 18 → 19 tasks로 갱신했습니다 (사유 기록 포함). 기존 T051~T060 번호는 재번호 매기지 않고 "T056a"로 끼워 넣어 기존 테스트 주석/task report 파일명과의 참조가 깨지지 않도록 했습니다.
