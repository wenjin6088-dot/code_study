# TASK-095. 문서 생성 큐 + 상태 추적 서비스 구현

## 상태
완료

## 날짜
2026-11-18

## 작업 요약
`backend/src/services/document/document_queue_service.py`에 `DocumentQueueService`를 구현했습니다. `LearningDocument` 행의 생성·재큐잉과, T097/T098 API가 상태를 읽기 위해 필요한 조회를 담당합니다. T094(Celery 태스크)는 이 서비스가 만들어 둔 행을 전제로 `pending` → `in_progress` → `completed`/`failed` 전환만 수행하고, 행 자체를 "처음 만드는" 책임과 "다시 큐에 넣는" 책임은 이 서비스가 집니다.

- **`enqueue_generation(task_id) -> LearningDocument`**:
  - 행이 없으면 `content=placeholder({chapter1..7: {}})`, `generation_status="pending"`으로 새로 생성.
  - 행이 있고 상태가 `pending`/`in_progress`(이미 큐에 있거나 실행 중)면 **그대로 반환, 재큐잉하지 않음** — 중복 Celery 태스크 방지.
  - 행이 있고 상태가 `completed`/`failed`(종료 상태)면 `content`를 placeholder로, 상태를 `pending`으로, `generation_error`/`generation_started_at`/`generation_completed_at`을 `None`으로 리셋한 뒤 재큐잉 — FR-094의 "수동 재시도" 경로.
  - 두 경우 모두 `self._enqueue(task_id)`(기본값은 실제 Celery `.delay()`)를 호출해 반환된 celery task id를 `celery_task_id` 컬럼에 저장.
- **`get_status(task_id) -> LearningDocument | None`**: 존재하지 않으면 `None` — T097/T098이 이를 "Learning document not found" 404로 변환.
- **`enqueue: EnqueueFn | None`을 생성자 주입**으로 받아, 테스트에서는 실제 Redis/Celery를 건드리지 않는 `FakeEnqueue`로 대체 가능. 기본값(`_default_enqueue`)은 `src.tasks.document_generation.generate_document_task.delay(str(task_id))`를 호출하는 실제 구현.

## 변경 파일
- `backend/src/services/document/document_queue_service.py` (신규 생성)
- `backend/tests/integration/test_document_queue_service.py` (신규 생성)
- `specs/001-ai-code-learning-platform/tasks.md` (T095 `[X]` 체크)
- `docs/task-reports/TASK-095-문서생성-큐-상태추적-서비스-구현.md` (본 보고서)

## TDD 결과
- RED: 해당 없음(git 저장소 아님). `pytest` 실행으로 RED 확인: `ModuleNotFoundError: No module named 'src.services.document.document_queue_service'`.
- GREEN: 구현 후 `tests/integration/test_document_queue_service.py` 8개 테스트(실 DB `db_session` + `FakeEnqueue`) 전부 통과.
- REFACTOR: 해당 없음(동일 사유). `ruff format` + `ruff check src/ tests/` 통과.
- 최종 전체 스위트: `pytest` 368개 전부 통과(회귀 없음).
- 커버리지: `src/services/document/document_queue_service.py` **100%**(40 stmts, 0 miss).

## 기술 결정
1. **`pending`/`in_progress`일 때 재큐잉 차단, `completed`/`failed`일 때만 재큐잉 허용**: data-model.md의 `generation_status` 상태값(`pending`/`in_progress`/`completed`/`failed`) 중 "이미 진행 중" 두 가지는 중복 실행 방지가 필요하고, "끝난" 두 가지는 FR-094가 요구하는 수동 재시도를 허용해야 한다고 판단해 이 두 그룹으로 나눴습니다. T096이 업로드 직후 자동으로 이 메서드를 호출하므로, 만약 사용자가 재업로드 등으로 같은 task에 두 번 트리거를 걸어도(이론상 현재는 업로드가 task당 1회이므로 발생하지 않지만 방어적으로) 중복 Celery 태스크가 쌓이지 않도록 했습니다.
2. **`enqueue`를 콜러블로 주입**: Celery `.delay()`는 Redis 연결이 필요합니다. 이 프로젝트의 테스트 환경에는 실제 Redis가 떠 있어 동작은 하지만(확인됨: `redis.Redis().ping() == True`), 서비스 로직 자체의 단위/통합 테스트는 인프라에 의존하지 않고 결정론적으로 검증해야 하므로 `FakeEnqueue`로 대체했습니다. `_default_enqueue`에서 `src.tasks.document_generation`을 함수 내부 지연 import한 것은 순환 참조를 피하기 위함이 아니라(실제로는 순환 참조가 없음) 모듈 임포트 시점에 Celery 앱 설정이 전부 끝난 뒤 태스크 객체를 참조하도록 하기 위한 안전장치입니다.
3. **재큐잉 시 `content`를 placeholder로 리셋**: `completed` 상태였던 행을 재큐잉하면 이전 생성 결과(`content`)가 남아있는 상태로 `pending`이 되는 것은 "생성 중인데 완료된 것처럼 보이는" 모순을 만들 수 있어, 재큐잉 즉시 placeholder로 되돌렸습니다.

## 비고
- T096(업로드 완료 트리거)과 T097/T098(API 엔드포인트) 모두 이 서비스를 통해서만 `LearningDocument`에 접근합니다. API 레이어가 직접 테이블을 조회하지 않도록 해, 상태 조회 로직을 한 곳에 모았습니다.
