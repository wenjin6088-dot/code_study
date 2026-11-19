# TASK-042. 로그아웃 브라우저 수동 테스트 (+ 쿠키 미삭제 버그 수정)

## 상태
완료

## 날짜
2026-11-09

## 작업 요약
로그인한 상태에서 로그아웃을 호출했을 때, 인증 쿠키가 실제로 지워지고 이후 보호된 페이지 접근 시 로그인 화면으로 돌아가는지 확인하는 작업입니다. 이 과정에서 실제 버그를 하나 발견해서 TDD 절차(RED → GREEN)로 수정했습니다.

### 발견한 문제
`backend/src/api/auth.py`의 `logout` 엔드포인트는 DB에서 refresh token을 폐기(revoke)만 할 뿐, 브라우저에 저장된 `access_token`/`refresh_token` 쿠키 자체를 지우는 코드가 없었습니다. 그 결과:
- 로그아웃을 호출해도 `access_token` 쿠키가 만료 전까지는 그대로 유효해서, 로그아웃 이후에도 `GET /auth/me`가 계속 200(로그인 상태)을 반환
- 이로 인해 보호된 페이지(`/trash` 등)에 재접근했을 때 로그인 화면으로 안 돌아가고 그대로 보임 (tasks.md T042가 요구하는 "쿠키 삭제 확인"을 충족하지 못함)

자동화된 백엔드 테스트(T028-T031, 23개)는 모두 통과하고 있었지만, 그 테스트들은 "DB에서 토큰이 폐기되는지"만 검증했지 "응답에 쿠키 삭제 헤더가 포함되는지"는 검증하지 않아서 이 버그를 못 잡고 있었습니다.

### 수정 절차 (TDD)
1. **RED**: `backend/tests/integration/test_auth_api.py`의 `TestLogout`에 `test_logout_clears_auth_cookies` 테스트를 추가 — 로그아웃 응답의 `Set-Cookie` 헤더에 `access_token`, `refresh_token` 둘 다 `Max-Age=0`(즉시 만료)으로 설정되는지 검증. 추가 직후 실행해서 실패(`AssertionError: []`, 즉 Set-Cookie 헤더가 아예 없음)하는 것을 확인.
2. **GREEN**: `backend/src/api/auth.py`의 `logout` 함수에 `Response` 파라미터를 추가하고, `response.delete_cookie(ACCESS_TOKEN_COOKIE_NAME, ...)` / `response.delete_cookie(REFRESH_TOKEN_COOKIE_NAME, ...)`를 호출하도록 수정. 테스트가 통과함을 확인.
3. 전체 백엔드 테스트(`pytest tests/ -q`) 58개 모두 통과, `ruff check src/` 깨끗함을 재확인.

### 브라우저 재검증
수정된 코드로 개발 서버를 재시작한 뒤:
1. 로그인 상태에서 `fetch('/api/v1/auth/logout', {credentials:'include'})` 호출 → 204 응답
2. 곧바로 `fetch('/api/v1/auth/me', {credentials:'include'})` 호출 → 401 응답 (쿠키가 실제로 지워졌음을 확인)
3. 보호된 페이지(`/trash`)로 이동 → 즉시 `/login`으로 리다이렉트됨 (스크린샷으로 확인)

## 변경 파일
- `backend/src/api/auth.py` — `logout` 핸들러가 `Response`를 받아 두 인증 쿠키를 명시적으로 삭제하도록 수정
- `backend/tests/integration/test_auth_api.py` — `test_logout_clears_auth_cookies` 테스트 추가 (TestLogout 클래스)
- `specs/001-ai-code-learning-platform/tasks.md` — T039~T042 `[X]` 처리

## TDD 결과
- RED: `test_logout_clears_auth_cookies` 추가 직후 실패 확인 (Set-Cookie 헤더 없음)
- GREEN: `response.delete_cookie(...)` 2줄 추가로 테스트 통과
- REFACTOR: 별도 리팩토링 불필요 (최소 수정)
- 테스트 커버리지: 백엔드 인증 API 테스트 24개 전체 통과 (전체 스위트 58개)
- Git 저장소가 아직 초기화되지 않아 커밋은 생략했습니다. (RED/GREEN 커밋 해시 없음)

## 기술 결정
자동화 테스트가 "성공 상태 코드"만 확인하고 "부수 효과(쿠키 삭제 같은 응답 헤더)"를 놓칠 수 있다는 걸 보여준 사례입니다. 이번 건은 수동 브라우저 테스트(E2E 관점)가 자동화 단위/통합 테스트의 사각지대를 잡아낸 경우이므로, 앞으로 인증·세션 관련 엔드포인트를 만들 때는 상태 코드뿐 아니라 쿠키/헤더 부수 효과도 테스트에 포함하는 습관이 필요합니다.

## 비고
현재 프론트엔드에는 아직 "로그아웃" 버튼 UI가 없습니다(T032-T038 범위에는 포함되지 않았고, Dashboard 자체가 아직 placeholder입니다). 이번 테스트는 `authService.logout()`과 동일한 API를 직접 호출해 백엔드/쿠키 동작을 검증했습니다. 실제 로그아웃 버튼 UI는 Dashboard 구현(Phase 4 이후) 시 `useAuth().logout()`을 연결하면 됩니다.
