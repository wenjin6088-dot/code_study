# TASK-062. UploadedCode SQLAlchemy 모델 생성

## 상태
완료

## 날짜
2026-11-12

## 작업 요약
`backend/src/models/uploaded_code.py`에 `UploadedCode` SQLAlchemy 모델을 생성했습니다. data-model.md의 UploadedCode 엔티티 정의 및 T009(`001_initial_schema.py`)의 `uploaded_code` 테이블 마이그레이션 스키마와 정확히 일치하도록 8개 컬럼(id, task_id, detected_language, complexity_level, total_lines, total_files, upload_size_bytes, created_at)을 매핑했습니다. `task_id`는 Task와의 1:1 관계를 반영해 `unique=True`로 매핑했습니다. 기존 `Task`/`Project` 모델과 동일한 SQLAlchemy 2.0 스타일을 따랐습니다.

용량 제한(10MB, `valid_upload_size` CHECK)과 `complexity_level` 허용값 제약은 DB 레벨 CHECK 제약으로 마이그레이션에 이미 존재하므로 모델에서는 별도 Python 레벨 검증을 추가하지 않았습니다(서비스 레이어에서 필요 시 검증, 기존 패턴과 동일).

## 변경 파일
- `backend/src/models/uploaded_code.py` (신규 생성)
- `specs/001-ai-code-learning-platform/tasks.md` (T062 `[X]` 체크)

## TDD 결과
- 해당 없음 — 모델 전용 태스크(T061-T063)로, 서비스/API 계층에서 TDD 적용 예정([[task-061-task-model]] 참고 패턴과 동일).
- 라이브 DB(Docker `codelearning_postgres`) 대상 수동 검증:
  - `ruff check src/models/uploaded_code.py` 통과 (경고 없음)
  - `psql \d uploaded_code`로 실제 테이블 스키마(8개 컬럼, 타입, unique 제약, FK, CHECK 제약)와 모델 컬럼 1:1 대조 — 완전히 일치
  - `AsyncSession`으로 `select(UploadedCode)` 실행 → 정상 쿼리 성공(0 rows, 테이블 존재 확인)

## 기술 결정
- `task_id`를 `unique=True`로 매핑하여 Task:UploadedCode = 1:1 관계를 SQLAlchemy 레벨에서도 명시(실제 제약은 DB `uploaded_code_task_id_key` UNIQUE가 담당).
- nullable 컬럼(`detected_language`, `complexity_level`, `total_lines`, `total_files`, `upload_size_bytes`)은 모두 `Mapped[T | None]`로 매핑 — 코드 분석 서비스(T065 이후)가 비동기로 채워 넣기 전까지 값이 없을 수 있음을 반영.

## 비고
없음
