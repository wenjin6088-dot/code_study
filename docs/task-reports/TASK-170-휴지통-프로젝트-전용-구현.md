# TASK-170. 휴지통(Trash) 관리 — 프로젝트 전용 구현 (T170, T171, T173-T175, T178, T180-T182, T184)

## 상태
완료 (범위 축소, 비고 참고)

## 날짜
2026-11-10

## 작업 요약
Phase 10(휴지통 & 소프트 삭제 슬라이스) 전체 중, **프로젝트 복원/영구삭제**에 해당하는 부분만 구현했습니다. 원래 tasks.md의 Phase 10은 프로젝트와 Task(작업) 양쪽을 다 다루도록 설계되어 있었지만(TrashedTaskCard, task restore/permanent-delete 등), 이 작업을 시작한 시점에 Task 엔티티 자체가 아직 존재하지 않았습니다(Phase 5 "Tasks & Code Upload Slice"가 전부 `[ ]` 미착수 상태). 복원/삭제할 대상이 없는 상태에서 Task 쪽 UI·API를 만드는 건 테스트도 불가능하고 YAGNI에 어긋난다고 판단해, 프로젝트 전용으로 범위를 좁혀 구현하고 Task 관련 부분(T172, T176, T177, T179, T183 일부, T185, T186)은 명시적으로 미룬 채 tasks.md에 사유를 남겼습니다.

### 백엔드 (TDD)
- `backend/src/services/trash_service.py` 신규: `TrashService(session)`
  - `list_trashed_projects(user_id)`: 호출자 소유의 `deletion_status == 'trashed'` 프로젝트 목록
  - `restore_project(user_id, project_id)`: trashed 상태인 소유 프로젝트만 복원 가능(active/타인 소유/존재하지 않음은 모두 `ProjectNotFoundError`로 동일하게 처리 — ProjectService의 "존재 여부를 흘리지 않는다" 원칙을 그대로 재사용). `deletion_status='active'`, `trashed_at=None`, `scheduled_deletion_at=None`.
  - `permanent_delete_project(user_id, project_id)`: trashed 상태인 소유 프로젝트만 대상으로 DB에서 행을 실제로 삭제(hard delete, 되돌릴 수 없음).
- `backend/src/api/trash.py` 신규: `GET /trash`, `POST /trash/projects/{id}/restore`, `DELETE /trash/projects/{id}/permanent-delete` (204). `backend/src/api/router.py`에 등록.
- `backend/tests/integration/test_trash_api.py` 신규: 서비스 레벨 9개 + API 레벨 10개, 총 19개 테스트.

### 프론트엔드 (TDD)
- `frontend/src/services/trash-service.ts` 신규: `listTrash()`, `restoreProject(id)`, `permanentDeleteProject(id)`.
- `frontend/src/components/trash/TrashedProjectCard.tsx` 신규: 제목/설명 표시 + "복원"/"영구 삭제" 버튼. "영구 삭제"는 되돌릴 수 없으므로 네이티브 `window.confirm()` 대신 인라인 확인 단계("정말 영구적으로 삭제하시겠습니까?" + "확인"/"취소")를 거침.
- `frontend/src/pages/Trash.tsx` 신규: `App.tsx`의 `function Trash() { return <div>Trash (placeholder)</div> }` 플레이스홀더를 대체. 목록 조회 + 복원/영구삭제 후 `['trash']`·`['projects']` 쿼리 무효화.
- `frontend/src/pages/Dashboard.tsx`: "휴지통 보기" 네비게이션 링크 추가 (T182).
- `frontend/tests/unit/services/trash-service.test.ts`, `tests/unit/components/trash/TrashedProjectCard.test.tsx`, `tests/integration/pages/Trash.test.tsx` 신규.

## 변경 파일
- `backend/src/services/trash_service.py` (신규)
- `backend/src/api/trash.py` (신규)
- `backend/src/api/router.py` (수정 — trash_router 등록)
- `backend/tests/integration/test_trash_api.py` (신규)
- `frontend/src/services/trash-service.ts` (신규)
- `frontend/src/components/trash/TrashedProjectCard.tsx` (신규)
- `frontend/src/pages/Trash.tsx` (신규)
- `frontend/src/pages/Dashboard.tsx` (수정 — 휴지통 링크)
- `frontend/src/App.tsx` (수정 — Trash 플레이스홀더를 실제 페이지로 교체)
- `frontend/tests/unit/services/trash-service.test.ts` (신규)
- `frontend/tests/unit/components/trash/TrashedProjectCard.test.tsx` (신규)
- `frontend/tests/integration/pages/Trash.test.tsx` (신규)

