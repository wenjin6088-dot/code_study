# TASK-085. 폴더 업로드 브라우저 수동 테스트

## 상태
완료

## 날짜
2026-11-16

## 작업 요약
T084에 이어 같은 세션에서 "폴더 업로드" 경로(FR-012: 폴더 구조 유지)를 검증했습니다.

절차:
1. `sample_project/src/app.py`, `sample_project/src/utils.py` 2개 파일로 구성된 폴더 픽스처 준비
2. CreateTaskModal에서 제목 "Sample project folder" 입력, 업로드 방식 "폴더" 선택
3. Playwright `browser_file_upload`에 폴더 경로(`...\t085_folder\sample_project`)를 전달(`webkitdirectory` input이므로 개별 파일 경로가 아닌 디렉터리 경로를 받음)
4. "Create" 제출 → **"Task 2: Sample project folder"** 생성 확인(`python`/`beginner`/`folder` 배지)
5. 폴더 구조가 실제로 보존됐는지 UI 배지만으로는 알 수 없어, 브라우저 컨텍스트에서 `fetch('/api/v1/tasks/{id}/code', {credentials:'include'})`를 직접 호출해 응답을 확인

결과: `file_path`가 각각 **`"sample_project/src/app.py"`**, **`"sample_project/src/utils.py"`**로 정확히 반환됨 — FolderUpload(T077)의 `webkitRelativePath` → task-service.ts(T080)의 FormData filename → 백엔드 CodeUploadService(T069)의 `UploadFile.filename` 경로 보존 체인이 끝까지 정상 동작함을 확인.

## 변경 파일
없음 (수동 검증만 수행)

## TDD 결과
해당 없음 — 수동 브라우저 테스트 단계.

## 기술 결정
없음

## 비고
Playwright의 `webkitdirectory` input 자동화는 개별 파일 경로 배열이 아니라 **디렉터리 경로 하나**를 줘야 동작합니다(개별 파일 경로를 주면 `[webkitdirectory] input requires passing a path to a directory` 에러 발생). 실제 사용자의 OS 폴더 선택 다이얼로그와 동일하게 디렉터리 내 모든 파일이 상대경로와 함께 선택됨을 확인했습니다.
