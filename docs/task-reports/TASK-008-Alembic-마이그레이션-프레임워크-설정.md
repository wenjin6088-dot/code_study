# TASK-008. Alembic 마이그레이션 프레임워크 설정

## 상태
완료

## 날짜
2026-10-29

## 작업 요약
데이터베이스 테이블 구조(스키마)는 시간이 지나며 계속 바뀝니다. "사용자 테이블에 컬럼 하나 추가" 같은 변경을 할 때마다 모든 개발자의 DB에 똑같이, 순서대로 적용되게 해주는 "변경 이력 관리자"가 Alembic입니다. 코드의 git 커밋 이력과 비슷한 개념인데, 대상이 "코드"가 아니라 "DB 테이블 구조"라는 점이 다릅니다.

이번 Task에서는 Alembic이라는 도구 자체를 이 프로젝트에 맞게 설정했습니다 (아직 실제 테이블을 만드는 내용은 넣지 않았습니다 — 그건 T009의 몫입니다).

1. **`backend/alembic.ini`**: Alembic의 메인 설정 파일. 어디서 마이그레이션 파일을 찾을지(`script_location = alembic`), 로그는 어떻게 남길지를 정의합니다. 데이터베이스 접속 주소(`sqlalchemy.url`)는 이 파일에 직접 적지 않고 비워뒀습니다 — 비밀번호가 포함된 접속 주소를 git에 커밋되는 설정 파일에 넣는 것은 보안 원칙(constitution V장 "민감 정보 하드코딩 금지")에 위배되기 때문입니다.
2. **`backend/alembic/env.py`**: 실제로 "어떻게 DB에 접속해서 마이그레이션을 실행할지"를 정의하는 스크립트입니다. 접속 주소는 `.env`의 `DATABASE_URL` 환경변수에서 읽어옵니다. 이 프로젝트는 비동기(async) 방식의 SQLAlchemy를 쓰기로 했기 때문(research.md), 일반적인 동기식 Alembic 템플릿이 아니라 **비동기 엔진으로 마이그레이션을 실행하는 방식**으로 작성했습니다.
3. **`backend/alembic/script.py.mako`**: 새 마이그레이션 파일을 만들 때 쓰이는 "빈 양식"입니다. `alembic revision` 명령을 실행하면 이 양식을 바탕으로 새 파일이 생성됩니다.
4. **`backend/alembic/versions/`**: 실제 마이그레이션 파일들이 쌓일 폴더 (T001에서 이미 만들어뒀던 빈 폴더를 그대로 사용).

## 변경 파일
- `backend/alembic.ini` (신규 생성)
- `backend/alembic/env.py` (신규 생성)
- `backend/alembic/script.py.mako` (신규 생성)
- `.env.example` (수정: `DATABASE_URL` 스킴을 `postgresql://` → `postgresql+asyncpg://`로 보정)

## TDD 결과
- Alembic 설정 자체는 테스트할 비즈니스 로직이 없어 RED-GREEN-REFACTOR 사이클은 적용하지 않았습니다. 대신 T004에서 띄워둔 실제 PostgreSQL 컨테이너에 연결해 다음을 직접 실행하고 확인했습니다.
  - `alembic current` → 정상 접속 확인 (exit 0)
  - `alembic upgrade head` → 마이그레이션이 아직 없는 상태에서 정상적으로 "할 일 없음"으로 종료 (exit 0)
  - `alembic revision -m "verify template"` → `script.py.mako` 템플릿이 올바른 Python 코드로 렌더링되는지 확인 후, 검증용으로 생성한 파일은 삭제
- 저장소가 아직 git으로 초기화되지 않아 관련 커밋은 생성하지 않았습니다.
- 테스트 커버리지: 해당 없음 (마이그레이션 프레임워크 설정, 비즈니스 로직 코드 없음)

## 기술 결정
- **비동기(async) 방식의 `env.py` 작성**: Alembic을 `alembic init`으로 생성하면 기본적으로 동기(sync) 방식 템플릿이 나옵니다. 하지만 이 프로젝트는 `asyncpg` 드라이버와 SQLAlchemy 2.0 async를 쓰기로 이미 결정했기 때문(research.md), 마이그레이션도 `async_engine_from_config` + `run_sync`를 쓰는 비동기 패턴으로 직접 작성했습니다. (참고로 `backend/alembic/`에 T001에서 만든 `versions/` 폴더가 이미 존재해서, `alembic init alembic` 명령 자체는 "디렉토리가 이미 있다"는 이유로 실행할 수 없었습니다. 대신 표준 비동기 템플릿의 구조를 참고해 필요한 세 파일을 직접 작성했습니다.)
- **`target_metadata = None`**: 보통 Alembic은 SQLAlchemy 모델의 메타데이터를 참조해 `alembic revision --autogenerate`로 변경사항을 자동 추론합니다. 하지만 T009의 설명에 "초기 마이그레이션은 수동 SQL로 작성하고 autogenerate는 쓰지 않는다"고 명시되어 있고(constitution III "Content Immutability Strategy"와 무관하게, tasks.md에 직접 적힌 방침), 아직 `backend/src/models/base.py`(T009에서 생성 예정)도 존재하지 않습니다. 그래서 이번 Task에서는 모델 메타데이터를 연결하지 않고 `None`으로 두어, T008이 T009의 작업 영역(모델 정의)을 침범하지 않도록 범위를 분리했습니다.
- **`.env.example`의 `DATABASE_URL` 스킴 수정**: 기존 값(`postgresql://...`, T005에서 quickstart.md 그대로 가져온 값)은 동기 드라이버(psycopg2 계열)를 가정한 주소입니다. 하지만 실제로 설치된 드라이버는 `asyncpg`(T002)이고, SQLAlchemy의 비동기 엔진은 URL에 `+asyncpg`가 명시되어야 올바른 드라이버를 찾습니다. 이 불일치를 고치지 않으면 T008의 `env.py`뿐 아니라 이후 T010(DB 연결)에서도 연결 실패가 날 것이 확실했기 때문에, 지금 바로잡았습니다.
- **`alembic.ini`에 접속 주소를 적지 않음**: 보안 원칙과, 이미 T005에서 정한 "민감하거나 환경마다 다른 값은 `.env`로" 패턴을 그대로 따랐습니다.

## 비고
- 실제 "테이블을 만드는" 마이그레이션(001_initial_schema.py)은 T009에서 작성됩니다. 이번 Task는 그 작업을 실행할 수 있는 "틀"만 준비한 것입니다.
- 검증은 T004에서 띄워둔 Docker PostgreSQL 컨테이너(`localhost:5432`, DB명 `codelearning`)를 그대로 사용했습니다. 컨테이너가 꺼져 있으면 이번에 실행한 `alembic` 명령들은 연결 실패로 끝납니다.
