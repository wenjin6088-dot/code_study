# TASK-029 / TASK-029A. POST /auth/login, GET /auth/me 엔드포인트 구현

## 상태
완료

## 날짜
2026-11-09

## 작업 요약
`backend/src/api/auth.py`에 로그인(`POST /api/v1/auth/login`)과 내 정보 조회(`GET /api/v1/auth/me`) 두 엔드포인트를 함께 구현했습니다. 두 개를 한 보고서에 묶은 이유는, "로그인하면 쿠키가 발급되고, 그 쿠키로 /me를 호출하면 내 정보가 나온다"는 하나의 흐름을 이루기 때문입니다.

**로그인**: 이메일/비밀번호를 받아 T025의 `UserService.login()`으로 자격 증명을 검증합니다. 비밀번호가 틀리거나 이메일이 존재하지 않으면 서비스가 `InvalidCredentialsError`를 던지는데, 이를 401(Unauthorized)로 변환합니다. 로그인에 성공하면 T026의 `TokenService.issue_tokens()`로 access/refresh 토큰 쌍을 발급받고, 이 토큰들을 `httponly` 쿠키 2개(`access_token`, `refresh_token`)로 응답에 심습니다. 응답 바디로는 Authorization 헤더나 토큰 문자열을 그대로 내려주지 않고, 사용자 정보(JSON)만 내려줍니다 — 토큰은 오직 쿠키로만 전달되고 JS로 읽을 수 없게(httponly) 만들어, XSS 공격으로 토큰이 탈취되는 위험을 줄였습니다.

**내 정보 조회**: 이 엔드포인트는 사실상 새 코드를 거의 쓰지 않았습니다. T027에서 이미 만들어진 `get_current_user` 의존성(Dependency)을 FastAPI의 `Depends()`로 꽂기만 하면, 쿠키 검사·토큰 검증·DB 조회가 전부 자동으로 처리됩니다. 쿠키가 없거나, 깨진 토큰이거나, 만료됐거나, access 자리에 refresh 토큰을 잘못 넣은 경우 전부 `get_current_user` 내부에서 401을 던지므로 `/me` 라우트 코드 자체는 "로그인된 사용자 정보를 그대로 돌려준다" 한 줄짜리 로직만 가집니다.

## 변경 파일
- `backend/src/api/auth.py` (login, me 라우트 포함)
- `backend/src/api/dependencies.py` (수정 없음 — T027에서 만든 `get_current_user`, `ACCESS_TOKEN_COOKIE_NAME`을 그대로 재사용)
- `specs/001-ai-code-learning-platform/tasks.md` (T029, T029A 완료 체크)

## TDD 결과
- **RED**: `TestLogin`(4개), `TestMe`(5개) 테스트가 라우트 미존재로 404 실패하는 것을 먼저 확인했습니다.
- **GREEN**: 구현 후 로그인 관련 4개(200 응답+쿠키 설정, httponly 속성 확인, 틀린 비밀번호 401, 존재하지 않는 이메일 401), /me 관련 5개(정상 토큰으로 조회 성공, 쿠키 없음 401, 깨진 토큰 401, refresh 토큰을 access 자리에 넣은 경우 401, 만료된 토큰 401) 전부 통과했습니다.
- 전체 테스트 57개 재실행, 회귀 없음. `ruff check` 통과.
- Git 저장소가 아직 초기화되지 않아 커밋은 생략했습니다.

## 기술 결정
- **refresh 토큰을 access 자리에 넣었을 때 거부하는 로직을 어디에 둘지**: 이 검사는 사실 이 Task에서 새로 만든 게 아니라, T012에서 만든 `src/utils/jwt.py`의 `decode_access_token()`이 토큰 payload의 `type` 필드가 `"access"`가 아니면 바로 예외를 던지도록 이미 구현돼 있었습니다. 즉 JWT를 만들 때부터 "이 토큰은 access용/refresh용" 용도를 못 박아두고, 디코딩 단계에서 용도가 안 맞으면 거부하는 구조라, `/me` 라우트는 이 안전장치에 대해 아무것도 신경 쓸 필요가 없었습니다.
- **로그인 응답 바디에 토큰을 넣지 않음**: 프론트엔드가 쿠키 기반으로만 동작하도록 설계되어 있어(SPA가 토큰을 localStorage 등에 직접 보관하지 않음), 응답 바디는 사용자 표시 정보만 담당하고 인증은 전적으로 쿠키가 담당하도록 역할을 분리했습니다.

## 비고
- 로그인 쿠키의 만료 시간(`max_age`)은 명시적으로 지정하지 않았습니다. 브라우저 세션 쿠키로 동작하며, 실제 만료 여부는 JWT 내부의 `exp` 클레임(T012에서 access 15분, refresh 7일로 설정됨)으로 서버가 검증합니다. 필요하다면 추후 Task에서 `max_age`를 쿠키 속성에도 명시적으로 맞춰주는 리팩토링을 고려할 수 있습니다.
