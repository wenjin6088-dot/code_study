# TASK-074. DELETE /tasks/{task_id} (소프트 삭제) 엔드포인트 구현

## 상태
완료

## 날짜
2026-11-16

## 작업 요약
`backend/src/api/tasks.py`에 `DELETE /tasks/{task_id}`를 구현했습니다. `TaskService.soft_delete(user_id, task_id)`를 호출해 **활성+소유** Task만 대상으로 `deletion_status='trashed'`, `trashed_at=now`, `scheduled_deletion_at=trashed_at+30일`을 설정합니다(`ProjectService.soft_delete`와 동일 패턴, row는 절대 물리 삭제하지 않음). 이미 트래시되었거나 존재하지 않거나 타인 소유면 404. 성공 시 200 + 트래시된 상태의 `TaskResponse`를 반환합니다.

tasks.md에 이미 명시된 대로, Trash 페이지/`trash_service.py` 연동(T176/T177/T179)은 이번 범위에 포함하지 않고 엔드포인트 자체만 구현했습니다.

## 변경 파일
- `backend/src/api/tasks.py` (`delete_task` 핸들러)
- `backend/tests/integration/test_tasks_api.py`의 `TestDeleteTaskEndpoint` 클래스(테스트 3개: 정상 소프트 삭제 후 DB 상태 확인, 이미 트래시된 Task 404, 타인 Task 404)

## TDD 결과
- RED → GREEN: 3개 테스트 모두 라우터 구현 후 1차 통과.
- `ruff check` 통과.
- 전체 회귀(`pytest -q`, 284 tests) 통과.
- Git 저장소 미초기화로 커밋 해시 없음.

## 기술 결정
- **30일 보존 기간을 `TaskService.TRASH_RETENTION = timedelta(days=30)` 상수로**: `ProjectService.TRASH_RETENTION`과 동일한 값/이름 규칙을 그대로 따라, 두 서비스의 트래시 정책이 한눈에 대응되도록 했습니다.

## 비고
- 삭제된 Task에 연결된 `UploadedCode`/`CodeFile`/디스크 파일은 이번 Task에서 함께 정리(cascade 삭제나 보존 만료 시 파일 정리)하지 않습니다. tasks.md가 이 연동을 T176/T177/T179로 명시적으로 미뤄두었기 때문입니다.
