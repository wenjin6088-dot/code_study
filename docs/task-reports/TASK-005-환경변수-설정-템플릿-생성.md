# TASK-005. 환경변수 설정 템플릿 생성

## 상태
완료

## 날짜
2026-10-29

## 작업 요약
비밀번호나 API 키처럼 "사람마다 다르고, 외부에 노출되면 안 되는 값"들을 코드에 직접 적지 않고 `.env` 파일에 따로 모아두는 것이 보안의 기본 원칙입니다. 하지만 `.env` 파일 자체는 git에 올리지 않기 때문에(비밀번호가 그대로 깃허브에 노출되면 안 되니까요), 새로 합류하는 개발자는 "어떤 값을 채워야 하는지" 알 방법이 없습니다. `.env.example`은 그 빈 양식지 역할을 합니다 — 실제 비밀번호 대신 "여기에 네 비밀번호를 넣어라"는 안내만 적혀 있는, git에 안전하게 올릴 수 있는 견본입니다.

루트 디렉토리에 `.env.example` 파일을 만들고, quickstart.md에 정의된 환경변수들을 그대로 담았습니다.

1. **Database**: `DATABASE_URL`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` — T004에서 만든 `docker-compose.yml`의 PostgreSQL 서비스가 쓰는 것과 정확히 같은 변수명입니다.
2. **Redis**: `REDIS_URL` — Celery 작업 큐와 캐시가 연결할 주소입니다.
3. **Google AI (Gemini)**: `GOOGLE_API_KEY` — 실제 키는 각자 Google AI Studio에서 발급받아 넣어야 합니다 (플레이스홀더만 적어둠).
4. **JWT 비밀키**: `JWT_SECRET_KEY`, `JWT_REFRESH_SECRET` — 로그인 토큰 서명에 쓰는 값으로, 반드시 각자 새로 생성해야 합니다 (주석에 `openssl rand -hex 32` 명령을 안내).
5. **환경 설정**: `ENVIRONMENT`, `DEBUG`, `ALLOWED_ORIGINS` — 개발/운영 모드 구분과 CORS 허용 도메인입니다.
6. **파일 저장소**: `UPLOAD_DIR`, `MAX_UPLOAD_SIZE_MB` — 업로드된 코드 파일을 어디에, 얼마나 큰 것까지 저장할지입니다.

## 변경 파일
- `.env.example` (신규 생성, 루트 디렉토리)

## TDD 결과
- 환경변수 템플릿 작성은 테스트할 비즈니스 로직이 없어 RED-GREEN-REFACTOR 사이클은 적용하지 않았습니다.
- 대신 실제로 동작하는지 수동으로 검증했습니다: `.env.example`을 임시 파일로 복사한 뒤 `docker compose --env-file <임시파일> config` 명령으로 `docker-compose.yml`(T004)이 이 템플릿의 변수들(`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`)을 정확히 읽어 들이는지 확인했고, 검증이 끝난 뒤 임시 파일은 삭제했습니다.
- 저장소가 아직 git으로 초기화되지 않아 관련 커밋은 생성하지 않았습니다.
- 테스트 커버리지: 해당 없음 (설정 템플릿 파일, 비즈니스 로직 코드 없음)

## 기술 결정
- **값은 전부 플레이스홀더/개발용 기본값으로만 채움**: `GOOGLE_API_KEY`, `JWT_SECRET_KEY`, `JWT_REFRESH_SECRET`처럼 실제로는 비밀이어야 하는 값은 "your-xxx-here" 형태의 안내 문구만 넣었습니다. `POSTGRES_USER`/`PASSWORD`/`DB`는 로컬 개발 전용 기본값(postgres/postgres/codelearning)이라 노출되어도 문제가 없어 quickstart.md 그대로 사용했습니다.
- **`DATABASE_URL`/`REDIS_URL` 호스트를 `localhost`로 설정**: quickstart.md는 두 가지 시나리오를 제시합니다 — (1) 백엔드까지 Docker로 묶어서 돌리는 경우(`db`, `redis`라는 서비스 이름을 호스트로 사용) (2) 백엔드는 로컬에서 직접 실행하고 DB/Redis만 Docker로 띄우는 경우(`localhost` 사용). T004에서 백엔드/Celery는 컨테이너화하지 않기로 결정했고(별도 Dockerfile Task가 없음), 실제로 T004 검증 때도 PostgreSQL/Redis를 Docker로 띄우고 Windows 호스트에서 `localhost:5432`/`localhost:6379`로 접속 성공을 확인했으므로, 이 프로젝트의 실제 구성에 맞는 `localhost` 방식을 선택했습니다.
- **frontend용 `.env.local`은 별도로 만들지 않음**: quickstart.md는 프론트엔드용 `VITE_API_BASE_URL`, `VITE_ENVIRONMENT`를 `frontend/.env.local`에 따로 둡니다. 하지만 tasks.md의 T005는 명시적으로 `.env.example` 한 개만을 범위로 지정하고 있어, 이번 Task에서는 루트 템플릿만 다뤘습니다. 프론트엔드 환경변수 파일은 필요해지는 시점(T020 API 클라이언트 등)에 별도로 추가하는 것을 제안합니다.

## 비고
- 실제 개발을 시작하려면 이 파일을 복사해 `.env`를 만들고, `GOOGLE_API_KEY`와 JWT 비밀키들을 직접 채워야 합니다 (`.env`는 git에 커밋되지 않도록 추후 T007에서 `.gitignore`에 포함될 예정입니다).
- `docker compose config`로 변수 해석까지 실제로 검증했기 때문에, T004의 `docker-compose.yml`과 이 템플릿 사이에 변수명 불일치는 없음을 확인했습니다.
