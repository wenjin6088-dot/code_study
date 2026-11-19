# TASK-016. 에러 핸들링 미들웨어 및 예외 스키마

## 상태
완료

## 날짜
2026-11-02

## 작업 요약
API가 에러를 낼 때마다 제각각 다른 형식으로 응답하면, 프론트엔드에서 "에러가 났을 때 어디를 보면 메시지가 있는지"를 매번 다르게 처리해야 합니다. 이번 Task에서는 **어떤 종류의 에러든 항상 같은 모양**(`{"error": {"message": "..."}}`)으로 응답하도록 통일했습니다. 비유하자면, 병원의 모든 과(접수, 진료, 검사)에서 문제가 생겼을 때 "같은 양식의 안내문"으로 환자에게 전달하도록 정한 것과 비슷합니다.

1. **`backend/src/api/exceptions.py`**:
   - `AppException`: 우리가 직접 정의하는 "업무상 에러"의 공통 부모 클래스입니다. 메시지와 HTTP 상태 코드를 가지고 있습니다.
   - `NotFoundError`(404), `UnauthorizedError`(401), `ForbiddenError`(403): 앞으로 서비스 코드에서 `raise NotFoundError("프로젝트를 찾을 수 없습니다")`처럼 바로 쓸 수 있는 자주 쓰이는 에러 3종을 미리 만들어뒀습니다.
   - `register_exception_handlers(app)`: 4가지 상황을 모두 같은 형식으로 바꿔주는 "번역기"를 FastAPI 앱에 등록합니다.
     - 우리가 만든 `AppException` (및 하위 클래스)
     - FastAPI의 기본 `HTTPException` (예: 라우트에서 `raise HTTPException(403, ...)`)
     - 요청 데이터 검증 실패 (`RequestValidationError`, 예: 필수 필드 누락)
     - 그 외 예상 못한 모든 에러 (`Exception`) → 내부 에러 내용은 숨기고 "Internal server error"만 보여주되, 서버 로그에는 전체 스택트레이스를 남겨 디버깅할 수 있게 함
2. **`backend/src/main.py` (수정)**: `register_exception_handlers(app)`를 호출해 실제로 앱에 연결했습니다.

## 변경 파일
- `backend/src/api/exceptions.py` (신규 생성)
- `backend/src/main.py` (수정: 예외 핸들러 등록 추가)

## TDD 결과
- 에러 핸들링은 "입력에 따라 분기가 갈리는" 로직이라, 4가지 시나리오를 실제로 발생시켜 응답 형식과 상태 코드가 설계대로 나오는지 직접 확인했습니다 (검증 전용 임시 라우트를 `router.py`에 잠깐 추가했다가 확인 후 제거).
  - `ruff check`(최초 줄 길이 초과 3건을 black 재포맷으로 해결), `black --check` 통과
  - **커스텀 `AppException`(`NotFoundError`)**: `GET .../app_exception` → `404 {"error":{"message":"tmp-not-found"}}`
  - **FastAPI `HTTPException(403)`**: `GET .../http_exception` → `403 {"error":{"message":"tmp-forbidden"}}`
  - **요청 검증 실패**(필수 쿼리 파라미터 누락): `GET .../validation` → `422`, `details`에 pydantic이 생성한 구조화된 에러 목록(`loc`, `msg` 등) 포함
  - **처리되지 않은 예외**(`RuntimeError`): `GET .../unhandled` → `500 {"error":{"message":"Internal server error"}}` — 클라이언트에게는 내부 구현이 전혀 노출되지 않음. 서버 로그에서는 `logger.exception()`으로 전체 스택트레이스(`RuntimeError: tmp-boom`까지)가 정상적으로 기록됨을 확인
  - **일반 404**(`/nonexistent`, 라우트 자체가 없는 경우): `{"error":{"message":"Not Found"}}` — `StarletteHTTPException` 핸들러가 FastAPI 기본 404까지도 동일한 형식으로 통일함을 확인
  - 검증 후 `router.py`의 임시 테스트 라우트 4개를 모두 제거하고 T015의 원래 빈 상태로 복원, 재검증으로 기존 엔드포인트(`/`, `/health`, `/nonexistent`)가 여전히 정상임을 재확인
