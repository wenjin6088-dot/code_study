# TASK-107. DocumentViewer 로딩 상태 + 진행률 표시

## 상태
완료

## 날짜
2026-11-18

## 작업 요약
`DocumentViewer`(T105)에 상태별 분기를 추가했다. `getTaskDocumentStatus`를 TanStack Query로 폴링하며 상태에 따라 아래처럼 렌더링한다.

- **초기 로딩**(`statusQuery.isLoading`): `role="status"` + "문서 상태를 확인하는 중..." 표시.
- **조회 실패**(`statusQuery.isError`, 404 등): "문서를 찾을 수 없습니다" 표시.
- **생성 실패**(`status === 'failed'`): `role="alert"` + "문서 생성에 실패했습니다." + 백엔드가 준 `error` 메시지(있는 경우) 표시.
- **생성 중**(`status === 'pending' | 'in_progress'`): `role="status"` + "문서를 생성하는 중입니다..." + `estimated_seconds_remaining`이 있으면 "예상 남은 시간: N초" 표시(FR-084).
- **완료**(`status === 'completed'`): 이때만 `getTaskDocument`/`getTaskCode`를 호출(`enabled: isCompleted`)해 실제 콘텐츠를 가져오고, 둘 다 준비되면 CodePanel+ExplanationPanel을 렌더링.

폴링은 `useQuery`의 `refetchInterval`에 `(query) => status가 pending/in_progress면 3000ms, 아니면 false`인 콜백을 전달해 구현했다. `completed`/`failed`가 되면 자동으로 멈춘다. TanStack Query의 쿼리 캐시가 `taskId` 기준으로 유지되므로, 사용자가 다른 탭/페이지로 이동했다가 돌아와도 마지막 상태가 그대로 보인다(FR-085, 별도 로컬 상태 없이 캐시로 자연히 해결).

## 변경 파일
- `frontend/src/components/document/DocumentViewer.tsx` (T105에서 생성한 파일에 로딩/진행률 분기 포함, 추가 파일 없음)
- `frontend/tests/unit/components/document/DocumentViewer.test.tsx` (T105에서 생성, 로딩/진행률/실패 케이스 포함)
- `specs/001-ai-code-learning-platform/tasks.md` (T107 `[X]` 체크)
- `docs/task-reports/TASK-107-로딩상태-진행률표시.md` (본 보고서)

## TDD 결과
- git 저장소가 아니므로 RED/GREEN 커밋 없음. T105와 같은 테스트 파일(`DocumentViewer.test.tsx`)에 로딩 상태(`new Promise(() => {})`로 영구 pending 모킹), 진행률(`estimated_seconds_remaining: 37` → `/37/` 텍스트 검증), 실패(`status: 'failed'` → 에러 메시지 검증) 3개 케이스를 포함해 작성 → RED 확인 → 구현 후 통과.
- 전체 회귀: `npm test` 207개 테스트 통과.

## 기술 결정
1. **상태 조회(`/document/status`)와 콘텐츠 조회(`/document`)를 분리된 쿼리로 유지**: 진행 중에는 가벼운 상태 엔드포인트만 짧은 간격으로 폴링하고, 완료된 뒤에야 무거운 `content`(7챕터 전체)와 `getTaskCode`(소스 전체)를 한 번만 가져오도록 해 불필요한 폴링 비용을 줄였다.
2. **`refetchInterval`에 콜백 함수를 사용**: TanStack Query v5 방식으로 `query.state.data?.status`를 읽어 매 틱마다 최신 상태로 폴링 여부를 재평가하므로, 상태가 바뀌는 즉시(다음 틱부터) 폴링이 멈춘다.
3. **로딩/진행률/실패 메시지를 한국어로 직접 노출**: 기존 코드베이스(`TaskDetail.tsx`의 "작업을 찾을 수 없습니다" 등)와 동일하게 한국어 사용자 메시지를 그대로 둬 일관성을 유지했다.

## 비고
- "업로드 → Generating... 상태가 예상 시간과 함께 표시되는지"의 실제 체감 확인은 T109(수동 브라우저 테스트) 범위이며 이번 작업 밖이다.
