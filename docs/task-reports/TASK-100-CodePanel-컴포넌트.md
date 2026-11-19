# TASK-100. CodePanel 컴포넌트 (문법 강조)

## 상태
완료

## 날짜
2026-11-18

## 작업 요약
`frontend/src/components/document/CodePanel.tsx`를 구현했다. `getTaskCode(taskId)`가 반환하는 `TaskCodeFile[]`을 받아 Monaco Editor로 읽기 전용 렌더링하며, T099의 `getMonacoLanguage`로 확장자 기반 언어 하이라이팅을 적용한다.

- **Props**: `files: TaskCodeFile[]`, `activeFilePath: string`(제어 컴포넌트, DocumentViewer가 상태 소유), `onActiveFileChange?`, `onVisibleLineChange?: (filePath, lineNumber) => void`, `highlightRange?: { file, lineStart, lineEnd } | null`.
- 파일이 2개 이상일 때만 `role="tablist"` + `role="tab"` 파일 탭을 렌더링(TaskCard 관례와 동일하게 시맨틱 HTML + ARIA role로 테스트 가능하게 구성).
- `onMount`에서 `editor.onDidScrollChange`를 등록해, 스크롤 시 `editor.getVisibleRanges()[0].startLineNumber`를 `onVisibleLineChange(activeFilePath, line)`으로 보고한다 — T105 동기 스크롤의 발신측.
- `highlightRange`가 현재 활성 파일과 일치하면 `editor.revealLineInCenter`로 스크롤하고 `editor.deltaDecorations`로 해당 줄 구간을 하이라이트하며, 불일치/해제 시 데코레이션을 제거한다.

## 변경 파일
- `frontend/src/components/document/CodePanel.tsx` (신규 생성)
- `frontend/tests/unit/components/document/CodePanel.test.tsx` (신규 생성)
- `specs/001-ai-code-learning-platform/tasks.md` (T100 `[X]` 체크)
- `docs/task-reports/TASK-100-CodePanel-컴포넌트.md` (본 보고서)

## TDD 결과
- git 저장소가 아니므로 RED/GREEN 커밋 없음. 테스트를 먼저 작성 후 `npx vitest run`으로 `Failed to resolve import "@/components/document/CodePanel"`(RED) 확인, 구현 후 5개 테스트 전부 통과(GREEN) 확인.
- 전체 회귀: `npm test` 207개 테스트 통과, `npx tsc --noEmit` 통과, `npm run lint`에 새 경고/에러 없음.

## 기술 결정
1. **`@monaco-editor/react`를 테스트에서 모킹**: jsdom은 실제 Monaco를 실행할 수 없으므로, `vi.mock('@monaco-editor/react', ...)` + `vi.hoisted`로 만든 가짜 editor 객체(`onDidScrollChange`, `getVisibleRanges`, `revealLineInCenter`, `deltaDecorations`)를 `onMount`에 주입해 CodePanel이 Monaco API를 올바르게 호출하는지만 검증했다. 이는 CodePanel의 "최소 구현"이 Monaco의 실제 렌더링이 아니라 그 위에 얹은 래퍼 로직이기 때문.
2. **`activeFilePath`를 CodePanel이 소유하지 않고 제어 prop으로 받음**: TaskDetail의 탭 상태 관례와 동일하게, 상태는 부모(DocumentViewer)가 갖고 CodePanel은 렌더링과 이벤트 발신만 담당하게 해 단일 책임을 유지했다.
3. **`Editor`에 `key={filePath}`를 부여**: 파일 전환 시 Monaco 인스턴스를 새로 마운트시켜, `onDidScrollChange` 콜백이 이전 파일의 클로저를 참조하는 문제를 피했다.
4. **데코레이션/스크롤 호출에 옵셔널 체이닝(`editor.revealLineInCenter?.`)을 사용**: 모든 Monaco 버전/모킹 환경에서 해당 메서드가 보장되지 않을 수 있어 방어적으로 처리했다(과한 방어 코드를 피하되, 외부 라이브러리 API 경계에서는 안전장치를 둠).

## 비고
- 실제 문법 강조/실시간 스크롤 체감은 수동 브라우저 테스트(T112) 범위이며 이번 작업 범위 밖이다.
