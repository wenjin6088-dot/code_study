# TASK-038. useAuth 훅(자동 토큰 갱신) 구현

## 상태
완료

## 날짜
2026-11-09

## 작업 요약
앱 전체의 로그인 상태를 관리하는 React 훅을 `frontend/src/hooks/useAuth.ts`에 만들었습니다. T021에서 만든 `useAuthStore`(zustand, 사용자 정보만 들고 있음)와 T034의 `auth-service`를 묶어서, "앱이 켜질 때 쿠키로 로그인 상태를 복구하고, 로그인된 동안 세션이 끊기지 않게 주기적으로 갱신해주는" 역할을 합니다.

동작 순서는 이렇습니다.
1. 훅이 처음 마운트되면 `isLoading`이 `true`로 시작하고, `authService.getCurrentUser()`로 "지금 쿠키로 로그인된 사용자가 있는지" 확인합니다.
2. 성공하면 `useAuthStore.setUser()`로 저장하고 배경 토큰 갱신 타이머(15분 간격 `authService.refreshToken()`)를 켭니다.
3. 실패하면(세션 쿠키가 만료됐을 수 있음) 한 번만 `authService.refreshToken()`을 시도하고, 성공하면 `getCurrentUser()`를 다시 불러 로그인 상태로 복구합니다. 그마저도 실패하면 `useAuthStore.clearAuth()`로 완전히 비로그인 상태로 정리합니다. 이 과정이 끝나야 `isLoading`이 `false`가 됩니다.
4. `login(email, password)`은 `authService.login`을 호출해 성공하면 스토어에 저장하고 갱신 타이머를 켭니다.
5. `logout()`은 `authService.logout()` 호출 후 스토어를 비우고 갱신 타이머를 멈춥니다.

이 훅은 `{ user, isAuthenticated, isLoading, login, logout }`을 반환하며, T037 `ProtectedRoute`가 바로 이 값을 읽어서 라우트를 보호합니다.

## 변경 파일
- `frontend/src/hooks/useAuth.ts` (신규 생성)

## TDD 결과
- `frontend/tests/unit/hooks/useAuth.test.ts`(6개 테스트, RED 상태)를 먼저 읽었습니다. 특히 "15분 뒤 배경 갱신이 호출되는지"를 확인하는 테스트는 vitest의 fake timer(`vi.useFakeTimers()` / `vi.advanceTimersByTimeAsync`)를 쓰므로, 구현에서 `setInterval`을 직접 써야 그 테스트가 통과한다는 점을 미리 확인했습니다.
- GREEN 확인: 6개 테스트 전부 통과 — 초기 로딩→정상 복구, 복구 실패 시 1회 재시도 흐름, 둘 다 실패 시 스토어 초기화, 15분 뒤 배경 갱신 호출, `login()` 성공 시 스토어 갱신, `logout()` 시 스토어 초기화와 타이머 중단(로그아웃 후 30분을 더 흘려도 추가 호출 없음)까지 모두 확인했습니다.
- Git 저장소가 아직 초기화되지 않아 커밋은 생략했습니다.

## 기술 결정
- **`setInterval` + `clearInterval`을 `useRef`로 관리**: 리렌더링 사이에 타이머 참조를 유지해야 `logout()`에서 정확히 멈출 수 있어서, 매 렌더마다 새로 만들어지는 일반 변수 대신 ref를 썼습니다.
- **배경 갱신 실패는 무시(`.catch(() => {})`)**: 15분 주기 갱신이 실패했다고 당장 사용자를 로그아웃시키는 동작은 테스트에 없고, 다음 API 호출이 401을 받았을 때 처리하는 것이 더 자연스럽다고 판단해 조용히 무시하도록 최소화했습니다.
- **`useEffect`의 mount 로직은 의도적으로 1회만 실행(`eslint-disable-next-line react-hooks/exhaustive-deps`)**: `setUser`/`clearAuth` 등 zustand 액션은 참조가 안정적이지만, 의존성 배열에 넣으면 불필요한 재마운트 위험이 있어 마운트 시 1회 실행 의도를 명시적으로 남겼습니다.

## 비고
- 이 훅은 아직 어떤 컴포넌트에서도 호출되지 않습니다(테스트에서만 `renderHook`으로 직접 사용). 실제로 세션을 살아있게 유지하려면 앱 최상단(예: `App.tsx`)에서 이 훅을 한 번 호출해 둬야 하는데, 이번 작업 범위(T032~T038)에는 포함되지 않아 손대지 않았습니다. 다음 작업에서 `App.tsx` 루트에 `useAuth()`를 호출하는 Provider나 최상위 컴포넌트를 추가하는 것을 권장합니다.
