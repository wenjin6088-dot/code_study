# TASK-083. TaskDetail 페이지 스켈레톤

## 상태
완료

## 날짜
2026-11-16

## 작업 요약
`/projects/:projectId/tasks/:taskId` 라우트가 보여줄 `TaskDetail` 페이지를 새로 만들고, `App.tsx`에 있던 인라인 플레이스홀더(`function TaskDetail() { return <div>Task Detail (placeholder)</div> }`)를 실제 페이지로 교체했습니다. `ProjectDetail`(T055)과 동일한 패턴으로 `useParams`에서 `taskId`를 읽어 `getTask(taskId)`를 TanStack Query로 조회하고, 로딩은 `role="status"`, 에러/404는 "찾을 수 없습니다" 문구로 처리합니다. 작업이 로드되면 제목과 함께 Document/Practice/Q&A 세 개의 탭으로 구성된 `role="tablist"` 스켈레톤을 보여주고, 로컬 state로 활성 탭만 전환합니다. 각 탭의 실제 콘텐츠(문서 뷰어/실습/Q&A 채팅)는 이후 Phase 6~8에서 구현될 예정이라 지금은 플레이스홀더 텍스트만 넣었습니다.

## 변경 파일
- `frontend/src/pages/TaskDetail.tsx` (신규)
- `frontend/src/App.tsx` (수정 — 인라인 `TaskDetail` 플레이스홀더 함수 제거, `import TaskDetail from './pages/TaskDetail'`로 교체. 라우트 path는 변경 없음)
- `frontend/tests/integration/pages/TaskDetail.test.tsx` (신규, RED 테스트)

## TDD 결과
- RED: 페이지가 없는 상태에서 import 실패로 8개 테스트 모두 실패.
- GREEN: 구현 후 `npx vitest run tests/integration/pages/TaskDetail.test.tsx` 8개 테스트 전부 통과.
- 전체 회귀: `npm test` 기준 22개 테스트 파일, 166개 테스트 전부 통과(T076~T083으로 추가/수정된 파일 포함).
- Git 저장소가 아직 초기화되지 않아 커밋 해시는 없습니다.

## 기술 결정 (해당 시)
- 탭 구현은 별도 UI 라이브러리(Radix Tabs 등) 없이 `role="tablist"` + `role="tab"` + `aria-selected`만으로 최소 구현했습니다. 현재는 각 탭에 들어갈 실제 콘텐츠가 플레이스홀더뿐이라, 포커스 트랩이나 방향키 탐색 같은 완전한 WAI-ARIA 탭 패턴까지 구현하는 것은 과도한 선행 투자(YAGNI 위반)라고 판단했습니다. 접근성 상 최소 요건인 `role`/`aria-selected`만 맞췄습니다.
- 탭 콘텐츠를 감싸는 `role="tabpanel"`을 하나만 두고 내부에서 `activeTab`에 따라 조건부로 문단을 바꿔 끼우는 방식을 택했습니다. 탭마다 별도 패널 엘리먼트(`aria-labelledby`로 탭과 연결)를 만드는 대신 단일 패널로 단순화했는데, 이는 지금 각 탭 내용이 플레이스홀더 한 줄뿐이라 여러 패널을 유지보수할 이점이 없기 때문입니다. 실제 콘텐츠가 들어가는 Phase 6~8에서 필요하면 리팩터링하면 됩니다.
- `App.tsx`에서 라우트 `path="/projects/:projectId/tasks/:taskId"`는 그대로 유지하고 `element`에 연결된 컴포넌트만 바꿨습니다. `ProtectedRoute`로 감싸는 구조도 그대로 유지했습니다.

## 비고
- `TaskDetail`은 `taskId`만 사용하고 `projectId`는 현재 읽어오되 사용하지 않습니다(향후 "프로젝트로 돌아가기" 링크 등에 쓰일 수 있어 타입에는 남겨뒀습니다). ESLint의 미사용 변수 경고(`argsIgnorePattern: '^_'`)에 걸리지 않도록, 구조분해 시 `projectId`를 실제로 꺼내지 않고 타입 파라미터로만 선언했습니다.
