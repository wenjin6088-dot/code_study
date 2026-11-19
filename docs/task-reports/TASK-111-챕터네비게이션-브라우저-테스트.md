# TASK-111. 챕터 네비게이션 브라우저 수동 테스트

## 상태
완료

## 날짜
2026-11-18

## 작업 요약
TASK-110과 같은 세션에서, 7개 챕터 탭을 클릭하면 선택 상태와 내용 패널이 함께 전환되는지 확인했습니다. "코드 한 줄씩 살펴보기"(기본 선택)에서 "사전 지식"(Prerequisites Knowledge) 탭을 클릭한 결과를 접근성 스냅샷으로 캡처했습니다.

결과: 클릭한 탭에 `[selected]`(`aria-selected="true"`)가 옮겨가고, 이전 탭의 Line-by-Line 목록이 사라지며 Chapter 2의 개념 카드 목록으로 패널 내용이 정확히 교체됐습니다. 탭 간 전환 시 코드 패널(Monaco)은 그대로 유지됐습니다.

## 변경 파일
없음 (수동 검증만 수행)

## TDD 결과
해당 없음 — 수동 브라우저 테스트 단계. `ExplanationPanel`의 탭 전환 로직은 `frontend/tests/unit/components/document/ExplanationPanel.test.tsx`(T101)로 이미 커버됨.

## 기술 결정
없음

## 비고
TASK-113(Chapter 2 개념 카드)이 이 테스트에서 전환한 화면을 그대로 이어서 검증했습니다.
