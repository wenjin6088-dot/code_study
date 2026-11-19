# TASK-080. task-service 구현

## 상태
완료

## 날짜
2026-11-16

## 작업 요약
Task(작업) CRUD와 코드 업로드를 담당하는 `task-service.ts`를 만들었습니다. `project-service.ts`와 동일하게 공유 `apiClient`(baseURL `/api/v1`, 에러 메시지 정규화 인터셉터 포함)를 그대로 사용하는 얇은 axios 래퍼 함수들로 구성됩니다. `listTasks`/`getTask`/`updateTask`/`removeTask`/`getTaskCode`는 JSON 기반 호출이고, `createTask`만 `multipart/form-data`(FormData)로 업로드 방식(file/folder/paste)에 따라 다른 필드를 채워 보냅니다. 백엔드(T067~T075, 병렬 작업 중)와 필드명을 한 글자도 다르지 않게 맞추는 것이 이 태스크의 핵심이었습니다.

## 변경 파일
- `frontend/src/services/task-service.ts` (신규)
- `frontend/tests/unit/services/task-service.test.ts` (신규, RED 테스트)

## TDD 결과
- RED: 서비스 파일이 없는 상태에서 import 실패로 9개 테스트 모두 실패.
- GREEN: 구현 후 `npx vitest run tests/unit/components/task/TaskCard.test.tsx tests/unit/services/task-service.test.ts` 16개 테스트(TaskCard 7 + task-service 9) 전부 통과.
- Git 저장소가 아직 초기화되지 않아 커밋 해시는 없습니다.

## 기술 결정 (해당 시)
- `createTask`의 FormData 필드명은 계약에 명시된 그대로 전부 스네이크 케이스(`title`, `description`, `upload_method`, `files`, `paste_content`, `paste_filename`)로 맞췄습니다. `description`은 값이 있을 때만 `formData.append`하고, 없으면 FormData에 키 자체를 추가하지 않도록 해서 백엔드가 `description`의 부재와 빈 문자열을 구분할 수 있게 했습니다.
- 파일/폴더 업로드 시 `formData.append('files', file, file.webkitRelativePath || file.name)`로 세 번째 인자(filename)를 명시적으로 지정했습니다. 폴더 업로드는 각 `File`에 브라우저가 채워준 `webkitRelativePath`(예: `myfolder/sub/b.py`)를, 일반 파일 업로드는 `webkitRelativePath`가 비어 있으므로 원래 파일명을 서버에 filename으로 전달합니다. 이렇게 하면 백엔드가 별도 가공 없이 전달받은 filename만으로 폴더 구조를 복원할 수 있습니다.
- axios에 FormData를 그대로 body로 넘기면 axios가 자동으로 `multipart/form-data; boundary=...` Content-Type을 설정하므로, 헤더를 직접 건드리지 않았습니다(요청사항에 명시된 주의사항 그대로 준수).
- `CreateTaskInput`을 `CreateTaskFileInput | CreateTaskPasteInput` 유니온으로 선언해, `uploadMethod === 'paste'`일 때는 `pasteContent`/`pasteFilename`이, 그 외에는 `files`가 반드시 있도록 타입 레벨에서 강제했습니다.

## 비고
- `getTaskCode`가 반환하는 파일 콘텐츠(`content: string`) 처리나 코드 뷰어 연동은 이후 Phase 6~8 범위이므로 이번에는 타입과 호출부만 구현했습니다.
