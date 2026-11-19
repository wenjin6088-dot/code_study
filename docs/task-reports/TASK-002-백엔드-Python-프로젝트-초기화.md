# TASK-002. 백엔드 Python 프로젝트 초기화

## 상태
완료

## 날짜
2026-10-27

## 작업 요약
백엔드(서버) 쪽에서 사용할 Python 도구들의 "장바구니 목록"을 만들고, 실제로 그 도구들을 설치해봤습니다. 비유하자면 요리를 시작하기 전에 필요한 재료 목록(장바구니)을 적고, 실제로 마트에서 장을 봐서 재료가 다 있는지 확인하는 과정입니다.

구체적으로 한 일은 다음과 같습니다.

1. `backend/requirements.txt` 파일을 만들어, quickstart.md에 정의된 기술 스택(FastAPI, SQLAlchemy, PostgreSQL 드라이버, JWT 인증 도구, Google Gemini SDK, Celery, Redis, pytest 등)을 정확한 버전으로 적었습니다.
2. `backend/venv` 가상환경(Python만의 독립된 작업 공간)을 만들고, 그 목록에 적힌 패키지들을 실제로 설치해 문제가 없는지 검증했습니다.
3. 설치 중 발견된 버전 충돌을 해결했습니다 (아래 "기술 결정" 참고).
4. `backend/src`와 `backend/tests` 하위의 모든 폴더에 `__init__.py` 파일을 추가해, 이 폴더들이 단순한 디렉토리가 아니라 Python이 인식하는 "패키지"가 되도록 만들었습니다. 이것이 없으면 나중에 `from src.models import ...` 같은 코드가 동작하지 않습니다.
5. import 테스트로 fastapi, sqlalchemy, pydantic, celery, redis 등 핵심 라이브러리가 실제로 문제없이 로드되는지 확인했습니다.

## 변경 파일
- `backend/requirements.txt` (신규 생성)
- `backend/venv/` (신규 생성, Python 가상환경 — 코드 추적 대상 아님)
- `backend/src/__init__.py` 및 하위 11개 패키지(`models`, `services`, `services/auth`, `services/code_analysis`, `services/ai`, `services/document`, `services/practice`, `services/qa`, `services/progress`, `api`, `db`, `utils`, `tasks`)의 `__init__.py` (신규 생성)
- `backend/tests/__init__.py` 및 하위 `contract`, `integration`, `unit`의 `__init__.py` (신규 생성)

## TDD 결과
- 이 작업은 의존성 목록 작성 및 설치 검증이며, 테스트로 검증할 비즈니스 로직이 없어 RED-GREEN-REFACTOR 사이클은 적용하지 않았습니다. 대신 "설치된 패키지가 실제로 import 되는가"를 수동으로 검증하는 방식으로 정확성을 확인했습니다.
- 저장소가 아직 git으로 초기화되지 않아 (Is a git repository: false) 관련 커밋은 생성하지 않았습니다.
- 테스트 커버리지: 해당 없음 (설정 작업, 비즈니스 로직 코드 없음)

## 기술 결정
- **celery 버전 조정 (5.3.4 → 5.4.0)**: quickstart.md가 제안한 `celery[redis]==5.3.4`와 `redis==5.0.1`을 함께 설치하려 하자, pip가 의존성 충돌(`ResolutionImpossible`)을 보고했습니다. celery 5.3.4의 redis extra는 `redis<5.0.0`을 요구하는데, 요구사항에는 `redis==5.0.1`이 명시되어 있어 양립할 수 없었습니다. redis 버전은 research.md/quickstart.md에서 명시적으로 고정된 값이라 낮추지 않고, celery를 redis 5.x를 지원하는 `5.4.0`으로 올려 해결했습니다. 이는 Python 3.12 환경에서도 더 안정적으로 동작합니다.
- **Python 3.12 사용**: 로컬 환경에 설치된 Python이 3.12.10이었고, 이는 plan.md의 "Python 3.11+" 요구사항을 만족하므로 그대로 사용했습니다. 모든 패키지(asyncpg, pydantic-core 등 C 확장 포함)가 3.12용 바이너리로 정상 설치되는 것을 확인했습니다.
- **`__init__.py` 추가**: plan.md와 tasks.md에는 명시적으로 언급되어 있지 않지만, Python 패키지 구조의 기본 전제 조건이라 T002의 "백엔드 프로젝트 초기화" 범위에 포함해 처리했습니다. 파일 내용은 비워 두었습니다(YAGNI - 필요해지면 그때 내용을 채움).
- **requirements.txt 외 설정 파일 보류**: `pyproject.toml`(Ruff/Black/MyPy 설정)은 T006(린팅/포맷팅 설정)의 범위이므로 이번 Task에서는 만들지 않았습니다.

## 비고
- `backend/venv/`는 로컬 가상환경이므로 추후 git 저장소 초기화 시(.gitignore 작업, T007) 반드시 제외 패턴에 포함되어야 합니다.
- 실제 FastAPI 앱 실행(`uvicorn src.main:app`)은 아직 `src/main.py`가 없어 테스트하지 못했습니다. 이는 T014(FastAPI 앱 초기화)에서 다룰 예정입니다.
- PostgreSQL, Redis 서버 자체는 아직 설치/실행하지 않았습니다. 이번 Task는 Python 패키지 레벨의 초기화만 다룹니다.
