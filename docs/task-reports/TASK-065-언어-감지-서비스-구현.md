# TASK-065. 언어 감지 서비스 구현

## 상태
완료

## 날짜
2026-11-16

## 작업 요약
`backend/src/services/code_analysis/language_detector.py`에 업로드된 코드 파일의 프로그래밍 언어를 감지하는 서비스를 TDD로 구현했습니다. Pygments(2.16.1, requirements.txt에 이미 포함)를 이용해 파일명 기반으로 언어를 판별합니다.

- `detect_language(file_name)`: 파일 하나의 언어를 감지. 확장자를 소문자로 정규화한 뒤 Pygments의 `get_lexer_for_filename()`으로 lexer를 찾고, lexer 이름을 `data-model.md`의 `uploaded_code.detected_language` 예시값 형식('python', 'javascript' 등)으로 정규화된 소문자 슬러그로 변환합니다. 감지 실패 시 `LanguageDetectionError`를 발생시킵니다.
- `detect_dominant_language(file_names)`: 업로드된 여러 파일 중 대표 언어 하나를 결정. 각 파일의 언어를 감지해 빈도를 집계하고, 문서 전용 포맷(`text`, `markdown`)은 "프로젝트의 프로그래밍 언어"가 아니므로 집계에서 제외합니다. 동률일 경우 알파벳 순으로 가장 앞선 언어를 선택해 결과를 결정적으로 만듭니다. 개별 파일 감지 실패는 무시하고 나머지 파일로 계속 집계하며, 집계된 언어가 하나도 없으면 `LanguageDetectionError`를 발생시킵니다.

## 변경 파일
- `backend/src/services/code_analysis/language_detector.py` (신규 생성)
- `backend/tests/unit/test_language_detector.py` (신규 생성, 단위 테스트 22개)
- `specs/001-ai-code-learning-platform/tasks.md` (T065 `[X]` 체크)

## TDD 결과
- RED: 구현 전 `tests/unit/test_language_detector.py` 작성 → `pytest` 실행 시 `ModuleNotFoundError: No module named 'src.services.code_analysis.language_detector'`로 수집 실패 확인.
- GREEN: `language_detector.py` 구현 후 1차 실행에서 대소문자 혼용 파일명(`App.PY`) 테스트 1개 실패 발견 → Pygments의 파일명 glob 매칭이 대소문자 구분임을 확인하고, lexer 조회 전 확장자를 소문자로 정규화하도록 수정 → 22개 테스트 전부 통과.
- 테스트 커버리지: **100%** (`src/services/code_analysis/language_detector.py`, `pytest --cov` 측정)
- `ruff check` 통과 (최초 1건의 줄 길이 초과(E501) 수정 후 경고 없음)
- Git 저장소가 아직 초기화되지 않아 RED/GREEN 커밋 해시는 기록하지 않았습니다(이전 Task Report들과 동일한 제약, 예: TASK-064).

## 기술 결정
- **감지 방식: 파일명 기반 vs 내용 기반**: Pygments의 `guess_lexer_for_filename(name, content)`(내용 분석 포함)를 실험해본 결과 `.css` 파일이 `CSS+Lasso`로, 빈 텍스트가 모호하게 감지되는 등 불안정했습니다. 반면 `get_lexer_for_filename(name)`(파일명/확장자 전용)은 `file_validator.py`의 고정된 12종 확장자 화이트리스트와 1:1로 대응되어 더 결정적이고 테스트하기 쉬웠으므로 파일명 기반 방식을 채택했습니다.
- **`.jsx`/`.tsx` 예외 처리**: 설치된 Pygments 2.16.1에는 `.jsx`/`.tsx`를 파일명으로 인식하는 lexer가 전혀 등록되어 있지 않음을 직접 확인했습니다(`get_all_lexers()`로 전체 lexer 목록 검사). 두 확장자 모두 JSX 문법이 포함된 JavaScript/TypeScript이므로, Pygments 조회 전에 `.jsx → javascript`, `.tsx → typescript`로 매핑하는 예외 테이블을 두어 처리했습니다.
- **문서 포맷(`text`/`markdown`) 집계 제외**: `file_validator.py`가 허용하는 12종 확장자에는 `.txt`/`.md`도 포함되어 있지만, 이는 README 등 보조 문서용이지 "업로드된 코드의 프로그래밍 언어"로 볼 수 없습니다. `detect_language()` 자체는 두 확장자에 대해서도 `text`/`markdown`을 정상적으로 반환하지만(필요 시 호출자가 활용 가능), `detect_dominant_language()`에서는 이 두 언어를 집계 대상에서 제외해 순수 문서만 업로드된 경우가 아니라면 실제 코드 언어가 대표 언어로 선택되도록 했습니다.
- **동률 처리**: 여러 언어의 파일 수가 같을 경우 결과가 매 실행마다 달라지면 안 되므로, `Counter.most_common()`의 삽입 순서 의존성을 피하고 알파벳 순으로 가장 앞선 언어를 선택하는 결정적 규칙을 추가했습니다.

## 비고
이번 태스크는 `data-model.md`의 `uploaded_code.detected_language` 필드 값을 채우기 위한 순수 서비스 함수만 구현했습니다. 실제 업로드 흐름에서 `UploadedCode` 레코드에 이 값을 저장하는 연결 작업은 tasks.md상 T069(CodeUploadService)의 범위입니다. 또한 T066(복잡도 분석기)과 함께 코드 분석 파이프라인의 한 축을 담당하며, 두 서비스는 서로 독립적으로 동작하도록 설계했습니다(공유 상태 없음).
