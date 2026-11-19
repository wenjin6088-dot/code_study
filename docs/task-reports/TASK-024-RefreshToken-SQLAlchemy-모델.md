# TASK-024. RefreshToken SQLAlchemy 모델

## 상태
완료

## 날짜
2026-11-05

## 작업 요약
T009 마이그레이션(`001_initial_schema.py`)이 SQL로 정의한 `refresh_tokens` 테이블을 Python ORM 객체로 다룰 수 있도록 `backend/src/models/refresh_token.py`에 `RefreshToken` 클래스를 만들었습니다. 컬럼은 마이그레이션과 하나하나 대응됩니다: `id`(UUID, `gen_random_uuid()`), `user_id`(UUID, `users.id` FK, `ON DELETE CASCADE`), `token_hash`(평문 토큰이 아닌 SHA-256 해시, UNIQUE), `expires_at`, `created_at`, `revoked`(기본값 false), `revoked_at`.

T023에서 "자식 모델이 생길 때 양쪽 관계를 함께 추가" 하기로 미뤄둔 `User` ↔ `RefreshToken` 관계도 이번에 함께 추가했습니다: `User.refresh_tokens`(`cascade="all, delete-orphan"`)와 `RefreshToken.user`(`back_populates="refresh_tokens"`)로 양방향 관계를 연결했습니다. `User`는 아직 생성되지 않은 `Project` 쪽 관계는 이번에도 손대지 않았습니다(T043 범위).

## 변경 파일
- `backend/src/models/refresh_token.py` (신규 생성)
- `backend/src/models/user.py` (수정: `refresh_tokens` relationship 추가)
- `specs/001-ai-code-learning-platform/tasks.md` (T024 완료 체크)

## TDD 결과
- 이 저장소는 아직 git으로 초기화되지 않아 RED/GREEN/REFACTOR 커밋은 생성하지 않았습니다.
- 모델-테이블 정합성은 반드시 실제 DB로 검증해야 의미가 있어서, 이미 켜져 있던 PostgreSQL 컨테이너(`codelearning_postgres`, healthy)에 대고 직접 실행했습니다.
  - `ruff check`, `black --check` 통과 (수정 1회: 라인 길이 초과를 `black`으로 재포맷, `user.py` import 순서를 `ruff --fix`로 정렬)
  - `mypy`는 현재 가상환경에 설치되어 있지 않아 실행하지 못했습니다(T023 시점과 동일한 환경 상태).
  - **INSERT/제약조건 검증**: `User`를 먼저 만들고, 그 `id`로 `RefreshToken(user_id=..., token_hash=..., expires_at=...)`을 저장 → `id`가 `gen_random_uuid()`로 자동 채워지고, `created_at`이 서버 타임스탬프로, `revoked`가 기본값 `False`로 채워짐을 확인
  - **재조회 검증**: `SELECT`로 다시 조회해 저장한 것과 동일한 `id`/`user_id`가 나오는지 확인 → 일치
  - **UNIQUE 제약 검증**: 동일한 `token_hash`로 두 번째 행을 넣으면 `IntegrityError`로 거부됨을 확인
  - **갱신 검증**: `revoked=True`, `revoked_at`에 타임스탬프를 설정 후 재조회해 값이 정확히 반영됨을 확인
  - **CASCADE 삭제 검증**: 연결된 `User`를 삭제하면 `refresh_tokens` 행도 DB 레벨 `ON DELETE CASCADE`로 함께 삭제됨을 확인
  - **관계(relationship) 검증**: `selectinload(User.refresh_tokens)`로 사용자의 토큰 목록을 조회(1건, `user_id` 일치), `selectinload(RefreshToken.user)`로 토큰에서 사용자 이메일을 역참조 → 양방향 모두 정상 동작 확인
  - 테스트에 사용한 데이터는 전부 정리했고, `psql` 대신 같은 비동기 세션으로 `COUNT(*)` 조회해 DB에 잔여 데이터가 없음을 재확인했습니다.
  - 테스트 커버리지: 해당 없음 (pytest 자동화 테스트는 아직 `backend/tests/`에 conftest/DB fixture가 구성되지 않아 작성하지 않았으며, T025 UserService 및 관련 서비스 레이어 구현과 함께 모델을 포함한 자동화 테스트가 추가될 예정입니다 — T023과 동일한 판단)

## 기술 결정
- **`relationship()`을 이번 Task에서 추가**: T023 보고서에서 "RefreshToken이 생기면 그쪽에서 관계를 추가하고 User에도 반대쪽을 추가한다"고 명시했던 후속 작업을 이번에 수행했습니다. `RefreshToken` 클래스가 이제 존재하므로 매퍼 설정(mapper configure) 시점에 문자열 참조(`"RefreshToken"`)가 안전하게 해석됩니다. 반면 `Project`는 아직 존재하지 않아(T043 범위) `User.projects` 관계는 이번에도 추가하지 않았습니다 — 존재하지 않는 클래스를 문자열로 미리 참조하면 매퍼 설정 시점에 에러가 나기 때문입니다.
- **`cascade="all, delete-orphan"`은 `User` 쪽에만 지정**: DB 레벨에서 이미 `ON DELETE CASCADE`가 걸려 있어 실제 삭제는 DB가 처리하지만, ORM 세션 내에서 `user.refresh_tokens`에서 항목을 제거하거나 `User` 객체를 ORM으로 삭제할 때도 일관되게 동작하도록 ORM 레벨 cascade를 User → RefreshToken 방향으로만 선언했습니다(FK를 가진 쪽에 `cascade`를 중복 선언할 필요는 없음).
- **`server_default` 사용 유지**: T023과 동일한 이유로 `created_at`, `revoked`의 기본값을 Python `default=`가 아닌 `server_default=text(...)`로 지정해, T009 마이그레이션이 정의한 DB 레벨 기본값과 ORM이 어긋나지 않도록 맞췄습니다.
- **`token_hash`는 평문 토큰을 담지 않음**: 컬럼명과 data-model.md의 설명대로, 이 필드에는 원본 리프레시 토큰이 아니라 SHA-256 해시만 저장한다는 전제를 모델 주석 없이도 컬럼명 자체로 드러나도록 했습니다. 실제 해시 계산 로직은 T026 TokenService 구현 범위입니다.

## 비고
- `User.refresh_tokens` / `RefreshToken.user` 양방향 관계가 이제 연결되었으므로, 추후 `Project` 모델(T043)이 생기면 그때 `User.projects` 관계를 추가하면 됩니다.
- Docker Desktop/PostgreSQL 컨테이너가 이번 세션에는 이미 정상 기동 중이었습니다(이전 보고서들에서 반복됐던 "컨테이너가 꺼져 있는" 환경 이슈가 이번에는 발생하지 않음).
