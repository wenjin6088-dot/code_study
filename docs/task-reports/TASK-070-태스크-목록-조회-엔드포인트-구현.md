# TASK-070. GET /projects/{project_id}/tasks 엔드포인트 구현

## 상태
완료

## 날짜
2026-11-16

## 작업 요약
`backend/src/api/tasks.py`에 `router = APIRouter(tags=["tasks"])`(prefix 없음)를 신설하고 `GET /projects/{project_id}/tasks`를 구현했습니다. `backend/src/api/router.py`에 `tasks_router`를 등록해 `/api/v1/projects/{project_id}/tasks`로 노출됩니다.

- `TaskService(session).list_active(user_id, project_id)`를 호출해 호출자 소유의 **활성** 프로젝트에 속한 **활성** Task를 `task_number` 오름차순으로 가져옵니다. 프로젝트가 없거나 소유자가 아니거나 트래시 상태면 `ProjectNotFoundError` → `NotFoundError`(404)로 변환합니다.
- 각 Task에 대해 `CodeUploadService(session).get_for_task(task.id)`로 업로드 정보를 조회해 `TaskResponse.uploaded_code`에 중첩시킵니다(업로드 전 Task는 `null`).
- 미인증 요청은 기존 `get_current_user` 의존성이 `UnauthorizedError`(401)를 던지므로 추가 처리가 필요 없었습니다(projects.py와 동일 패턴).

## 변경 파일
- `backend/src/api/tasks.py` (신규 생성 — 본 Task 외 T071~T075도 같은 파일에 구현되어 있어 보고서들이 파일을 공유합니다)
- `backend/src/api/router.py` (`tasks_router` import 및 `include_router` 추가)
- `backend/tests/integration/test_tasks_api.py`의 `TestListTasksEndpoint` 클래스(테스트 4개)

## TDD 결과
- RED: `TestListTasksEndpoint`를 먼저 작성 → 라우터가 등록되지 않아 모든 요청이 404(미등록 경로)로 응답해 테스트 실패 확인.
- GREEN: 엔드포인트 구현 및 라우터 등록 후 4개 테스트 통과(인증 필요, 활성만 반환+트래시 제외, 타인 프로젝트 404, 트래시 프로젝트 404).
- `ruff check` 통과.
- 전체 회귀(`pytest -q`, 284 tests) 통과.
- Git 저장소 미초기화로 커밋 해시 없음.

## 기술 결정
- **N+1 쿼리 허용**: Task 목록을 가져온 뒤 각 Task마다 `get_for_task`를 개별 호출합니다(업로드 정보가 없는 Task가 대부분일 초기 사용 패턴, Task 수가 많지 않은 교육용 플랫폼 규모를 감안해 JOIN 최적화 대신 명확성을 선택). 추후 목록 화면의 체감 성능 이슈가 확인되면 배치 조회로 리팩터링할 수 있는 지점으로 남겨둡니다.
- **ProjectNotFoundError를 그대로 재사용**: `TaskService.list_active`가 프로젝트 소유/활성 검증 실패 시 `ProjectService`의 `ProjectNotFoundError`를 그대로 전파하도록 했고, 라우터는 이를 `NotFoundError`로 변환합니다 — Task 전용 예외를 새로 만들지 않고 projects.py와 동일한 변환 패턴을 재사용했습니다.

## 비고
- 응답 모델(`TaskResponse`, `UploadedCodeResponse`, `CodeFileResponse`)과 변환 헬퍼(`_task_response` 등)는 T071~T075와 공유되므로 이 보고서에서 한 번만 설명하고 이후 보고서에서는 중복 서술을 생략합니다.
