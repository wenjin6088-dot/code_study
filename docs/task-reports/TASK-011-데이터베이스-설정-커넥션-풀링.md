# TASK-011. 데이터베이스 설정 및 커넥션 풀링

## 상태
완료

## 날짜
2026-10-30

## 작업 요약
T010에서는 DB 연결 주소를 `session.py` 안에서 직접 환경변수로 읽었습니다. 이번 Task에서는 그 "연결 정보"와 "연결 풀 운영 방침"을 한곳(`backend/src/db/config.py`)으로 모았습니다.

연결 풀이란 식당의 "테이블 여러 개를 미리 세팅해두고 손님이 올 때마다 새로 세팅하지 않고 돌려쓰는 것"과 비슷합니다. 매번 DB에 새로 접속하는 건 비용이 크기 때문에, 미리 몇 개의 연결을 만들어두고(`pool_size`), 손님이 몰리면 추가로 더 만들고(`max_overflow`), 너무 오래 기다리게 하지 않고(`pool_timeout`), 너무 오래된 연결은 주기적으로 새 걸로 바꿔줍니다(`pool_recycle`).

1. **`backend/src/db/config.py`**: `DatabaseConfig`라는 데이터 묶음(dataclass)과, 환경변수에서 값을 읽어 그 묶음을 만들어주는 `get_database_config()` 함수를 정의했습니다. `DATABASE_URL`뿐 아니라 `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_TIMEOUT`, `DB_POOL_RECYCLE` 환경변수도 읽되, 설정하지 않으면 안전한 기본값을 씁니다.
2. **`backend/src/db/session.py` (리팩토링)**: T010에서 직접 읽던 `DATABASE_URL`과 `pool_pre_ping=True`만 있던 자리에, 이제 `get_database_config()`로 가져온 설정값 전체(`pool_size`, `max_overflow`, `pool_timeout`, `pool_recycle`, `pool_pre_ping`)를 엔진에 전달하도록 바꿨습니다.

## 변경 파일
- `backend/src/db/config.py` (신규 생성)
- `backend/src/db/session.py` (수정: `config.py`를 사용하도록 리팩토링)
- `docs/task-reports/TASK-010-데이터베이스-연결-세션-관리.md` (수정: session.py 리팩토링 사실을 추가 기록)

## TDD 결과
- 설정 모듈 자체는 테스트할 복잡한 로직이 없어(환경변수 읽기 + 기본값 적용) RED-GREEN-REFACTOR 사이클 대신, **실제 값이 올바르게 전달되는지 직접 실행**해 검증했습니다.
  - `ruff check`, `black --check` 통과
  - 환경변수를 `DB_POOL_SIZE=3`, `DB_MAX_OVERFLOW=7`로 설정하고 `get_database_config()` 호출 → 정확히 그 값으로 반영됨을 확인
  - 실제 `engine.pool`(`AsyncAdaptedQueuePool`)의 `size()`와 `_max_overflow` 속성을 직접 조회해 → 3, 7로 정확히 적용됨을 확인 (SQLAlchemy가 내부적으로 설정값을 제대로 받았는지까지 확인)
  - 같은 세션으로 `SELECT 1`과 테이블 개수(11개) 조회 → 정상 동작
  - 환경변수를 설정하지 않은 경우 → 기본값(`pool_size=5`, `max_overflow=10`, `pool_timeout=30`, `pool_recycle=1800`)이 정확히 적용됨을 별도로 확인
- **중간에 발견한 환경 이슈**: 검증 도중 Docker Desktop이 꺼져 있어(`ConnectionRefusedError`) 처음 테스트가 실패했습니다. Docker Desktop을 다시 실행하고 엔진이 기동될 때까지 기다린 뒤, `docker compose up -d`로 컨테이너를 복구하고 재검증했습니다. 볼륨이 보존되어 있어 T009에서 만든 11개 테이블이 그대로 남아있음을 확인했습니다.
- 저장소가 아직 git으로 초기화되지 않아 관련 커밋은 생성하지 않았습니다.
- 테스트 커버리지: 해당 없음 (설정 모듈, 아직 자동화된 pytest 테스트는 작성하지 않음)

## 기술 결정
- **`dataclass(frozen=True)` 사용**: 설정값은 한 번 읽어오면 애플리케이션 실행 중에 바뀌지 않아야 하므로, 불변(frozen) dataclass로 만들어 실수로 값이 변경되는 것을 막았습니다. Pydantic `BaseSettings` 같은 더 무거운 도구 대신 표준 라이브러리 `dataclass`를 선택한 이유는, 이 모듈이 다루는 설정이 DB 전용 5개 값뿐이라 YAGNI 원칙상 추가 의존성이 필요 없다고 판단했기 때문입니다. (참고: `requirements.txt`에도 `pydantic-settings`가 없습니다 — T002에서 의도적으로 제외했던 부분과 일관성을 유지했습니다.)
- **풀 크기 기본값 (`pool_size=5`, `max_overflow=10`)**: research.md/plan.md에 정확한 숫자가 명시되어 있지 않아, SQLAlchemy의 통상적인 운영 기본값과 plan.md의 "100+ 동시 사용자" 목표를 고려해 합리적인 기본값을 정했습니다. 기본 연결 5개 + 피크 시 추가 10개(최대 15개 동시 연결)로, 이번 프로젝트 규모(plan.md: "Small user base, hundreds of users")에 적절한 수준입니다. 운영 환경에서 실측 후 환경변수로 조정 가능하도록 했습니다.
- **`pool_recycle=1800`(30분)**: 방화벽이나 DB 서버가 오래 유휴 상태인 연결을 끊는 경우가 흔해서, 그보다 먼저 SQLAlchemy가 스스로 연결을 재활용하도록 설정했습니다.
- **환경변수 이름을 `DB_*` 접두사로 통일**: `.env.example`(T005)의 `DATABASE_URL`과 구분되면서도 관련 설정임이 드러나도록 `DB_POOL_SIZE` 등으로 네이밍했습니다. 다만 `.env.example`에는 아직 이 값들을 추가하지 않았습니다 — 기본값만으로도 정상 동작하기 때문에, 명시적으로 조정이 필요해지는 시점(성능 튜닝)에 추가하는 것이 YAGNI에 맞다고 판단했습니다.

## 비고
- `.env.example`에 `DB_POOL_SIZE` 등을 당장 추가하지 않았습니다. 필요 시 나중에 추가할 수 있도록 이 Task Report에 환경변수 이름을 기록해 둡니다: `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_TIMEOUT`, `DB_POOL_RECYCLE`.
- 검증 과정에서 Docker Desktop이 꺼져 있던 것을 발견하고 복구했습니다. 이 프로젝트를 다시 열 때마다 Docker Desktop이 실행 중인지 먼저 확인하는 습관이 필요합니다.
