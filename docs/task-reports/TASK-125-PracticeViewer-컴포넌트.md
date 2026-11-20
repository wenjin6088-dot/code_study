# TASK-125. PracticeViewer 컴포넌트

## 상태
완료

## 날짜
2026-11-19

## 작업 요약
실습 탭 전체를 담당하는 컴포넌트입니다. TanStack Query로 `GET /tasks/{task_id}/practice`를 호출해 문제 5개를 가져오고, 각 문제를 `ProblemCard`로 감싸면서 그 안에 `HintReveal`과 `SolutionDisplay`를 끼워 넣습니다.

상태별 화면:
- 불러오는 중: `role="status"` 로딩 표시
- 아직 생성 중(`status: "pending"`): "실습 문제를 생성하는 중입니다..." 안내
- 실패: "실습 문제를 불러오지 못했습니다" 안내
- 완료: 문제 5개를 번호 순서대로 표시

## 변경 파일
- `frontend/src/components/practice/PracticeViewer.tsx` (신규)
- `frontend/tests/unit/components/practice/PracticeViewer.test.tsx` (신규)

## TDD 결과
- RED: 테스트 먼저 작성 → 컴포넌트가 없어 실패.
- GREEN: `DocumentViewer`(T105)의 데이터 패칭 패턴(TanStack Query `useQuery`)을 재사용해 구현 → 4개 테스트 통과(로딩/생성 중/5개 전부 표시/에러).
- 커밋: 아직 생성하지 않음
- 테스트 커버리지: 신규 테스트 4개 전부 통과

## 기술 결정
문서 생성(T105 DocumentViewer)과 달리 "진행 중 자동 재조회(polling)"는 넣지 않았습니다. 실습 문제 생성은 문서 생성이 끝난 뒤에 트리거되고(T119) 데이터 모델에 진행률/ETA 정보가 없어서, 문서처럼 "몇 초 남았습니다"를 보여줄 방법이 없기 때문입니다. 사용자가 탭을 다시 열면 React Query가 새로 조회하므로, 당장은 수동 새로고침으로도 충분하다고 판단했습니다(YAGNI) — 다만 사용자가 Practice 탭에 머무는 동안 생성이 끝나는 걸 자동으로 감지하지 못한다는 한계가 있습니다. 더 나은 사용자 경험을 위해서는 추후 폴링(polling)을 추가하는 것도 고려할 수 있습니다.

## 비고
없음.
