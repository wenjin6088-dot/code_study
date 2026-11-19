# TASK-018. React Router 설정

## 상태
완료

## 날짜
2026-11-02

## 작업 요약
웹사이트에서 "주소창의 URL이 바뀌면 화면도 바뀌는" 동작을 만드는 게 라우터입니다. 일반 웹사이트는 주소가 바뀔 때마다 서버에 새 페이지를 요청하지만, React 같은 SPA(싱글 페이지 앱)는 페이지 전체를 다시 불러오지 않고 "화면의 일부만 바꿔 끼우는" 방식으로 동작합니다. `react-router-dom`이 바로 이 "주소 ↔ 화면" 매칭을 담당합니다.

`frontend/src/App.tsx`에 plan.md가 정의한 6개 페이지에 대응하는 경로를 만들었습니다.

| 경로 | 페이지 | 비고 |
|---|---|---|
| `/login` | 로그인 | |
| `/register` | 회원가입 | |
| `/` | Dashboard(프로젝트 목록) | |
| `/projects/:projectId` | ProjectDetail | 프로젝트 ID를 URL에 담음 |
| `/projects/:projectId/tasks/:taskId` | TaskDetail | 프로젝트+태스크 ID를 URL에 담음 |
| `/trash` | Trash(휴지통) | |
| 그 외 모든 경로 | `/`로 리다이렉트 | 오타 등 잘못된 주소 처리 |

T003에서 "AI Code Learning Platform"이라는 제목만 보여주던 placeholder `App.tsx`를 이번에 실제 라우팅 구조로 교체했습니다.

## 변경 파일
- `frontend/src/App.tsx` (수정: placeholder 제목 → `BrowserRouter`/`Routes` 기반 라우팅 구조)

## TDD 결과
- 라우팅 구조는 "URL과 화면이 올바르게 매칭되는가"가 핵심이라, 실제 Vite 개발 서버를 띄워 각 경로에 직접 접근해 검증했습니다.
  - `eslint`, `prettier --check` 통과
  - `npm run build`(타입체크 + 프로덕션 빌드) 성공
  - `npm run dev`로 실제 서버 기동 후:
    - `GET /` → `200`
    - `GET /trash` (클라이언트 라우트에 **직접** 접근/새로고침하는 상황을 흉내냄) → `200`, SPA fallback으로 `index.html`이 정상 응답됨을 확인. 이게 안 되면 사용자가 `/trash`에서 새로고침할 때 404가 뜨는 흔한 SPA 라우팅 버그가 생깁니다.
    - `GET /projects/abc/tasks/123` (동적 파라미터가 2단계로 중첩된 경로) → `200`
    - `/src/App.tsx`가 Vite에서 에러 없이 변환됨을 확인 (react-router-dom import 정상 작동)
  - 검증 후 `npm run build`가 남긴 `dist/` 산출물은 정리했습니다.
  - Chrome 브라우저 자동화 도구가 이 세션에서 연결 해제되어 있어, 각 페이지에 실제로 어떤 placeholder 문구가 보이는지 **시각적으로는 직접 확인하지 못했습니다** (HTTP 상태 코드와 SPA fallback 동작까지만 검증).
- 저장소가 아직 git으로 초기화되지 않아 관련 커밋은 생성하지 않았습니다.
- 테스트 커버리지: 해당 없음 (라우팅 구조, 아직 테스트 대상 로직 없음)

## 기술 결정
- **각 페이지를 `App.tsx` 안에 임시 placeholder 컴포넌트로 직접 정의**: 실제 페이지 파일(`Dashboard.tsx` T054, `Login.tsx` T036, `Register.tsx` T035, `ProjectDetail.tsx`/`TaskDetail.tsx` T055/T083, `Trash.tsx` T181)은 각자의 Task에서 만들어질 예정이라, 지금 미리 만들지 않았습니다(YAGNI, 범위 침범 방지). 대신 `<div>Dashboard (placeholder)</div>` 같은 최소한의 더미 컴포넌트로 라우팅 구조 자체만 검증 가능하게 했습니다. 해당 Task들이 진행되면 이 파일을 수정해 `import Dashboard from './pages/Dashboard'` 형태로 교체하면 됩니다.
- **인증 보호(`ProtectedRoute`) 적용 안 함**: T037("ProtectedRoute wrapper 컴포넌트")이 아직 구현되지 않아, 지금은 모든 경로가 보호 없이 열려 있습니다. T037이 완료되면 `/`, `/projects/*`, `/trash` 같은 보호가 필요한 경로를 `<ProtectedRoute>`로 감싸는 작업이 필요합니다.
- **알 수 없는 경로는 `/`로 리다이렉트**: 404 전용 페이지를 아직 만들지 않은 상태에서, 잘못된 URL로 들어온 사용자가 완전히 빈 화면을 보지 않도록 홈으로 돌려보내는 가장 단순한 처리를 선택했습니다.
- **`BrowserRouter` 사용** (History API 기반): `HashRouter`(URL에 `#`가 붙는 방식)보다 깔끔한 URL을 제공하며, quickstart.md에도 `http://localhost:5173/`처럼 `#` 없는 주소로 안내되어 있어 이에 맞췄습니다.

## 비고
- T019(TanStack Query), T020(axios API 클라이언트), T021(Zustand 스토어)가 완료되면, 이 라우팅 구조 위에 실제 데이터 로딩과 상태 관리가 연결될 예정입니다.
- 각 페이지의 실제 시각적 렌더링(placeholder 문구가 보이는지 등)은 사용자가 `npm run dev` 실행 후 브라우저에서 `http://localhost:5173/`, `/login`, `/trash` 등을 직접 열어 확인하는 것을 권장합니다.
