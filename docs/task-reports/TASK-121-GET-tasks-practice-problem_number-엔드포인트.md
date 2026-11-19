# TASK-121. GET /tasks/{task_id}/practice/{problem_number} 엔드포인트 구현

## 상태
완료

## 날짜
2026-11-19

## 작업 요약
실습 문제 5개 중 특정 1개만 조회하는 API를 추가했습니다. `GET /api/v1/tasks/{task_id}/practice/{problem_number}`를 호출하면 그 번호의 문제 하나만 돌려주고, 번호가 존재하지 않으면 404("Practice problem not found")를 돌려줍니다. T120에서 만든 "소유자 확인 + 전체 문제 조회" 로직을 재사용해서, 그중 번호가 일치하는 것 하나만 골라 반환하도록 구현했습니다.

이 엔드포인트는 당장 프론트엔드(T125 PracticeViewer)에서는 "한 번에 5개를 다 보여주는" 방식을 쓰기 때문에 직접 사용하지는 않지만, tasks.md 명세(T121)가 요구한 API이고, 추후 "문제 하나만 딥링크로 공유" 같은 기능이 필요할 때를 위한 것입니다.

## 변경 파일
- `backend/src/api/practice.py` (T120과 같은 파일에 함께 구현)
- `backend/tests/integration/test_practice_api.py` (T120과 같은 파일에 테스트 포함)

## TDD 결과
- RED/GREEN: T120과 동일한 커밋 단위로 함께 진행했습니다 (같은 RED 테스트 파일, 같은 GREEN 구현 파일).
- 커밋: 아직 생성하지 않음
- 테스트 커버리지: 로그인 필요/존재하지 않는 작업/존재하지 않는 문제 번호/정상 조회 — 4개 테스트 통과

## 기술 결정
없음.

## 비고
없음.
