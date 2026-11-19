# TASK-098. GET /tasks/{task_id}/document/status 엔드포인트 구현

## 상태
완료

## 날짜
2026-11-18

## 작업 요약
`backend/src/api/documents.py`에 `GET /api/v1/tasks/{task_id}/document/status`를 T097과 같은 파일에 구현했습니다(두 엔드포인트가 "task 소유 + LearningDocument 조회" 로직을 공유).

**응답 (200)**:
```json
{
  "status": "pending" | "in_progress" | "completed" | "failed",
  "error": string 또는 null,
  "estimated_seconds_remaining": number 또는 null
}
```
- `error`는 `status == "failed"`가 아니면 `null`.
- `estimated_seconds_remaining`: FR-083의 목표 생성 시간 180초(`TARGET_GENERATION_SECONDS`)에서 `generation_started_at` 이후 경과 시간을 뺀 값, 0 미만이면 0으로 클램프. `status != "in_progress"`이거나 `generation_started_at`이 `None`이면(아직 시작 안 함/완료/실패) `null`. 과도한 정교화 없이 YAGNI에 맞게 선형 추정치만 제공.

**404**: T097과 동일한 두 가지 메시지("Task not found" / "Learning document not found")를 그대로 공유(`_get_owned_document` 헬퍼).

## 변경 파일
- `backend/src/api/documents.py` (T097과 함께 신규 생성 — `get_document_status` + `_estimated_seconds_remaining`)
- `backend/tests/integration/test_documents_api.py` (신규 생성 — `TestGetDocumentStatusEndpoint`)
- `specs/001-ai-code-learning-platform/tasks.md` (T098 `[X]` 체크)
- `docs/task-reports/TASK-098-GET-tasks-document-status-엔드포인트.md` (본 보고서)

## TDD 결과
- RED: T097/T095와 동일 세션에서 `ModuleNotFoundError`로 확인.
- GREEN: `TestGetDocumentStatusEndpoint` 8개 테스트 통과:
  - 인증 필요, 두 종류의 404.
  - `pending` → `estimated_seconds_remaining is None`.
  - `in_progress`(30초 전 시작) → 대략 150초 전후(140~155초 범위로 허용 오차를 두고 검증, 테스트 실행 시간 변동 흡수).
  - `in_progress`인데 매우 오래 전에 시작(10,000초 전) → `estimated_seconds_remaining == 0`(음수 방지).
  - `completed`/`failed` → `estimated_seconds_remaining is None`, `failed`는 `error` 필드에 메시지 그대로.
- REFACTOR: 해당 없음. `ruff format` + `ruff check src/ tests/` 통과.
- 최종 전체 스위트: `pytest` 368개 전부 통과.
- 커버리지: T097 보고서와 동일한 측정 한계로 `src/api/documents.py` 전체 77%(로직은 테스트 assertion으로 정확성 보장).

## 기술 결정
1. **단순 선형 추정**: "FR-083 목표 180초 - 경과 시간"이라는 가장 단순한 추정치만 제공했습니다. 실제 생성 시간 분포, 파일 개수/크기에 따른 보정 등은 요구사항에 없고(YAGNI), 과도하게 정교할 필요 없다는 지침을 그대로 따랐습니다.
2. **`max(remaining, 0.0)`로 음수 방지**: 생성이 180초를 넘겨도(네트워크 지연, Gemini 응답 지연 등) 음수 ETA를 보여주는 것은 사용자 경험상 혼란스러우므로 0으로 바닥을 뒀습니다.
3. **`pending` 상태는 `estimated_seconds_remaining = null`**: 아직 `generation_started_at`이 없는 상태(큐에 들어갔지만 Celery 워커가 아직 집지 않음)에서는 "언제 시작할지" 알 수 없으므로 추정하지 않습니다.

## 비고
- T097/T098 두 엔드포인트 모두 같은 `_get_owned_document` 헬퍼를 사용하므로, 두 응답의 404 동작은 항상 동일하게 유지됩니다. 추후 한쪽 엔드포인트의 404 메시지를 바꾸면 다른 쪽도 자동으로 따라갑니다(의도된 결합).
