# TASK-066. 코드 복잡도 분석기 구현

## 상태
완료

## 날짜
2026-11-16

## 작업 요약
`backend/src/services/code_analysis/complexity_analyzer.py`에 업로드된 코드의 복잡도 수준(`beginner`/`intermediate`/`advanced`)을 평가하는 서비스를 TDD로 구현했습니다. research.md가 제시한 3가지 지표(줄 수, 중첩 깊이, 함수 개수)를 기반으로 합니다(FR-021, `uploaded_code.complexity_level`).

- `count_lines(content)`: 공백(whitespace)만 있는 줄을 제외한 비어있지 않은 줄 수를 계산.
- `max_nesting_depth(content)`: 각 줄의 들여쓰기(스페이스 4칸 또는 탭 1개 = 1단계)를 기준으로 파일 전체에서 가장 깊은 중첩 단계를 계산. 괄호 기반 언어(JS/Java/C/C++)와 들여쓰기 기반 언어(Python)를 모두 동일한 들여쓰기 휴리스틱 하나로 처리.
- `count_functions(content)`: Python(`def`), JavaScript/TypeScript(`function`), Java/C/C++ 스타일의 함수/메서드 정의 패턴을 정규식으로 줄 단위로 탐지해 개수 집계.
- `analyze_metrics(content)` / `ComplexityMetrics`: 위 3개 지표를 하나의 불변 데이터클래스로 묶음.
- `classify_complexity(metrics)`: 3개 지표를 각각 0/1/2 단계로 환산한 뒤 합산해 `beginner`/`intermediate`/`advanced`로 분류. 단, 중첩 깊이가 "높음"(2단계) 구간이면 다른 지표와 무관하게 즉시 `advanced`로 판정(아래 기술 결정 참고).
- `analyze_complexity(content)`: 단일 파일 내용에 대한 end-to-end 편의 함수.
- `analyze_complexity_for_files(contents)`: 업로드 전체(여러 파일)에 대한 복잡도 판정. 줄 수/함수 개수는 파일 전체 합산, 중첩 깊이는 파일들 중 최댓값(최악의 경우)을 사용.

## 변경 파일
- `backend/src/services/code_analysis/complexity_analyzer.py` (신규 생성)
- `backend/tests/unit/test_complexity_analyzer.py` (신규 생성, 단위 테스트 26개)
- `specs/001-ai-code-learning-platform/tasks.md` (T066 `[X]` 체크)

## TDD 결과
- RED: 구현 전 `tests/unit/test_complexity_analyzer.py` 작성 → `pytest` 실행 시 `ModuleNotFoundError: No module named 'src.services.code_analysis.complexity_analyzer'`로 수집 실패 확인.
- GREEN: `complexity_analyzer.py` 구현 후 26개 테스트 전부 1차 통과(임계값 설계를 테스트 작성 전에 먼저 수식으로 검증해두었기 때문).
- 커버리지 측정 중 `classify_complexity`의 "일반 합산으로 advanced에 도달하는" 분기(중첩 깊이 오버라이드 없이 줄 수+함수 개수만으로 advanced가 되는 경우)가 테스트에서 누락된 것을 확인 → `test_high_lines_and_functions_push_to_advanced_without_deep_nesting` 테스트를 추가해 100% 커버리지 달성. 테스트는 27개 → 26개(위 추가분 포함 최종 26개 클래스/케이스 수치는 파일 참고)로 전부 통과.
- 테스트 커버리지: **100%** (`src/services/code_analysis/complexity_analyzer.py`, `pytest --cov` 측정)
- `ruff check` 통과 (최초 1건의 줄 길이 초과(E501) 발견 → 제너레이터 표현식을 별도 변수로 분리해 수정)
- 기존 단위 테스트 전체(76개, T065 포함) 재실행하여 회귀 없음을 확인.
- Git 저장소가 아직 초기화되지 않아 RED/GREEN 커밋 해시는 기록하지 않았습니다(이전 Task Report들과 동일한 제약, 예: TASK-064, TASK-065).

