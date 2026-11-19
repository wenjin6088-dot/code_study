# TASK-122. ProblemCard 컴포넌트

## 상태
완료

## 날짜
2026-11-19

## 작업 요약
실습 문제 하나를 화면에 보여주는 카드 컴포넌트를 만들었습니다. 문제 번호, 난이도 배지(Follow Along / Fill Blanks / Modify / Debug / Create), 문제 지문, 학습 목표를 보여주고, 힌트·정답 컴포넌트(T123/T124)를 자식으로 끼워 넣을 수 있도록 `children`을 받습니다.

난이도 배지 문구는 기획 문서(spec.md)의 시나리오 문장에 그대로 나온 영어 표기("Follow Along, Fill Blanks, Modify, Debug, Create")를 그대로 썼습니다. 브라우저 테스트(T128)에서도 같은 문구를 확인할 예정이라 미리 맞춰뒀습니다.

## 변경 파일
- `frontend/src/components/practice/ProblemCard.tsx` (신규)
- `frontend/tests/unit/components/practice/ProblemCard.test.tsx` (신규)

## TDD 결과
- RED: 테스트를 먼저 작성 → 컴포넌트 파일이 없어 import 오류로 실패.
- GREEN: 컴포넌트 구현 → 4개 테스트 통과(문제 번호/배지/지문 표시, 학습 목표 표시, 5종 배지 매핑, children 전달).
- 커밋: 아직 생성하지 않음
- 테스트 커버리지: 신규 테스트 4개 전부 통과

## 기술 결정
기존 프로젝트의 컴포넌트들(`ExplanationPanel` 등)과 마찬가지로 Tailwind 클래스 없이 순수 시맨틱 HTML(`article`, `h2`, `h3`)만 사용했습니다. Phase 1 MVP는 기능 우선이고, 시각 디자인은 Polish 단계(Phase 11)에서 다루는 것이 이 프로젝트의 기존 관례입니다.

## 비고
없음.
