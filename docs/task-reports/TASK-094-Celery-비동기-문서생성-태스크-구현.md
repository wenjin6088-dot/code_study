# TASK-094. Celery 비동기 문서 생성 태스크 구현

## 상태
완료

## 날짜
2026-11-18

## 작업 요약
`backend/src/tasks/document_generation.py`에 Celery 태스크 `generate_document_task`와 그 핵심 로직인 순수 async 함수 `generate_document_async`를 구현했습니다. T093의 `DocumentGenerationService.generate_document(...)`를 "호출"하는 오케스트레이션(코드 파일 로딩, 상태 전환, 에러 기록)만 담당하며, AI 재시도/7챕터 검증은 전부 T093에 위임합니다.

- Celery 태스크 함수(`generate_document_task`)는 동기(sync)이며 `asyncio.run(_run(...))`으로 async core(`generate_document_async`)를 구동하는 얇은 wrapper입니다. `_run`은 자체 `AsyncSessionLocal()` DB 세션과 `GeminiClient()`(환경변수 `GOOGLE_API_KEY` 필요)를 생성해 `DocumentGenerationService`를 주입합니다.
- `generate_document_async(task_id, session, *, document_service)`는 DB 세션과 `document_service`(Protocol: `generate_document(files, *, detected_language, complexity_level) -> dict`)를 인자로 받아 Celery/GeminiClient에 전혀 의존하지 않습니다. 이 덕분에 Celery 워커나 실제 Gemini API 키 없이 통합 테스트가 가능합니다.
- 흐름: `LearningDocument` 행 조회(없으면 `TaskCodeNotFoundError` — T095가 먼저 행을 만들어야 하므로 이는 오케스트레이션 버그를 의미) → `generation_status="in_progress"` + `generation_started_at` 커밋 → `UploadedCode`/`CodeFile` 조회 및 `file_storage.read_file(...)`로 원본 코드 읽기 → `DocumentGenerationService.generate_document(...)` 호출 → 성공 시 `content` 덮어쓰고 `completed`, 실패(코드 없음/Gemini 설정오류/재시도 소진/구조 검증 실패 등 모든 예외) 시 `failed` + `generation_error=str(exc)` + `generation_completed_at` 기록(FR-094: 명확한 에러 메시지).

## 변경 파일
- `backend/src/tasks/document_generation.py` (신규 생성)
- `backend/tests/integration/test_document_generation_task.py` (신규 생성)
- `specs/001-ai-code-learning-platform/tasks.md` (T094 `[X]` 체크)
- `docs/task-reports/TASK-094-Celery-비동기-문서생성-태스크-구현.md` (본 보고서)

## TDD 결과
- RED: 해당 없음(git 저장소 아님). 대신 `pytest` 실행으로 RED 확인: `ModuleNotFoundError: No module named 'src.tasks.document_generation'`.
- GREEN: 구현 후 `tests/integration/test_document_generation_task.py` 7개 테스트 전부 통과(실 DB `db_session` + 실 파일시스템 `file_storage`로 통합 테스트, Gemini는 Fake `DocumentGenerationService`로 대체).
- REFACTOR: 해당 없음(동일 사유). `ruff format` + `ruff check src/ tests/` 통과.
- 최종 전체 스위트: `pytest` 368개 전부 통과(회귀 없음).
- 커버리지: `src/tasks/document_generation.py` 93%(60 stmts, 4 miss — 미달 라인은 `_run`/`generate_document_task`, 즉 실제 Gemini API 키가 필요한 Celery wrapper 자체로, 관례상 Fake로 대체할 수 없는 부분이라 의도적으로 테스트 제외).

## 기술 결정
1. **동기 Celery 태스크 ↔ async core 분리**: Celery 태스크는 동기 함수여야 하지만 DB 세션과 `DocumentGenerationService`는 async이므로, `@celery_app.task`로 감싼 `generate_document_task(task_id: str)`가 `asyncio.run(_run(uuid.UUID(task_id)))`만 수행하고, 실제 로직은 `generate_document_async`에 전부 위임했습니다. CLAUDE.md 사전 지침과 동일한 패턴.
2. **실패를 "모두" 캡처해 `failed`로 기록**: `_load_code_files`(업로드된 코드 없음 → `TaskCodeNotFoundError`)와 `document_service.generate_document(...)`(Gemini 설정오류/API오류/구조검증오류) 양쪽에서 터지는 모든 예외를 `generate_document_async`의 `try/except Exception`에서 포괄적으로 잡아 `generation_error=str(exc)`로 기록합니다. 백그라운드 작업의 최종 에러 경계이므로, 어떤 예외든 사용자에게 "실패 + 에러 메시지"로 전달되는 것이 "영원히 in_progress로 멈춤"보다 안전하다고 판단했습니다(FR-094).
3. **`LearningDocument` 행이 없으면 예외를 그대로 전파**: 이 경우는 T095가 먼저 pending 행을 만들어야 하는 전제가 깨진 상황(오케스트레이션 버그)이므로 조용히 삼키지 않고 `TaskCodeNotFoundError`를 바로 올립니다. (반면 행은 있지만 업로드된 코드가 없는 경우는 "failed" 상태로 정상 기록 — 사용자에게 보여줄 수 있는 정상적인 실패 시나리오로 취급.)
4. **`content`는 실패 시에도 placeholder 유지**: `learning_documents.valid_content_structure` CHECK 제약 때문에 실패 시에도 `content` 컬럼을 건드리지 않고(이미 T095가 넣어둔 `{chapter1: {}, ...}` placeholder 그대로) `generation_status`/`generation_error`/`generation_completed_at`만 갱신합니다.
5. **`DocumentServiceProtocol`로 테스트 대역 허용**: `document_service` 파라미터를 `typing.Protocol`로 타입해 실제 `DocumentGenerationService`든 테스트용 Fake든 동일한 인터페이스로 주입 가능하게 했습니다.

