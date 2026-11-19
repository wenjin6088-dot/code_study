# TASK-116. 실습 문제 생성 프롬프트 템플릿

## 상태
완료

## 날짜
2026-11-19

## 작업 요약
AI(Gemini)에게 "이 코드를 가지고 초보자용 연습 문제 5개를 만들어줘"라고 정확하게 지시하는 프롬프트(명령문)를 작성했습니다. 학습 문서(T092)를 만들 때 썼던 프롬프트 설계 방식을 그대로 재사용했습니다.

구체적으로 다음을 추가했습니다:
1. `PRACTICE_PROBLEM_TYPES`: 문제 유형 5가지를 난이도 순서대로 고정한 목록 (`follow_along`→`fill_blanks`→`modify`→`debug`→`create`). 기획 문서(spec.md FR-049)가 요구한 "따라하기 → 빈칸채우기 → 수정하기 → 디버깅 → 새로만들기" 순서와 정확히 일치합니다.
2. `PRACTICE_SYSTEM_INSTRUCTION`: AI에게 "초보자 대상, 코드에 나온 개념만 사용, 브라우저에서 실행 안 하는 텍스트 전용 문제, JSON으로만 응답"이라는 역할/규칙을 알려주는 시스템 지침입니다.
3. `build_practice_prompt(...)`: 실제 소스 코드, 언어, 난이도, 출력 언어(기본 한국어)를 받아 완성된 프롬프트 문자열을 만들어주는 함수입니다. 결과 JSON의 정확한 형태(문제 5개, 각 문제가 가져야 할 필드들)를 예시로 보여줘서 AI가 엉뚱한 형식으로 답하지 않도록 유도합니다.

## 변경 파일
- `backend/src/services/ai/prompts.py` (수정: 함수/상수 추가, 기존 `build_document_prompt` 로직은 그대로 둠)
- `backend/tests/unit/test_practice_prompts.py` (신규)

## TDD 결과
- RED: `test_practice_prompts.py`를 먼저 작성 → `PRACTICE_PROBLEM_TYPES`를 import할 수 없어 실패하는 것을 확인했습니다.
- GREEN: `prompts.py`에 실제 구현을 추가 → 13개 테스트 전부 통과.
- REFACTOR: 별도 리팩토링은 필요하지 않았습니다 (기존 `build_document_prompt`의 구조를 그대로 따라 만들어서 처음부터 일관된 형태였습니다).
- 커밋: 아직 생성하지 않음 (사용자 요청 시 생성 예정)
- 테스트 커버리지: 신규 테스트 13개 모두 통과

## 기술 결정
문제 유형과 순서를 상수(`PRACTICE_PROBLEM_TYPES`)로 고정해 둔 이유는, 이후 서비스 계층(T117)과 DB 체크 제약(마이그레이션)이 똑같은 5가지 값을 기준으로 검증해야 하기 때문입니다. 한 곳에서만 정의해 두면 나중에 값이 바뀌어도 한 군데만 고치면 됩니다.

## 비고
없음.
