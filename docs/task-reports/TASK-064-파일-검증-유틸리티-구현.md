# TASK-064. 파일 검증 유틸리티 구현

## 상태
완료

## 날짜
2026-11-12

## 작업 요약
`backend/src/utils/file_validator.py`에 파일 업로드 검증 유틸리티 3종(확장자 검사, 용량 검사, 바이너리 파일 감지)을 TDD로 구현했습니다.

- `validate_extension(file_name)`: 확장자 화이트리스트 검사. 허용 목록은 data-model.md의 `code_files.supported_extension` CHECK 제약(T009 마이그레이션에 이미 구현됨, `.py`/`.js`/`.ts`/`.jsx`/`.tsx`/`.html`/`.css`/`.java`/`.cpp`/`.c`/`.txt`/`.md` 12종)과 정확히 동일하게 맞췄습니다(FR-015, FR-해당 DB 제약 일치가 목적).
- `validate_total_size(total_size_bytes)`: 업로드 총 용량이 10MB(FR-014, `uploaded_code.valid_upload_size` 제약과 동일 값)를 넘는지 검사.
- `is_binary_content(content)` / `validate_not_binary(file_name, content)`: 외부 라이브러리(python-magic 등 requirements.txt에 없음) 없이 null byte 존재 여부 + UTF-8 디코딩 가능 여부로 바이너리 파일을 판별(research.md의 "Reject binary files (magic number detection)" 방침을 현재 의존성 범위 내에서 구현한 실용적 방법).

## 변경 파일
- `backend/src/utils/file_validator.py` (신규 생성)
- `backend/tests/unit/test_file_validator.py` (신규 생성, 단위 테스트 28개)
- `specs/001-ai-code-learning-platform/tasks.md` (T064 `[X]` 체크)

## TDD 결과
- RED: 구현 전 `tests/unit/test_file_validator.py` 작성 → `pytest` 실행 시 `ModuleNotFoundError: No module named 'src.utils.file_validator'`로 수집 실패 확인(RED 상태 확인).
- GREEN: `file_validator.py` 구현 후 28개 테스트 전부 통과.
- 테스트 커버리지: **100%** (`src/utils/file_validator.py`, `pytest --cov` 측정)
- `ruff check` 통과 (경고 없음)
- Git 저장소가 아직 초기화되지 않아 RED/GREEN 커밋 해시는 기록하지 않았습니다(이전 Task Report들과 동일한 제약).

## 기술 결정
- **바이너리 판별 방식**: python-magic 등 매직 넘버 전용 라이브러리를 추가하지 않고, (1) 처음 8KB 내 null byte(`\x00`) 존재 여부, (2) 해당 청크의 UTF-8 디코딩 가능 여부 두 가지 휴리스틱만으로 판별. 코드 학습 플랫폼 특성상 업로드 대상이 텍스트 기반 소스 코드로 제한되어 있어(FR-015 확장자 화이트리스트와 결합) 이 정도 휴리스틱으로 충분하다고 판단했으며, 새 의존성 추가를 피함.
- **확장자 목록 소스**: spec.md FR-015는 9종(.ts/.jsx/.tsx 누락)만 명시하지만, 실제 DB 스키마(T009 마이그레이션 `supported_extension` CHECK, data-model.md)는 12종을 허용함. 검증 유틸리티가 DB보다 더 좁은 목록을 쓰면 DB가 허용하는 유효한 업로드(.ts/.jsx/.tsx)를 애플리케이션 레벨에서 먼저 막아버리는 불일치가 생기므로, **이미 구현된 DB 제약과 동일한 12종 목록**을 채택했습니다.
- **용량 검사 단위**: FR-014/DB 제약 모두 "업로드 총량(task당)" 기준이므로, 개별 파일이 아닌 `total_size_bytes` 하나의 값을 받는 함수로 설계(여러 파일의 크기를 합산하는 책임은 호출자/업로드 서비스인 T069에 위임).

## 비고
파일 개수 제한(1-20개, FR-018)과 폴더 업로드 시 `.git`/`node_modules`/`.DS_Store`/`__pycache__` 제외(FR-017)는 이번 태스크(확장자/용량/바이너리 검증) 범위 밖이며, tasks.md상 T069(CodeUploadService)에서 다룰 예정입니다.

## 수동 검증 (2026-11-12, 가상 데이터)
사용자 요청으로 실제 구현된 3개 함수(확장자/용량/바이너리)를 가상 데이터로 수동 재검증했습니다. 자동화 단위 테스트(28개, 위 TDD 결과 참고)로 이미 커버되는 케이스이지만, 요청받은 구체적인 입력값으로 별도 확인했습니다.

1. **확장자 체크**
   - `main.py` → 통과(예외 없음)
   - `virus.exe` → 차단: `지원하지 않는 파일 형식입니다: virus.exe (지원 형식: .c, .cpp, .css, .html, .java, .js, .jsx, .md, .py, .ts, .tsx, .txt)`
2. **용량 체크**
   - 5MB(5,242,880 bytes) → 통과
   - 15MB(15,728,640 bytes) → 차단: `업로드 용량이 10MB를 초과했습니다 (15728640 bytes > 10485760 bytes)`
3. **바이너리 감지**
   - `b"print('hello')"` → `is_binary_content = False` → 통과
   - `bytes([0x00, 0x01])` → `is_binary_content = True` → 차단: `바이너리 파일은 업로드할 수 없습니다: unknown.bin`
4. **개수 체크(15개 통과 / 25개 차단 시나리오)** → **테스트 불가(미구현)**: `file_validator.py`에는 개수 검증 함수가 없음(공개 함수는 `validate_extension`, `validate_total_size`, `is_binary_content`, `validate_not_binary`, `get_file_extension` 뿐). 사용자 확인 결과, 원래 계획대로 **T069(CodeUploadService)에서 처리**하기로 결정 — 이번 태스크 범위에 추가하지 않음(코드 변경 없음).

**결론**: T064에서 구현한 3개 검증 기능(확장자/용량/바이너리)은 모두 요청된 가상 데이터 시나리오에서 기대한 대로 동작함을 재확인. 개수 검증은 계획대로 T069로 이연하며 T064는 이 상태로 완료 처리.
