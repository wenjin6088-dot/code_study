# TASK-127. TaskDetail 페이지 Practice 탭 연결

## 상태
완료

## 날짜
2026-11-19

## 작업 요약
Task 상세 페이지의 3개 탭(Document/Practice/Q&A) 중 "준비 중" 플레이스홀더였던 Practice 탭에 실제로 `PracticeViewer`(T125)를 연결했습니다. Document 탭이 `DocumentViewer`에 `taskId`를 넘기는 것과 똑같은 방식으로, Practice 탭도 `taskId`를 넘깁니다.

## 변경 파일
- `frontend/src/pages/TaskDetail.tsx` (수정: import 추가, `<p>실습 탭 (준비 중)</p>` → `<PracticeViewer taskId={...} />` 로 교체)
- `frontend/tests/integration/pages/TaskDetail.test.tsx` (수정: `PracticeViewer`를 모킹하고, Practice 탭 클릭 시 올바른 `taskId`로 렌더링되는지 확인하는 테스트 1개 추가)

## TDD 결과
- RED: 새 테스트를 추가 → 아직 플레이스홀더 문구만 있어서 `practice-viewer` 테스트 id를 찾지 못해 실패.
- GREEN: `TaskDetail.tsx`를 수정 → 추가한 테스트 포함 기존 10개 테스트 전부 통과(총 11개).
- REFACTOR: 불필요(한 줄짜리 교체).
- 커밋: 아직 생성하지 않음
- 테스트 커버리지: `TaskDetail.test.tsx` 11개 전부 통과, 프론트엔드 전체(224개)·백엔드 전체(413개) 회귀 테스트 모두 통과

## 기술 결정
없음.

## 비고
이 작업으로 Phase 7(T115~T127)의 백엔드·프론트엔드 구현이 모두 끝났습니다. 남은 것은 브라우저 수동 테스트(T128~T131)이며, 이는 프로젝트 constitution에 따라 진행 전 사용자 승인이 필요합니다.
