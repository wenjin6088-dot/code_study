# TASK-015. API 라우터 구조 (/api/v1)

## 상태
완료

## 날짜
2026-11-02

## 작업 요약
앞으로 만들어질 수십 개의 API 엔드포인트(로그인, 프로젝트 목록, 태스크 업로드 등)를 전부 `main.py` 한 파일에 몰아넣으면 금방 관리가 안 됩니다. 그래서 "모든 API 요청은 `/api/v1`이라는 공통 대문을 통과한다"는 구조를 먼저 만들었습니다. 이 대문 자체는 지금은 텅 비어있고, 앞으로 T028(인증), T046(프로젝트) 같은 Task들이 각자의 라우터를 이 대문에 하나씩 연결할 예정입니다.

1. **`backend/src/api/router.py`**: `api_router = APIRouter(prefix="/api/v1")` — 아직 아무 경로도 없는 빈 라우터를 만들었습니다. 앞으로 `api_router.include_router(auth_router)`처럼 각 기능별 라우터를 여기에 꽂아 넣으면, 자동으로 `/api/v1/auth/...` 형태의 경로가 됩니다.
2. **`backend/src/main.py` (수정)**: 이 빈 대문(`api_router`)을 실제 앱(`app`)에 연결했습니다 (`app.include_router(api_router)`). 이 연결이 없으면 나중에 각 라우터를 `api_router`에 꽂아도 앱이 그걸 몰라서 반영이 안 됩니다.

## 변경 파일
- `backend/src/api/router.py` (신규 생성)
- `backend/src/main.py` (수정: `api_router` import 및 `app.include_router(api_router)` 추가)

## TDD 결과
- 빈 라우터를 연결하는 작업은 테스트할 비즈니스 로직이 없어, "실제로 연결이 되어 있는가"를 직접 실행으로 검증했습니다.
  - `ruff check`, `black --check` 통과
  - `uvicorn src.main:app` 실제 기동 → 정상 시작, 기존 `/`, `/health` 엔드포인트 계속 정상 응답(`200 OK`) 확인 — 라우터 추가가 기존 기능을 깨뜨리지 않음을 확인
  - `app.routes`를 직접 출력해 확인한 결과, `api_router`가 비어있어 눈에 보이는 경로 변화는 없었습니다. 이것만으로는 "연결이 진짜로 동작하는지"를 확신할 수 없어서, **임시로 `api_router`에 테스트용 경로(`/_verify_prefix_tmp`)를 추가**해 다시 검증했습니다:
    - `GET /api/v1/_verify_prefix_tmp` → `200 OK` (prefix가 정확히 적용됨)
    - `GET /_verify_prefix_tmp` (prefix 없이) → `404 Not Found` (prefix 없이는 접근 안 됨, 중복 등록 같은 실수가 없음을 확인)
  - 검증이 끝난 뒤 테스트용 경로는 제거하고, `router.py`를 원래의 빈 상태로 되돌렸습니다.
- 저장소가 아직 git으로 초기화되지 않아 관련 커밋은 생성하지 않았습니다.
- 테스트 커버리지: 해당 없음 (라우터 구조 설정, 비즈니스 로직 없음)

## 기술 결정
- **지금은 완전히 빈 라우터로 둠**: 실제 서브 라우터(`auth.py`, `projects.py` 등)는 각자의 Task(T028, T046 등)에서 만들어질 예정이라, 이번 Task에서 미리 추측해서 만들지 않았습니다(YAGNI). `api_router`라는 "연결 지점"만 먼저 만들어두는 것이 이번 Task의 범위입니다.
- **`main.py`에 연결까지 포함**: tasks.md에는 "router.py 생성"이라고만 적혀 있지만, 라우터를 만들고 앱에 연결하지 않으면 아무 의미가 없어서 `app.include_router(api_router)`를 함께 추가했습니다. 이는 T011(db config를 session.py에 연결)에서와 같은 패턴입니다 — 부품을 만들면 실제로 조립까지 끝내서 다음 Task가 바로 이어서 쓸 수 있게 합니다.
- **임시 검증 라우트 추가 후 제거**: 빈 라우터는 연결 여부를 눈으로 확인할 방법이 없어서, 검증 전용 임시 엔드포인트를 잠깐 추가했다가 확인 후 즉시 제거했습니다. 이 임시 코드는 최종 결과물에 남아있지 않습니다.

## 비고
- 다음에 인증 라우터(T028)가 추가되면 `backend/src/api/router.py`에 `from src.api.auth import router as auth_router` 후 `api_router.include_router(auth_router)` 형태로 연결하면 됩니다.
- 현재 `main.py`는 `root()`, `health_check()` 두 엔드포인트가 `/api/v1` 바깥(앱 최상단)에 남아있습니다. 이들은 인프라 상태 확인용이라 `/api/v1` 비즈니스 API와 분리해두는 것이 맞다고 판단해 그대로 두었습니다.
