# TASK-078. PasteCode 컴포넌트

## 상태
완료

## 날짜
2026-11-16

## 작업 요약
코드를 직접 붙여넣어 작업을 생성하는 "붙여넣기" 업로드 방식을 위한 `PasteCode` 컴포넌트를 만들었습니다. "코드 붙여넣기" 라벨이 붙은 `<textarea>`와 "언어 선택" 라벨이 붙은 `<select>`로 구성된 순수 컨트롤드 컴포넌트입니다. 값과 변경 핸들러를 모두 props(`content`/`onContentChange`/`language`/`onLanguageChange`)로 받기 때문에, 실제 상태는 이 컴포넌트를 사용하는 `CreateTaskModal`(T081)이 관리합니다. 더불어 언어 선택 옵션과 각 언어에 대응하는 기본 파일명을 담은 `LANGUAGE_OPTIONS` 배열을 함께 export해서, 모달이 제출 시 백엔드로 보낼 `paste_filename`을 알 수 있게 했습니다.

## 변경 파일
- `frontend/src/components/upload/PasteCode.tsx` (신규)
- `frontend/tests/unit/components/upload/PasteCode.test.tsx` (신규, RED 테스트)

## TDD 결과
- RED: 컴포넌트/상수가 없는 상태에서 6개 테스트 모두 import 실패.
- GREEN: 구현 후 6개 테스트 전부 통과.
- Git 저장소가 아직 초기화되지 않아 커밋 해시는 없습니다.

## 기술 결정 (해당 시)
- `LANGUAGE_OPTIONS`는 백엔드 `file_validator.py`가 지원하는 12개 확장자 중 React 전용 확장자인 `.jsx`/`.tsx`를 뺀 9종(Python/JavaScript/TypeScript/HTML/CSS/Java/C++/C/Markdown)만 포함했습니다. 붙여넣기 기능은 "이 코드가 어떤 언어/확장자인지" 사용자가 직접 고르는 것이므로, jsx/tsx처럼 이미 js/ts로 커버되는 변형까지 따로 선택지를 늘릴 필요가 없다고 판단했습니다(YAGNI).
- `.txt`(Text)는 계약 설명에 예시로 나와 있었지만, 실제로는 9개(jsx/tsx 제외)만 필요하다고 명시되어 있어 Markdown까지 9개를 맞추고 Text는 제외했습니다. 테스트도 `LANGUAGE_OPTIONS`가 정확히 9개임을 검증합니다.
- select의 `value`/`onChange`를 완전한 controlled component로 구현해, 상태를 모달에 위임하면서도 이 컴포넌트 자체는 테스트하기 쉬운 순수 함수형 UI로 남겼습니다.

## 비고
- 코드 신택스 하이라이팅이나 Monaco 에디터 연동은 이번 태스크 범위가 아닙니다(단순 `<textarea>`). 프로젝트에 `@monaco-editor/react` 의존성이 있지만, 테스트 계약이 평범한 textarea만 요구했으므로 추가하지 않았습니다.
