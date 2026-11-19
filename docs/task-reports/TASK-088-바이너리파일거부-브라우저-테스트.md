# TASK-088. 바이너리 파일 업로드 거부 브라우저 수동 테스트

## 상태
완료

## 날짜
2026-11-16

## 작업 요약
FR-016(바이너리 파일 거부)의 거부 경로를 검증했습니다.

절차:
1. PNG 매직 넘버 + null byte로 구성된 12바이트 바이너리 내용을, 지원 확장자인 `.py`로 저장한 파일(`t088_binary.py`) 생성 — 확장자 검증을 통과시켜 실제로 "바이너리 내용 감지" 로직까지 도달하도록 의도적으로 구성
2. CreateTaskModal "파일" 방식으로 해당 파일 선택 후 "Create" 제출

결과: 모달에 **"바이너리 파일은 업로드할 수 없습니다: t088_binary.py"** 에러가 `role="alert"`로 표시됨. Task 목록은 여전히 3개로, 고아 Task가 생성되지 않음을 확인 — `file_validator.validate_not_binary`(T064)가 CodeUploadService(T069)의 검증 파이프라인에서 정상 호출됨을 실증.

## 변경 파일
없음 (수동 검증만 수행)

## TDD 결과
해당 없음 — 수동 브라우저 테스트 단계. 동일 시나리오는 이미 `backend/tests/integration/test_tasks_api.py`의 자동화 테스트로도 커버됨.

## 기술 결정
없음

## 비고
없음