## 비고
- `generate_document_task`/`_run`(실제 `GeminiClient()` 생성 포함) 자체는 `GOOGLE_API_KEY`가 필요해 자동 테스트 대상에서 제외했습니다. T093 보고서의 수동 검증 메모와 동일하게, 실제 Celery 워커 동작은 수동/운영 환경에서 별도 확인이 필요합니다.
- Celery 태스크 라우팅(`document_generation` 큐, `task_time_limit=300`)은 기존 `celery_app.py` 설정을 그대로 사용했고 수정하지 않았습니다.

## 검증 메모 (2026-11-18 추가) — 실제 Celery 워커 구동 중 버그 발견·수정
T094~T108을 병렬 구현 완료한 뒤, 실제 환경(Docker PostgreSQL+Redis, `uvicorn`으로 띄운 FastAPI 서버, `celery -A src.tasks.celery_app worker -Q document_generation --include=src.tasks.document_generation`)으로 HTTP API → 자동 트리거(T096) → Celery 워커 → 실제 Gemini API까지 전체 경로를 수동으로 끝까지 실행해 확인했습니다.

- **발견한 버그**: 실제 Celery 워커 프로세스에서 작업이 `pending`에 멈춰 진행되지 않음. 워커 로그에 `sqlalchemy.exc.NoReferencedTableError: ... could not find table 'tasks'` 발생.
- **원인**: `document_generation.py`는 `CodeFile`/`LearningDocument`/`UploadedCode` 모델만 import하고 `Task` 모델은 import하지 않았습니다. `LearningDocument.task_id`에는 `ForeignKey("tasks.id")`가 걸려 있어, `generation_status="in_progress"`로 바꾸고 `session.commit()`하는 순간 SQLAlchemy가 FK 대상 테이블(`tasks`)의 매퍼 등록을 찾는데, **이 모듈만 단독으로 import된 프로세스(Celery 워커)에서는 `tasks` 테이블이 전혀 등록돼 있지 않아** 실패했습니다. FastAPI 프로세스(pytest 포함)에서는 `src/api/tasks.py`가 먼저 `Task`를 import해 두기 때문에 같은 버그가 가려져 있었습니다 — 전체 테스트 스위트(368개)는 이 버그를 전혀 잡지 못했습니다.
- **수정**: `document_generation.py`에 `from src.models.task import Task  # noqa: F401`를 추가해, 이 모듈이 어느 프로세스에서 단독으로 import되더라도 `tasks` 테이블이 매퍼 레지스트리에 등록되도록 했습니다. 수정 후 재실행 결과:
  - `pending` → `in_progress`(`estimated_seconds_remaining` 응답 포함) → `completed`까지 약 25초 내 정상 전환.
  - 실제 Gemini 호출로 생성된 문서에 `chapter1~7` 전부 존재(112~3157자 분량).
  - 존재하지 않는 `task_id`로 `/document`, `/document/status` 둘 다 호출 시 `404 {"error":{"message":"Task not found"}}` 정상 응답.
  - 수정 후 `pytest` 전체 368개 재통과(회귀 없음 확인).
- **부수적으로 발견한 테스트 품질 이슈(수정하지 않음, 참고용으로만 기록)**: `tests/integration/test_documents_api.py`의 `test_does_not_create_document_when_upload_validation_fails`가 `select(LearningDocument)`로 테이블 전체를 조회해 "0건"을 기대하는데, 이는 같은 개발 DB에 수동/탐색적 테스트로 생성된 행이 하나라도 남아 있으면 깨지는 취약한 가정입니다(실제로 위 수동 검증 중 생긴 행 때문에 1회 실패했고, 해당 행을 정리하자 다시 통과함). 이번 작업 범위를 벗어나 고치지 않았으나, 이후 유지보수 시 "이 테스트가 만든 행만" 필터링하도록 바꾸는 게 안전합니다.
- 수동 검증에 사용한 사용자/프로젝트/태스크는 검증 후 DB에서 삭제했고, 띄웠던 `uvicorn`/`celery worker` 프로세스도 모두 종료했습니다. Docker의 PostgreSQL/Redis 컨테이너는 계속 실행 중입니다.
