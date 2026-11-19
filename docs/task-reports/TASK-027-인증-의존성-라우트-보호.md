# TASK-027. 인증 의존성(라우트 보호) 구현

## 상태
완료

## 날짜
2026-11-06

## 작업 요약
`backend/src/api/dependencies.py`에 FastAPI 의존성(Dependency) 2개를 만들었습니다. 이건 "건물 출입 게이트"와 비슷합니다 — 앞으로 만들 보호된 API(T028~T031 이후의 프로젝트/학습 관련 엔드포인트들)는 이 게이트를 거치기만 하면, 요청을 보낸 사람이 누구인지(또는 로그인 안 한 사람인지) 자동으로 확인됩니다. 라우트 코드 자체에는 인증 검사 로직을 반복해서 넣지 않아도 됩니다.

- **`get_current_user_id(request)`**: HTTPOnly 쿠키(`access_token`)에서 토큰을 꺼내 T026의 `TokenService.verify_access_token()`으로 검증하고, 사용자 UUID만 돌려줍니다. 쿠키가 없거나, 토큰이 깨졌거나 만료됐거나, refresh 토큰을 access 자리에 잘못 넣었거나 — 모든 실패 케이스를 `src/api/exceptions.py`의 `UnauthorizedError`(HTTP 401)로 통일해서 던집니다. DB 조회가 필요 없는 가벼운 검사라 "이 사용자가 로그인했는지만 알면 되는" 라우트에 적합합니다.
- **`get_current_user(user_id, session)`**: 위 의존성 결과(user_id)를 받아 실제 `User` 엔티티를 DB에서 조회해 돌려줍니다. 토큰은 유효하지만 그 사이 계정이 삭제된 경우(`session.get()`이 `None` 반환)에도 동일하게 401로 처리합니다. 사용자의 `skill_level` 같은 실제 데이터가 필요한 라우트는 이 의존성을 쓰면 됩니다.

쿠키 이름(`ACCESS_TOKEN_COOKIE_NAME = "access_token"`)을 이 파일에 상수로 정의해, 앞으로 로그인/로그아웃/토큰갱신 엔드포인트(T028~T031)가 쿠키를 설정할 때 같은 이름을 가져다 쓰도록 했습니다. 이 Task는 "검사하는 쪽"만 만들었고, "쿠키를 실제로 심어주는" 로그인 엔드포인트는 범위 밖입니다.

## 변경 파일
- `backend/src/api/dependencies.py` (신규 생성)
- `backend/tests/integration/test_dependencies.py` (신규 생성: 7개 테스트)
- `backend/pyproject.toml` (수정: ruff `B008` 규칙을 프로젝트 전역에서 무시하도록 추가 — FastAPI의 `Depends()` 기본값 패턴은 버그가 아니라 프레임워크의 정석 사용법이라 오탐이었습니다)
- `specs/001-ai-code-learning-platform/tasks.md` (T027 완료 체크)

## TDD 결과
- **RED**: `src/api/dependencies.py`가 없는 상태에서 테스트를 먼저 작성 → `ModuleNotFoundError: No module named 'src.api.dependencies'`로 수집 실패 확인.
- **GREEN**: `dependencies.py` 구현 후 재실행 → 7개 테스트 전부 1차 시도에 통과.
  - `get_current_user_id`: 쿠키 없음/깨진 토큰/refresh 토큰 오용 모두 401, 정상 토큰은 사용자 ID 반환
  - `get_current_user`: 정상 토큰이면 실제 `User` 엔티티 반환, 쿠키 없으면 401, 토큰 발급 후 계정이 삭제되면 401
  - 백엔드 전체 테스트(34개, 기존 T025/T026 포함) 재실행 → 전부 통과, 회귀 없음
