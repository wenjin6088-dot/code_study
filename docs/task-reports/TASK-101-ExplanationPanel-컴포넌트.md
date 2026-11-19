# TASK-101. ExplanationPanel 컴포넌트 (챕터 네비게이션)

## 상태
완료

## 날짜
2026-11-18

## 작업 요약
`frontend/src/components/document/ExplanationPanel.tsx`를 구현했다. `DocumentContent` 전체와 현재 활성 챕터를 받아 7개 챕터 탭(`role="tablist"` + `role="tab"`, TaskCard/TaskDetail 관례와 동일)을 렌더링하고, 활성 챕터에 맞는 본문을 `role="tabpanel"` 안에 보여준다.

- chapter1/2/4는 각각 T102/T103/T104에서 만든 `Chapter1Summary`/`Chapter2Prerequisites`/`Chapter4LineByLine`에 위임.
- chapter3(흐름도 + 파일별 설명), chapter5(실행 단계), chapter6(핵심 개념), chapter7(흔한 실수)은 전용 컴포넌트 작업이 tasks.md에 없으므로, 과한 추상화를 피해 ExplanationPanel 안에서 최소한의 시맨틱 마크업(`<section>`, `<h2>`, `<ul>/<ol>`)으로 직접 렌더링했다.
- `activeExplanationIndex` prop을 받아 chapter4가 활성일 때만 `Chapter4LineByLine`에 전달 — T105 동기 스크롤의 수신측 배선.

## 변경 파일
- `frontend/src/components/document/ExplanationPanel.tsx` (신규 생성)
- `frontend/tests/unit/components/document/ExplanationPanel.test.tsx` (신규 생성)
- `specs/001-ai-code-learning-platform/tasks.md` (T101 `[X]` 체크)
- `docs/task-reports/TASK-101-ExplanationPanel-컴포넌트.md` (본 보고서)

## TDD 결과
- git 저장소가 아니므로 RED/GREEN 커밋 없음. 테스트 먼저 작성 → `npx vitest run`에서 모듈 미존재로 RED 확인 → 구현 후 10개 테스트 전부 통과(GREEN). 구현 1차 버전에서 `Chapter4LineByLine`의 `scrollIntoView` 호출이 jsdom에 없어 1건 실패했고, T104의 `?.scrollIntoView?.()` 옵셔널 체이닝으로 수정 후 전체 통과.
- 전체 회귀: `npm test` 207개 테스트, `npx tsc --noEmit` 통과.

## 기술 결정
1. **탭 라벨을 각 챕터의 `title` 필드로 사용**: 백엔드 AI가 생성하는 챕터 제목을 그대로 노출해, 하드코딩된 한국어/영어 라벨과 실제 생성된 문서 제목이 불일치할 가능성을 없앴다(`DocumentContent.chapter{N}.title`이 계약에 항상 존재).
2. **chapter3/5/6/7을 별도 컴포넌트로 분리하지 않음**: tasks.md T102~T104가 명시적으로 chapter1/2/4만 지정했고, 나머지 챕터는 재사용되는 복잡한 UI 패턴(카드 리스트 수준)이 아니라 단순 목록이라 ExplanationPanel에 인라인으로 두는 것이 YAGNI 원칙에 맞다고 판단했다.
3. **`document` prop을 `doc`으로 구조분해 별칭**: 전역 `window.document`와의 섀도잉을 피하기 위함.

## 비고
- chapter4 외 챕터에서는 `activeExplanationIndex`가 전달되지 않아(undefined) 하이라이트가 발생하지 않는다 — 명세가 chapter4에 한정된 동기 스크롤만 요구하므로 의도된 동작이다.
