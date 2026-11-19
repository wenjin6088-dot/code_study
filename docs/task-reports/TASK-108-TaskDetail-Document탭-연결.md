# TASK-108. TaskDetail 페이지의 Document 탭에 DocumentViewer 연결

## 상태
완료

## 날짜
2026-11-18

## 작업 요약
`frontend/src/pages/TaskDetail.tsx`의 Document 탭 placeholder(`<p>문서 탭 (준비 중)</p>`)를 실제 `DocumentViewer`로 교체했다.

```tsx
{activeTab === 'Document' && <DocumentViewer taskId={taskId as string} />}
```

`taskId`는 이미 `useParams`로 읽어 `getTask(taskId as string)` 호출에 쓰이던 값을 그대로 재사용했다(이 분기는 `task` 로딩이 끝난 성공 렌더링 경로 안에 있으므로 `taskId`가 반드시 존재).

## 변경 파일
- `frontend/src/pages/TaskDetail.tsx` (import 추가 + Document 탭 분기 교체)
- `frontend/tests/integration/pages/TaskDetail.test.tsx` (기존 파일 확장: `@/components/document/DocumentViewer` 모킹 추가 + 새 테스트 1건)
- `specs/001-ai-code-learning-platform/tasks.md` (T108 `[X]` 체크)
- `docs/task-reports/TASK-108-TaskDetail-Document탭-연결.md` (본 보고서)

## TDD 결과
- git 저장소가 아니므로 RED/GREEN 커밋 없음. 기존 `TaskDetail.test.tsx`(T083에서 작성된 9개 테스트)를 깨지 않는 것을 최우선으로, `DocumentViewer`를 `vi.mock`으로 교체한 뒤 "Document 탭에 taskId와 함께 DocumentViewer가 렌더링되는지" 검증하는 테스트 1건을 추가 → 구현 전 `screen.getByTestId('document-viewer')`를 찾지 못해 RED 확인 → 구현 후 해당 파일 10개 테스트 전부 통과(GREEN).
- `DocumentViewer`를 모킹한 이유: 그 자체의 데이터 페칭/렌더링은 T105~T107의 전용 단위 테스트가 이미 검증하므로, TaskDetail 통합 테스트는 "탭 전환에 맞춰 올바른 컴포넌트가 올바른 prop으로 연결되는지"만 책임지도록 범위를 좁혔다(기존에 `getTask`만 모킹하던 이 테스트 파일에 `document-service`/`task-service.getTaskCode` 등 추가 모킹 부담을 지우지 않기 위함).
- 전체 회귀: `npm test` 207개 테스트, `npx tsc --noEmit`, `npm run lint`(기존에 있던 `vite.config.ts`의 triple-slash 경고/`button.tsx` 등 fast-refresh 경고 외 신규 에러 없음) 모두 확인.

## 기술 결정
- 기존 import 스타일(`'../services/task-service'` 상대 경로)을 그대로 따라 `'../components/document/DocumentViewer'`로 import해, 파일 내 import 스타일을 일관되게 유지했다.

## 비고
- 백엔드 T094~T098이 완료되면, 이 화면을 실제로 띄워 Generating → 완료 전환과 동기 스크롤을 눈으로 확인하는 작업은 T109~T114(수동 브라우저 테스트)가 담당하며 이번 작업 범위에 포함하지 않았다.
