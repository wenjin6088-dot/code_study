# TASK-023. User SQLAlchemy 모델

## 상태
완료

## 날짜
2026-11-05

## 작업 요약
T009에서 데이터베이스에 `users` 테이블을 SQL로 직접 만들었다면, 이번에는 Python 코드에서 그 테이블을 "객체처럼" 다룰 수 있게 해주는 다리(ORM 모델)를 놓았습니다. 이제부터는 `INSERT INTO users ...` 같은 SQL 문자열을 직접 쓰는 대신, `User(email=..., password_hash=...)`처럼 평범한 Python 객체를 만들어 저장하면 SQLAlchemy가 알아서 SQL로 바꿔줍니다.

`backend/src/models/user.py`에 T009 마이그레이션의 `users` 테이블과 컬럼 하나하나 정확히 대응하는 `User` 클래스를 만들었습니다: `id`(UUID), `email`, `password_hash`, `skill_level`(기본값 'Complete Beginner'), `created_at`, `updated_at`, `last_login_at`.

## 변경 파일
- `backend/src/models/user.py` (신규 생성)

## TDD 결과
- 모델이 실제 테이블과 정확히 맞는지는 반드시 실제 DB로 검증해야 의미가 있어서, T004에서 띄워둔 PostgreSQL 컨테이너(7일간 켜져 있던 것을 다시 복구)에 대고 직접 실행했습니다.
  - `ruff check`, `black --check` 통과
  - **(환경 이슈)** 검증 시작 시 Docker Desktop이 또 꺼져 있었습니다(반복되는 패턴). 재실행 후 `docker compose up -d`로 복구, `alembic current` → `001 (head)`로 마이그레이션 상태 정상 확인
  - **실제 INSERT 검증**: `User(email=..., password_hash=...)`로 객체를 만들어 저장 → `id`가 실제 Python `UUID` 타입으로 자동 채워짐(DB의 `gen_random_uuid()` 기본값이 ORM 쪽에도 정확히 반영됨), `skill_level`이 `'Complete Beginner'`로 자동 채워짐, `created_at`/`updated_at`이 타임스탬프로 자동 채워짐을 확인
  - **재조회 검증**: 같은 이메일로 `SELECT` 쿼리를 다시 실행해, 방금 저장한 것과 동일한 `id`가 나오는지 확인 → 일치
  - **제약조건 연동 검증**: T009에서 만든 `valid_email` CHECK 제약(이메일 형식 정규식)이 ORM을 통한 삽입에서도 여전히 동작해, 잘못된 형식의 이메일을 넣으면 `IntegrityError`로 정확히 거부됨을 확인
  - 테스트에 사용한 데이터는 전부 삭제하고, DB에서 실제로 사라졌는지 `psql`로 재확인했습니다.
- 저장소가 아직 git으로 초기화되지 않아 관련 커밋은 생성하지 않았습니다.
- 테스트 커버리지: 해당 없음 (pytest 자동화 테스트는 T025 UserService와 함께 작성될 예정이며, 이번에는 모델 자체가 실제 테이블과 정확히 매핑되는지를 수동 스크립트로 검증했습니다)

## 기술 결정
- **관계(relationship) 미정의**: data-model.md는 User가 "Has many Projects", "Has many RefreshTokens" 관계를 가진다고 설명하지만, `Project`(T043)와 `RefreshToken`(T024)는 아직 존재하지 않거나 이번 Task 범위 밖이라 `relationship()`을 추가하지 않았습니다. SQLAlchemy의 관계는 상대 클래스 이름을 문자열로 참조하는데, 존재하지 않는 클래스를 미리 참조하면 매퍼 설정 시점에 에러가 날 수 있어, 각 자식 모델이 만들어지는 Task에서 양쪽 관계를 함께 추가하는 것이 더 안전하다고 판단했습니다(YAGNI + 범위 침범 방지).
- **`server_default` 사용 (Python 쪽 `default`가 아님)**: `skill_level`, `created_at`, `updated_at`의 기본값을 SQLAlchemy의 Python 레벨 `default=`가 아니라 `server_default=text(...)`로 지정했습니다. 이는 T009 마이그레이션이 이미 DB 레벨에서 동일한 기본값을 정의해뒀기 때문에, ORM이 별도로 값을 계산하지 않고 DB가 계산한 값을 그대로 가져오도록 일치시킨 것입니다. 실제로 `session.refresh(user)`로 DB가 채운 값을 정확히 읽어옴을 확인했습니다.
- **`UUID(as_uuid=True)`**: 컬럼 값을 문자열이 아니라 Python의 `uuid.UUID` 객체로 다루도록 설정했습니다. 실제 검증에서 `user.id`가 `UUID` 타입으로 반환됨을 확인했습니다 — 이렇게 해야 나중에 다른 모델(Project 등)에서 외래키로 연결할 때 타입 비교 실수를 줄일 수 있습니다.

## 비고
- T024(RefreshToken 모델), T043(Project 모델)가 진행되면 그쪽에서 `relationship("User", back_populates=...)`을 추가하고, 이 `User` 모델에도 반대쪽 관계를 함께 추가하는 후속 작업이 필요합니다.
- Docker Desktop이 세션마다 꺼져 있는 문제가 계속 반복되고 있습니다 (T017, T021 보고서에도 동일 현상 기록). 근본적으로는 Docker Desktop을 "Windows 시작 시 자동 실행"으로 설정하는 것이 반복 작업을 줄이는 방법일 수 있습니다 (사용자 환경 설정이라 직접 변경하지 않았습니다).
