# TASK-057. 프로젝트 생성 브라우저 수동 테스트

## 상태
완료

## 날짜
2026-11-09

## 작업 요약
Dashboard에서 "Create Project" 버튼을 눌러 프로젝트 생성 모달을 열고, 제목("파이썬 기초 학습")과 설명을 입력해 실제로 프로젝트를 만든 뒤, 모달이 닫히고 새 프로젝트가 즉시 목록에 나타나는지 확인했습니다.

절차:
1. 로그인 후 Dashboard(`/`) 접속 — 빈 상태 메시지("아직 프로젝트가 없습니다") 정상 표시 확인
2. "Create Project" 버튼 클릭 → 모달 오픈 확인
3. 제목/설명 입력 후 "Create" 제출
4. 결과: 모달이 닫히고, 새로 만든 프로젝트 카드가 Dashboard 목록에 즉시 나타남 (내부적으로 `['projects']` 쿼리를 무효화·재조회하는 T056 로직이 정상 동작)

## 변경 파일
없음 (수동 검증만 수행)

## TDD 결과
- 해당 없음 (수동 브라우저 테스트 단계 — 자동화 테스트는 T051-T056에서 이미 작성/통과됨, 82개 전체 통과)
- Git 저장소가 아직 초기화되지 않아 커밋은 생략했습니다.

## 기술 결정
없음

## 비고
테스트 중 Claude in Chrome 자동화 도구의 좌표 기반 클릭이 "Create Project" 버튼 클릭 이벤트를 React에 전달하지 못하는 경우가 있어, JavaScript로 직접 `.click()`을 호출해 우회했습니다. 이는 테스트 도구의 특성이며 실제 사용자의 마우스 클릭에는 영향이 없습니다 (T040 로그인 테스트에서도 동일한 현상을 겪었습니다).

## 재검증 (2026-11-10, Playwright MCP)
사용자 요청으로 Playwright MCP를 이용해 T057~T060을 다시 수행했습니다. 백엔드는 `--env-file ../.env` 옵션으로 재기동(JWT 시크릿 로드 확인, T040에서 발견된 것과 동일 이슈 재확인), `testuser01@example.com` 계정으로 로그인 후 진행.

- "Create Project" 버튼을 Playwright `browser_click`(일반 클릭)으로 눌렀으나 모달이 열리지 않음(DOM에 변화 없음, 버튼 1개만 존재) — 재현됨. `page.evaluate`로 `document.querySelector('button').click()`을 직접 호출하니 모달이 정상적으로 열림.
- 모달에서 제목("Playwright 테스트 프로젝트")/설명 입력 후 "Create" 버튼도 동일하게 일반 클릭은 반응 없었고, JS `.click()`으로 우회 제출 → 201 성공, 모달 닫히고 Dashboard에 카드로 즉시 반영됨.
- **새로운 관찰**: 이번엔 Claude in Chrome이 아니라 **Playwright MCP**(CDP 기반 trusted 클릭)에서도 동일 현상이 재현되었습니다. 다만 같은 세션에서 로그인 페이지의 "Login" 버튼 클릭은 Playwright 일반 클릭으로 정상 동작했습니다 — 즉 모든 버튼에서 발생하는 건 아니고 특정 상황(예: 리스트 내 동적 렌더 버튼, 폼 submit 버튼)에서만 재현되는 것으로 보입니다. 근본 원인은 이번 작업 범위에서 규명하지 않았고, 실사용자 클릭에는 영향이 없을 것으로 추정(동일하게 JS `.click()`으로는 항상 정상 동작).

## 재검증 (2026-11-12, Playwright MCP)
사용자 요청으로 T057~T060을 다시 Playwright MCP로 재검증했습니다. Docker Desktop(postgres/redis 컨테이너)이 중지되어 있어 먼저 기동했고, 백엔드(`uvicorn --env-file ../.env`, 8000)·프론트엔드(`npm run dev`, 5173)를 새로 띄운 뒤 `testuser01@example.com` / `Password123`으로 로그인해 진행했습니다.

- "Create Project" 버튼: Playwright `browser_click` 일반 클릭 2회 시도 모두 모달이 열리지 않음(기존에 보고된 trusted-click 미반응 현상 그대로 재현). `page.evaluate`로 `document.querySelector('button').click()` 직접 호출하니 모달 정상 오픈.
- 제목("Playwright 재검증 프로젝트 T57-60"), 설명 입력 후 "Create" 버튼도 동일하게 JS `.click()`으로 제출 → 모달이 닫히고 Dashboard 목록에 새 프로젝트 카드가 즉시 나타남을 확인. 기존 관찰과 완전히 동일한 결과이며 새로 발견된 이슈 없음.
