# TASK-099. Monaco Editor 설치 및 설정

## 상태
완료

## 날짜
2026-11-18

## 작업 요약
`@monaco-editor/react@^4.6.0`은 이미 `frontend/package.json`과 `node_modules`에 설치되어 있어, 이번 작업은 "설치"가 아니라 "설정"에 집중했다. CodePanel(T100)에서 재사용할 공통 설정을 `frontend/src/components/document/monacoConfig.ts`로 분리했다:
- `getMonacoLanguage(extension: string | null): string` — `getTaskCode`가 반환하는 `TaskCodeFile.file_extension`(예: `.py`, `.ts`)을 Monaco 언어 id(`python`, `typescript` 등)로 매핑. 대소문자 무시, 매핑 없는 확장자/`null`은 `plaintext`로 안전하게 폴백.
- 읽기 전용 모드와 줄 번호 표시는 T100(CodePanel)에서 `<Editor options={{ readOnly: true, lineNumbers: 'on' }}>`로 적용해, 실제로 에디터가 로드되고 언어 하이라이팅이 동작하는 것을 CodePanel 단위 테스트에서 확인했다(Monaco 모듈을 모킹해 전달된 `language`/`value` prop을 검증).

## 변경 파일
- `frontend/src/components/document/monacoConfig.ts` (신규 생성)
- `frontend/tests/unit/components/document/monacoConfig.test.ts` (신규 생성)
- `specs/001-ai-code-learning-platform/tasks.md` (T099 `[X]` 체크)
- `docs/task-reports/TASK-099-Monaco-Editor-설정.md` (본 보고서)

## TDD 결과
- git 저장소가 아니므로 RED/GREEN 커밋은 생성하지 않음. `monacoConfig.test.ts`를 먼저 작성한 뒤 `npx vitest run`으로 `Failed to resolve import "@/components/document/monacoConfig"` 에러(RED)를 확인했고, `monacoConfig.ts` 구현 후 4개 테스트 전부 통과(GREEN)를 확인했다.
- 최종적으로 `frontend`에서 `npm test`(vitest run) 전체 207개 테스트, `npx tsc --noEmit` 통과.

## 기술 결정
1. jsdom 환경에서는 실제 Monaco 워커/CDN 로딩이 불가능하므로, "실제로 로드되는지" 확인은 CodePanel 단위 테스트에서 `@monaco-editor/react`를 모킹해 `Editor`에 전달되는 `language`/`value` prop을 검증하는 방식으로 대체했다. 브라우저에서의 실제 렌더링 확인은 범위 밖의 수동 테스트(T109~T114)가 담당한다.
2. 언어 매핑 테이블은 현재 프로젝트가 지원하는 업로드 언어(Python/JS/TS 등 흔한 백엔드/프론트엔드 언어) 위주로 최소 구성했고, 매핑 누락 시 에디터가 깨지지 않도록 `plaintext` 폴백을 기본으로 삼았다.

## 비고
- CodePanel(T100)이 이 모듈의 유일한 소비자다. 추후 지원 언어가 늘면 `EXTENSION_LANGUAGE_MAP`에 항목만 추가하면 된다.
