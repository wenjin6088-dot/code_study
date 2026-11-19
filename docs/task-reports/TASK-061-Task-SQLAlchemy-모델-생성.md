# TASK-061. Task SQLAlchemy 모델 생성

## 상태
완료

## 날짜
2026-11-12

## 작업 요약
`backend/src/models/task.py`에 `Task` SQLAlchemy 모델을 생성했습니다. data-model.md의 Task 엔티티 정의 및 T009(`001_initial_schema.py`)의 `tasks` 테이블 마이그레이션 스키마와 정확히 일치하도록 11개 컬럼(id, project_id, task_number, title, description, upload_method, created_at, updated_at, deletion_status, trashed_at, scheduled_deletion_at)을 매핑했습니다. 기존 `Project` 모델(T043)과 동일한 스타일(SQLAlchemy 2.0 `Mapped`/`mapped_column`, UUID PK with `gen_random_uuid()` server_default)을 따랐습니다.

`task_number`는 Integer, not-null로 매핑했으며, 순차 번호 자체의 유일성(`unique_task_number_per_project`)과 제목 길이(5자 이상)/설명 길이(500자 이하) 제약은 DB 레벨 CHECK 제약으로 이미 마이그레이션에 존재하므로 모델에서는 별도 Python 레벨 검증을 추가하지 않았습니다(ProjectService 패턴과 동일하게 서비스 레이어에서 필요 시 검증).

## 변경 파일
- `backend/src/models/task.py` (신규 생성)
- `specs/001-ai-code-learning-platform/tasks.md` (T061 `[X]` 체크)

## TDD 결과
- 해당 없음 — 모델 전용 태스크로, 기존 `Project` 모델(T043)도 별도 단위 테스트 없이 서비스/API 통합 테스트(T044-T050 범위)에서 간접 검증되는 동일한 패턴을 따름. T061은 Phase 5 "Backend: Task & Code Models" 섹션의 모델 정의 전용 태스크(T061-T063)이며, 서비스/API 계층에서 TDD가 적용될 예정.
- 대신 라이브 DB(Docker `codelearning_postgres`, T009 마이그레이션 적용된 상태)를 대상으로 수동 검증 수행:
  - `ruff check src/models/task.py` 통과 (경고 없음)
  - `psql \d tasks`로 실제 테이블 스키마(11개 컬럼, 타입, default, 제약조건)와 모델 컬럼을 1:1 대조 — 완전히 일치
  - `AsyncSession`으로 `select(Task)` 실행 → 정상 쿼리 성공(0 rows, 테이블 존재 확인)

## 기술 결정
- `task_number`를 `Mapped[int]`로 매핑(불변/순차 보장은 서비스 레이어 책임, FR-004/FR-005).
- `upload_method`, `description`, `trashed_at`, `scheduled_deletion_at`은 `Mapped[str | None]` / `Mapped[datetime | None]`로 nullable 매핑 — DB 스키마의 nullable 여부와 일치.

## 비고
없음
