# TASK-037. ProtectedRoute 래퍼 컴포넌트 구현

## 상태
완료

## 날짜
2026-11-09

## 작업 요약
로그인하지 않은 사용자가 보호된 페이지에 들어오지 못하게 막는 래퍼 컴포넌트를 `frontend/src/components/auth/ProtectedRoute.tsx`에 만들었습니다. `<ProtectedRoute>{children}</ProtectedRoute>` 형태로 감싸서 쓰고, 내부에서 T038의 `useAuth()` 훅이 돌려주는 `{ isAuthenticated, isLoading }` 값으로 세 가지 상태를 구분합니다.

- `isLoading`이 `true`인 동안: 아직 로그인 여부를 확인 중이므로 "Loading..." 문구(`role="status"`)만 보여주고, children도 렌더링하지 않고 리다이렉트도 하지 않습니다. (앱이 처음 켜질 때 쿠키로 로그인 상태를 복구하는 중간에 깜빡 로그인 화면으로 튕기는 것을 막는 핵심 동작입니다.)
- 로딩이 끝났고 `isAuthenticated`가 `true`: children을 그대로 렌더링합니다.
- 로딩이 끝났고 `isAuthenticated`가 `false`: react-router의 `<Navigate to="/login" />`로 보내면서, 지금 있던 위치(`location`)를 `state.from`에 담아서 넘깁니다. 이렇게 하면 T036 Login 페이지가 로그인 성공 후 원래 가려던 곳으로 되돌려 보낼 수 있습니다.

## 변경 파일
- `frontend/src/components/auth/ProtectedRoute.tsx` (신규 생성)

## TDD 결과
- `frontend/tests/unit/components/auth/ProtectedRoute.test.tsx`(4개 테스트, RED 상태)를 먼저 읽었습니다. 이 테스트는 `useAuth` 훅 자체를 모킹해서 세 가지 상태(인증됨/로딩중/비인증) 각각의 렌더링 결과와, 리다이렉트 시 `state.from.pathname`이 실제로 전달되는지를 검증합니다.
- GREEN 확인: 4개 테스트 전부 통과.
- Git 저장소가 아직 초기화되지 않아 커밋은 생략했습니다.

## 기술 결정
- **`useLocation()`으로 얻은 `location` 객체를 그대로 `from`에 전달**: 테스트가 `from.pathname`만 확인하지만, `location` 객체 전체(pathname, search, hash 등)를 넘겨두면 나중에 쿼리스트링까지 보존해서 돌려보낼 수 있어 더 유용합니다. 굳이 `{ pathname: location.pathname }`로 축소하지 않았습니다.
- **로딩 표시를 `<div role="status">Loading...</div>`로 최소화**: 테스트는 `/loading/i` 텍스트와 children 비노출만 확인하므로, 스피너 애니메이션 등 추가 UI를 만들지 않았습니다.
- **`<Navigate replace />` 사용**: 인증 실패로 인한 리다이렉트를 히스토리에 남기지 않아, 로그인 후 뒤로가기를 눌렀을 때 보호된 페이지로 튕겨나가는 루프를 만들지 않도록 했습니다.

## 비고
- `frontend/src/App.tsx`에서 대시보드(`/`), `/projects/:projectId`, `/projects/:projectId/tasks/:taskId`, `/trash` 라우트를 이 컴포넌트로 감쌌습니다. 이 네 라우트는 아직 placeholder 컴포넌트지만, 로그인 여부와 무관하게 항상 보이던 기존 동작을 실제 인증 체크로 바꿨습니다. 기존 어떤 테스트도 이 네 라우트의 비보호 상태를 가정하지 않아 회귀가 없음을 전체 테스트 실행으로 확인했습니다.
