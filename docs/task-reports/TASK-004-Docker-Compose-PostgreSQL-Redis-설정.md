# TASK-004. Docker Compose 설정 (PostgreSQL, Redis)

## 상태
완료

## 날짜
2026-10-29

## 작업 요약
이 프로젝트는 데이터를 저장할 창고(PostgreSQL)와, 빠른 심부름꾼 역할을 할 Redis(Celery 작업 큐 + 캐시)가 필요합니다. 두 서버를 개발자 PC마다 일일이 설치하는 대신, "레시피 한 장(docker-compose.yml)"만 있으면 명령 한 줄(`docker-compose up -d`)로 똑같은 환경을 누구나 재현할 수 있도록 설정했습니다.

구체적으로 루트 디렉토리에 `docker-compose.yml`을 만들고 두 개의 서비스를 정의했습니다.

1. **db (PostgreSQL 15-alpine)**: data-model.md가 요구하는 PostgreSQL 15+ 버전을 사용합니다. 포트 5432로 외부에서 접속할 수 있고, `postgres_data`라는 이름의 볼륨에 데이터를 저장해 컨테이너를 껐다 켜도 데이터가 사라지지 않습니다. 접속 계정 정보(`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`)는 `.env` 파일의 값을 사용하되, 값이 없으면 quickstart.md와 동일한 기본값(postgres/postgres/codelearning)을 쓰도록 했습니다.
2. **redis (Redis 7-alpine)**: research.md가 요구하는 Redis 7+ 버전을 사용합니다. 포트 6379로 접속 가능하고, `redis_data` 볼륨으로 데이터를 보존합니다.

두 서비스 모두 "healthcheck"(상태 확인 장치)를 추가했습니다. 이는 "이 서버가 켜져있다"가 아니라 "이 서버가 실제로 요청을 받을 준비가 됐다"를 확인하는 장치로, 나중에 백엔드/Celery 워커가 DB/Redis보다 먼저 뜨려다 실패하는 문제를 예방하는 데 도움이 됩니다.

## 변경 파일
- `docker-compose.yml` (신규 생성, 루트 디렉토리)

## TDD 결과
- Docker Compose 설정 파일 작성은 테스트할 비즈니스 로직이 없어 RED-GREEN-REFACTOR 사이클은 적용하지 않았습니다. 대신 PyYAML로 파일을 파싱해 문법 오류가 없는지, 그리고 `services.db`/`services.redis`가 올바른 이미지(`postgres`, `redis`)를 쓰는지 구조적으로 검증했습니다.
- **(추가 업데이트, 2026-10-29)** 작성 당시에는 이 환경에 Docker가 없어 실제 실행 검증을 못 했지만, 이후 사용자가 Docker Desktop과 WSL2를 설치해 실행 검증을 완료했습니다:
  - `docker compose up -d` → `postgres:15-alpine`, `redis:7-alpine` 이미지 pull 및 컨테이너 생성 성공
  - `docker compose ps` → 두 컨테이너 모두 `Up (healthy)` 상태 확인
  - 컨테이너 내부 검증: `pg_isready -U postgres` → `accepting connections`, `redis-cli ping` → `PONG`
  - Windows 호스트에서 포트 접근 검증: `Test-NetConnection localhost -Port 5432`, `-Port 6379` 모두 `TcpTestSucceeded: True`
  - 즉, docker-compose.yml이 설계 의도대로 실제 환경에서 정확히 동작함을 확인했습니다.
- 저장소가 아직 git으로 초기화되지 않아 관련 커밋은 생성하지 않았습니다.
- 테스트 커버리지: 해당 없음 (인프라 설정 파일, 비즈니스 로직 코드 없음)

## 기술 결정
- **범위를 PostgreSQL + Redis로만 제한**: quickstart.md의 예시 docker-compose는 backend/frontend/celery 컨테이너까지 포함하지만, tasks.md의 T004는 명시적으로 "PostgreSQL, Redis"만 범위로 지정하고 있고, tasks.md 전체를 검토한 결과 backend/frontend용 `Dockerfile`을 만드는 별도 Task가 존재하지 않습니다. 따라서 이번 Task에서는 Dockerfile이 없는 backend/frontend 서비스를 억지로 compose에 넣지 않고, 데이터베이스/캐시 인프라만 담당하도록 범위를 좁혔습니다(YAGNI). 백엔드/Celery 워커는 현재 로컬 가상환경(`uvicorn`, `celery worker`)으로 직접 실행하는 것을 전제로 합니다.
- **`version` 키 생략**: 최신 Docker Compose(v2)는 `version:` 필드가 더 이상 필요하지 않고 오히려 "obsolete" 경고를 띄웁니다. 그래서 최신 Compose Spec 방식으로 `version` 없이 작성했습니다.
- **환경변수 기본값 패턴 (`${VAR:-default}`)**: `.env` 파일이 아직 없는 상태(T005에서 생성 예정)에서도 `docker-compose up`이 즉시 동작하도록, quickstart.md에 명시된 기본값(postgres/postgres/codelearning)을 폴백으로 넣었습니다. `.env` 파일이 생기면 자동으로 그 값이 우선 적용됩니다.
- **healthcheck 추가**: tasks.md에 명시되어 있지는 않지만, Celery/백엔드가 DB 준비 전에 연결을 시도해 실패하는 흔한 문제를 예방하기 위해 넣었습니다. `pg_isready`와 `redis-cli ping`은 각 공식 이미지에 기본 포함된 도구라 추가 설치가 필요 없습니다.

## 비고
- Docker Desktop 설치 과정에서 WSL2가 함께 필요했고(최초 환경에 WSL2 미설치), 설치 후 재부팅과 Docker Desktop 앱 수동 실행이 필요했습니다. 이후 환경에서는 Docker Desktop이 자동으로 백그라운드 실행되는지 별도 확인이 필요합니다.
- `.env` 파일은 여전히 실제로 생성하지 않았고(T005에서 템플릿만 작성), 현재는 compose의 기본값(`${VAR:-default}`)만으로 동작을 확인했습니다. T005의 `.env.example`과 변수명이 정확히 일치함을 교차 확인했습니다.
- backend/frontend/celery를 컨테이너화하는 작업은 현재 tasks.md 범위에 없으므로, 필요해지면 별도 Task로 추가하는 것을 제안합니다.
