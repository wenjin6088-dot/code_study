# TASK-096. 코드 업로드 완료 후 문서 생성 자동 트리거

## 상태
완료

## 날짜
2026-11-18

## 작업 요약
tasks.md 원문은 "Add document generation trigger after code upload in TaskService"라고 되어 있으나, 실제 코드에서 코드 업로드 저장은 `TaskService`가 아니라 `CodeUploadService.create_upload()`가 담당하고, 둘 다 `backend/src/api/tasks.py`의 `create_task` 엔드포인트에서 순차 호출됩니다. "TaskService 안에"라는 문구를 문자 그대로 따르기보다 "코드 업로드가 성공적으로 끝난 직후 문서 생성이 자동으로 큐에 들어간다"는 의도를 살렸습니다.

**트리거 위치**: `backend/src/api/tasks.py`의 `create_task` 엔드포인트, `upload_service.create_upload(...)` 호출이 **성공적으로 끝난 직후**(반환된 `upload_result`를 얻은 다음, `_task_response(...)`를 반환하기 전):

```python
upload_result = await upload_service.create_upload(
    user_id=user.id, task_id=task.id, files=validated_files
)

# T096: code upload succeeded, so queue AI document generation (T094/T095)
# right away instead of waiting for the user to open the task.
await DocumentQueueService(session).enqueue_generation(task.id)

return _task_response(task, upload_result)
```

**이 지점을 고른 근거**:
1. `create_task` 엔드포인트 안에서만 "제목/설명 검증 → upload_method 검증 → 파일 검증(`validate_files`, 이 시점에 400 에러로 실패할 수 있음) → `Task` 생성 → `create_upload`(업로드 영속화)"가 전부 순서대로 일어나며, 이 순서가 끝나는 지점이 "코드 업로드가 성공적으로 끝난 직후"와 정확히 일치합니다. `TaskService.create()` 내부에 넣으면 아직 코드가 업로드되기 *전*(심지어 업로드 자체가 `CodeUploadError`로 실패할 수도 있는 시점)에 문서 생성이 트리거되어, "코드 없음" 상태로 Celery 태스크가 실행되는 문제가 생깁니다.
2. `CodeUploadService.create_upload()` 내부에 넣는 대안도 검토했으나, 그 경우 `CodeUploadService`가 `DocumentQueueService`(→ Celery 태스크 → `GeminiClient`)를 알게 되어 "파일 검증/영속화"라는 단일 책임을 넘어서는 의존성이 생깁니다. API 레이어(`create_task`)가 "업로드 서비스 호출 다음에 큐 서비스 호출"이라는 오케스트레이션을 담당하는 것이 기존 관례(엔드포인트가 `TaskService`+`CodeUploadService` 두 서비스를 순서대로 호출하는 기존 패턴)와 더 잘 맞습니다.
3. 검증 실패(`CodeUploadError`, title/description 검증 실패 등)로 400을 반환하는 경로는 `create_upload` 호출 자체에 도달하지 않으므로 자동으로 트리거가 걸리지 않습니다(테스트로 확인).

## 변경 파일
- `backend/src/api/tasks.py` (수정: `DocumentQueueService` import + `create_task`에서 업로드 성공 직후 `enqueue_generation` 호출)
- `backend/tests/integration/test_documents_api.py` (신규 생성, T096 트리거 테스트 포함 — T097/T098과 같은 파일)
- `specs/001-ai-code-learning-platform/tasks.md` (T096 `[X]` 체크)
- `docs/task-reports/TASK-096-코드업로드-후-문서생성-자동트리거.md` (본 보고서)

## TDD 결과
- RED: 별도 RED 커밋 없음(git 저장소 아님). T096 테스트는 T097/T098과 같은 파일(`test_documents_api.py`)에 함께 작성했고, `src/api/documents.py`/`src/services/document/document_queue_service.py`가 아직 없던 시점에 전체 파일이 `ModuleNotFoundError`로 수집 실패하는 것으로 RED를 확인(T095/T097/T098 보고서와 동일 세션에서 함께 확인).
- GREEN: 구현 후 `TestDocumentGenerationTriggeredOnUpload` 2개 테스트 통과:
  - `test_creates_pending_learning_document_after_successful_upload`: 실제 `POST /api/v1/projects/{project_id}/tasks`(paste 업로드) 호출 → DB에서 `LearningDocument` 행이 `pending` 상태, `content`가 7챕터 placeholder 키를 모두 가짐, `celery_task_id`가 `None`이 아님(즉 실제 Redis에 `.delay()`가 성공적으로 전달됨)을 확인. **이 테스트는 실제 Redis 브로커를 사용**(환경에 이미 떠 있는 컨테이너, 추가 설정 없이 통과).
  - `test_does_not_create_document_when_upload_validation_fails`: 업로드 검증 실패(400) 시 `LearningDocument` 행이 전혀 생성되지 않음을 확인.
- REFACTOR: 해당 없음(동일 사유). `ruff format` + `ruff check src/ tests/` 통과.
- 최종 전체 스위트: `pytest` 368개 전부 통과(기존 `test_tasks_api.py`의 `create_task` 관련 테스트들도 전부 회귀 없이 통과 — 각 성공 케이스마다 실제 Redis enqueue가 추가로 일어나지만 실패하지 않음).

## 기술 결정
- **에러를 삼키지 않음**: `enqueue_generation(...)` 호출을 `try/except`로 감싸 Redis 장애 시에도 task 생성을 성공시키는 방어적 코드는 추가하지 않았습니다. YAGNI 원칙과 "최소 구현" 원칙에 따라, 현재 스펙(T096)이 요구하는 것은 "성공 시 트리거"뿐이고 "큐 인프라 장애 시 성능 저하 처리"는 별도 요구사항이 명시되지 않았기 때문입니다. Redis가 다운되면 `create_task` 자체가 500으로 실패하며, 이는 기존 코드베이스의 다른 인프라 의존 호출(`file_storage.save_file` 등)과 동일한 수준의 에러 처리 관례입니다.

## 비고
- 이 트리거는 `DocumentQueueService.enqueue_generation`의 멱등성(T095)에 의존합니다: 만약 미래에 코드 재업로드 기능이 추가되어 같은 task에 대해 `create_upload`가 여러 번 호출되더라도, 이미 `pending`/`in_progress`인 문서는 중복 큐잉되지 않습니다.