- 커버리지: `dependencies.py` 22줄 중 1줄(`raise UnauthorizedError("User not found")`) 미집계로 95% 표시. 디버그 프린트를 임시로 넣어 실제로는 해당 분기가 정상 실행되고 테스트도 401을 올바르게 검증함을 직접 확인했습니다 — `coverage.py`가 SQLAlchemy의 비동기 greenlet 전환 지점 근처 코드를 추적하지 못하는 알려진 한계로 보이며, 실제 테스트 공백은 아닙니다.
- `ruff check`, `black --check` 모두 통과(위 `B008` 설정 추가 후).
- 저장소가 git 초기화 전이라 RED/GREEN 커밋은 생성하지 않았습니다(T025/T026과 동일).

## 기술 결정
- **테스트 방식: 실제 FastAPI 앱 + `httpx.AsyncClient(transport=ASGITransport(...))`**: 의존성 함수를 직접 호출하는 대신, 작은 FastAPI 테스트 앱에 보호된 라우트를 2개 붙이고 `register_exception_handlers`까지 적용해 실제 HTTP 요청으로 검증했습니다. 동기식 `TestClient`(Starlette)는 내부적으로 별도 스레드/이벤트 루프(portal)에서 요청을 실행해 `db_session` 픽스처(현재 테스트의 이벤트 루프에 바인딩된 asyncpg 연결)와 충돌할 위험이 있어(T025 보고서의 "이벤트 루프 충돌" 사례와 동일 계열 문제), 같은 이벤트 루프에서 동작하는 `httpx.AsyncClient` + `ASGITransport`를 선택했습니다.
- **두 단계 의존성 분리(`get_current_user_id` vs `get_current_user`)**: 모든 보호된 라우트가 매번 `User` 전체를 DB에서 조회할 필요는 없습니다(예: "내가 쓴 글만 삭제 가능한지" 같은 ID 비교만 필요한 경우). 가벼운 ID 검사와 무거운 엔티티 조회를 분리해, 호출하는 라우트가 필요한 만큼만 선택하게 했습니다.
- **실패 사유를 전부 동일한 `UnauthorizedError`(401)로 통일**: 쿠키 없음/토큰 위조/만료/계정 삭제를 구분하지 않고 같은 응답을 줍니다. T025(`UserService`)·T026(`TokenService`)과 동일하게, 공격자가 실패 이유로 계정 존재 여부나 토큰 상태를 추측하지 못하게 하는 설계를 이 계층에서도 일관되게 유지했습니다.
- **`ruff`의 `B008` 규칙을 프로젝트 전역에서 무시**: `Depends(get_db)`처럼 FastAPI는 "함수 기본값 자리에 함수 호출을 넣는" 패턴을 공식적으로 요구합니다. `flake8-bugbear`의 `B008`(기본값에 함수 호출 금지)은 일반 파이썬 코드에서는 유효한 경고지만 FastAPI 라우트/의존성에는 해당되지 않는 오탐이라, 이 파일에서 처음 등장한 패턴에 맞춰 설정을 한 번에 고쳤습니다. 이후 T028~T031의 모든 라우터 코드도 같은 패턴을 쓰게 되므로 파일별 `# noqa` 대신 전역 설정이 맞다고 판단했습니다.

## 비고
- 이 의존성들은 아직 어떤 실제 라우트에도 연결돼 있지 않습니다 — T028(`POST /auth/register`), T029(`POST /auth/login`), T029A(`GET /auth/me`) 등에서 로그인 성공 시 `TokenService.issue_tokens()` 결과를 `access_token`/`refresh_token` 쿠키로 심어주고, 보호가 필요한 라우트에서 `Depends(get_current_user)` 또는 `Depends(get_current_user_id)`를 쓰면 됩니다.
- 쿠키의 `HttpOnly`/`Secure`/`SameSite` 속성 설정은 "쿠키를 읽는" 이 Task가 아니라 "쿠키를 심는" 로그인/토큰갱신 엔드포인트(T028~T031)의 책임입니다.
