# TASK-084. 단일 파일 업로드 브라우저 수동 테스트

## 상태
완료

## 날짜
2026-11-16

## 작업 요약
Playwright MCP로 실제 브라우저를 구동해, 코드 업로드 기능(T067~T083)의 "단일 파일 업로드" 경로를 end-to-end로 검증했습니다.

절차:
1. 백엔드(`uvicorn`, :8000)·프런트엔드(`vite dev`, :5173) 기동, Docker(Postgres/Redis) healthy 확인
2. 테스트 계정(`task-upload-tester@example.com`) 회원가입·로그인
3. 프로젝트("Code Upload QA Project") 생성 후 상세 페이지 진입
4. "작업 추가" → CreateTaskModal에서 제목 "Calculator functions" 입력, 업로드 방식 "파일"(기본값) 유지, `calculator.py`(간단한 `add`/`subtract` 함수) 선택
5. "Create" 제출

결과: Task 목록에 **"Task 1: Calculator functions"**가 즉시 나타났고, 배지로 `python`/`beginner`/`file`이 표시됨 — language_detector(T065)와 complexity_analyzer(T066)가 업로드 파이프라인(T069)을 통해 정상적으로 연동됨을 확인.

## 변경 파일
없음 (수동 검증만 수행)

## TDD 결과
해당 없음 — 수동 브라우저 테스트 단계. 기반이 되는 자동화 테스트는 T067~T083에서 이미 작성/통과(백엔드 284개, 프런트엔드 166개 전부 통과).

## 기술 결정
없음

## 비고
- 테스트에 사용한 프로젝트/계정/업로드 파일은 정리하지 않고 DB·`storage/uploads/`에 남겨두었습니다(T085~T089을 같은 프로젝트에서 이어서 검증하기 위함).
- Playwright MCP의 파일 선택 도구(`browser_file_upload`)는 자신의 허용 루트(`c:\kh\1027_speckit`) 밖의 파일을 열 수 없어, 테스트 픽스처를 `c:\kh\1027_speckit\.playwright-mcp\fixtures\`에 복사해 사용했습니다.
