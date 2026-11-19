# TASK-053. project-service 구현

## 상태
완료

## 날짜
2026-11-09

## 작업 요약
프로젝트 관련 CRUD(생성/조회/수정/삭제) API를 호출하는 `project-service.ts`를 만들었습니다. 이미 있던 `auth-service.ts`와 똑같은 스타일로, 공유 axios 인스턴스인 `apiClient`를 감싸는 얇은(thin) 함수들로 구성했습니다. 즉, 이 파일 자체는 비즈니스 로직 없이 "어떤 URL로 어떤 메서드를 호출하는지"만 책임지고, 실제 데이터 가공이나 에러 메시지 변환은 `api-client.ts`의 공통 인터셉터가 처리합니다.

제공하는 함수는 5개입니다. `listProjects()`는 내 프로젝트 목록을 가져오고(GET /projects), `getProject(id)`는 특정 프로젝트 하나를 가져옵니다(GET /projects/{id}). `createProject({title, description?})`는 새 프로젝트를 만들고(POST /projects), `updateProject(id, {title?, description?})`는 기존 프로젝트를 수정하며(PATCH /projects/{id}), `removeProject(id)`는 프로젝트를 삭제(실제로는 백엔드에서 휴지통으로 이동하는 소프트 삭제)합니다(DELETE /projects/{id}).

## 변경 파일
- `frontend/src/services/project-service.ts` (신규)

## TDD 결과
- 테스트 파일: `frontend/tests/unit/services/project-service.test.ts` (11개 테스트, 기존에 이미 작성되어 있던 실패 테스트)
- GREEN 확인: `npx vitest run` 실행 결과 11개 테스트 전부 통과
- Git 저장소가 아직 초기화되지 않아 커밋은 생략했습니다.

## 기술 결정 (해당 시)
- 삭제 함수의 이름을 `deleteProject`가 아니라 `removeProject`로 지었습니다. 테스트 파일 자체의 주석에 이 이름을 쓰도록 명시되어 있었고, JavaScript의 예약어인 `delete`와 겹치는 것을 피하는 목적도 있습니다.
- `Project` 인터페이스는 백엔드가 그대로 내려주는 snake_case 필드명(`created_at`, `updated_at`, `last_activity_at`)을 그대로 사용했습니다. camelCase로 변환하는 매핑 레이어는 테스트에서 요구하지 않았고, `auth-service.ts`의 `AuthUser`가 camelCase를 쓰는 것과는 다르지만, 이는 백엔드 프로젝트 API(T043-T050)의 응답 스키마를 그대로 따른 것입니다.
- 에러 처리를 별도로 하지 않고 그대로 다시 던지는(rethrow) 방식을 택했습니다. `apiClient`의 응답 인터셉터가 이미 모든 axios 에러를 사람이 읽을 수 있는 메시지를 가진 `Error` 객체로 바꿔주기 때문에, 서비스 함수에서 추가로 할 일이 없습니다.

## 비고
- 없음.
