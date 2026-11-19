# TASK-044. ProjectService 구현 및 소유권 검증 (T044, T045)

## 상태
완료

## 날짜
2026-11-09

## 작업 요약
프로젝트 생성/조회/목록/수정/소프트 삭제를 담당하는 `ProjectService`를 `backend/src/services/project_service.py`에 구현했습니다. 같은 파일에 커스텀 예외 `ProjectNotFoundError`, `InvalidProjectTitleError`(공통 베이스 `ProjectError`)도 함께 정의했습니다. 테스트 파일이 이 두 예외를 `src.services.project_service`에서 직접 import하고 있어서, 기존 `src/services/auth/exceptions.py`처럼 별도 exceptions 모듈을 만들지 않고 서비스와 같은 파일에 두었습니다(테스트가 요구하는 import 경로를 그대로 맞춤).

메서드별 동작:
- `create(user_id, title, description=None)`: 제목이 비었거나 공백뿐이면 `InvalidProjectTitleError`. 통과하면 `Project` 생성 후 커밋.
- `get(user_id, project_id)`: 소유자만 조회 가능하며, 활성/트래시 상태 모두 반환(상세 조회/내부용). id가 없거나 다른 사용자 소유면 **동일하게** `ProjectNotFoundError` — 403으로 존재 여부를 흘리지 않도록 함.
- `list_active(user_id)`: 호출자 소유의 `deletion_status == 'active'` 프로젝트만 반환.
- `update(user_id, project_id, title=None, description=None)`: 활성 상태의 소유 프로젝트만 수정 가능(트래시 상태면 `ProjectNotFoundError`). `title`/`description`이 `None`이면 "값 변경 안 함"으로 처리(설명을 빈 값으로 지울 수는 없음). 빈/공백 제목은 `InvalidProjectTitleError`.
- `soft_delete(user_id, project_id)`: 활성 상태의 소유 프로젝트만 삭제 가능. `deletion_status='trashed'`, `trashed_at=now`, `scheduled_deletion_at=trashed_at+30일`로 갱신하고 행은 DB에서 제거하지 않음. 이미 트래시된 프로젝트를 다시 지우려 하면 `ProjectNotFoundError`.

소유권 검증은 모든 조회/수정 쿼리에 `WHERE user_id = :user_id` 조건을 넣어서 처리했고, "존재하지 않음"과 "남의 것"을 구분하지 않고 둘 다 `ProjectNotFoundError`로 통일했습니다.

## 변경 파일
- `backend/src/services/project_service.py` (신규)

## TDD 결과
- Git 저장소가 아직 초기화되지 않아 커밋은 생략했습니다.
- 테스트 대상: `test_projects_api.py`의 `TestProjectServiceCreate`, `TestProjectServiceGet`, `TestProjectServiceList`, `TestProjectServiceUpdate`, `TestProjectServiceSoftDelete` (총 19개 테스트)
- 전부 통과 (19/19 PASSED)
- `ruff check src/`도 통과(경고 1건 `datetime.UTC` alias 권장을 반영해 수정 완료)

## 기술 결정 (해당 시)
- 소유권 체크를 서비스 쿼리 조건(`user_id` 필터)에 바로 넣는 방식을 택해, "조회 후 소유자 비교" 2단계 로직 대신 단일 쿼리로 처리했습니다. 덕분에 다른 사용자의 프로젝트는 쿼리 결과 자체가 없어 `ProjectNotFoundError`로 자연스럽게 귀결되고, 403으로 존재를 흘릴 가능성이 구조적으로 차단됩니다.
- `update`/`soft_delete`는 내부적으로 `_get_active` 헬퍼(활성 상태만 조회)를 공유해서 "활성 소유 프로젝트만 대상"이라는 규칙을 한 곳에서만 구현했습니다.

## 비고
- 없음
