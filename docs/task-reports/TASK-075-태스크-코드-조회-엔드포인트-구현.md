# TASK-075. GET /tasks/{task_id}/code 엔드포인트 구현

## 상태
완료

## 날짜
2026-11-16

## 작업 요약
`backend/src/api/tasks.py`에 `GET /tasks/{task_id}/code`를 구현했습니다. `TaskService.get`으로 소유권을 확인한 뒤(소유 Task만, 아니면 404), `CodeUploadService.get_for_task`로 해당 Task의 `CodeFile` 목록을 가져와 각 파일의 `storage_path`를 `file_storage.read_file`(T067)로 읽어 실제 내용을 반환합니다. 응답은 `{"files": [{"file_name", "file_path", "file_extension", "content"}]}`이며, 업로드가 없는 Task는 `{"files": []}`를 반환합니다.

## 변경 파일
- `backend/src/api/tasks.py` (`get_task_code` 핸들러, `TaskCodeFileResponse`/`TaskCodeResponse`)
- `backend/tests/integration/test_tasks_api.py`의 `TestGetTaskCodeEndpoint` 클래스(테스트 4개: paste로 업로드한 코드의 내용이 그대로 반환되는지, 업로드 전 빈 배열, 타인 Task 404, 미인증 401)

## TDD 결과
- RED → GREEN: 4개 테스트 모두 라우터 구현 후 1차 통과.
- `ruff check` 통과.
- 전체 회귀(`pytest -q`, 284 tests) 통과.
- Git 저장소 미초기화로 커밋 해시 없음.

## 기술 결정
- **전용 응답 스키마(`TaskCodeFileResponse`) 분리**: `GET /tasks/{task_id}/code`의 응답은 Task/업로드 메타데이터용 `CodeFileResponse`(file_size_bytes 포함, content 없음)와 모양이 다르므로(content 포함, file_size_bytes 없음) 별도 Pydantic 모델로 분리했습니다. 두 스키마를 하나로 합쳐 옵셔널 필드를 늘리는 대신, 엔드포인트별 계약을 그대로 반영하는 쪽을 선택했습니다.
- **파일 내용은 매 요청마다 디스크에서 다시 읽음(캐싱 없음)**: 10MB 총용량 제한(FR-014) 아래에서는 매 요청 디스크 읽기 비용이 크지 않다고 판단해, 별도 캐시 계층을 두지 않았습니다(YAGNI).

## 비고
- 파일 내용은 `utf-8`로 디코드합니다. 업로드 시점에 `file_validator.validate_not_binary`가 이미 UTF-8 디코드 가능 여부를 검증했으므로(T064), 이 경로에서 `UnicodeDecodeError`가 발생할 가능성은 없다고 판단했습니다.
