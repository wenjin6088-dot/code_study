# TASK-067. 파일 저장소 서비스 구현

## 상태
완료

## 날짜
2026-11-16

## 작업 요약
`backend/src/services/code_analysis/file_storage.py`에 업로드된 코드 파일을 파일시스템에 저장/읽기하는 순수 서비스를 TDD로 구현했습니다(FR 업로드 저장 경로 요구사항, data-model.md의 `CodeFile.storage_path` 규칙).

- `save_file(user_id, task_id, relative_name, content: bytes) -> str`: `{UPLOAD_DIR}/{user_id}/{task_id}/{uuid4()}_{basename}` 경로에 바이트를 기록하고 실제로 기록된 경로 문자열을 반환합니다. `UPLOAD_DIR`은 `os.environ.get("UPLOAD_DIR", "storage/uploads")`로 호출 시점에 매번 읽어(`db/config.py`의 패턴과 동일), 테스트에서 `monkeypatch.setenv`로 임시 디렉터리를 주입할 수 있게 했습니다.
- `_safe_basename(relative_name)`: 폴더 업로드로 들어온 `"src/app.py"` 같은 상대 경로에서 디렉터리 부분을 모두 제거하고 파일명(`"app.py"`)만 남깁니다(`Path.name`). 백슬래시도 슬래시로 정규화한 뒤 처리합니다.
- 저장 파일명에 `uuid4()`를 접두사로 붙여, 서로 다른 폴더에서 온 동일 이름 파일(`main.py` 두 개 등)이 디스크에서 덮어쓰지 않도록 했습니다.
- `read_file(storage_path) -> bytes`: 저장된 파일을 그대로 읽어 반환합니다(T075 `GET /tasks/{task_id}/code`에서 사용).

## 변경 파일
- `backend/src/services/code_analysis/file_storage.py` (신규 생성)
- `backend/tests/unit/test_file_storage.py` (신규 생성, 단위 테스트 4개)

## TDD 결과
- RED: `tests/unit/test_file_storage.py`를 먼저 작성 → `pytest` 수집 시 `ModuleNotFoundError: No module named 'src.services.code_analysis.file_storage'`로 실패 확인.
- GREEN: `file_storage.py` 구현 후 4개 테스트 전부 통과.
- 테스트 커버리지: **100%** (`src/services/code_analysis/file_storage.py`, `pytest --cov` 측정, 16 statements / 0 missing).
- `ruff check` 통과.
- 전체 회귀(`pytest -q`, 284 tests) 통과, 기존 테스트에 영향 없음.
- Git 저장소가 아직 초기화되지 않아 RED/GREEN 커밋 해시는 기록하지 않았습니다(TASK-064~066과 동일한 제약).

## 기술 결정
- **환경변수를 호출마다 읽음(모듈 로드 시 캐시하지 않음)**: `UPLOAD_DIR`을 모듈 상수로 캐시하면 테스트에서 `monkeypatch.setenv`로 바꿔도 이미 임포트된 모듈의 상수는 갱신되지 않아 테스트 격리가 깨집니다. `db/config.py`의 `get_database_config()`가 함수 호출 시점에 `os.environ.get`을 읽는 패턴을 그대로 따라, `_upload_root()` 함수를 매번 호출하도록 했습니다.
- **UUID 접두사 + basename 분리 저장**: 폴더 업로드 시 같은 파일명(`main.py`)이 여러 하위 폴더에 존재할 수 있으므로, 원본 상대 경로(`file_path` 컬럼)는 DB에만 보존하고 실제 디스크 파일명은 `{uuid4()}_{basename}`으로 충돌 없이 유일화했습니다. 디렉터리 구조 자체를 디스크에 재현하지 않은 이유는, 그렇게 하면 경로 트래버설/충돌 검증이 디스크 I/O 계층까지 번져 복잡도가 커지기 때문입니다(YAGNI).
- **동기(sync) I/O 유지**: 프로젝트 의존성에 `aiofiles`가 없고(`requirements.txt` 확인), 다른 서비스 레이어도 동기 함수로 작성되어 있어 일관성을 위해 `pathlib.Path.write_bytes`/`read_bytes`를 그대로 사용했습니다. 업로드 용량이 10MB로 제한되어 있어(FR-014) 블로킹 I/O로 인한 이벤트 루프 지연이 실질적인 문제가 되지 않는다고 판단했습니다.

## 비고
- 저장된 파일을 DB 트랜잭션 롤백 시 자동으로 지우는 보상(compensating) 로직은 범위 밖입니다. T069에서 DB 커밋이 실패해도 디스크에 파일이 남을 수 있으나, 이는 이번 Task 세트의 명시적 요구사항에 포함되지 않았습니다.
