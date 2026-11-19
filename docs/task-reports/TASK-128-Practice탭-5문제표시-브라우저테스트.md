# TASK-128. Practice 탭 5개 문제 표시 — 브라우저 테스트

## 상태
완료

## 날짜
2026-11-19

## 작업 요약
Docker(PostgreSQL+Redis), `uvicorn`(:8000), `celery worker -Q document_generation,practice_generation --include=src.tasks.document_generation,src.tasks.practice_generation`, `vite`(:5173) 네 가지를 모두 실제로 띄운 뒤, Playwright MCP로 실제 브라우저를 조작해 끝까지 확인했습니다.

절차: 회원가입 → 로그인 → 프로젝트 생성 → "곱하기 함수" 코드를 붙여넣기로 Task 생성 → 문서 생성 완료 대기 → Practice 탭 클릭. 결과: 5개 문제가 모두 표시되었고, 각 문제의 난이도 배지가 순서대로 "Follow Along / Fill Blanks / Modify / Debug / Create"로 정확히 나타났습니다. 문제 지문도 실제 업로드한 코드(곱하기 함수)를 기반으로 AI가 생성한 구체적인 내용이었습니다(예: "3과 7을 곱한 결과를 출력하는 코드를 똑같이 작성해 보세요").

## 변경 파일
없음 (테스트만 수행, 코드 변경은 TASK-129 보고서에 기록된 버그 수정 참고)

## TDD 결과
- 커밋: 아직 생성하지 않음
- 검증 방식: 자동화 테스트가 아닌 Playwright MCP 수동 브라우저 조작 (constitution IV항 요구사항)

## 기술 결정
없음.

## 비고
테스트에 사용한 사용자(`phase7-test@example.com`)·프로젝트·Task 2개는 검증 완료 후 실제 DB에서 삭제했습니다(`DELETE FROM users WHERE email = ...` cascade). 또한 이 검증 과정에서 중요한 버그를 하나 발견해 고쳤는데, 자세한 내용은 TASK-129 보고서에 기록했습니다.
