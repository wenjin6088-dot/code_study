# TASK-081. CreateTaskModal 구현

## 상태
완료

## 날짜
2026-11-16

## 작업 요약
프로젝트 상세 페이지에서 새 작업(Task)을 만드는 `CreateTaskModal`을 구현했습니다. `CreateProjectModal`(TASK-052)과 동일한 철학을 따릅니다: 모달이 `createTask` 서비스 함수를 직접 호출하고(부모에게 위임하지 않음), 성공 시 `onCreate(task)`만 호출하며 `onClose`는 직접 부르지 않습니다(모달을 닫을지는 부모인 `ProjectDetail`이 결정). Title/Description 입력 필드와 "파일"/"폴더"/"붙여넣기" 세 개의 버튼으로 업로드 방식을 전환하면서 각각 `FileUpload`/`FolderUpload`/`PasteCode`(T076~T078)를 조건부로 렌더링합니다.

## 변경 파일
- `frontend/src/components/task/CreateTaskModal.tsx` (신규)
- `frontend/tests/unit/components/task/CreateTaskModal.test.tsx` (신규, RED 테스트)

## TDD 결과
- RED: 컴포넌트가 없는 상태에서 import 실패로 13개 테스트 모두 실패.
- GREEN: 구현 후 13개 테스트 전부 통과.
- Git 저장소가 아직 초기화되지 않아 커밋 해시는 없습니다.

## 기술 결정 (해당 시)
- 제출 버튼(Create) disabled 조건은 세 가지를 OR로 묶었습니다: `title.trim().length < 5`, 파일/폴더 방식인데 선택된 파일이 0개, 붙여넣기 방식인데 내용이 빈 문자열. 업로드 방식을 전환(`switchMethod`)할 때마다 `files`와 `pasteContent`를 초기화해서, 예를 들어 파일을 선택한 뒤 "붙여넣기"로 전환해도 이미 선택했던 파일 개수 때문에 조건이 잘못 통과되는 일이 없게 했습니다.
- 붙여넣기 제출 시 `paste_filename`은 사용자가 입력한 텍스트가 아니라, `PasteCode`가 export하는 `LANGUAGE_OPTIONS`에서 현재 선택된 `language` 값에 대응하는 `filename`을 찾아 사용합니다(예: `javascript` 선택 시 `pasted.js`). 일치하는 옵션이 없는 예외적인 경우를 위해 `'pasted.txt'`를 fallback으로 남겼습니다.
- 업로드 방식 전환 버튼은 `<Button variant={...}>`로 현재 선택된 방식만 `default`(강조), 나머지는 `outline`으로 보이게 했습니다. 실제 라디오 버튼 시맨틱(`role="radio"`) 대신 일반 버튼으로 구현한 이유는, 계약 설명이 "업로드 방식 전환용 버튼/라디오 3개"로 버튼 방식을 허용했고, `Button` 컴포넌트를 그대로 재사용하는 것이 기존 패턴(파일 선택 버튼 등)과 더 일관되기 때문입니다.
- 에러 처리는 `CreateProjectModal`과 동일하게 `role="alert"`로 표시하고, 실패 시 `onCreate`/`onClose`를 호출하지 않습니다.

## 비고
- `uploadMethod`가 `'file'`과 `'folder'`일 때 모두 동일한 `files: File[]` state를 공유합니다. `FileUpload`와 `FolderUpload`가 같은 `onFilesSelected` 콜백 시그니처를 가지므로 자연스럽게 재사용할 수 있었습니다.
