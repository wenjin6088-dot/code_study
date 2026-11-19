# TASK-104. Chapter4LineByLine 컴포넌트

## 상태
완료

## 날짜
2026-11-18

## 작업 요약
`frontend/src/components/document/chapters/Chapter4.tsx`에 `Chapter4LineByLine`을 구현했다. `DocumentChapter4`(`{ title, explanations: Explanation[] }`)의 각 항목을 순서대로 `<ol><li>`로 렌더링하며, 파일명/줄 범위/코드/동작 설명/문법 분해/비유/대안 예시/주의사항을 모두 노출한다.

T105 동기 스크롤의 수신측 역할을 겸한다: `activeIndex?: number` prop을 받아 해당 `<li>`에 `aria-current="true"`를 부여하고, `activeIndex`가 바뀌면 `useEffect`로 그 항목을 `scrollIntoView({ block: 'nearest' })`한다.

## 변경 파일
- `frontend/src/components/document/chapters/Chapter4.tsx` (신규 생성)
- `frontend/tests/unit/components/document/chapters/Chapter4.test.tsx` (신규 생성)
- `specs/001-ai-code-learning-platform/tasks.md` (T104 `[X]` 체크)
- `docs/task-reports/TASK-104-Chapter4LineByLine-컴포넌트.md` (본 보고서)

## TDD 결과
- git 저장소가 아니므로 RED/GREEN 커밋 없음. 테스트 먼저 작성(제목/항목 렌더링/`aria-current`/`scrollIntoView` 호출 검증, `Element.prototype.scrollIntoView`를 테스트에서 `vi.fn()`으로 교체) → RED 확인 → 구현 후 4개 테스트 통과.
- 이후 ExplanationPanel 통합 테스트(T101)에서 jsdom에 `scrollIntoView`가 전혀 정의되지 않은 환경에서 `TypeError`가 1건 발생 → `itemRefs.current[activeIndex]?.scrollIntoView?.(...)`로 메서드 자체에도 옵셔널 체이닝을 추가해 수정, 전체 재통과.

## 기술 결정
1. **스크롤 로직을 Chapter4 내부에 캡슐화**: ExplanationPanel이나 DocumentViewer가 ref를 직접 다루지 않고, "활성 인덱스가 바뀌면 스크롤"이라는 책임을 항목을 렌더링하는 Chapter4 자신이 지도록 했다 — 참조(ref) 관리가 렌더링 로직과 분리되지 않게 하기 위함.
2. **`aria-current="true"`로 활성 항목을 표시**: 불필요한 커스텀 class/style 대신 시맨틱 속성을 사용해 접근성과 테스트 용이성을 동시에 확보했다(값이 없을 때는 속성 자체를 생략).
3. **`scrollIntoView` 호출에 옵셔널 체이닝 2단 적용**: 요소 자체의 존재(`?.`)뿐 아니라 메서드의 존재(`?.scrollIntoView?.`)까지 방어해, `scrollIntoView`가 구현되지 않은 테스트/구형 환경에서도 예외 없이 동작하게 했다.

## 비고
- "한 방향"(코드 스크롤 → 설명 패널 강조) 요구사항에 맞춰, Chapter4는 외부에서 `activeIndex`를 받기만 하고 스스로 코드 패널 스크롤을 유발하지 않는다.
