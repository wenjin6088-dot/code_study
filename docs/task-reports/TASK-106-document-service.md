# TASK-106. document-service (문서 조회 + 상태 폴링)

## 상태
완료

## 날짜
2026-11-18

## 작업 요약
`frontend/src/services/document-service.ts`를 `task-service.ts`/`project-service.ts`와 동일한 패턴(공유 `apiClient`를 감싼 얇은 axios 래퍼 함수 + 타입)으로 구현했다. 백엔드 에이전트(T097/T098)가 구현 중인 계약에 맞춰 두 함수를 제공한다.

- `getTaskDocument(taskId)` → `GET /tasks/{taskId}/document` → `{ task_id, status, content: DocumentContent | null, error: string | null, generated_at: string | null }`
- `getTaskDocumentStatus(taskId)` → `GET /tasks/{taskId}/document/status` → `{ status, error, estimated_seconds_remaining }`

`DocumentContent`와 7개 챕터 각각의 타입(`DocumentChapter1`~`DocumentChapter7`, `DocumentConcept`, `DocumentExplanation`, `DocumentStep`, `DocumentCoreConcept`, `DocumentMistake`)은 `backend/src/services/ai/prompts.py`의 `_DOCUMENT_SCHEMA_EXAMPLE`을 1:1로 TypeScript 인터페이스로 옮긴 것이며, CodePanel/ExplanationPanel/Chapter* 컴포넌트 전체가 이 파일의 타입을 import해서 쓴다(Task 타입이 `task-service.ts`에 있는 것과 동일한 구조).

404(task 없음/소유자 아님) 등 에러는 별도 처리를 추가하지 않았다 — 기존 `apiClient`의 응답 인터셉터가 `error.response.data.error.message`를 꺼내 `Error`로 던지는 방식을 그대로 재사용하며, 이는 task-service.ts/project-service.ts와 동일한 전파 방식이다.

## 변경 파일
- `frontend/src/services/document-service.ts` (신규 생성)
- `frontend/tests/unit/services/document-service.test.ts` (신규 생성)
- `specs/001-ai-code-learning-platform/tasks.md` (T106 `[X]` 체크)
- `docs/task-reports/TASK-106-document-service.md` (본 보고서)

## TDD 결과
- git 저장소가 아니므로 RED/GREEN 커밋 없음. `task-service.test.ts`의 `vi.mock('@/services/api-client', ...)` 모킹 패턴을 그대로 따라 테스트를 먼저 작성(요청 URL과 응답 데이터 전달만 검증, 실제 네트워크 호출 없음) → 구현 전 import 실패로 RED 확인 → 구현 후 2개 테스트 통과(GREEN).
- 전체 회귀: `npm test` 207개 테스트, `npx tsc --noEmit` 통과.

## 기술 결정
1. **폴링(`refetchInterval`)은 이 파일이 아니라 DocumentViewer(T105/T107)에 둠**: 이 파일은 순수 axios 래퍼만 제공하고, TanStack Query의 `useQuery`/`refetchInterval` 사용은 `getTask`를 쓰는 `TaskDetail.tsx`처럼 호출부(DocumentViewer)의 책임으로 분리했다 — 서비스 레이어와 쿼리/캐싱 레이어의 경계를 기존 코드베이스 관례와 동일하게 유지.
2. **`/document`와 `/document/status` 두 엔드포인트를 모두 노출**: `/document`만으로는 `estimated_seconds_remaining`을 얻을 수 없어(계약상 `/document/status`에만 존재) FR-084(예상 남은 시간 표시)를 만족시키려면 두 호출이 모두 필요하다고 판단했다.
3. **타입을 백엔드 스키마 예시와 1:1로 유지**: 필드명(`snake_case`)을 그대로 TypeScript에 옮겨 백엔드-프런트 간 변환 레이어 없이 그대로 소비하도록 했다 — 추가 매핑 코드가 없어 계약 변경 시 diff가 바로 드러난다.

## 비고
- 백엔드 T094~T098이 동시 구현 중이므로, 실제 서버 응답으로의 통합 확인(E2E)은 두 에이전트의 작업이 모두 끝난 뒤 별도로 필요하다. 이번 작업은 계약 문서에 기술된 응답 모양을 기준으로 단위 테스트만 수행했다.
