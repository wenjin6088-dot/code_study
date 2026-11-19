# TASK-025. UserService 구현 (register, login, logout)

## 상태
완료

## 날짜
2026-11-05

## 작업 요약
`backend/src/services/auth/user_service.py`에 `UserService` 클래스를 구현했습니다. `User`/`RefreshToken` 모델(T023/T024)과 기존 유틸리티(`utils/security.py`의 bcrypt 해싱, `utils/jwt.py`)를 조합해, 회원가입·로그인·로그아웃의 핵심 비즈니스 로직을 담당합니다. API 라우터(T028~T031)와 토큰 발급(T026 TokenService)은 이번 범위 밖이며, `UserService`는 순수하게 "사용자 자격 증명과 세션 상태"만 다룹니다.

- **`register(email, password)`**: 이메일을 소문자로 정규화 → 형식 검증(T009 마이그레이션의 `valid_email` CHECK 제약과 동일한 정규식) → 비밀번호 강도 검증(8자 이상 + 문자/숫자 혼합) → 중복 이메일 사전 확인 → `bcrypt`로 해싱 후 저장. 사전 확인을 통과했더라도 동시 가입 요청으로 DB의 `UNIQUE` 제약이 걸리면 `IntegrityError`를 잡아 동일한 `EmailAlreadyRegisteredError`로 변환합니다.
- **`login(email, password)`**: 이메일 정규화 후 조회, `verify_password`로 비밀번호 확인, 성공 시 `last_login_at`을 갱신합니다. 사용자가 없거나 비밀번호가 틀려도 동일하게 `InvalidCredentialsError`를 던져(이메일 존재 여부를 노출하지 않음) 계정 열거(enumeration) 공격을 어렵게 했습니다.
- **`logout(refresh_token)`**: 전달받은 평문 리프레시 토큰을 해시(`hash_token`, 신규 추가)해 `refresh_tokens.token_hash`로 조회하고 `revoked=True`, `revoked_at`을 설정합니다. 토큰이 없거나 이미 취소된 경우에도 에러 없이 조용히 종료(idempotent)하도록 해, 로그아웃이 토큰의 존재/유효성을 외부에 노출하지 않게 했습니다.

서비스 전용 예외(`EmailAlreadyRegisteredError`, `InvalidCredentialsError`, `InvalidEmailError`, `WeakPasswordError`)를 `backend/src/services/auth/exceptions.py`에 새로 정의했습니다. API 레이어(`src/api/exceptions.py`)의 `AppException`/`ConflictError` 등을 서비스가 직접 참조하지 않고, HTTP와 무관한 도메인 예외를 던지도록 분리했습니다 — 이 예외를 HTTP 상태 코드로 변환하는 책임은 이후 T028~T031 엔드포인트에서 맡습니다.

이번 Task에서 `backend/tests/`에 처음으로 실제 pytest 자동화 테스트와 공용 `conftest.py`를 추가했습니다(T023/T024 보고서에서 "T025와 함께 작성될 예정"이라 명시했던 부분).

## 변경 파일
- `backend/src/services/auth/user_service.py` (신규 생성)
- `backend/src/services/auth/exceptions.py` (신규 생성)
- `backend/src/utils/security.py` (수정: `hash_token` 유틸리티 추가)
- `backend/tests/conftest.py` (신규 생성: DB 세션 테스트 픽스처)
- `backend/tests/integration/test_user_service.py` (신규 생성: 15개 테스트)
- `backend/pyproject.toml` (수정: `[tool.pytest.ini_options]` 추가 — `asyncio_mode = "auto"`, `testpaths`)
- `specs/001-ai-code-learning-platform/tasks.md` (T025 완료 체크)

## TDD 결과
- **RED**: `UserService`가 존재하지 않는 상태에서 `backend/tests/integration/test_user_service.py`를 먼저 작성하고 실행 → `ModuleNotFoundError: No module named 'src.services.auth.user_service'`로 수집(collection) 단계에서 실패하는 것을 확인했습니다.
- **GREEN**: `UserService`, `exceptions.py`, `utils/security.hash_token`을 구현한 뒤 재실행 → 15개 테스트 전부 통과.
  - 커버리지: `pytest-cov` 기준 `user_service.py` 100%, `exceptions.py` 100%, `security.py`(신규 `hash_token` 포함) 100% — 핵심 비즈니스 로직 100% 요구사항 충족.
  - 회원가입: 정상 가입/비밀번호 해싱 확인, 이메일 대소문자 정규화, 중복 이메일 거부(사전 확인 경로 + `IntegrityError` 변환 경로 둘 다 테스트), 이메일 형식 오류, 비밀번호 길이/문자종류 부족 거부
  - 로그인: 정상 로그인 및 `last_login_at` 갱신, 이메일 대소문자 무관 로그인, 잘못된 비밀번호/존재하지 않는 이메일 모두 동일한 `InvalidCredentialsError`로 거부
  - 로그아웃: 리프레시 토큰 해시 조회 후 `revoked`/`revoked_at` 정상 반영, 존재하지 않는 토큰에 대해 예외 없이 idempotent하게 종료
