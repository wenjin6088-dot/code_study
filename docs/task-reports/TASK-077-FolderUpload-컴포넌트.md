# TASK-077. FolderUpload 컴포넌트

## 상태
완료

## 날짜
2026-11-16

## 작업 요약
폴더 전체를 업로드하는 `FolderUpload` 컴포넌트를 만들었습니다. 핵심은 `<input type="file" webkitdirectory multiple>` 하나입니다. `webkitdirectory` 속성이 설정된 input에서 폴더를 선택하면, 브라우저가 폴더 내 모든 파일을 가져오면서 각 `File` 객체에 `webkitRelativePath`(예: `myfolder/sub/b.py`)를 자동으로 채워줍니다. 이 컴포넌트는 그 파일들을 가공 없이 그대로 `onFilesSelected`로 전달하기만 합니다. 실제로 그 경로 정보를 읽어서 서버에 전달하는 책임은 `task-service.ts`의 `createTask`(T080)에 있습니다.

## 변경 파일
- `frontend/src/components/upload/FolderUpload.tsx` (신규)
- `frontend/tests/unit/components/upload/FolderUpload.test.tsx` (신규, RED 테스트)

## TDD 결과
- RED: 컴포넌트가 없는 상태에서 2개 테스트 모두 import 실패.
- GREEN: 구현 후 2개 테스트 통과(단, `webkitdirectory` 프로퍼티 반영 문제로 중간에 한 번 수정 필요 — 아래 기술 결정 참고).
- Git 저장소가 아직 초기화되지 않아 커밋 해시는 없습니다.

## 기술 결정 (해당 시)
- `webkitdirectory`는 표준 HTML 속성이 아니라 브라우저가 지원하는 비표준 IDL 프로퍼티라서, React JSX에 `webkitdirectory=""` 형태로 attribute로 써도 jsdom 테스트 환경에서는 `input.webkitdirectory` 프로퍼티가 `undefined`로 남는 문제가 있었습니다(실제 Chrome 등에서는 attribute reflection이 되지만 jsdom은 이 비표준 프로퍼티를 구현하지 않음). 그래서 `useRef` + `useEffect`로 마운트 후 `inputRef.current.webkitdirectory = true`를 직접 프로퍼티로 설정하는 방식으로 바꿔 테스트와 실제 브라우저 모두에서 동작하도록 했습니다.
- TypeScript가 `HTMLInputElement.webkitdirectory`를 기본적으로 알지 못하므로, 컴포넌트 파일 내부에 `declare global { interface HTMLInputElement { webkitdirectory: boolean } }` 모듈 보강을 추가했습니다. 전역 타입 파일을 따로 만들기보다, 이 프로퍼티를 사용하는 유일한 파일에 선언을 두어 YAGNI를 지켰습니다.

## 비고
- 드래그 앤 드롭은 지원하지 않습니다(브라우저가 드롭된 폴더 구조를 안정적으로 노출하지 않으므로, input 기반 선택만 사용). 테스트 계약에도 드롭 관련 요구사항이 없었습니다.
