# TASK-105. DocumentViewer 컴포넌트 (2단 레이아웃 + 동기 스크롤)

## 상태
완료

## 날짜
2026-11-18

## 작업 요약
`frontend/src/components/document/DocumentViewer.tsx`를 구현했다. `taskId`만 받아 CodePanel(좌)과 ExplanationPanel(우)을 `display: flex` 2단 레이아웃으로 조합하고, 동기 스크롤 배선과 로딩/상태 폴링(T106/T107)을 모두 이 컴포넌트에서 담당한다.

**동기 스크롤(한 방향)**: 순수 함수 `findExplanationForLine`을 `frontend/src/components/document/syncScroll.ts`로 분리했다 — "스크롤 위치(파일+줄 번호) → chapter4 explanations 중 매칭되는 인덱스"만 계산하는 함수로, React/DOM에 의존하지 않아 독립적으로 단위 테스트했다. CodePanel이 `onVisibleLineChange(filePath, line)`을 호출하면 DocumentViewer가 이 함수로 매칭되는 설명 인덱스를 찾고, 매칭되면(`index >= 0`) `activeChapter`를 `'chapter4'`로 전환하고 `activeExplanationIndex`를 설정해 ExplanationPanel/Chapter4로 전달한다. 반대 방향(설명 패널 → 코드 패널)은 명세(T112 문구)상 요구되지 않아 구현하지 않았다.

활성 설명 항목이 있으면 그 `{file, line_start, line_end}`를 `highlightRange`로 CodePanel에 다시 전달해, 코드 패널에서도 해당 줄 구간이 하이라이트되도록 양쪽을 연결했다.

## 변경 파일
- `frontend/src/components/document/DocumentViewer.tsx` (신규 생성)
- `frontend/src/components/document/syncScroll.ts` (신규 생성, 순수 함수)
- `frontend/tests/unit/components/document/DocumentViewer.test.tsx` (신규 생성)
- `frontend/tests/unit/components/document/syncScroll.test.ts` (신규 생성)
- `specs/001-ai-code-learning-platform/tasks.md` (T105 `[X]` 체크)
- `docs/task-reports/TASK-105-DocumentViewer-컴포넌트.md` (본 보고서)

## TDD 결과
- git 저장소가 아니므로 RED/GREEN 커밋 없음. `syncScroll.test.ts`(경계값 포함 6개 케이스)와 `DocumentViewer.test.tsx`(로딩/진행률/실패/완료 렌더링/스크롤 연동 5개 케이스)를 먼저 작성 → `npx vitest run`에서 모듈 미존재로 RED 확인 → 구현 후 전체 통과(GREEN).
- `DocumentViewer.test.tsx`는 `CodePanel`/`ExplanationPanel`을 `vi.mock`으로 교체해, 두 컴포넌트 자체의 렌더링(이미 각자 단위 테스트로 커버됨)이 아니라 DocumentViewer의 데이터 페칭·배선 책임만 검증했다.
- 전체 회귀: `npm test` 207개 테스트, `npx tsc --noEmit` 통과.

## 기술 결정
1. **스크롤 매칭 로직을 순수 함수로 분리(CLAUDE.md 지침 준수)**: `syncScroll.ts`의 `findExplanationForLine`은 배열과 원시값만 받고 돌려주는 순수 함수라, CodePanel/ExplanationPanel을 렌더링하지 않고도 경계값(구간의 시작/끝 줄, 파일 불일치, 매칭 없음)을 빠르고 명확하게 테스트할 수 있다.
2. **"매칭 실패 시 챕터를 바꾸지 않음"**: 스크롤 중 일시적으로 chapter4 구간 밖(예: import문, 공백 줄)을 지나갈 때마다 활성 챕터가 깜빡이지 않도록, 매칭된 경우에만 `setActiveChapter('chapter4')`를 호출한다.
3. **2단 레이아웃은 인라인 스타일(`flex`)로 최소 구현**: 프로젝트에 Tailwind가 설정돼 있지만, 기존 컴포넌트(TaskCard, FileUpload)들이 과한 스타일링을 하지 않는 관례를 따라 레이아웃에 필요한 최소 속성만 인라인으로 부여했다.

## 비고
- 2번째 요구사항(T112 "스크롤 코드 패널 → 설명 패널이 해당 섹션으로 스크롤되는지")에 대한 실제 브라우저 체감 검증은 수동 테스트 범위이며 이번 작업 밖이다.
