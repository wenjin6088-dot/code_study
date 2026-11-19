# TASK-028. POST /auth/register 엔드포인트 구현

## 상태
완료

## 날짜
2026-11-09

## 작업 요약
`backend/src/api/auth.py` 파일을 새로 만들고, 그 안에 회원가입 API(`POST /api/v1/auth/register`)를 구현했습니다. 이 엔드포인트는 이메일과 비밀번호를 JSON으로 받아서, 이미 T025에서 만들어진 `UserService.register()`를 그대로 호출하는 "얇은 껍데기" 역할만 합니다. 실제 이메일 형식 검사, 비밀번호 강도 검사, 중복 이메일 검사 로직은 전부 서비스 계층에 이미 있으므로 이 라우트에서 새로 만들지 않았습니다.

회원가입이 성공하면 HTTP 201과 함께 `{"id": ..., "email": ..., "skill_level": ...}` 형태의 JSON을 돌려줍니다. 비밀번호나 비밀번호 해시 값은 응답에 절대 포함되지 않도록, `User` DB 모델을 그대로 반환하지 않고 `UserResponse`라는 별도의 Pydantic 응답 모델을 만들어 그것만 변환해서 내려줍니다. 이렇게 하면 나중에 `User` 모델에 새 컬럼(예: 내부 설정값)이 추가되어도 실수로 외부에 노출될 위험이 없습니다.

서비스 계층에서 던지는 예외들(`EmailAlreadyRegisteredError`, `InvalidEmailError`, `WeakPasswordError`)은 이미 만들어져 있는 `src/api/exceptions.py`의 공용 에러 처리 구조에 맞게 각각 409(충돌), 400(잘못된 요청)으로 변환했습니다. 요청 본문에 `email`이나 `password` 필드가 누락된 경우는 FastAPI/Pydantic이 자동으로 422(검증 실패)를 돌려주므로 별도 코드를 작성하지 않았습니다.

## 변경 파일
- `backend/src/api/auth.py` (신규 생성 — register 외에 login/me/logout/refresh도 같은 파일에 함께 들어있습니다. 자세한 내용은 TASK-029~031 참고)
- `backend/src/api/router.py` (수정 — `auth_router`를 `api_router`에 연결)
- `specs/001-ai-code-learning-platform/tasks.md` (T028 완료 체크)

## TDD 결과
- **RED**: 테스터 Agent가 미리 작성한 `backend/tests/integration/test_auth_api.py`의 `TestRegister` 5개 테스트가 라우트 미존재로 전부 404 실패하는 것을 먼저 확인했습니다.
- **GREEN**: `auth.py` 구현 후 `TestRegister`의 5개 테스트(정상 가입 201, 중복 이메일 409, 잘못된 이메일 400, 약한 비밀번호 400, 필드 누락 422) 전부 통과했습니다.
- 백엔드 전체 테스트(기존 34개 + 신규 23개 = 57개) 재실행 결과 전부 통과, 회귀 없음.
- `ruff check src/` 통과 (경고 없음).
- 저장소가 git 초기화 전이라 RED/GREEN 커밋은 생성하지 않았습니다. (Git 저장소가 아직 초기화되지 않아 커밋은 생략했습니다)

## 기술 결정
- **Pydantic `EmailStr` 대신 `str` 사용**: 처음에는 요청 스키마에서 `pydantic.EmailStr`로 이메일 형식을 검증하려 했으나, 이 프로젝트의 가상환경에 `email-validator` 패키지가 설치되어 있지 않아 import 단계에서 에러가 났습니다. 어차피 `UserService.register()`가 정규식으로 이메일 형식을 이미 검증하고 있어서(T025), 라우트에서는 단순히 문자열로만 받고 실제 검증은 서비스 계층에 맡기는 쪽이 더 간단하고, 테스트가 기대하는 "형식이 이상하면 400"이라는 동작도 그대로 만족됩니다.
- **응답 전용 스키마 분리**: `User` SQLAlchemy 모델을 바로 반환하지 않고 `id`/`email`/`skill_level`만 담은 `UserResponse`를 만들어 반환값으로 썼습니다. 테스트가 "`password`, `password_hash`가 응답에 없어야 한다"를 명시적으로 검증하기 때문에, 화이트리스트 방식(꼭 필요한 필드만 담기)이 블랙리스트 방식(위험한 필드만 지우기)보다 실수할 여지가 적다고 판단했습니다.

## 비고
- 이 라우트 하나만으로는 로그인/쿠키 발급과 무관합니다. 로그인 쿠키 발급은 TASK-029에서 다룹니다.
