# TASK-079. TaskCard 컴포넌트

## 상태
완료

## 날짜
2026-11-16

## 작업 요약
프로젝트 상세 페이지에서 작업(Task) 하나를 카드 형태로 보여주는 `TaskCard` 컴포넌트를 만들었습니다. `ProjectCard`(TASK-051)와 똑같은 철학으로, 순수 프레젠테이션 컴포넌트이며 클릭 시 어디로 이동할지는 직접 정하지 않고 `onClick` prop에 현재 `task` 객체를 그대로 넘기기만 합니다. "Task {번호}: {제목}" 형태의 제목과 설명을 보여주고, `task.uploaded_code`가 있으면 감지된 언어/복잡도/업로드 방식을 작은 배지 텍스트로 추가로 표시합니다.

## 변경 파일
- `frontend/src/components/task/TaskCard.tsx` (신규)
- `frontend/tests/unit/components/task/TaskCard.test.tsx` (신규, RED 테스트)

## TDD 결과
- RED: 컴포넌트가 없는 상태에서 import 실패로 7개 테스트 모두 실패.
- GREEN: 구현 후 7개 테스트 전부 통과.
- Git 저장소가 아직 초기화되지 않아 커밋 해시는 없습니다.

## 기술 결정 (해당 시)
- `ProjectCard`와 동일하게 `<div role="button" tabIndex={0}>` + `onKeyDown`에서 Enter 키 감지 패턴을 그대로 재사용했습니다. 코드베이스 전체에서 "클릭 가능한 카드"의 접근성 패턴을 통일하기 위함입니다.
- `task.uploaded_code`가 `null`인 경우(아직 분석이 끝나지 않았거나 붙여넣기 직후 등) 배지 영역 전체를 렌더링하지 않도록 조건부 처리했습니다. 설명이 없을 때는 `ProjectCard`처럼 "설명이 없습니다" 플레이스홀더를 보여줍니다.
- 배지는 별도 스타일링 없이 `<span>` 텍스트로만 구현했습니다(GREEN 단계 최소 구현 — 디자인/뱃지 컴포넌트화는 테스트가 요구하지 않음).

## 비고
- `task-service.ts`(T080)에 정의된 `Task`/`UploadedCodeInfo` 타입에 의존합니다. 두 파일을 독립적으로 테스트할 수 있도록, 이 컴포넌트는 `task-service`의 함수를 호출하지 않고 타입만 import합니다.
