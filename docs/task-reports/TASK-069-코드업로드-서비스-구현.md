# TASK-069. CodeUploadService 구현

## 상태
완료

## 날짜
2026-11-16

## 작업 요약
`backend/src/services/code_analysis/code_upload_service.py`에 file/folder/paste 3가지 업로드 방식을 **동일한 파이프라인**으로 검증하고, 검증을 통과한 파일들을 저장소(T067)에 쓰고 `UploadedCode`/`CodeFile` row를 생성하는 `CodeUploadService`를 TDD로 구현했습니다.

- `UploadedFileInput(filename: str, content: bytes)`: file/folder/paste 입력을 하나의 형태로 통일하는 작은 데이터클래스. paste는 `filename=paste_filename, content=paste_content.encode("utf-8")`로 변환해 이 타입에 담으면 이후 로직은 업로드 방식을 더 이상 구분하지 않습니다.
- `validate_files(files) -> list[UploadedFileInput]` (DB/디스크 I/O 없는 순수 함수): 계약이 요구한 순서대로 ① `.git`/`node_modules`/`.DS_Store`/`__pycache__` 경로 세그먼트를 가진 파일을 조용히 제외(FR-017) → ② 남은 파일에 `..` 세그먼트나 `/` 시작 절대경로가 있으면 `CodeUploadError` → ③ 제외 후 개수가 1~20개(FR-018)가 아니면 `CodeUploadError` → ④ `file_validator`의 `validate_extension`/`validate_total_size`/`validate_not_binary`를 호출하고 그 `FileValidationError`를 `CodeUploadError`로 감싸 단일 예외 타입으로 라우터에 전달.
- `create_upload(user_id, task_id, files) -> UploadResult`: (이미 검증된 파일 목록을 받아) 언어/복잡도 분석 → `UploadedCode` row 생성(flush로 id 확보) → 각 파일을 `file_storage.save_file`로 저장 후 `CodeFile` row 생성 → 커밋. `detect_dominant_language`가 `LanguageDetectionError`를 던지면(.txt/.md만 업로드된 경우) `detected_language=None`으로 흡수하고 업로드 자체는 성공시킵니다(계약 명시 사항).
- `get_for_task(task_id) -> UploadResult | None`: 특정 Task의 `UploadedCode`+`CodeFile` 목록을 조회(응답 조립/코드 조회용, T070~T075에서 공용으로 사용).
- `UploadResult(uploaded_code, files)`: `UploadedCode`와 `CodeFile` 사이에 ORM 관계(relationship)를 선언하지 않았으므로(모델이 이미 FK만 가진 상태로 고정, T062/T063 변경 금지), 둘을 함께 들고 다니는 가벼운 데이터클래스로 응답 조립을 단순화했습니다.

## 변경 파일
- `backend/src/services/code_analysis/code_upload_service.py` (신규 생성)
- `backend/tests/unit/test_code_upload_service.py` (신규 생성, `validate_files` 순수 로직 단위 테스트 12개)
- `backend/tests/integration/test_tasks_api.py`의 `TestCodeUploadServiceCreateUpload` 클래스(DB/파일시스템 통합 테스트 4개)

## TDD 결과
- RED: `tests/unit/test_code_upload_service.py` 작성 → `ModuleNotFoundError: No module named 'src.services.code_analysis.code_upload_service'`로 실패 확인.
- GREEN: 구현 후 단위 12개 + 통합 4개 1차 통과.
- 테스트 커버리지: **96%** (`src/services/code_analysis/code_upload_service.py`, 81 statements / 3 missing — `get_for_task`의 `files_result` 조회 경로 중 일부가 단위 테스트(`session=None`)로는 닿지 않고 통합 테스트에서만 실행되는 라인; 통합 테스트로 실제로는 호출/검증됨을 `test_get_for_task_returns_none_without_upload` 등으로 확인했습니다).
- `ruff check` 통과(줄 길이 초과 1건 → 멀티라인 집합 리터럴로 수정).
- 전체 회귀(`pytest -q`, 284 tests) 통과.
- Git 저장소 미초기화로 커밋 해시 없음.

## 기술 결정
- **검증(`validate_files`)과 저장(`create_upload`)을 분리**: 계약이 "검증을 모두 통과하기 전까지는 Task 레코드를 생성하지 마세요(고아 Task 방지)"를 명시했기 때문에, 파일 내용 검증은 DB에 아무것도 쓰지 않는 순수 함수로 만들고, Task 생성과 UploadedCode/CodeFile 생성을 모두 **검증이 끝난 뒤**에만 호출하도록 라우터(T071)에서 순서를 강제했습니다. `validate_files`가 `session`을 전혀 쓰지 않아 단위 테스트에서 `CodeUploadService(session=None)`으로도 안전하게 테스트할 수 있었습니다.
- **paste를 특별 취급하지 않고 동일 파이프라인 통과**: paste 입력도 `UploadedFileInput` 하나로 변환되면 `validate_files`를 그대로 통과하므로, paste로 올린 코드도 지원되지 않는 확장자(`paste_filename`이 `.zip` 등)나 바이너리 내용이면 동일하게 거부됩니다. 별도의 paste 전용 검증 분기를 만들지 않은 것이 계약의 "특별 취급 최소화" 요구와 일치합니다.
- **`FileValidationError` → `CodeUploadError`로 단일화**: `file_validator`가 던지는 예외와 개수/경로 검증 실패를 모두 `CodeUploadError` 하나로 감싸, 라우터가 catch해야 하는 예외 타입을 하나로 줄였습니다(file_validator의 내부 예외 타입을 API 레이어가 알 필요가 없도록 경계를 명확히 함).
- **`UploadedCode`를 먼저 flush해 FK를 확보한 뒤 파일 저장**: `CodeFile.uploaded_code_id`가 FK이므로, `session.add(uploaded_code); await session.flush()`로 PK를 먼저 받아온 뒤 각 `CodeFile`을 생성합니다. 디스크 저장(`file_storage.save_file`)은 DB 트랜잭션 바깥의 부작용이라 롤백 시 디스크에 파일이 남을 수 있음을 인지했지만, 이번 범위에서 2단계 커밋/보상 트랜잭션까지 구현하는 것은 과설계(YAGNI)라고 판단했습니다(T067 비고와 동일한 결정).

## 비고
- `get_for_task`가 반환하는 `CodeFile` 목록은 `file_name` 오름차순으로 정렬합니다(안정적인 응답 순서 보장 목적). 업로드 당시 입력 순서를 그대로 보존해야 한다는 요구사항은 계약에 없었습니다.
- T065(언어 감지)/T066(복잡도 분석)과의 연결 지점이 바로 이 Task입니다 — 두 분석 함수 보고서에 남겨둔 "실제 저장 연결은 T069에서" 메모가 이번에 해소되었습니다.
