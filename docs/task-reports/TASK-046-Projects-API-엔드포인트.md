# TASK-046. Projects API 엔드포인트 (T046-T050)

## 상태
완료

## 날짜
2026-11-09

## 작업 요약
`/api/v1/projects` 하위 5개 엔드포인트(GET 목록, POST 생성, GET 단건, PATCH 수정, DELETE 소프트삭제)를 `backend/src/api/projects.py`에 구현하고, `backend/src/api/router.py`의 `api_router`에 등록했습니다. 인증은 기존 `get_current_user`(쿠키 기반 access_token) 의존성을 그대로 재사용했고, 예외 매핑은 `backend/src/api/auth.py`의 try/except 패턴을 그대로 따랐습니다: `ProjectNotFoundError` → `NotFoundError`(404), `InvalidProjectTitleError` → `AppException`(400).

- `GET /api/v1/projects`: 호출자 소유의 활성 프로젝트만 배열로 반환(200).
- `POST /api/v1/projects`: `{"title": str, "description"?: str}` 바디로 생성(201). `title` 필드 자체가 없으면 Pydantic이 422를 자동 처리하고, 빈 문자열/공백 문자열이면 서비스 예외를 통해 400으로 응답.
- `GET /api/v1/projects/{id}`: 단건 조회(200/404). 경로 파라미터를 `uuid.UUID`로 타입 지정해서 UUID가 아닌 값이 오면 FastAPI가 자동으로 422 처리.
- `PATCH /api/v1/projects/{id}`: 제목/설명 부분 수정(200/404/400).
- `DELETE /api/v1/projects/{id}`: 소프트 삭제 후 트래시 상태가 된 프로젝트 바디를 반환(200/404).

응답 바디는 모두 `{"id", "title", "description", "deletion_status"}`를 포함하는 `ProjectResponse` 모델로 통일했습니다.

## 변경 파일
- `backend/src/api/projects.py` (신규)
- `backend/src/api/router.py` (수정 — `projects_router`를 `api_router`에 등록)

## TDD 결과
- Git 저장소가 아직 초기화되지 않아 커밋은 생략했습니다.
- 테스트 대상: `test_projects_api.py`의 `TestListProjectsEndpoint`, `TestCreateProjectEndpoint`, `TestGetProjectEndpoint`, `TestUpdateProjectEndpoint`, `TestDeleteProjectEndpoint` (총 29개 테스트)
- 전체 결과: `backend/tests/integration/test_projects_api.py` 51개 전부 통과, 기존 58개(인증 등) 포함 전체 스위트 `backend/tests/` 109개 전부 통과, 회귀 없음.
- `ruff check src/` 통과(수정 후 오류 0건).

## 기술 결정 (해당 시)
- 인증 실패(401)는 라우트 핸들러가 아니라 `get_current_user` 의존성 체인(`get_current_user_id` → `UnauthorizedError`)에서 이미 처리되므로, projects 라우터에는 별도 코드 없이 `Depends(get_current_user)`만 선언했습니다.
- "없음"과 "남의 것"을 구분하지 않는 보안 요구사항은 서비스 레이어(`ProjectNotFoundError`)에서 이미 통일되어 있어서, API 레이어는 그 예외를 그대로 404로 매핑만 하면 되었습니다(존재 여부를 흘리는 403 분기를 만들지 않음).

## 비고
- 없음
