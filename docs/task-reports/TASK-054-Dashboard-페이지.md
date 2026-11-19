# TASK-054. Dashboard 페이지

## 상태
완료

## 날짜
2026-11-09

## 작업 요약
로그인 후 가장 먼저 보는 화면인 Dashboard 페이지를 구현했습니다. 기존 `App.tsx`에 있던 "Dashboard (placeholder)"라는 임시 컴포넌트를 실제 페이지로 교체했습니다.

화면이 열리면 TanStack Query의 `useQuery`로 `listProjects`를 호출해 내 프로젝트 목록을 가져옵니다. 데이터를 불러오는 동안에는 `role="status"` 로딩 표시를 보여줍니다. 로딩이 끝났는데 프로젝트가 하나도 없으면 "아직 프로젝트가 없습니다"라는 안내 문구를 보여주고, 프로젝트가 있으면 각 프로젝트마다 TASK-051에서 만든 `ProjectCard`를 하나씩 그립니다. 카드를 클릭하면 `useNavigate`를 이용해 `/projects/{프로젝트 id}` 경로로 이동합니다(ProjectCard 자체는 이동 로직을 모르고, Dashboard가 "클릭하면 이렇게 이동해라"는 함수를 넘겨줍니다).

화면 위쪽에는 항상 "Create Project" 버튼이 보이고, 누르면 TASK-052의 `CreateProjectModal`이 열립니다. 모달에서 프로젝트 생성이 성공하면(`onCreate` 콜백이 호출되면) 모달을 닫고, TanStack Query의 캐시를 무효화(`invalidateQueries`)해서 프로젝트 목록을 다시 불러오게 합니다. 이렇게 하면 새로고침 없이 방금 만든 프로젝트가 목록에 바로 나타납니다.

## 변경 파일
- `frontend/src/pages/Dashboard.tsx` (신규)
- `frontend/src/App.tsx` (기존 placeholder `Dashboard`, `ProjectDetail` 함수를 제거하고, 각각 `./pages/Dashboard`와 `./pages/ProjectDetail`의 default export로 교체)

## TDD 결과
- 테스트 파일: `frontend/tests/integration/pages/Dashboard.test.tsx` (7개 테스트, 기존에 이미 작성되어 있던 실패 테스트. 이 중 하나는 TASK-056 프로젝트 생성 플로우를 검증합니다)
- GREEN 확인: `npx vitest run` 실행 결과 7개 테스트 전부 통과. 함께 전체 스위트(82개 테스트)도 모두 통과하는 것을 확인했습니다.
- Git 저장소가 아직 초기화되지 않아 커밋은 생략했습니다.

## 기술 결정 (해당 시)
- `QueryClientProvider`는 이미 `frontend/src/main.tsx`에서 앱 전체를 감싸고 있었기 때문에(싱글턴 `queryClient`, `frontend/src/lib/queryClient.ts`), `App.tsx`나 `Dashboard.tsx`에 별도로 추가하지 않았습니다. 중복된 QueryClient 인스턴스를 만들지 않기 위한 결정입니다.
- `useQueryClient().invalidateQueries({ queryKey: ['projects'] })`로 캐시 무효화 후 자동 재조회(refetch)되도록 했습니다. 별도의 `refetch()` 호출이나 수동 상태 갱신 코드를 추가하지 않은 것은 TanStack Query의 기본 동작(활성 쿼리는 무효화되면 자동으로 다시 불러옴)에 맡겼기 때문입니다.
- 라우팅은 `react-router-dom`의 `useNavigate`를 사용했고, ProjectCard가 아니라 Dashboard가 네비게이션 책임을 가지도록 했습니다(TASK-051 설계 결정과 일치).

## 비고
- 없음.
