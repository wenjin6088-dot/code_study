# TASK-052. CreateProjectModal 컴포넌트

## 상태
완료

## 날짜
2026-11-09

## 작업 요약
새 프로젝트를 만들 때 쓰는 모달(팝업) 창인 `CreateProjectModal`을 구현했습니다. `isOpen`이 false면 아무것도 그리지 않고, true일 때만 "Title"(필수), "Description"(선택) 입력란과 "Create", "Cancel" 버튼이 있는 `role="dialog"` 창을 보여줍니다.

이 모달은 로그인/회원가입 폼(LoginForm, RegisterForm)과 같은 패턴을 따라서, API 호출(`createProject`)을 모달이 직접 수행합니다. 제목이 비어 있거나 공백만 있으면 Create 버튼이 비활성화되어 실수로 빈 프로젝트를 만드는 것을 막습니다. 설명란이 비어 있으면 빈 문자열(`''`)이 아니라 `undefined`로 보내서, 서버에 "설명 없음"이라는 의미가 명확히 전달되도록 했습니다.

생성이 성공하면 만들어진 프로젝트 객체를 가지고 `onCreate` 콜백만 호출하고, 모달을 닫는 것(`onClose`)은 호출하지 않습니다. 모달을 닫을지 말지는 이 컴포넌트를 쓰는 쪽(Dashboard)이 결정하도록 책임을 분리했습니다. 생성이 실패하면 에러 메시지를 `role="alert"` 요소로 보여주고, `onCreate`나 `onClose`는 호출하지 않아 사용자가 입력을 다시 고칠 수 있게 모달이 열린 채로 남습니다.

## 변경 파일
- `frontend/src/components/project/CreateProjectModal.tsx` (신규)

## TDD 결과
- 테스트 파일: `frontend/tests/unit/components/project/CreateProjectModal.test.tsx` (10개 테스트, 기존에 이미 작성되어 있던 실패 테스트)
- GREEN 확인: `npx vitest run` 실행 결과 10개 테스트 전부 통과
- Git 저장소가 아직 초기화되지 않아 커밋은 생략했습니다.

## 기술 결정 (해당 시)
- Create 버튼의 활성/비활성 여부는 `title.trim().length === 0`으로 판단해, 공백만 입력된 제목도 "비어 있음"으로 취급합니다.
- 설명 값을 서버로 보낼 때 `description.trim() ? description : undefined` 방식을 써서, 사용자가 입력한 원래 값(앞뒤 공백 포함)은 그대로 보내되 공백만 있을 때만 `undefined`로 바꿉니다.
- 에러 메시지는 `err instanceof Error ? err.message : '프로젝트 생성에 실패했습니다'`로 처리해, 서비스 레이어(`project-service.ts`)에서 던지는 Error의 메시지를 그대로 노출합니다. 이는 `api-client.ts`의 인터셉터가 백엔드 에러 메시지를 이미 사람이 읽을 수 있는 한국어 문장으로 정규화해 주기 때문에 가능합니다.
- shadcn/ui의 기존 `Button` 컴포넌트를 재사용했습니다(outline variant를 Cancel 버튼에 사용).

## 비고
- 포커스 트랩, ESC 키로 닫기, 배경 클릭으로 닫기 등 접근성 편의 기능은 테스트에서 요구하지 않아 구현하지 않았습니다(GREEN 단계 최소 구현 원칙). 필요하다면 REFACTOR 단계나 별도 Task에서 추가할 수 있습니다.
