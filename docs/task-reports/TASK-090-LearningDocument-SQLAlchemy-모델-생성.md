# TASK-090. LearningDocument SQLAlchemy 모델 생성

## 상태
완료

## 날짜
2026-11-17

## 작업 요약
`backend/src/models/learning_document.py`에 `LearningDocument` SQLAlchemy 모델을 생성했습니다. data-model.md의 LearningDocument 엔티티 정의 및 T009(`001_initial_schema.py`)의 `learning_documents` 테이블 마이그레이션 스키마와 정확히 일치하도록 10개 컬럼(id, task_id, content, generation_status, generation_started_at, generation_completed_at, generation_error, celery_task_id, created_at, updated_at)을 매핑했습니다. 기존 `UploadedCode`/`Task` 모델(T061-T063)과 동일한 스타일(SQLAlchemy 2.0 `Mapped`/`mapped_column`, UUID PK with `gen_random_uuid()` server_default)을 따랐습니다.

`content`는 7챕터 구조를 담는 JSONB 컬럼으로 `postgresql.JSONB` + `Mapped[dict]`로 매핑했습니다. 7챕터 키 존재 여부(`valid_content_structure` CHECK)와 `generation_status` 허용값(`pending/in_progress/completed/failed`) 제약은 DB 레벨 CHECK 제약으로 이미 마이그레이션에 존재하므로, 기존 모델 패턴과 동일하게 모델 레이어에는 별도 Python 검증을 추가하지 않았습니다(필요 시 서비스 레이어에서 검증).

## 변경 파일
- `backend/src/models/learning_document.py` (신규 생성)
- `specs/001-ai-code-learning-platform/tasks.md` (T090 `[X]` 체크)

## TDD 결과
- 해당 없음 — 모델 전용 태스크로, 기존 `Task`/`UploadedCode` 모델(T061-T063)도 별도 단위 테스트 없이 서비스/API 통합 테스트에서 간접 검증되는 동일한 패턴을 따름(`backend/tests/`에 모델 단위 테스트 없음을 확인). T090은 Phase 6 "Backend: Document Models & AI Integration" 섹션의 모델 정의 전용 태스크이며, 이후 DocumentGenerationService(T093)·API(T097-T098) 계층에서 TDD가 적용될 예정.
- 라이브 DB(Docker)가 현재 환경에서 실행 중이지 않아 `psql`을 통한 실제 테이블 대조는 수행하지 못함. 대신 정적 검증 수행:
  - `python -c "from src.models.learning_document import LearningDocument; print(LearningDocument.__table__)"` → import 및 테이블 메타데이터 생성 정상 확인
  - `ruff check src/models/learning_document.py` 통과 (경고 없음)
  - T009 마이그레이션(`backend/alembic/versions/001_initial_schema.py`)의 `learning_documents` 테이블 정의와 컬럼별 1:1 대조(컬럼명/타입/nullable/default) — 완전히 일치

## 기술 결정
- `content`를 `Mapped[dict]` + `JSONB`로 매핑(7챕터 구조의 스키마 검증은 DB CHECK 제약과 추후 서비스/프롬프트 레이어 책임).
- `generation_status`는 `Mapped[str]`에 `server_default="pending"`으로 매핑(enum 제약은 DB CHECK로 위임, 기존 모델들의 상태 필드 패턴과 동일).
- `generation_started_at`/`generation_completed_at`/`generation_error`/`celery_task_id`는 `Mapped[... | None]`로 nullable 매핑 — DB 스키마의 nullable 여부와 일치.

## 비고
없음
