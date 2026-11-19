# TASK-073. PATCH /tasks/{task_id} 엔드포인트 구현

## 상태
완료

## 날짜
2026-11-16

## 작업 요약
`backend/src/api/tasks.py`에 `PATCH /tasks/{task_id}`를 구현했습니다. 요청 바디는 `UpdateTaskRequest{title?: str, description?: str}`이며, `TaskService.update(user_id, task_id, title, description)`을 호출합니다. **활성(active)+소유** Task만 수정 가능(트래시/존재하지 않음/타인 소유는 모두 404로 동일 취급)하고, 제공된 필드만 갈아끼우며 `None`은 "변경하지 않음"을 의미합니다(Project의 PATCH와 동일한 시맨틱). title/description 길이 위반은 400.

## 변경 파일
- `backend/src/api/tasks.py` (`update_task` 핸들러, `UpdateTaskRequest`)
- `backend/tests/integration/test_tasks_api.py`의 `TestUpdateTaskEndpoint` 클래스(테스트 4개: 정상 수정, title 5자 미만 400, 트래시된 Task 404, 타인 Task 404)

## TDD 결과
- RED → GREEN: 4개 테스트 모두 라우터 구현 후 1차 통과.
- `ruff check` 통과.
- 전체 회귀(`pytest -q`, 284 tests) 통과.
- Git 저장소 미초기화로 커밋 해시 없음.

## 기술 결정
- **"활성 Task만 수정 가능"을 `_get_active_owned`로 단일화**: `TaskService.update`와 `soft_delete`가 동일한 내부 헬퍼(`_get_active_owned`)를 공유해, "트래시된 Task는 수정도 삭제도 불가"라는 규칙을 한 곳에서만 구현합니다. `ProjectService._get_active`와 동일한 구조입니다.

## 비고
- 없음.
