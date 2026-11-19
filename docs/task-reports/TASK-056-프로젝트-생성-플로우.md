# TASK-056. 프로젝트 생성 플로우

## 상태
완료

## 날짜
2026-11-09

## 작업 요약
Dashboard 페이지에서 "Create Project" 버튼을 눌러 새 프로젝트를 만들고, 그 결과가 새로고침 없이 목록에 바로 나타나는 전체 흐름(플로우)을 연결했습니다. 이 Task는 별도의 새 파일을 만들지 않고, TASK-052(`CreateProjectModal`)와 TASK-054(`Dashboard`)에서 이미 구현한 두 컴포넌트를 올바르게 연결하는 작업입니다.

흐름은 다음과 같습니다. 1) 사용자가 "Create Project"를 누르면 Dashboard의 `isModalOpen` 상태가 true가 되어 모달이 열립니다. 2) 모달에서 제목(필수)과 설명(선택)을 입력하고 "Create"를 누르면 모달이 직접 `createProject` API를 호출합니다. 3) 생성이 성공하면 모달은 `onCreate(생성된 프로젝트)`를 호출합니다. 4) Dashboard의 `handleCreate` 함수가 이를 받아서 모달을 닫고(`setIsModalOpen(false)`), TanStack Query 캐시에서 `['projects']` 쿼리를 무효화합니다. 5) 캐시 무효화로 `listProjects`가 다시 호출되어, 새로 만든 프로젝트가 포함된 최신 목록이 화면에 그려집니다.

## 변경 파일
별도 신규 파일은 없습니다. 이 흐름은 아래 두 파일의 구현으로 완성됩니다(각각 TASK-052, TASK-054에서 작성).
- `frontend/src/components/project/CreateProjectModal.tsx`
- `frontend/src/pages/Dashboard.tsx`

## TDD 결과
- 테스트: `frontend/tests/integration/pages/Dashboard.test.tsx`의 `'should show the newly created project in the list after a successful creation'` 테스트가 이 플로우 전체를 검증합니다. 이 테스트는 `listProjects`가 1번째 호출 때는 기존 프로젝트만, 2번째 호출(캐시 무효화 후 재조회) 때는 기존 프로젝트 + 새 프로젝트를 반환하도록 모킹되어 있고, 모달을 열어 제목을 입력하고 Create를 누른 뒤 새 프로젝트가 화면에 보이는지, `listProjects`가 정확히 2번 호출됐는지를 확인합니다.
- GREEN 확인: 이 테스트를 포함한 Dashboard 테스트 7개 전부 통과했습니다. `npx vitest run` 기준 전체 82개 테스트 통과.
- Git 저장소가 아직 초기화되지 않아 커밋은 생략했습니다.

## 기술 결정 (해당 시)
- "모달을 닫을지"와 "목록을 어떻게 갱신할지"를 모두 Dashboard의 `onCreate` 핸들러 한곳에 모아서, CreateProjectModal은 "생성 성공/실패를 알리는 역할"만 하도록 책임을 분리했습니다. 이렇게 하면 추후 다른 화면(예: 프로젝트 목록이 아닌 다른 곳)에서 같은 모달을 재사용할 때 그 화면에 맞는 후처리를 자유롭게 정의할 수 있습니다.
- 목록 갱신은 수동으로 로컬 상태 배열에 새 프로젝트를 추가하는 대신, TanStack Query의 `invalidateQueries`로 서버에서 다시 받아오는 방식을 택했습니다. 서버가 내려주는 정렬 순서, 추가 필드 등을 신뢰할 수 있고 코드도 더 단순해지기 때문입니다.

## 비고
- 없음.
