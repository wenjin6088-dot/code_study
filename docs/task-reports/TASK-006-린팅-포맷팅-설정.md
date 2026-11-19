# TASK-006. 린팅 및 포맷팅 설정 (Ruff/Black, ESLint/Prettier)

## 상태
완료

## 날짜
2026-10-29

## 작업 요약
코드를 여러 사람(또는 미래의 나 자신)이 함께 보고 고치려면 "맞춤법 검사기"와 "자동 줄 맞추기 도구"가 필요합니다. 이번 Task에서는 백엔드(Python)와 프론트엔드(TypeScript) 양쪽에 그 도구들을 설정했습니다.

- **맞춤법 검사기(Linter)**: 오타나 잘못된 문법, 안 쓰는 변수 같은 "실수"를 찾아줍니다. 백엔드는 Ruff, 프론트엔드는 ESLint를 사용합니다.
- **자동 줄 맞추기(Formatter)**: 들여쓰기, 줄 길이, 인용부호(홑/겹따옴표) 같은 "스타일"을 모두가 똑같이 맞추게 해줍니다. 백엔드는 Black, 프론트엔드는 Prettier를 사용합니다.

### 백엔드
1. `backend/pyproject.toml`에 `[tool.ruff]`, `[tool.black]` 설정을 추가했습니다 (줄 길이 88자, Python 3.11 문법 기준).
2. `backend/requirements-dev.txt`를 새로 만들어 `ruff==0.1.6`, `black==23.11.0`을 담았습니다. 이 둘은 "코드를 운영 서버에서 실제로 실행할 때" 필요한 게 아니라 "개발하는 동안에만" 필요한 도구라, 운영용 `requirements.txt`(T002)와 분리했습니다.
3. 두 개의 백엔드 가상환경(`venv`, `.venv`) 모두에 설치하고, `ruff check src/ tests/`와 `black --check src/ tests/`를 직접 실행해 정상 동작을 확인했습니다 (현재는 빈 `__init__.py` 파일들뿐이라 "문제 없음"으로 통과).

### 프론트엔드
1. `frontend/.eslintrc.cjs`: TypeScript(`@typescript-eslint`)와 React Hooks 규칙을 검사하도록 설정했습니다.
2. `frontend/.prettierrc`: 기존에 이미 작성된 코드 스타일(세미콜론 없음, 홑따옴표)과 일치하도록 `semi: false`, `singleQuote: true`로 설정했습니다.
3. `frontend/.eslintignore`, `frontend/.prettierignore`: `node_modules`, `dist`, `coverage` 등 검사 대상에서 제외할 폴더를 지정했습니다.
4. `package.json`에 `format`(자동 수정), `format:check`(검사만) 스크립트를 추가하고, 필요한 ESLint 플러그인(`@typescript-eslint/*`, `eslint-plugin-react-hooks`, `eslint-plugin-react-refresh`, `eslint-config-prettier`)을 devDependencies에 추가해 설치했습니다.
5. `npm run lint`, `npm run format:check`, `npm run build`를 모두 실행해 실제로 통과하는지 확인했습니다. 처음 `format:check`에서 `.eslintrc.cjs`와 `src/index.css` 2개 파일이 스타일 불일치로 걸렸고, `npm run format`(prettier --write)으로 자동 수정한 뒤 재검사에서 통과했습니다.

## 변경 파일
- `backend/pyproject.toml` (신규 생성)
- `backend/requirements-dev.txt` (신규 생성)
- `frontend/.eslintrc.cjs` (신규 생성)
- `frontend/.eslintignore` (신규 생성)
- `frontend/.prettierrc` (신규 생성)
- `frontend/.prettierignore` (신규 생성)
- `frontend/package.json` (수정: lint 플러그인 devDependencies 추가, format/format:check 스크립트 추가)
- `frontend/.eslintrc.cjs`, `frontend/src/index.css` (prettier 자동 포맷으로 스타일 일부 수정)

## TDD 결과
- 린팅/포맷팅 설정 자체는 테스트할 비즈니스 로직이 없어 RED-GREEN-REFACTOR 사이클은 적용하지 않았습니다. 대신 각 도구를 실제로 실행해 "설정이 유효하고 정상 동작하는가"를 검증했습니다.
  - 백엔드: `ruff check src/ tests/` (exit 0), `black --check src/ tests/` (18 files unchanged)
  - 프론트엔드: `eslint . --ext ts,tsx` (exit 0), `prettier --check .` (전체 통과, 2개 파일은 `--write`로 먼저 수정), `npm run build` (타입체크+빌드 성공)
- 저장소가 아직 git으로 초기화되지 않아 관련 커밋은 생성하지 않았습니다.
- 테스트 커버리지: 해당 없음 (설정 파일, 비즈니스 로직 코드 없음)

## 기술 결정
- **MyPy는 이번 Task 범위에서 제외**: constitution(코드 품질 표준)과 quickstart.md는 백엔드 타입 검사 도구로 MyPy strict mode도 요구하지만, tasks.md의 T006 설명은 명시적으로 "Ruff, Black"만 언급하고 있고, T002(requirements.txt)에도 mypy가 포함되어 있지 않았습니다. 범위를 벗어나는 추가 도구 설치 대신, 이 Task에서는 Ruff/Black만 다루고 MyPy 설정은 별도로 필요성을 판단해 추가하는 것을 "비고"에 남겨둡니다.
- **ruff/black을 `requirements-dev.txt`로 분리**: 운영 환경에는 필요 없는 개발 도구라, 운영용 `requirements.txt`를 오염시키지 않도록 별도 파일로 뺐습니다.
- **Prettier 설정값을 기존 코드 스타일에 맞춤**: T003에서 이미 세미콜론 없이, 홑따옴표로 작성된 파일들(`main.tsx`, `App.tsx`, `vite.config.ts`)이 있었기 때문에, Prettier 규칙을 그 스타일에 맞춰(`semi: false`, `singleQuote: true`) 정해서 기존 파일들이 대량으로 재포맷되는 것을 피했습니다.
- **ESLint 8(legacy `.eslintrc.cjs`) 유지**: `package.json`에 ESLint `^8.54.0`을 이미 고정해뒀는데(T003), ESLint 9의 "flat config"(`eslint.config.js`) 방식은 8.x와 호환되지 않습니다. 버전을 바꾸지 않기 위해 8.x에 맞는 전통적인 `.eslintrc.cjs` 방식을 사용했습니다.
- **`eslint-config-prettier` 추가**: ESLint의 스타일 관련 규칙(들여쓰기, 줄 길이 등)이 Prettier와 충돌해 서로 다른 답을 내는 걸 막기 위해, ESLint의 스타일 규칙을 끄는 이 설정을 추가했습니다. 두 도구가 "같은 지적을 서로 다르게" 하지 않도록 역할을 분리했습니다(ESLint=문법/실수, Prettier=스타일).

## 비고
- 두 개의 백엔드 가상환경(`backend/venv`, `backend/.venv`)이 계속 공존하고 있어, 이번에도 양쪽 모두에 ruff/black을 설치했습니다. 어느 쪽을 표준으로 쓸지는 여전히 결정되지 않았습니다.
- MyPy strict mode 설정은 constitution/quickstart.md가 요구하는 사항이지만 이번 Task 범위 밖이라 보류했습니다. 필요 시 별도 Task로 추가를 제안합니다.
- CLAUDE.md의 커맨드 섹션(`cd backend; pytest; ruff check src/`)과 일치하도록 설정했습니다.
