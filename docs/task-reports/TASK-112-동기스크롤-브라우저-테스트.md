# TASK-112. 코드-설명 패널 동기 스크롤 브라우저 수동 테스트

## 상태
완료

## 날짜
2026-11-18

## 작업 요약
Stack 자료구조 Task(35줄)의 "코드 한 줄씩 살펴보기" 탭에서, 코드 패널을 스크롤하면 설명 패널이 해당 줄의 설명으로 반응하는지 확인했습니다(T105/T112 명세: 코드→설명 한 방향).

Monaco 에디터 내부 `<textarea>`는 자체 렌더링 레이어에 가려져 Playwright의 일반 클릭으로는 포커스를 줄 수 없어서, 브라우저 컨텍스트에서 `window.monaco.editor.getEditors()[0].revealLineInCenter(30)`을 직접 호출해 29~34번째 줄이 보이도록 스크롤시켰습니다(사용자의 마우스 스크롤과 동일하게 Monaco의 `onDidScrollChange`를 거칩니다).

결과: 접근성 스냅샷에는 `aria-current`가 보이지 않았지만(Playwright 스냅샷 트리가 `[selected]`/`[active]`는 표시해도 `aria-current`는 표시하지 않음), `document.querySelectorAll('[aria-current]')`로 DOM을 직접 조회하자 "stack.py (L28-34)" 설명 항목 하나에만 `aria-current="true"`가 정확히 걸려 있었습니다. 30번째 줄이 그 설명이 다루는 범위(L28-34)에 포함되므로 매칭이 정확함을 확인했습니다. 스크린샷: `.playwright-mcp/t112-sync-scroll.png`.

## 변경 파일
없음 (수동 검증만 수행)

## TDD 결과
해당 없음 — 수동 브라우저 테스트 단계. 줄 번호 → 설명 항목 매칭 순수 함수(`findExplanationForLine`)는 `frontend/tests/unit/components/document/syncScroll.test.ts`(T105, 경계값 포함 6케이스)로 이미 커버됨. 이번 수동 테스트는 그 로직이 실제 Monaco 스크롤 이벤트와 실제 DOM에 끝까지 연결돼 있는지를 확인한 것입니다.

## 기술 결정
없음

## 비고
Playwright의 접근성 스냅샷 도구가 `aria-current`를 시각적으로 표시하지 않아 처음에는 "반응이 없다"로 오판할 뻔했습니다. `aria-current`/`aria-selected` 같은 속성을 수동 테스트로 검증할 때는 스냅샷만 보지 말고 `document.querySelectorAll('[attr]')`로 DOM을 직접 확인하는 편이 안전합니다.
