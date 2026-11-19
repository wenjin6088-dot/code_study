# TASK-001. 프로젝트 디렉토리 구조 생성

## 상태
완료

## 날짜
2026-10-27

## 작업 요약
AI Code Learning Platform 프로젝트의 전체 뼈대(디렉토리 구조)를 만들었습니다. 이것은 집을 짓기 전에 방 배치도를 그리고 기초 공사를 하는 것과 비슷합니다. 앞으로 백엔드 코드, 프론트엔드 코드, 업로드된 파일, 문서들이 들어갈 "방"들을 미리 만들어 둔 것입니다.

구체적으로 다음 세 영역의 폴더를 plan.md에 정의된 구조에 맞춰 생성했습니다.

1. **backend/** - 서버(두뇌) 역할을 하는 Python/FastAPI 코드가 들어갈 공간
   - `src/models` (데이터 설계도), `src/services` (비즈니스 로직, 하위에 auth/code_analysis/ai/document/practice/qa/progress), `src/api` (외부와 통신하는 창구), `src/db` (데이터베이스 연결), `src/utils` (공용 도구), `src/tasks` (백그라운드 작업), `alembic/versions` (데이터베이스 변경 기록), `scripts`, `tests/{contract,integration,unit}` (테스트 코드)
2. **frontend/** - 사용자가 직접 보는 화면(React) 코드가 들어갈 공간
   - `src/components` 하위에 auth/project/task/upload/document(chapters 포함)/practice/qa/progress/trash, `src/pages`, `src/services`, `src/hooks`, `src/stores`, `src/lib`, `src/utils`, `tests/{integration,unit}`
3. **storage/uploads/** - 사용자가 업로드한 코드 파일을 저장할 공간
4. **docs/** - 프로젝트 관련 문서가 들어갈 공간 (task-reports 하위 폴더는 TASK-001A에서 별도로 다룸)

## 변경 파일
- `backend/` 하위 디렉토리 전체 (신규 생성, 파일 없음)
- `frontend/` 하위 디렉토리 전체 (신규 생성, 파일 없음)
- `storage/uploads/` (신규 생성, 파일 없음)
- `docs/` (신규 생성, 파일 없음)

## TDD 결과
- 이 작업은 "로직을 작성"하는 작업이 아니라 빈 디렉토리를 만드는 순수한 구조 설정 작업이라, 테스트로 검증할 동작(behavior)이 존재하지 않습니다. 따라서 RED-GREEN-REFACTOR 사이클은 적용하지 않았습니다.
- 현재 저장소가 아직 git 저장소로 초기화되지 않은 상태라 (Is a git repository: false), RED/GREEN/REFACTOR 커밋도 아직 생성하지 않았습니다. git 초기화는 추후 Task에서 진행될 예정입니다.
- 테스트 커버리지: 해당 없음 (코드 없음)

## 기술 결정
- plan.md의 "Project Structure" 섹션에 명시된 경로를 그대로 따랐습니다. 임의로 폴더 이름을 바꾸거나 추가하지 않고, 설계 문서와 1:1로 매칭되도록 했습니다.
- 디렉토리만 먼저 만들고 `__init__.py`, `package.json` 같은 실제 설정 파일은 넣지 않았습니다. 이는 YAGNI 원칙에 따라, 해당 파일이 필요한 시점(T002, T003 등)에 만들기로 했기 때문입니다.
- 경로 구분자는 Windows 환경이지만 Git Bash의 `mkdir -p`를 사용해 슬래시(`/`) 기반으로 생성하여 크로스 플랫폼 호환성을 유지했습니다.

## 비고
- 빈 디렉토리는 git이 추적하지 않는 특성이 있어, 추후 git 저장소 초기화 시 일부 폴더가 보이지 않을 수 있습니다. 필요 시 `.gitkeep` 파일 추가를 고려할 수 있으나, 어차피 다음 Task들에서 해당 폴더에 실제 파일이 들어갈 예정이므로 현재는 추가하지 않았습니다.
- 다음 단계(T002, T003)에서 backend/frontend 각각의 의존성 초기화가 진행됩니다.
