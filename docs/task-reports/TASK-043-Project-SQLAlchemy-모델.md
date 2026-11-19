# TASK-043. Project SQLAlchemy 모델

## 상태
완료

## 날짜
2026-11-09

## 작업 요약
프로젝트(학습 과제) 데이터를 담는 `Project` SQLAlchemy 모델을 새로 만들었습니다. 이미 존재하는 Alembic 마이그레이션(`001_initial_schema.py`, projects 테이블)과 1:1로 맞춰서 컬럼을 정의했고, `src/models/user.py`가 쓰는 스타일(`Mapped`/`mapped_column`, `Base`를 `src.models.base`에서 가져오는 방식)을 그대로 따랐습니다.

필드는 `id`(UUID, DB가 `gen_random_uuid()`로 기본값 생성), `user_id`(UUID, `users.id`를 CASCADE로 참조, NOT NULL), `title`(String(255), NOT NULL), `description`(Text, NULL 허용), `created_at`/`updated_at`/`last_activity_at`(TIMESTAMP WITH TIME ZONE, DB 기본값 CURRENT_TIMESTAMP), `deletion_status`(String(20), 기본값 'active'), `trashed_at`/`scheduled_deletion_at`(TIMESTAMP WITH TIME ZONE, NULL 허용)입니다. 제목 최소 길이 체크(`char_length(title) >= 1`)와 `deletion_status` 체크 제약은 이미 마이그레이션에 들어 있어서 모델에서 따로 선언하지 않고 DB 제약에 맡겼습니다.

## 변경 파일
- `backend/src/models/project.py` (신규)

## TDD 결과
- Git 저장소가 아직 초기화되지 않아 커밋은 생략했습니다.
- 테스트 대상: `backend/tests/integration/test_projects_api.py`의 `TestProjectModel` 클래스 3개 테스트
  - `test_create_project_applies_defaults` — 기본값(deletion_status='active', trashed_at/scheduled_deletion_at=None 등) 확인
  - `test_empty_title_violates_title_min_length_check` — 빈 제목이면 `IntegrityError` 발생 확인 (DB 체크 제약)
  - `test_project_requires_user_id` — `user_id` 없으면 `IntegrityError` 발생 확인 (NOT NULL 제약)
- 전부 통과 (3/3 PASSED)

## 기술 결정 (해당 시)
- 체크 제약(제목 최소 길이, deletion_status 허용값)은 모델 레벨 validator가 아니라 DB 제약으로만 걸어두었습니다. 테스트가 `IntegrityError`(DB 레벨 예외)를 기대하고 있어서, 애플리케이션 레벨 검증은 서비스 레이어(`ProjectService`)에서 별도로 수행하도록 역할을 분리했습니다.

## 비고
- 없음
