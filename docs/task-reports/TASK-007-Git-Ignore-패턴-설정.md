# TASK-007. Git Ignore 패턴 설정

## 상태
완료

## 날짜
2026-10-29

## 작업 요약
git은 "이 파일들은 추적(기록)해줘"라고 명시하지 않는 한 모든 파일을 추적하려고 합니다. 하지만 `node_modules`(수십만 개의 라이브러리 파일), 가상환경(`venv`), 비밀번호가 담긴 `.env`, 사용자가 업로드한 코드 파일 같은 것들은 저장소에 올리면 안 됩니다. 용량이 너무 크거나, 사람마다 달라서 의미가 없거나, 보안상 위험하기 때문입니다. `.gitignore`는 "이런 것들은 아예 쳐다보지도 마"라고 git에게 미리 일러두는 명단입니다.

루트 디렉토리에 `.gitignore`를 만들고 tasks.md가 명시한 4가지 범주(`node_modules`, `venv`, `.env`, `storage/uploads/`)를 중심으로, 지금까지 실제로 만들어진 산출물들(빌드 결과물, 캐시, 로그 등)까지 포괄하는 패턴을 작성했습니다.

1. **Python 관련**: `__pycache__/`, `venv/`, `.venv/`(지금 공존 중인 두 가상환경 이름 모두), `.pytest_cache/`, `.ruff_cache/`, `htmlcov/` 등
2. **Node/프론트엔드 관련**: `node_modules/`, `dist/`, `build/`, `coverage/` 등
3. **환경변수**: `.env`, `.env.*`를 전부 막되, `!.env.example`로 예외를 둬서 T005에서 만든 템플릿 파일만은 계속 git에 남도록 했습니다.
4. **업로드된 코드 파일**: `storage/uploads/*`로 내용은 막되, `!storage/uploads/.gitkeep`으로 "이 폴더가 존재한다"는 사실만은 git에 남도록 했습니다. 이를 위해 빈 마커 파일 `storage/uploads/.gitkeep`도 함께 만들었습니다 (git은 완전히 빈 폴더를 추적하지 않기 때문입니다).
5. **그 외**: 로그 파일, OS/에디터가 자동으로 만드는 파일(`.DS_Store`, `Thumbs.db`, `.vscode/`, `.idea/` 등)

## 변경 파일
- `.gitignore` (신규 생성, 루트 디렉토리)
- `storage/uploads/.gitkeep` (신규 생성, 빈 폴더를 git에 남기기 위한 마커)

## TDD 결과
- `.gitignore` 작성 자체는 테스트할 비즈니스 로직이 없어 RED-GREEN-REFACTOR 사이클은 적용하지 않았습니다. 하지만 "이 패턴이 실제로 git에서 의도대로 동작하는가"는 반드시 실제로 검증이 필요한 부분이라, 별도의 **임시 디스포저블 테스트 저장소**를 스크래치패드 디렉토리에 만들어 검증했습니다 (현재 프로젝트 자체는 git 저장소가 아니라서, 실제 프로젝트에 `git init`을 하지 않고 격리된 곳에서 테스트).
  - 테스트 저장소에 `.gitignore`를 복사하고, 실제 프로젝트와 똑같은 구조의 샘플 파일들(`backend/venv/...`, `frontend/node_modules/...`, `.env`, `.env.example`, `storage/uploads/.gitkeep`, 일반 소스 파일 등)을 만들었습니다.
  - `git add -A` 후 `git status --short`로 실제로 스테이징되는 파일을 확인한 결과:
    - **추적됨(의도대로)**: `.env.example`, `.gitignore`, `backend/requirements.txt`, 소스 코드 파일들, `docs/task-reports/*.md`, `storage/uploads/.gitkeep`
    - **무시됨(의도대로)**: `backend/venv/`, `backend/.venv/`, `frontend/node_modules/`, `frontend/dist/`, `storage/uploads/user1/code.py`(실제 업로드 파일 가정), `.env`, `.env.local`
  - 검증이 끝난 뒤 임시 테스트 저장소는 완전히 삭제했습니다.
- 저장소가 아직 git으로 초기화되지 않아(Is a git repository: false) 실제 프로젝트에 대한 커밋은 생성하지 않았습니다.
- 테스트 커버리지: 해당 없음 (설정 파일, 비즈니스 로직 코드 없음)

## 기술 결정
- **두 백엔드 가상환경 이름(`venv`, `.venv`) 모두 포함**: 이전 Task에서 사용자 요청으로 `backend/venv`와 `backend/.venv`가 함께 존재하게 됐는데, 어느 쪽이 표준이 될지 아직 결정되지 않았으므로 둘 다 무시 패턴에 포함해 둘 중 어느 것을 쓰든 안전하게 git에서 제외되도록 했습니다.
- **`.env*`에 네거티브 패턴(`!.env.example`)을 사용**: 단순히 `.env`만 막으면 향후 `.env.production`, `.env.local` 같은 변형이 실수로 커밋될 위험이 있어 `.env.*`까지 넓게 막았습니다. 그 결과 템플릿 파일(`.env.example`)도 같이 막히는 부작용이 생기므로, 느낌표(`!`) 예외 패턴으로 다시 풀어줬습니다.
- **`storage/uploads/.gitkeep` 추가**: tasks.md가 "storage/uploads/"를 무시 대상으로 명시했지만, 폴더 자체가 아예 git에서 사라지면 새로 클론한 사람은 그 폴더가 존재해야 한다는 사실조차 알 수 없습니다. 빈 마커 파일로 폴더의 "존재"만 추적하고 "내용물"은 계속 무시하는 흔한 패턴을 적용했습니다.
- **`Dockerfile*`을 무시 목록에 넣지 않음**: 명령어 실행 지침(이 커맨드의 4단계)에 있는 Docker 패턴 예시에는 `Dockerfile*`도 포함되어 있었지만, 이는 `.dockerignore`(이미지 빌드 시 제외할 파일) 맥락의 예시이고 `.gitignore`(버전 관리에서 제외할 파일)에는 맞지 않는 항목이라 판단해 제외했습니다. Dockerfile은 소스 코드이므로 git에 반드시 추적되어야 합니다 (현재는 Dockerfile 자체가 없어 해당 사항 없음).
- **`git init`은 수행하지 않음**: T007의 범위는 "ignore 패턴 설정"이며, 실제 git 저장소 초기화는 별도의 결정이 필요한 작업이라고 판단해 이번 Task에서는 수행하지 않았습니다. 검증은 격리된 임시 저장소에서 진행했습니다.

## 비고
- 실제로 `git init`을 하게 되면, 이 `.gitignore`가 있는 상태에서 `git add -A`를 해도 `backend/venv`, `backend/.venv`, `frontend/node_modules` 같은 무거운 디렉토리가 실수로 커밋되지 않습니다 (임시 테스트 저장소에서 이미 확인됨).
- `backend/venv` vs `backend/.venv` 중복 문제는 여전히 미해결 상태입니다. git 저장소를 초기화하기 전에 한 번 정리하는 것을 권장합니다.
