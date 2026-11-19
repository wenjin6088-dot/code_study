# TASK-102. Chapter1Summary 컴포넌트

## 상태
완료

## 날짜
2026-11-18

## 작업 요약
`frontend/src/components/document/chapters/Chapter1.tsx`에 `Chapter1Summary`를 구현했다. `DocumentChapter1`(`{ title, summary }`)을 받아 `<section>` + `<h2>`(제목) + `<p>`(한 문장 요약)만 렌더링하는 가장 단순한 챕터 컴포넌트다.

## 변경 파일
- `frontend/src/components/document/chapters/Chapter1.tsx` (신규 생성)
- `frontend/tests/unit/components/document/chapters/Chapter1.test.tsx` (신규 생성)
- `specs/001-ai-code-learning-platform/tasks.md` (T102 `[X]` 체크)
- `docs/task-reports/TASK-102-Chapter1Summary-컴포넌트.md` (본 보고서)

## TDD 결과
- git 저장소가 아니므로 RED/GREEN 커밋 없음. 테스트 먼저 작성 → RED(`Failed to resolve import`) 확인 → 구현 후 2개 테스트 통과(GREEN).

## 기술 결정
- 제목을 `<h2 role="heading">`(시맨틱 `h2`로 암묵적 role)으로 렌더링해 테스트가 `getByRole('heading', { name })`으로 접근 가능하게 했다. `<section aria-label>`로 챕터 영역을 구분해 추후 챕터 간 스크롤/포커스 이동에 쓸 수 있는 앵커를 남겨 두었다.

## 비고
- 테스트/본문 모두에 과한 스타일링(CSS)을 추가하지 않았다 — CLAUDE.md의 "과한 스타일링은 하지 않는다" 지침을 따름.
