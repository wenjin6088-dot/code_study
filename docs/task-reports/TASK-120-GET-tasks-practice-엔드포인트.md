# TASK-120. GET /tasks/{task_id}/practice 엔드포인트 구현

## 상태
완료

## 날짜
2026-11-19

## 작업 요약
프론트엔드가 "이 작업(Task)의 실습 문제들을 보여줘"라고 요청할 수 있는 API를 만들었습니다. `GET /api/v1/tasks/{task_id}/practice`를 호출하면:
- 그 Task가 내 소유가 아니거나 존재하지 않으면 404("Task not found")
- 문제가 아직 생성되지 않았으면 `{status: "pending", problems: []}`
- 문제 5개가 다 생성되어 있으면 `{status: "completed", problems: [...]}` (문제 번호 순서대로)

`practice_problems` 테이블에는 생성 상태를 나타내는 컬럼이 없기 때문에, "문제가 하나라도 있으면 완료, 없으면 아직 생성 중"이라는 규칙으로 상태를 즉석에서 계산했습니다. 이는 문서 생성 API(T097/T098)가 쓰는 명시적 상태 컬럼과는 다르지만, DB에 있는 정보만으로 충분히 판단할 수 있는 단순한 방법입니다.

## 변경 파일
- `backend/src/api/practice.py` (신규)
- `backend/src/api/router.py` (수정: 새 라우터 등록)
- `backend/tests/integration/test_practice_api.py` (신규)

## TDD 결과
- RED: API 통합 테스트를 먼저 작성 → 라우트가 없어 404(엔드포인트 자체가 없음)로 실패하는 것을 확인했습니다.
- GREEN: `practice.py` 구현 및 `router.py`에 등록 → 관련 테스트 전부 통과.
- 커밋: 아직 생성하지 않음
- 테스트 커버리지: 로그인 필요/타인 소유 작업 차단/존재하지 않는 작업/대기 상태/완료 상태 등 5개 테스트 통과

## 기술 결정
없음(기존 `documents.py`의 소유권 검증·에러 처리 패턴을 그대로 재사용).

## 비고
Pydantic이 `model_solution`이라는 필드명을 "model_"로 시작하는 예약된 이름으로 오인해 경고를 내길래, `model_config = ConfigDict(protected_namespaces=())`로 경고를 없앴습니다. 실제 동작에는 영향 없는 사소한 정리입니다.
