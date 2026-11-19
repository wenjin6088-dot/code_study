# TASK-119. 문서 생성 완료 후 실습 문제 생성 자동 트리거

## 상태
완료

## 날짜
2026-11-19

## 작업 요약
사용자가 따로 버튼을 누르지 않아도, "학습 문서 생성이 성공적으로 끝나면 → 곧바로 실습 문제 생성이 시작"되도록 두 비동기 작업을 연결했습니다. 코드 업로드가 끝나면 문서 생성이 자동으로 시작되는 기존 흐름(T096)의 다음 단계라고 보면 됩니다.

구체적으로 `document_generation.py`의 `generate_document_async` 함수가 문서 상태를 "completed"로 바꾸고 저장한 바로 다음에, 실습 문제 생성 Celery 태스크를 큐에 넣도록(`generate_practice_task.delay(...)`) 한 줄을 추가했습니다. 반대로 문서 생성이 실패하면 실습 문제 생성은 아예 시작되지 않습니다(의미 없는 선행 조건이 실패했기 때문).

## 변경 파일
- `backend/src/tasks/document_generation.py` (수정: `enqueue_practice` 매개변수와 트리거 호출 추가)

## TDD 결과
- RED: `test_practice_generation_task.py`에 트리거 테스트 2개(성공 시 호출/실패 시 미호출)를 먼저 작성 → `generate_document_async`가 `enqueue_practice` 매개변수를 받지 않아 실패하는 것을 확인했습니다.
- GREEN: 매개변수를 추가하고 성공 분기 끝에서 호출하도록 구현 → 2개 테스트 통과.
- REFACTOR: 기존 문서 생성 테스트(`test_document_generation_task.py`, `test_documents_api.py`)도 모두 다시 돌려 회귀가 없는지 확인했습니다 (30개 전부 통과).
- 커밋: 아직 생성하지 않음
- 테스트 커버리지: 트리거 전용 테스트 2개 + 전체 회귀 테스트 통과

## 기술 결정
실제 운영 환경에서 쓸 기본 함수(`_default_enqueue_practice`, 실제 Celery 태스크를 호출)와, 테스트에서 주입할 수 있는 매개변수(`enqueue_practice`)를 분리했습니다. 이렇게 하면 테스트에서 가짜(fake) 함수를 넣어 "정말로 호출됐는지"만 확인할 수 있고, Redis/Celery 워커 없이도 테스트가 가능합니다. 이는 T095의 `DocumentQueueService`가 썼던 `EnqueueFn` 패턴과 동일한 방식입니다.

## 비고
없음.
