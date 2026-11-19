# TASK-068. TaskService 구현

## 상태
완료

## 날짜
2026-11-16

## 작업 요약
`backend/src/services/task_service.py`에 `ProjectService`와 동일한 설계 철학을 따르는 `TaskService`를 TDD로 구현했습니다. Task의 생성/조회/목록/수정/소프트 삭제를 담당하며, 프로젝트 소유권 확인은 `ProjectService`를 생성자로 주입받아 재사용합니다(헌장 III, 서비스 간 직접 DB 우회 금지).

- `create(user_id, project_id, title, description=None, upload_method=None) -> Task`: 프로젝트가 호출자 소유의 **활성** 프로젝트인지 확인 → title(5자 이상, FR-008)/description(500자 이하, FR-009) 검증 → 해당 project의 기존 최대 `task_number`+1(없으면 1)로 Task 생성.
- `get(user_id, task_id) -> Task`: Task의 `deletion_status`와 무관하게(active/trashed 둘 다) 반환하되, 프로젝트 소유자가 아니면 `TaskNotFoundError`(`ProjectService.get`과 동일한 "존재 여부 노출 금지" 정책).
- `list_active(user_id, project_id) -> list[Task]`: 활성 프로젝트 확인 후 해당 프로젝트의 `deletion_status == 'active'`인 Task만 `task_number` 오름차순으로 반환.
- `update(...)` / `soft_delete(...)`: **활성+소유** Task만 대상(트래시된 Task는 404 동일 취급), `scheduled_deletion_at = trashed_at + 30일`.
- `ensure_project_access(user_id, project_id)`: 프로젝트 활성+소유 여부만 확인하는 읽기 전용 메서드로 분리해, API 레이어가 (Task 레코드를 커밋하기 전에) 먼저 검증만 수행할 수 있게 노출했습니다(T071의 "검증 전부 통과 전 Task 미생성" 요구사항 지원).

## 변경 파일
- `backend/src/services/task_service.py` (신규 생성)
- `backend/tests/unit/test_task_service_validation.py` (신규 생성, 순수 검증 로직 단위 테스트 7개)
- `backend/tests/integration/test_tasks_api.py`의 `TestTaskServiceCreate`/`Get`/`List`/`Update`/`SoftDelete` 클래스(DB 통합 테스트 17개)

## TDD 결과
- RED: 먼저 `tests/unit/test_task_service_validation.py`와 `tests/integration/test_tasks_api.py`의 서비스 테스트 클래스들을 작성 → `ModuleNotFoundError: No module named 'src.services.task_service'`로 실패 확인.
- GREEN: `task_service.py` 구현 후 단위 7개 + 통합 17개(수정 1건, 아래 참고) 전부 통과.
- 1차 GREEN 시도에서 `test_get_returns_own_active_task`가 `InvalidTaskTitleError`로 실패 — 테스트 자체가 title `"Mine"`(4자)을 사용해 FR-008(5자 이상) 규칙을 위반한 테스트 버그였음을 확인하고 `"Mine indeed"`로 수정 → 통과.
- 테스트 커버리지: **100%** (`src/services/task_service.py`, 87 statements / 0 missing).
- `ruff check` 통과(최초 생성자 시그니처 줄 길이 초과(E501) 1건 → 멀티라인으로 분리해 수정).
- 전체 회귀(`pytest -q`, 284 tests) 통과.
- Git 저장소 미초기화로 커밋 해시 없음.

## 기술 결정
- **project 소유권 확인을 ProjectService 위임**: `TaskService`가 `projects` 테이블을 직접 쿼리하지 않고 생성자로 주입받은 `ProjectService.get()`을 호출합니다. `ProjectService.get()`은 trashed 프로젝트도 소유자에게는 반환하므로, "활성" 조건은 `TaskService.ensure_project_access()`에서 `project.deletion_status != "active"`를 추가로 검사해 별도로 강제합니다 — 활성 여부 판단 책임을 Task 레이어에 남겨 Project 레이어의 기존 계약(get은 trashed도 반환)을 깨지 않았습니다.
- **Task 소유권 확인은 project_id를 경유**: `Task` 모델에는 `user_id` 컬럼이 없으므로(소유권은 `project.user_id`를 통해서만 결정), `TaskService.get/_get_active_owned`는 먼저 `session.get(Task, task_id)`로 Task를 직접 조회(Task는 자기 테이블이므로 직접 쿼리 허용)한 뒤, `project_service.get(user_id, task.project_id)`로 소유권만 재확인합니다. `ProjectNotFoundError`를 잡아 `TaskNotFoundError`로 변환해, Task 조회 실패와 프로젝트 소유권 실패가 호출자에게 동일한 예외 타입으로 보이도록 통일했습니다.
- **task_number는 프로젝트별 독립적 최댓값+1**: `select(func.max(Task.task_number)).where(Task.project_id == project_id)`로 (active/trashed 무관) 전체 Task 중 최댓값을 구해 다음 번호를 매깁니다. 트래시된 Task의 번호를 재사용하지 않도록 `deletion_status` 필터를 걸지 않았습니다 — 번호가 "몇 번째로 만들어졌는가"를 나타내는 영속적 식별자라는 판단입니다.
- **검증 메서드를 `@staticmethod`로 공개**: `validate_title`/`validate_description`을 정적 메서드로 두어, API 레이어(T071)가 Task 레코드 커밋 전에 동일한 검증 로직을 재사용할 수 있게 했습니다(로직 중복 없이 "검증 → 생성" 두 단계로 분리).

## 비고
- `ensure_project_access`는 읽기 전용(쓰기 없음)이라 `create()` 내부에서도 다시 호출됩니다. 동일 SELECT가 API 핸들러와 `create()` 양쪽에서 한 번씩 더 실행될 수 있지만(T071 참고), 추가 비용은 단순 조회 1회이며 "검증 통과 전 Task 미생성" 요구사항을 지키는 더 간단한 방법이라고 판단했습니다.
