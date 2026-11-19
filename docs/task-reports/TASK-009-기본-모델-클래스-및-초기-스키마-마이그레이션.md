# TASK-009. 기본 모델 클래스 및 초기 스키마 마이그레이션

## 상태
완료

## 날짜
2026-10-29

## 작업 요약
T008에서 만든 "빈 틀"에 실제로 집(데이터베이스 테이블)을 짓는 설계도를 넣었습니다. data-model.md에 정의된 10개 테이블(users, projects, tasks, uploaded_code, code_files, learning_documents, practice_problems, questions, progress, refresh_tokens)을 하나도 빠짐없이, 거기 적힌 컬럼·제약조건·인덱스까지 전부 그대로 옮겨서 실제 PostgreSQL에 만들었습니다.

1. **`backend/src/models/base.py`**: 앞으로 만들어질 모든 SQLAlchemy 모델(User, Project, Task 등, T023부터 차례로 생성 예정)이 공통으로 상속받을 `Base` 클래스입니다. 지금은 이 클래스 하나만 있고, 실제 모델들은 각자의 Task에서 만듭니다.
2. **`backend/alembic/versions/001_initial_schema.py`**: data-model.md의 SQL을 "손으로" Alembic 코드로 옮긴 마이그레이션입니다. (헌법과 tasks.md가 명시한 대로, 모델에서 자동으로 추론하는 autogenerate 방식이 아니라 사람이 직접 작성했습니다.) FK(외래키) 의존 순서를 지켜서 `users` → `refresh_tokens`/`projects` → `tasks` → `uploaded_code` → `code_files`/`learning_documents`/`practice_problems`/`questions`/`progress` 순으로 테이블을 만들고, 롤백(`downgrade`)은 정반대 순서로 삭제합니다.

## 변경 파일
- `backend/src/models/base.py` (신규 생성)
- `backend/alembic/versions/001_initial_schema.py` (신규 생성)

## TDD 결과
- 마이그레이션 자체는 "테스트할 함수 로직"이 아니라 DB 스키마 정의라, RED-GREEN-REFACTOR 사이클 대신 **실제 PostgreSQL 컨테이너에 적용해서 동작을 검증**하는 방식을 택했습니다 (T004/T008에서 이미 검증된 Docker 컨테이너 재사용).
  - `ruff check`, `black --check` 모두 통과 (처음 걸린 39건은 `--fix`/`black` 자동 수정 + 긴 SQL 문자열 줄바꿈 수동 조정으로 모두 해결)
  - `alembic upgrade head` → 10개 테이블 + `alembic_version` 테이블, 총 11개 테이블 생성 확인 (`\dt`로 직접 확인)
  - **제약조건 실제 동작 검증** (psql로 직접 INSERT 시도):
    - 정상 유저 생성 → 성공, `gen_random_uuid()`/`skill_level` 기본값('Complete Beginner')/`created_at` 모두 정상 자동 채움
    - 잘못된 이메일 형식(`not-an-email`) → `valid_email` CHECK로 정확히 거부
    - 이메일 중복 삽입 → UNIQUE 제약으로 정확히 거부
    - 같은 프로젝트에 `task_number` 중복 → `unique_task_number_per_project`로 정확히 거부
    - 5자 미만 제목(`'Hi'`)으로 태스크 생성 → `title_min_length` CHECK로 정확히 거부
    - `progress` 테이블 기본값(`chapters_completed=[]`, `document_read_percentage=0`, `task_completed=false`) 정확히 적용 확인
    - 프로젝트 삭제 → 연결된 tasks, progress까지 CASCADE로 함께 삭제됨을 확인
  - `alembic downgrade base` → 모든 테이블이 깨끗하게 제거됨을 확인 후, `alembic upgrade head`로 다시 원상복구해 다음 Task(T010 등)가 사용할 수 있는 상태로 마무리
  - 테스트에 사용한 샘플 데이터(유저/프로젝트/태스크)는 전부 삭제해 DB를 빈 상태로 되돌렸습니다.
- 저장소가 아직 git으로 초기화되지 않아 관련 커밋은 생성하지 않았습니다.
- 테스트 커버리지: 해당 없음 (마이그레이션 코드, 단위 테스트 대상 비즈니스 로직 아님)

## 기술 결정
- **`target_metadata`/모델 import 없이 순수 `op.create_table` 사용**: data-model.md의 SQL DDL을 SQLAlchemy Core의 `op.create_table` + `sa.Column`/`sa.CheckConstraint`/`sa.UniqueConstraint`로 1:1 변환했습니다. 이렇게 하면 "사람이 직접 작성"했다는 요건을 지키면서도, raw SQL 문자열을 통째로 `op.execute()`하는 것보다 Alembic의 자동 롤백 지원(`downgrade`에서 `op.drop_table`만 쓸 수 있는 것) 등의 이점을 살릴 수 있습니다.
- **`idx_users_email`을 명세 그대로 유지**: `email` 컬럼은 `unique=True`로도 이미 암묵적으로 유니크 인덱스가 생기기 때문에, 명세의 `CREATE INDEX idx_users_email ON users(email)`은 사실상 중복된 인덱스입니다. 하지만 이번 Task의 목적이 "data-model.md와 정확히 일치하는 스키마"이므로, 효율성보다 명세 충실도를 우선해 그대로 두 개 다 만들었습니다. **(비고에 후속 정리 후보로 남깁니다.)**
- **CHECK 제약 이름을 명세에 없는 곳은 직접 지음**: data-model.md는 일부 CHECK에 이름을 안 적어둔 경우가 있어(예: `complexity_level IN (...)`), Postgres가 자동 생성하는 이름 대신 `{table}_{column}_check` 패턴으로 명시적인 이름을 붙였습니다. 이렇게 해야 나중에 특정 제약을 `ALTER TABLE ... DROP CONSTRAINT`로 찾아 수정하기 쉽습니다.
- **`gen_random_uuid()`는 추가 extension 없이 사용**: PostgreSQL 13부터 `pgcrypto` 확장 없이도 core에 포함되어 있어, `CREATE EXTENSION` 없이 그대로 사용했습니다 (postgres:15-alpine으로 실제 검증 완료).
- **마이그레이션 파일명/리비전 ID를 `001`로 고정**: tasks.md가 파일명을 `001_initial_schema.py`로 명시했기 때문에, Alembic이 보통 자동 생성하는 해시 기반 리비전 ID(`69edc6b5fa64` 같은) 대신 사람이 읽기 쉬운 `"001"`을 리비전 ID로 직접 지정했습니다.

## 비고
- `idx_users_email`과 `email` 컬럼의 암묵적 UNIQUE 인덱스가 중복이라는 점은 알고 있지만, data-model.md 명세 충실도를 위해 그대로 구현했습니다. 실제 운영 전 성능 튜닝 단계에서 제거를 검토할 수 있습니다.
- 이번 마이그레이션은 **FK/CHECK/UNIQUE 제약과 CASCADE 동작까지 실제 데이터로 검증**했기 때문에, 이후 T023(User 모델)부터 시작되는 각 Task들이 "T009 마이그레이션 스키마와 일치해야 한다"는 요구사항을 충족하기 위한 정확한 기준선이 마련되었습니다.
- 두 백엔드 가상환경(`venv`, `.venv`) 중 `venv`로만 이번 검증을 수행했습니다. 두 환경 모두 동일한 `requirements.txt`를 설치했으므로 `.venv`에서도 동일하게 동작할 것으로 예상되지만, 실제로는 `venv`만 테스트했습니다.