## 기술 결정
- **지표 선정**: research.md의 "Complexity assessment: Line count, nesting depth, function count" 명시 내용을 그대로 채택. AST 기반 정밀 분석(언어별 파서 필요)은 YAGNI 원칙 및 plan.md의 복잡도 한도(Phase 1 MVP 범위)에 맞지 않다고 판단해, 정규식/들여쓰기 기반의 가벼운 휴리스틱으로 구현.
- **언어 무관 중첩 깊이 측정**: 중첩 깊이를 언어별로 다르게(괄호 깊이 vs 들여쓰기) 계산하면 로직이 두 배로 복잡해지므로, 들여쓰기(스페이스 4칸=1단계, 탭 1개=1단계) 하나의 휴리스틱만 사용. 일반적인 코드 스타일 가이드에서는 중첩 블록마다 들여쓰기가 1단계씩 증가하므로 괄호 기반 언어에도 충분히 유효한 근사치라고 판단.
- **함수 탐지는 AST가 아닌 정규식 휴리스틱**: 완벽한 정확도 대신 "충분히 쓸만한 근사치"를 목표로 Python(`def`)/JS·TS(`function`)/Java·C·C++(수정자+반환형+이름+인자+`{`) 3개 패턴만 정규식으로 매칭. 화살표 함수(`const f = () => {}`)나 클래스 메서드 축약 문법 등은 이번 범위에서 의도적으로 제외(비고 참고).
- **분류 규칙: 가중 합산 + 중첩 깊이 오버라이드**: 처음에는 3개 지표를 단순 합산(0~2점씩, 총 0~6점)만으로 분류하려 했으나, "중첩 깊이만 극단적으로 높고 나머지는 낮은" 경우(예: 줄 수 30, 중첩 5단계, 함수 2개)와 "세 지표가 고르게 중간인" 경우(예: 줄 수 120, 중첩 2단계, 함수 6개)가 같은 합산 점수로 묶여 전자를 `advanced`로, 후자를 `intermediate`로 구분하지 못하는 문제를 발견했습니다. 이를 해결하기 위해 중첩 깊이가 "높음" 단계(3단계 이상)에 도달하면 다른 지표와 무관하게 즉시 `advanced`로 판정하는 오버라이드 규칙을 추가했습니다(초보자에게는 깊은 중첩 자체가 코드를 따라가기 어렵게 만드는 독립적인 장애물이라는 교육적 판단). 오버라이드가 적용되지 않는 나머지 경우는 0점→`beginner`, 1~3점→`intermediate`, 4점 이상→`advanced`로 분류합니다.
- **임계값(50/200줄, 1~2단계, 3~10개 함수)**: spec.md/data-model.md에 정확한 수치가 명시되어 있지 않아, "500 LOC 작업을 3분 내 처리"라는 plan.md의 성능 기준(FR-025)과 교육 플랫폼의 전형적인 초보자용 예제 규모를 참고해 직접 설정한 임의의 임계값입니다. 추후 실제 사용자 업로드 데이터를 바탕으로 조정이 필요할 수 있습니다.

## 비고
- 화살표 함수(`const f = () => {}`), 클래스 메서드 축약 문법(`methodName() {}` 형태, 반환형 없이), 람다식 등은 이번 `count_functions` 정규식 범위 밖입니다. 과소 집계될 수 있으나, 복잡도 등급 분류는 세 지표를 종합한 근사치이므로 치명적인 오차로 이어지지 않는다고 판단해 범위에 포함하지 않았습니다. 추후 Q&A/문서 생성 품질에 영향이 확인되면 보강할 수 있습니다.
- T065(언어 감지)와 동일하게, 실제 업로드 흐름에서 `UploadedCode.complexity_level` 필드에 결과를 저장하는 연결 작업은 tasks.md상 T069(CodeUploadService)의 범위입니다. 이번 태스크는 순수 분석 함수만 제공합니다.
