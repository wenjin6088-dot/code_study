# TASK-072. GET /tasks/{task_id} 엔드포인트 구현

## 상태
완료

## 날짜
2026-11-16

## 작업 요약
`backend/src/api/tasks.py`에 `GET /tasks/{task_id}`를 구현했습니다. `TaskService.get(user_id, task_id)`을 호출해 소유자면 Task의 `deletion_status`(active/trashed)와 무관하게 조회할 수 있게 했습니다(`ProjectService.get`과 동일한 정책이라는 계약을 그대로 따름). 존재하지 않거나 소유자가 아니면 `TaskNotFoundError` → 404.

조회된 Task에 대해 `CodeUploadService.get_for_task`로 업로드 정보를 조회해 `TaskResponse.uploaded_code`에 중첩시킵니다(업로드 전이면 `null`).

## 변경 파일
- `backend/src/api/tasks.py` (`get_task` 핸들러)
- `backend/tests/integration/test_tasks_api.py`의 `TestGetTaskEndpoint` 클래스(테스트 4개: 미인증 401, 본인 Task 200, 존재하지 않는 id 404, 타인 Task 404)

## TDD 결과
- RED → GREEN: 4개 테스트 모두 라우터 구현 후 1차 통과.
- `ruff check` 통과.
- 전체 회귀(`pytest -q`, 284 tests) 통과.
- Git 저장소 미초기화로 커밋 해시 없음.

## 기술 결정
- **트래시된 Task도 조회 가능하게 유지**: `TaskService.get`이 `deletion_status` 필터를 걸지 않으므로, 삭제된(trashed) Task의 상세 화면(예: Trash 복구 미리보기)을 나중에 만들 때 이 엔드포인트를 그대로 재사용할 수 있습니다. 이번 Task 세트에는 Trash 페이지 연동이 범위 밖(T176/T177/T179에서 처리)이지만, 조회 자체를 막을 이유가 없어 계약에 명시된 정책을 그대로 구현했습니다.

## 비고
- 없음.
