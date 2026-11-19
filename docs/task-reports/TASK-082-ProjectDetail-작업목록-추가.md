# TASK-082. ProjectDetail 작업 목록/생성 추가

## 상태
완료

## 날짜
2026-11-16

## 작업 요약
기존 `ProjectDetail` 페이지(TASK-055/056a)에 작업(Task) 목록 표시와 생성 기능을 추가했습니다. 기존에 보기 모드/수정 모드 두 곳에 각각 정적으로 박혀 있던 `<h2>Tasks</h2><p>아직 작업이 없습니다</p>` 블록을 `listTasks(projectId)` 쿼리 결과를 반영하는 공통 `tasksSection`으로 교체했습니다. 작업이 있으면 `<ul>` 안에 `TaskCard`(T079)를 `<li>`로 렌더링하고, 클릭 시 `/projects/{projectId}/tasks/{task.id}`로 이동합니다. "작업 추가" 버튼으로 `CreateTaskModal`(T081)을 열고, 생성이 성공하면 `queryClient.invalidateQueries({queryKey:['tasks', projectId]})`로 목록을 갱신합니다.

## 변경 파일
- `frontend/src/pages/ProjectDetail.tsx` (수정)
- `frontend/tests/integration/pages/ProjectDetail.test.tsx` (수정 — task-service 모킹 추가 및 작업 목록/생성 테스트 5개 추가)

## TDD 결과
- RED: 새로 추가한 5개 테스트(목록 렌더링, `listTasks` 호출 검증, 카드 클릭 네비게이션, "작업 추가" 버튼으로 모달 열기, 생성 후 모달 닫힘+목록 갱신)가 기존 `CreateTaskModal` import 실패 등으로 실패하는 것을 확인.
- GREEN: 구현 후 `npx vitest run tests/integration/pages/ProjectDetail.test.tsx` 22개 테스트(기존 17개 + 신규 5개) 전부 통과.
- Git 저장소가 아직 초기화되지 않아 커밋 해시는 없습니다.

## 기술 결정 (해당 시)
- 기존에 있던 "getProject만 모킹하고 listTasks는 모킹하지 않는" "Tasks placeholder" 테스트를 보호하기 위해, 테스트 파일에 `vi.mock('@/services/task-service')`를 추가하고 `beforeEach`에서 `mockedListTasks.mockResolvedValue([])`를 기본값으로 설정했습니다. 이렇게 하면 실제 백엔드로 네트워크 요청을 보내는 대신 "작업 없음" 상태를 결정적으로 재현하면서도, 원래 테스트가 검증하던 "Tasks" 헤딩과 `listitem` 없음이라는 두 어서션을 그대로 통과시킵니다. 이는 과제 설명에서 허용한 "필요하면 그 테스트 파일도 함께 업데이트하되, 기존 어서션을 깨지 않게" 범위 내의 변경입니다.
- `tasksSection`을 JSX 변수로 한 번만 만들어서 보기 모드/수정 모드 두 분기에 `{tasksSection}`으로 똑같이 삽입했습니다. 두 모드에서 작업 목록 UI가 완전히 동일해야 하므로(수정 모드에서도 작업 목록은 그대로 보여야 함), 중복 마크업을 피하고 한 곳만 수정하면 되도록 했습니다.
- `listTasks` 쿼리는 `getProject` 쿼리와 독립적으로 Hook 규칙을 지키기 위해 두 early return(로딩/에러) 이전에 선언했습니다. `project`가 아직 없어도 `projectId`만으로 작업 목록을 미리 가져올 수 있어, 프로젝트 로딩이 끝난 직후 작업 목록도 바로 보이는 효과가 있습니다.
- 작업 생성 콜백에서 `setIsTaskModalOpen(false)`로 모달을 직접 닫는 책임은 `ProjectDetail`(부모)에 있습니다. `CreateTaskModal` 자신은 `onClose`를 호출하지 않는다는 T081의 계약을 그대로 지켰습니다.

## 비고
- 테스트에서 `navigate` 동작을 검증하기 위해 `MemoryRouter`의 `<Routes>`에 `/projects/:projectId/tasks/:taskId` 플레이스홀더 라우트("Task Detail Page")를 추가했습니다. 실제 앱에서는 이 라우트가 T083의 `TaskDetail` 페이지로 연결됩니다.
