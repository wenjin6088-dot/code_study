# TASK-126. practice-service 구현

## 상태
완료

## 날짜
2026-11-19

## 작업 요약
프론트엔드가 실습 문제 API를 호출할 때 쓰는 얇은 함수 모음(axios 래퍼)을 만들었습니다. `document-service.ts`(T106)와 똑같은 구조입니다: TypeScript 타입 정의(`PracticeProblem`, `TaskPracticeResponse`)와 `getTaskPractice(taskId)` 함수 하나를 제공합니다.

## 변경 파일
- `frontend/src/services/practice-service.ts` (신규)
- `frontend/tests/unit/services/practice-service.test.ts` (신규)

## TDD 결과
- RED: 테스트 먼저 작성 → 모듈이 없어 실패.
- GREEN: 구현 → 1개 테스트 통과(올바른 엔드포인트 호출 및 응답 그대로 반환 확인).
- 커밋: 아직 생성하지 않음
- 테스트 커버리지: 신규 테스트 1개 통과

## 기술 결정
없음(기존 `document-service.ts` 패턴을 그대로 복사해 사용).

## 비고
없음.
