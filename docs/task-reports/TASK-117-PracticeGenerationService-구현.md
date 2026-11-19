# TASK-117. PracticeGenerationService 구현

## 상태
완료

## 날짜
2026-11-19

## 작업 요약
실제로 Gemini AI를 호출해서 실습 문제 5개를 받아오고, 그 결과가 올바른지 검사하는 서비스를 만들었습니다. 학습 문서를 만들던 `DocumentGenerationService`(T093)와 쌍둥이 같은 구조입니다.

동작 방식:
1. T116에서 만든 프롬프트를 AI에게 보냅니다.
2. AI가 JSON으로 답하면, "문제가 정확히 5개인가?", "문제 번호가 1~5 중복 없이 다 있는가?", "문제 유형이 정해진 5종류 중 하나인가?"를 검사합니다. 하나라도 틀리면 `InvalidPracticeStructureError`를 일으킵니다.
3. AI 서버가 일시적으로 오류를 내거나(503 등), 응답이 깨진 JSON이거나, 구조가 틀렸으면 — 최대 3번까지 점점 긴 간격(1초→2초→4초)으로 다시 시도합니다. 이건 기존 문서 생성 서비스와 똑같은 재시도 전략(FR-090)입니다.
4. 사용자 요청이 잘못된 경우(예: 400 Bad Request)처럼 다시 시도해도 소용없는 오류는 즉시 포기합니다.

## 변경 파일
- `backend/src/services/practice/practice_generation_service.py` (신규)
- `backend/tests/unit/test_practice_generation_service.py` (신규)

## TDD 결과
- RED: 서비스 테스트를 먼저 작성 → `practice_generation_service` 모듈이 없어서 import 오류로 실패하는 것을 확인했습니다.
- GREEN: `PracticeGenerationService`를 구현 → 14개 테스트 전부 통과 (성공 케이스, 재시도 4종, 재시도 불가 오류 2종, 입력 검증 포함).
- REFACTOR: `DocumentGenerationService`와 거의 동일한 뼈대를 재사용했기 때문에 추가 리팩토링은 필요 없었습니다.
- 커밋: 아직 생성하지 않음
- 테스트 커버리지: 신규 테스트 14개 모두 통과, 기존 전체 테스트(413개)에도 영향 없음

## 기술 결정
AI가 응답한 문제 순서가 뒤바뀌어 있을 가능성을 대비해, 검증을 통과한 뒤 `problem_number` 기준으로 다시 정렬해서 반환하도록 했습니다. 호출하는 쪽(Celery 태스크)이 "항상 1번부터 순서대로 온다"고 믿고 바로 DB에 저장할 수 있게 하기 위함입니다.

## 비고
없음.
