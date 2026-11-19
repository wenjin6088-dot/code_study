# TASK-076. FileUpload 컴포넌트

## 상태
완료

## 날짜
2026-11-16

## 작업 요약
작업(Task) 생성 시 코드 파일을 업로드하는 세 가지 방식(파일/폴더/붙여넣기) 중 "파일" 업로드를 담당하는 `FileUpload` 컴포넌트를 만들었습니다. 드래그 앤 드롭 영역과 숨겨진 `<input type="file" multiple>`, 그리고 "파일 선택" 버튼으로 구성됩니다. 사용자가 파일을 드롭하거나 input으로 선택하면, 선택된 `File` 객체 배열을 그대로 `onFilesSelected` prop으로 전달합니다. 파일 내용을 읽거나 가공하는 로직은 전혀 없고, 순수하게 "사용자가 고른 파일들을 부모에게 전달"하는 책임만 가집니다.

## 변경 파일
- `frontend/src/components/upload/FileUpload.tsx` (신규)
- `frontend/tests/unit/components/upload/FileUpload.test.tsx` (신규, RED 테스트)

## TDD 결과
- RED: 컴포넌트가 없는 상태에서 테스트 실행 → import 실패로 4개 테스트 모두 실패 확인.
- GREEN: 구현 후 `npx vitest run tests/unit/components/upload/FileUpload.test.tsx` 4개 테스트 전부 통과.
- Git 저장소가 아직 초기화되지 않아 커밋 해시는 없습니다.

## 기술 결정 (해당 시)
- "파일 선택" 버튼 클릭 시 `useRef`로 참조한 숨김 input의 `.click()`을 호출하는 방식을 사용했습니다. 숨김 input을 직접 클릭하게 하면 브라우저 기본 파일 선택 UI 스타일을 커스터마이징할 수 없기 때문에, 보이는 버튼이 숨겨진 input을 대신 트리거하는 흔한 패턴을 그대로 적용했습니다.
- 드롭 영역에는 `onDragOver`에서 `e.preventDefault()`를 호출해 브라우저의 기본 드롭 차단 동작(파일을 새 탭으로 여는 등)을 막았습니다.
- `data-testid="file-upload-input"` / `data-testid="file-upload-dropzone"`을 부여해 테스트가 role 기반 쿼리로 식별하기 어려운 input/드롭존 요소를 안정적으로 찾을 수 있게 했습니다.

## 비고
- 파일 확장자나 크기 검증은 이 컴포넌트의 책임이 아닙니다(백엔드 `file_validator.py`가 검증 담당, 프런트는 `task-service.ts`의 `createTask`가 그대로 전달). YAGNI 원칙에 따라 여기서는 검증 로직을 추가하지 않았습니다.