- 저장소가 아직 git으로 초기화되지 않아 관련 커밋은 생성하지 않았습니다.
- 테스트 커버리지: 해당 없음 (pytest 자동화 테스트는 실제 서비스 계층에서 예외를 던지는 시점에 함께 작성될 예정)

## 기술 결정
- **공통 응답 형식 `{"error": {"message": ...}}`**: contracts/API 스펙 문서가 아직 없어(프로젝트에 `contracts/` 디렉토리가 없음) 정해진 스키마가 없었습니다. 프론트엔드가 "에러면 항상 `error.message`를 보면 된다"는 하나의 규칙만 기억하면 되도록 가장 단순한 구조를 직접 정했습니다. 복잡한 에러 코드 체계(예: `error.code`)는 지금 당장 필요하다는 근거가 없어 추가하지 않았습니다(YAGNI). 다만 검증 실패의 경우에는 필드별 상세 정보가 실전에서 꼭 필요해서 `details`를 추가로 넣었습니다.
- **`Exception`(최상위) 핸들러로 내부 정보 은닉**: constitution V장("Security: 민감 정보 하드코딩 금지" 등 보안 원칙)의 취지에 맞춰, 예상 못한 서버 에러가 나도 스택트레이스나 내부 모듈 경로 같은 정보가 API 응답으로 노출되지 않게 했습니다. 대신 `logger.exception()`으로 서버 쪽에만 전체 내용을 남겨, 운영자는 디버깅할 수 있지만 외부 사용자나 공격자는 내부 구조를 알 수 없습니다.
- **`NotFoundError`/`UnauthorizedError`/`ForbiddenError` 3종만 미리 정의**: data-model.md와 향후 서비스 Task들(프로젝트 조회, 인증 등)에서 가장 빈번하게 쓰일 패턴이라 미리 만들어뒀습니다. 그 외 세분화된 에러(예: `DuplicateEmailError`)는 실제로 필요해지는 서비스 Task(T025 UserService 등)에서 `AppException`을 상속해 추가하면 됩니다.
- **처리되지 않은 예외가 서버 로그에 두 번 기록되는 현상 확인**: 검증 중 `logger.exception()`에 의한 로그 1회와, Starlette의 최상위 `ServerErrorMiddleware`가 남기는 `ERROR: Exception in ASGI application` 로그가 한 번 더 찍히는 것을 확인했습니다. 이는 Starlette가 핸들러로 예외를 처리해 응답을 보낸 뒤에도, 로깅/모니터링 도구(Sentry 등)가 알 수 있도록 예외를 상위로 다시 전달하는 **정상적인 설계**입니다 — 클라이언트가 받는 응답은 깨끗한 JSON 하나뿐이고, 버그가 아님을 확인했습니다.

## 비고
- 앞으로 서비스 계층(T025 UserService, T044 ProjectService 등)에서 `from src.api.exceptions import NotFoundError, ForbiddenError` 형태로 가져와 바로 사용하면 됩니다.
- T199(CSRF 보호)나 T016 이후의 보안 강화 Task에서, 특정 에러에 대해 추가 헤더나 로깅(예: 인증 실패 횟수 추적)이 필요해지면 이 모듈을 확장하면 됩니다.
- **(추가 업데이트, 2026-11-02)** 사용자 요청으로 `ConflictError`(409, "Resource conflict" 기본 메시지)를 추가했습니다. 중복 생성(예: 이미 존재하는 이메일로 가입 시도) 같은 409 Conflict 상황에서 사용할 수 있습니다. 검증용으로 임시로 만들었던 `/api/v1/test-errors` 엔드포인트는 확인 후 제거했고, `ConflictError` 클래스만 `exceptions.py`에 남겼습니다.
