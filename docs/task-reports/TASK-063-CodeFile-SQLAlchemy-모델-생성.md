# TASK-063. CodeFile SQLAlchemy 모델 생성

## 상태
완료

## 날짜
2026-11-12

## 작업 요약
`backend/src/models/code_file.py`에 `CodeFile` SQLAlchemy 모델을 생성했습니다. data-model.md의 CodeFile 엔티티 정의 및 T009(`001_initial_schema.py`)의 `code_files` 테이블 마이그레이션 스키마와 정확히 일치하도록 9개 컬럼(id, uploaded_code_id, file_name, file_path, file_extension, file_size_bytes, storage_path, mime_type, created_at)을 매핑했습니다. `UploadedCode`와의 1:N 관계(FK `ON DELETE CASCADE`)를 반영했습니다. 기존 `Task`/`UploadedCode` 모델과 동일한 SQLAlchemy 2.0 스타일을 따랐습니다.

지원 확장자 허용값(`.py`, `.js`, `.ts` 등 12종) 제약은 DB 레벨 CHECK 제약(`supported_extension`)으로 마이그레이션에 이미 존재하므로 모델에서는 별도 Python 레벨 검증을 추가하지 않았습니다(서비스/검증 유틸 레이어인 T064 `file_validator.py`에서 담당, 기존 패턴과 동일).

## 변경 파일
- `backend/src/models/code_file.py` (신규 생성)
- `specs/001-ai-code-learning-platform/tasks.md` (T063 `[X]` 체크)

## TDD 결과
- 해당 없음 — 모델 전용 태스크(T061-T063)로, 서비스/API 계층에서 TDD 적용 예정([[task-061-task-model]], [[task-062-uploadedcode-model]]과 동일 패턴).
- 라이브 DB(Docker `codelearning_postgres`) 대상 수동 검증:
  - `ruff check src/models/code_file.py` 통과 (경고 없음)
  - `psql \d code_files`로 실제 테이블 스키마(9개 컬럼, 타입, FK, CHECK 제약)와 모델 컬럼 1:1 대조 — 완전히 일치
  - `AsyncSession`으로 `select(CodeFile)` 실행 → 정상 쿼리 성공(0 rows, 테이블 존재 확인)

## 기술 결정
- `file_name`, `storage_path`는 not-null로 매핑(DB 스키마와 동일) — 파일 업로드 시 항상 필수 값.
- `file_path`, `file_extension`, `file_size_bytes`, `mime_type`은 nullable로 매핑 — 단일 파일 업로드(폴더 아님) 시 `file_path`가 비어있을 수 있고, 확장자/크기/MIME 분석이 비동기로 수행되기 전 상태를 반영.

## 비고
T061-T063(Task/UploadedCode/CodeFile 모델)이 모두 완료되어 Phase 5 "Backend: Task & Code Models" 섹션의 모델 정의 태스크가 마무리되었습니다. 다음은 T064(파일 검증 유틸리티)와 T065(언어 감지 서비스)입니다.