## TDD 결과
- 백엔드: RED(19개 중 15개가 "모듈 없음/라우트 없음"으로 실패, 4개는 "라우트 없어서 우연히 404"로 통과하는 올바른 RED) → GREEN 19/19 통과 → 전체 스위트 128/128 통과(회귀 없음) → `ruff check` 클린
- 프론트엔드: RED(신규 파일 3개 전부 import 실패 + 기존 테스트 통과 유지) → GREEN → 전체 스위트 15개 파일 112/112 통과(회귀 없음) → `eslint`, `tsc --noEmit` 클린
- 실브라우저(Playwright MCP) 전체 플로우 재검증:
  1. ProjectDetail "Delete" → 확인 → 소프트 삭제 → 대시보드로 자동 이동, 목록에서 제외
  2. "휴지통 보기" 링크로 Trash 페이지 진입
  3. "복원" 클릭 → 목록에서 제외됨 → 대시보드에 다시 활성 상태로 표시
  4. 다른 프로젝트를 소프트 삭제 후 Trash에서 "영구 삭제" → 확인 단계 노출 → "확인" → 목록에서 제외 → `GET /api/v1/projects/{id}`가 404로 DB에서 완전히 삭제됨을 확인
- 검증 중 `uvicorn --reload`가 새로 생성한 `trash_service.py`/`trash.py` 파일 변경을 감지하지 못해 일시적으로 404가 발생했는데(코드 버그 아님, 기존 WatchFiles 재시작 이슈), 백엔드를 수동 재시작해서 해결했습니다.
- Git 저장소가 아직 초기화되지 않아 커밋은 생략했습니다.

## 기술 결정
- **범위를 프로젝트 전용으로 축소**: Task 엔티티가 없는 상태에서 TrashedTaskCard/task restore·permanent-delete를 만들면 테스트 불가능한 코드가 생기므로, YAGNI 원칙에 따라 명시적으로 미뤘습니다. tasks.md에 각 미룬 태스크(T172, T176, T177, T179, T186)와 부분 검증된 태스크(T183, T185)에 사유를 남겨 Phase 5 완료 후 이어서 작업할 수 있게 했습니다.
- **영구 삭제 확인에 `window.confirm()` 대신 인라인 확인 UI 사용**: 네이티브 confirm 다이얼로그는 Playwright 등 브라우저 자동화 도구의 이벤트 루프를 블로킹해서 이후 명령을 받지 못하게 만들 수 있고, 테스트(vitest + Testing Library)로도 다루기 번거롭습니다. 2단계 클릭(버튼→확인/취소 노출)으로 같은 "실수 방지" 목적을 달성하면서 완전히 인앱 상태로 테스트 가능하게 했습니다. (ProjectDetail의 소프트 삭제 확인(T056b)에도 동일한 패턴을 썼습니다.)
- **`permanent_delete_project`는 `ProjectNotFoundError`를 재사용**: `ProjectService`가 이미 "존재하지 않음"과 "남의 것"을 구분하지 않는 설계(T045)를 쓰고 있어서, `TrashService`도 같은 에러 타입·같은 원칙(trashed 상태가 아닌 프로젝트에 접근해도 404로 통일, 상태 유출 방지)을 그대로 재사용했습니다.
- **`setQueryData` 대신 `invalidateQueries` 사용 (Trash 페이지)**: Dashboard의 생성 플로우(T056)와 동일한 패턴. 복원/영구삭제는 두 개의 서로 다른 목록(`['trash']`, `['projects']`)에 동시에 영향을 주므로, 응답 하나로 캐시를 직접 채우기보다 두 쿼리를 모두 무효화해 재조회하는 편이 더 단순하고 일관적입니다.

## 비고
- **T183 (30일 카운트다운)**: "삭제 후 휴지통에 나타남"은 검증했지만, `scheduled_deletion_at`을 화면에 "30일 카운트다운"으로 보여주는 UI는 만들지 않았습니다(`TrashedProjectCard`가 해당 필드를 아예 받지 않음 — API 응답 모델에 `scheduled_deletion_at`이 없습니다). tasks.md에 미완료로 남겨뒀습니다.
- **T185 (Task 영구삭제 확인 다이얼로그)**: Task 대상 부분은 미룼지만, 동일한 "확인 다이얼로그 → 완전 삭제" 플로우는 프로젝트 기준으로 이미 Playwright로 검증했습니다.
- Task 엔티티가 생기면(Phase 5) T176/T177(백엔드), T179(TrashedTaskCard), T181의 "tasks 섹션", T183의 카운트다운 UI, T185의 task 삭제 확인을 이어서 구현하는 것을 제안합니다.
