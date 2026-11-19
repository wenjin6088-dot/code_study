# TASK-071. POST /projects/{project_id}/tasks (multipart 업로드) 엔드포인트 구현

## 상태
완료

## 날짜
2026-11-16

## 작업 요약
`backend/src/api/tasks.py`에 `POST /projects/{project_id}/tasks`를 FastAPI `Form`/`File` 파라미터로 구현했습니다. 프런트엔드(T076~T083, 병렬 진행)가 보내는 FormData 필드명(`title`, `description`, `upload_method`, `files`, `paste_content`, `paste_filename`)과 한 글자도 다르지 않게 맞췄고, 완료 후 `frontend/src/services/task-service.ts`의 실제 구현을 직접 읽어 필드명이 정확히 일치함을 확인했습니다.

검증·생성 순서(오케스트레이션, 비즈니스 로직은 서비스에 위임):
1. `TaskService.ensure_project_access` — 프로젝트 소유/활성 확인(아니면 404).
2. `TaskService.validate_title` / `validate_description` — 5자 이상 / 500자 이하(아니면 400).
3. `upload_method`가 `file`/`folder`/`paste` 중 하나인지 확인(아니면 400).
4. paste면 `paste_content`+`paste_filename`을 **파일 하나**(`UploadedFileInput`)로 변환, file/folder면 업로드된 `UploadFile`들을 읽어 동일한 타입으로 변환(둘 다 필수 필드 누락 시 400).
5. `CodeUploadService.validate_files` — 제외 경로 필터링 → 경로 트래버설 차단 → 개수(1~20) → 확장자/총용량/바이너리 검증(전부 400).
6. **위 5단계를 모두 통과한 뒤에만** `TaskService.create`로 Task를 커밋하고, 이어서 `CodeUploadService.create_upload`로 파일을 저장소에 쓰고 `UploadedCode`/`CodeFile`을 커밋합니다.

성공 시 201 + `TaskResponse`(중첩 `uploaded_code` 포함)를 반환합니다.

## 변경 파일
- `backend/src/api/tasks.py` (`create_task` 핸들러, `TaskResponse`/`UploadedCodeResponse`/`CodeFileResponse`/`UpdateTaskRequest` Pydantic 모델)
- `backend/src/api/router.py`
- `backend/tests/integration/test_tasks_api.py`의 `TestCreateTaskEndpoint` 클래스(테스트 15개: paste/file/folder 성공 케이스, 제외 경로 보존 확인, title/description/upload_method/paste 필드/files 필드/경로 트래버설/개수 초과/확장자/바이너리 검증 각각의 400, 고아 Task 미생성 확인, 타인 프로젝트 404, 미인증 401)

## TDD 결과
- RED: `TestCreateTaskEndpoint` 작성 → 라우터 미등록으로 전부 실패 확인.
- GREEN: 구현 후 15개 테스트 전부 1차 통과.
- `test_does_not_persist_orphan_task_when_validation_fails`로 "검증 실패 시 고아 Task가 DB에 남지 않는다"를 직접 검증 — 파일 검증(step 5)이 Task 생성(step 6)보다 먼저 실행되도록 라우터 순서를 구성했기 때문에 별도 트랜잭션 보상 로직 없이도 통과합니다.
- `ruff check` 통과.
- 전체 회귀(`pytest -q`, 284 tests) 통과.
- Git 저장소 미초기화로 커밋 해시 없음.

## 기술 결정
- **라우터는 오케스트레이션만, 비즈니스 로직은 0줄**: 핸들러는 `TaskService`/`CodeUploadService`의 메서드를 순서대로 호출하고 예외를 HTTP 응답으로 변환하는 역할만 합니다. 실제 검증 규칙(길이, 확장자, 개수, 경로 등)은 모두 서비스 레이어에 있어, 이 핸들러만 보면 "검증 → 생성" 두 단계라는 흐름이 그대로 드러납니다.
- **project 접근 검증을 라우터와 `TaskService.create` 양쪽에서 호출(중복 허용)**: `ensure_project_access`가 쓰기 없는 단순 SELECT이므로, 라우터에서 먼저 호출해 파일 검증 전에 프로젝트 존재를 확인하고, `TaskService.create` 내부에서도 다시 검증합니다. 코드 중복보다 "Task 서비스 메서드 하나만 호출해도 항상 안전하다"는 불변식을 유지하는 쪽을 선택했습니다.
- **`files: list[UploadFile] = File(default=[])`**: paste 방식일 때 클라이언트가 `files` 필드를 전혀 보내지 않으므로 기본값을 빈 리스트로 두었습니다. FastAPI의 가변 기본값 경고(B008)는 프로젝트의 `ruff` 설정에서 이미 `Depends()` 패턴을 위해 ignore 처리되어 있어 동일하게 적용됩니다.
- **folder 업로드의 상대경로는 프런트가 보내는 그대로 신뢰**: `UploadFile.filename`에 `"src/app.py"`처럼 슬래시가 포함된 경로가 그대로 들어온다는 계약을 그대로 수용하고, 안전성은 `CodeUploadService`의 제외 필터링 + 트래버설 차단으로 확보했습니다(라우터 자체는 경로 문자열을 가공하지 않음).

## 비고
- `files.webkitRelativePath`로 전달되는 폴더 업로드의 최상위 폴더명이 상대경로에 포함될 수 있는데(`"myproject/src/app.py"`), 이 경우도 `.git`/`node_modules` 등 제외 대상 세그먼트 검사와 트래버설 검사가 세그먼트 단위로 동작하므로 올바르게 처리됩니다. `CodeFile.file_path`에는 받은 그대로의 상대경로가 저장되고, 화면 표시용 가공(최상위 폴더명 제거 등)은 프런트엔드 책임으로 남겨두었습니다.
