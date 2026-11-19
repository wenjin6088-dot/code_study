# TASK-103. Chapter2Prerequisites 컴포넌트 (개념 카드)

## 상태
완료

## 날짜
2026-11-18

## 작업 요약
`frontend/src/components/document/chapters/Chapter2.tsx`에 `Chapter2Prerequisites`를 구현했다. `DocumentChapter2`(`{ title, concepts: Concept[] }`, 최대 5개)를 받아 챕터 제목과 개념별 카드 리스트(`<ul><li>`)를 렌더링한다. 각 카드는 `name`(`<h3>`), `explanation`, `analogy`, `example`(`<pre>`로 코드 서식 유지), `use_cases`를 모두 노출한다.

## 변경 파일
- `frontend/src/components/document/chapters/Chapter2.tsx` (신규 생성)
- `frontend/tests/unit/components/document/chapters/Chapter2.test.tsx` (신규 생성)
- `specs/001-ai-code-learning-platform/tasks.md` (T103 `[X]` 체크)
- `docs/task-reports/TASK-103-Chapter2Prerequisites-컴포넌트.md` (본 보고서)

## TDD 결과
- git 저장소가 아니므로 RED/GREEN 커밋 없음. 테스트 먼저 작성(2개 개념으로 카드 렌더링 검증) → RED 확인 → 구현 후 2개 테스트 통과(GREEN).

## 기술 결정
1. **개수 상한(최대 5개)을 컴포넌트에서 강제하지 않음**: 백엔드 `_CHAPTER_RULES`(`MAX_PREREQUISITE_CONCEPTS`)가 이미 생성 시점에 강제하는 불변식이라, 프런트는 받은 배열을 그대로 렌더링하는 것으로 충분하다고 판단(동일 검증을 두 곳에 중복시키지 않음, YAGNI).
2. **`key`로 `concept.name` 사용**: 백엔드 계약상 각 개념 이름이 한 챕터 내에서 고유하다고 가정(테스트 데이터로도 확인). 인덱스보다 안정적인 키.

## 비고
- "5개 개념 카드 + 비유 표시" 수동 확인은 T113(수동 브라우저 테스트) 범위이며 이번 작업 밖이다.
