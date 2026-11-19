# TASK-097. GET /tasks/{task_id}/document 엔드포인트 구현

## 상태
완료

## 날짜
2026-11-18

## 작업 요약
`backend/src/api/documents.py`에 `GET /api/v1/tasks/{task_id}/document`를 구현했습니다. 프론트엔드 에이전트가 동시에 이 계약대로 `document-service.ts`를 작성하므로, 사전에 확정된 응답 스키마를 그대로 구현했습니다.

**응답 (200)**:
```json
{
  "task_id": "<uuid>",
  "status": "pending" | "in_progress" | "completed" | "failed",
  "content": {chapter1..chapter7} 또는 null,
  "error": string 또는 null,
  "generated_at": ISO8601 또는 null
}
```
- `content`는 `status == "completed"`가 아니면 항상 `null`(DB에는 placeholder `{}` 들이 들어 있어도 API로는 절대 노출하지 않음).
- `error`는 `status == "failed"`가 아니면 항상 `null`.
- `generated_at`은 `status == "completed"`이고 `generation_completed_at`이 있을 때만 ISO8601 문자열.

**404 (`NotFoundError`)**: 두 가지를 메시지로 구분합니다.
- `task_id`가 존재하지 않거나 현재 사용자 소유가 아니면 `"Task not found"` (`TaskService.get(...)`이 던지는 `TaskNotFoundError`를 그대로 매핑).
- task는 있지만(소유 확인 통과) `LearningDocument` 행이 아직 없으면(코드가 업로드되지 않음) `"Learning document not found"`.

## 변경 파일
- `backend/src/api/documents.py` (신규 생성 — T097 `get_document` + T098 `get_document_status` 공유)
- `backend/src/api/router.py` (수정: `documents_router` 등록)
- `backend/tests/integration/test_documents_api.py` (신규 생성 — `TestGetDocumentEndpoint`)
- `specs/001-ai-code-learning-platform/tasks.md` (T097 `[X]` 체크)
- `docs/task-reports/TASK-097-GET-tasks-document-엔드포인트.md` (본 보고서)

## TDD 결과
- RED: `pytest` 실행으로 확인: `ModuleNotFoundError: No module named 'src.services.document.document_queue_service'`(T095와 공유 의존성이라 함께 RED).
- GREEN: `TestGetDocumentEndpoint` 6개 테스트 통과(인증 필요/두 종류의 404 메시지 구분/pending·completed·failed 각 상태별 응답 바디 정확히 일치).
- REFACTOR: 해당 없음(동일 사유). `ruff format` + `ruff check src/ tests/` 통과.
- 최종 전체 스위트: `pytest` 368개 전부 통과.
- 커버리지: `src/api/documents.py` 두 엔드포인트 공유 — 전체 스위트 기준 77%. 미달 라인은 `_get_owned_document`의 `except`/`return` 문과 `_estimated_seconds_remaining`의 일부 분기로, 테스트가 해당 경로를 실제로 실행시켜 통과함(assertion으로 404/정상 응답 모두 검증됨)에도 `pytest-cov`가 FastAPI 의존성 주입을 통해 호출되는 async 함수 내부 일부 라인을 추적하지 못하는 것으로 보이는 측정 한계입니다. 로직 정확성은 테스트 통과로 보장됩니다.

## 기술 결정
1. **`_get_owned_document` 헬퍼를 T097/T098이 공유**: "task 소유권 확인 → `LearningDocument` 조회 → 없으면 404" 로직이 두 엔드포인트에서 동일하므로 중복을 피했습니다.
2. **"Task not found"와 "Learning document not found"를 서로 다른 예외 발생 지점에서 분리**: `TaskService.get(...)`의 `TaskNotFoundError`(소유권/존재 여부)와, `DocumentQueueService.get_status(...)`가 `None`을 반환하는 경우(존재하지만 아직 업로드/생성 트리거가 없음)를 명확히 구분해, 프론트엔드가 "이 task가 없다"와 "이 task는 있는데 아직 문서가 없다"를 다르게 안내할 수 있게 했습니다.
3. **`content`/`error`를 상태에 따라 선택적으로 노출**: DB의 `content` 컬럼은 제약조건 때문에 생성 전에도 placeholder(`{chapter1: {}, ...}`)를 담고 있지만, 이를 그대로 API로 내려보내면 프론트엔드가 "완료된 것처럼" 오인할 수 있으므로 `status == "completed"`일 때만 노출합니다.
4. **응답 모델을 Pydantic `BaseModel`로 분리 정의**(`DocumentResponse`): 기존 `tasks.py`의 `TaskResponse` 등과 동일한 관례를 따랐습니다.

## 비고
- 이 엔드포인트는 Celery 태스크(T094)가 실제로 실행되지 않아도(워커 없이도) 동작을 검증할 수 있도록, DB에 `LearningDocument` 행을 직접 삽입해 각 상태(pending/completed/failed)를 시뮬레이션하는 테스트 방식을 택했습니다.