- **(환경 이슈 및 해결)** 실제 Postgres 컨테이너(이미 기동 중)에 대고 `pytest-asyncio`로 비동기 테스트를 처음 실행하자, Windows의 `ProactorEventLoop` 환경에서 테스트마다 새 이벤트 루프를 만드는 기본 동작과 `backend/src/db/session.py`의 모듈 전역 `engine`(앱 생애 동안 하나만 생성되는 싱글톤)이 충돌해 `RuntimeError: Event loop is closed` / `AttributeError: 'NoneType' object has no attribute 'send'`가 두 번째 테스트부터 발생했습니다. `tests/conftest.py`의 `event_loop` 픽스처를 세션 스코프로 재정의해(전체 테스트 세션이 하나의 이벤트 루프를 공유) 해결했습니다 — `asyncpg` 커넥션이 생성된 루프와 이후 재사용되는 루프가 항상 같아지도록 맞춘 것입니다.
- **테스트 격리 방식**: DB 레벨 트랜잭션 롤백 패턴을 사용했습니다. `db_session` 픽스처가 연결(`engine.connect()`)을 열고 외부 트랜잭션을 시작한 뒤, SQLAlchemy 2.0의 `AsyncSession(bind=conn, join_transaction_mode="create_savepoint")`로 세션을 만듭니다. 서비스 코드 내부의 `session.commit()` 호출은 SAVEPOINT만 해제할 뿐 외부 트랜잭션을 실제로 커밋하지 않으므로, 테스트가 끝나면 `trans.rollback()`으로 모든 변경을 되돌립니다. 테스트 실행 전/후로 `users`/`refresh_tokens` 테이블을 직접 조회해 잔여 데이터가 0건임을 재확인했습니다.
- `ruff check`, `black --check` 모두 통과.
- 저장소가 git 초기화 전이라 RED/GREEN 커밋은 생성하지 않았습니다.

## 기술 결정
- **서비스 전용 예외 계층 분리**: `src/api/exceptions.py`의 `AppException` 계열을 서비스가 직접 사용하지 않고, `src/services/auth/exceptions.py`에 HTTP와 무관한 도메인 예외를 새로 정의했습니다. 계층 구조 규칙("API Router → Service → Model, 단방향 의존")상 Service가 상위 계층(API)의 타입을 참조하면 의존 방향이 역전되기 때문입니다. HTTP 상태 코드로의 변환은 추후 T028~T031 엔드포인트가 이 예외를 잡아 `ConflictError`/`UnauthorizedError` 등으로 매핑하는 몫으로 남겨뒀습니다.
- **이메일 정규화(소문자화)**: data-model.md의 "Email must be unique" 요구사항을 실질적으로 지키려면 `Foo@Example.com`과 `foo@example.com`을 같은 계정으로 취급해야 합니다. DB의 `UNIQUE` 제약은 대소문자를 구분하므로, 서비스 레이어에서 저장/조회 전에 `strip().lower()`로 정규화해 대소문자로 인한 중복 계정 생성을 막았습니다.
- **비밀번호 강도 규칙 확정**: research.md는 "최소 8자, 복잡도 규칙"이라고만 명시해 정확한 기준이 없었습니다. 과도한 제약(특수문자 강제 등)은 초보자 대상 서비스의 진입장벽을 높일 수 있다고 판단해, "8자 이상 + 문자와 숫자를 각 1개 이상 포함"으로 최소한의 규칙을 정했습니다. 이 결정은 향후 프론트엔드 유효성 검사 메시지와 일치시켜야 합니다.
- **로그인/로그아웃을 의도적으로 정보 비노출형(oracle-free)으로 설계**: 로그인 실패 시 "이메일이 없음"과 "비밀번호가 틀림"을 구분하지 않고 동일한 `InvalidCredentialsError`로, 로그아웃 시 토큰이 없거나 이미 취소된 경우도 에러 없이 조용히 종료되도록 했습니다. 공격자가 응답 차이로 계정 존재 여부나 토큰 유효성을 추측하지 못하게 하는 일반적인 보안 관행입니다.
- **`logout`은 토큰 발급/회전(Rotate) 책임과 분리**: T026 TokenService가 "생성/검증/회전"을 맡으므로, `UserService.logout`은 평문 리프레시 토큰을 받아 해시 후 단순히 취소(revoke)만 수행합니다. 해싱 알고리즘(`hash_token`, SHA-256)은 `utils/security.py`에 추가해 T026에서도 동일한 함수를 재사용할 수 있게 했습니다(토큰 저장은 "해시만 저장" 규칙이 양쪽에서 일관되게 지켜져야 하기 때문).
- **pytest 비동기 테스트 인프라를 세션 스코프 이벤트 루프로 구성**: Windows에서 모듈 전역 비동기 엔진과 pytest-asyncio의 기본(함수 스코프) 이벤트 루프가 충돌하는 문제를 피하기 위해 `conftest.py`에서 `event_loop`를 세션 스코프로 오버라이드했습니다. 이는 `backend/tests/` 전체에 영향을 미치는 설정이므로, 이후 추가되는 모든 비동기 테스트가 이 전제를 따르게 됩니다.

## 비고
- `backend/tests/conftest.py`와 `[tool.pytest.ini_options]`(`asyncio_mode = "auto"`)는 이번에 처음 만들어진 공용 테스트 인프라로, 앞으로의 모든 백엔드 서비스 테스트(T026 TokenService 등)가 이 `db_session` 픽스처를 그대로 재사용할 수 있습니다.
- `register`/`login`은 JWT 발급을 하지 않습니다 — 토큰 발급은 T026(TokenService)과 API 엔드포인트(T028~T031)에서 `UserService`가 반환한 `User`를 받아 처리할 예정입니다.
- 레이트 리밋(로그인 5회/15분, 가입 3회/시간)과 인증 이벤트 로깅은 requirements-addendum.md에 명시돼 있지만 API/미들웨어 레이어의 책임이라 이번 Task에는 포함하지 않았습니다.
