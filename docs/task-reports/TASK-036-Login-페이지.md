# TASK-036. Login 페이지 구현

## 상태
완료

## 날짜
2026-11-09

## 작업 요약
로그인 라우트(`/login`)에서 보여줄 페이지를 `frontend/src/pages/Login.tsx`에 만들었습니다. T033의 `LoginForm`을 렌더링하고, 로그인이 성공하면(`onSuccess` 콜백으로 받은 사용자 정보를) `frontend/src/stores/auth-store.ts`의 `useAuthStore.setUser()`로 전역 상태에 저장합니다. 그다음 어디로 이동할지는 두 가지 경우로 나뉩니다.

- 사용자가 `ProtectedRoute`(T037)에 막혀서 로그인 페이지로 리다이렉트되어 온 경우: react-router의 네비게이션 state(`location.state.from.pathname`)에 원래 가려던 경로가 담겨 있으므로, 로그인 성공 후 그 경로로 되돌려 보냅니다.
- 그런 state가 없는 경우(그냥 `/login`으로 바로 들어온 경우): 기본 목적지인 대시보드(`/`)로 보냅니다.

로그인 실패 시의 에러 표시·버튼 재활성화는 `LoginForm`이 처리하므로 이 페이지는 `/login`에 그대로 머뭅니다.

## 변경 파일
- `frontend/src/pages/Login.tsx` (신규 생성)

## TDD 결과
- `frontend/tests/integration/pages/Login.test.tsx`(4개 테스트, RED 상태)를 먼저 읽었습니다. `LoginForm`은 모킹하지 않고 실제로 렌더링하며, `authService.login`만 모킹해서 "폼이 보이는지", "이전 경로 정보가 없을 때 `/`로 이동하며 스토어에 사용자가 저장되는지", "`location.state.from.pathname`이 있을 때 그 경로로 이동하는지", "실패 시 `/login`에 머물고 스토어는 비로그인 상태로 남는지"를 검증합니다.
- GREEN 확인: 4개 테스트 전부 통과.
- Git 저장소가 아직 초기화되지 않아 커밋은 생략했습니다.

## 기술 결정
- **`navigate(..., { replace: true })` 사용**: 로그인 페이지를 브라우저 히스토리에 남기지 않아서, 로그인 후 뒤로가기를 눌렀을 때 다시 로그인 폼으로 돌아가지 않도록 했습니다. 테스트가 직접 요구하지는 않지만, 일반적인 로그인 UX 관례이고 다른 동작과 충돌하지 않아 적용했습니다.
- **`location.state`를 `{ from?: { pathname: string } } | null`로 타입 단언**: `ProtectedRoute`(T037)가 `state={{ from: location }}` 형태로 넘기는 것과 맞춰, `from.pathname`만 꺼내 씁니다. react-router의 `Location` state는 타입이 `unknown`이라 이 지점에서만 좁혀서 사용했습니다.
- **store 업데이트와 네비게이션을 모두 페이지가 담당**: `LoginForm`은 인증 상태를 전혀 모르는 순수 폼으로 남기고, "로그인 성공 후 무엇을 할지"는 전부 이 페이지에 모아뒀습니다.

## 비고
- `frontend/src/App.tsx`의 `/login` 라우트를 이 페이지로 교체했습니다(기존 placeholder `Login` 함수 제거).
- 이 페이지는 T038 `useAuth` 훅을 쓰지 않고 `useAuthStore`를 직접 씁니다. 로그인 성공 처리에는 훅의 자동 세션 복구·갱신 로직이 필요 없고, 테스트도 `useAuthStore`를 직접 검증하기 때문입니다.
