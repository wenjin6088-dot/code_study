# TASK-086. 붙여넣기 코드 업로드 브라우저 수동 테스트

## 상태
완료

## 날짜
2026-11-16

## 작업 요약
"붙여넣기" 업로드 경로(FR-013: 언어 선택 드롭다운이 있는 직접 붙여넣기)를 검증했습니다.

절차:
1. CreateTaskModal에서 제목 "Pasted JS snippet" 입력, 업로드 방식 "붙여넣기" 선택
2. "언어 선택" 드롭다운에서 "JavaScript" 선택(PasteCode 컴포넌트의 `LANGUAGE_OPTIONS`에서 `filename: 'pasted.js'`로 매핑됨, T078)
3. "코드 붙여넣기" 텍스트영역에 `function greet(name) { ... } console.log(greet('world'));` 입력
4. "Create" 제출

결과: **"Task 3: Pasted JS snippet"**가 생성되고 `javascript`/`beginner`/`paste` 배지가 정확히 표시됨 — 사용자가 드롭다운에서 선택한 언어가 `paste_filename`(예: `pasted.js`)으로 변환되어 백엔드에 전달되고, language_detector(T065)가 그 파일명의 확장자로 `javascript`를 정확히 감지함을 확인.

## 변경 파일
없음 (수동 검증만 수행)

## TDD 결과
해당 없음 — 수동 브라우저 테스트 단계.

## 기술 결정
없음

## 비고
드롭다운에서 선택한 언어와 실제 감지된 언어가 일치하는지까지 검증한 것으로, "사용자가 선택한 언어 ≠ 실제 코드 내용"인 경우(예: Python 코드를 붙여넣고 JavaScript를 선택)는 이번 테스트 범위 밖입니다 — language_detector는 파일명(확장자) 기반이라 그 경우 사용자가 선택한 언어가 그대로 저장되며, 이는 설계상 의도된 동작입니다(T065 Task Report 참고).
