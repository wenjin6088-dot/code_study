# TASK-055. ProjectDetail 페이지

## 상태
완료

## 날짜
2026-11-09

## 작업 요약
프로젝트 하나를 자세히 보는 ProjectDetail 페이지를 구현했습니다. 기존 `App.tsx`에 있던 "Project Detail (placeholder)" 임시 컴포넌트를 실제 페이지로 교체했습니다.

이 페이지는 URL 경로 파라미터(`/projects/:projectId`)에서 `projectId`를 읽어서, TanStack Query로 `getProject(projectId)`를 호출해 해당 프로젝트 정보를 가져옵니다. 불러오는 동안에는 `role="status"` 로딩 표시를 보여줍니다. 성공하면 프로젝트 제목(heading)과 설명을 보여주고, 그 아래에는 항상 "Tasks"라는 제목의 섹션이 나옵니다. 이 Tasks 섹션은 아직 실제 작업(Task) 기능이 구현되지 않았기 때문에(명세 T055에서 의도적으로 정해둔 스켈레톤/플레이스홀더), 안내 문구만 보여주고 실제 작업 목록(`<li>` 항목)은 하나도 그리지 않습니다.

프로젝트를 가져오다가 실패하면(예: 존재하지 않거나 내 소유가 아닌 프로젝트, 404 에러), 화면이 깨지지 않고 "프로젝트를 찾을 수 없습니다"라는 문구를 보여줍니다.

## 변경 파일
- `frontend/src/pages/ProjectDetail.tsx` (신규)
- `frontend/src/App.tsx` (TASK-054와 함께 placeholder 교체, 상세 내용은 TASK-054 보고서 참고)

## TDD 결과
- 테스트 파일: `frontend/tests/integration/pages/ProjectDetail.test.tsx` (5개 테스트, 기존에 이미 작성되어 있던 실패 테스트)
- GREEN 확인: `npx vitest run` 실행 결과 5개 테스트 전부 통과. 전체 스위트(82개 테스트)도 모두 통과하는 것을 확인했습니다.
- Git 저장소가 아직 초기화되지 않아 커밋은 생략했습니다.

## 기술 결정 (해당 시)
- `useParams<{ projectId: string }>()`로 라우트 파라미터를 읽었고, TanStack Query의 `queryKey`를 `['project', projectId]`로 설정해 프로젝트별로 캐시가 분리되도록 했습니다.
- 에러 상태(`isError`)와 데이터 없음(`!project`) 두 경우를 하나의 조건으로 묶어 "찾을 수 없음" 메시지를 보여주도록 했습니다. 서버가 404를 내려주면 `getProject`가 던지는 에러 메시지 자체도 "프로젝트를 찾을 수 없습니다"를 포함하지만, 화면에는 고정 문구를 직접 표시하도록 해서 에러 메시지 형식이 바뀌어도 화면 문구가 흔들리지 않게 했습니다.
- Tasks 섹션은 실제 Task 엔티티나 API가 아직 없으므로(명세에서 "Task 엔티티가 아직 만들어지지 않았다"고 명시), 고정된 안내 문구만 넣은 최소 스켈레톤으로 구현했습니다.

## 비고
- Task 목록, Task 추가 등 실제 기능은 이후 별도 Task(Task 엔티티 구현 이후)에서 이 Tasks 섹션을 교체하게 될 것입니다.
