# TASK-089. 작업 3개 연속 생성 시 순차 번호 브라우저 수동 테스트

## 상태
완료

## 날짜
2026-11-16

## 작업 요약
FR-002/FR-004(작업 번호는 Task 1, 2, 3... 순서로 자동 부여되며 불변)를 검증했습니다. T084~T086에서 같은 프로젝트에 파일→폴더→붙여넣기 순으로 작업 3개를 연속 생성한 결과를 그대로 활용했습니다(UI 라벨만으로는 `task_number` 필드 자체를 확정할 수 없어, API로 별도 재확인).

절차: 브라우저 컨텍스트에서 `fetch('/api/v1/projects/{project_id}/tasks', {credentials:'include'})`를 호출해 생성 순서대로 응답을 확인.

결과:
```json
[
  {"task_number":1,"title":"Calculator functions","upload_method":"file"},
  {"task_number":2,"title":"Sample project folder","upload_method":"folder"},
  {"task_number":3,"title":"Pasted JS snippet","upload_method":"paste"}
]
```
세 작업의 `task_number`가 업로드 방식과 무관하게 생성 순서대로 **1, 2, 3**으로 정확히 부여됨을 확인 — TaskService(T068)의 "해당 project의 기존 최대 task_number+1" 로직이 정상 동작함을 실증.

## 변경 파일
없음 (수동 검증만 수행)

## TDD 결과
해당 없음 — 수동 브라우저 테스트 단계. 동일 시나리오(동시성 제외)는 이미 `backend/tests/integration/test_tasks_api.py`의 자동화 테스트로도 커버됨.

## 기술 결정
없음

## 비고
T084~T089 전 과정에서 사용한 백엔드(uvicorn :8000)·프런트엔드(vite :5173) 서버는 이번 QA 세션 종료 후 종료했습니다. 테스트 계정(`task-upload-tester@example.com`)과 생성된 프로젝트/작업 3개는 DB에 그대로 남아있습니다(Trash/삭제 기능 자체도 아직 Task 레벨에선 Trash 페이지에 연동되지 않은 상태 — T176/T177/T179에서 다룰 예정).
