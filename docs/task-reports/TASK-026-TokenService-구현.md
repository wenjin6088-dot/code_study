# TASK-026. TokenService 구현 (토큰 발급/검증/회전)

## 상태
완료

## 날짜
2026-11-06

## 작업 요약
`backend/src/services/auth/token_service.py`에 `TokenService` 클래스를 새로 만들었습니다. 이 서비스는 "로그인에 성공한 사용자에게 입장권(access token)과 재입장권(refresh token)을 발급하고, 입장권이 진짜인지 검사하고, 재입장권을 새것으로 교체(rotate)해주는" 역할만 담당합니다. 회원가입/로그인 자체(비밀번호 확인 등)는 T025의 `UserService` 몫이고, 이 서비스는 그 뒤에 "토큰"이라는 증명서를 발행하는 발급기 역할만 합니다.

- **`issue_tokens(user_id)`**: 기존 유틸리티(T012 `utils/jwt.py`)로 access/refresh JWT를 만들고, refresh 토큰은 해시(SHA-256)해서 DB(`refresh_tokens` 테이블)에 저장합니다. 영화관 입장권을 발급할 때, 매표소 장부에는 표의 "일련번호 해시"만 적어두고 실제 표(토큰 원문)는 손님에게 주는 것과 비슷합니다 — 장부가 유출돼도 표를 위조할 수 없습니다.
- **`verify_access_token(access_token)`**: access 토큰을 복호화해 사용자 ID를 돌려줍니다. 서명이 틀리거나 만료됐거나 refresh 토큰을 access 토큰 자리에 끼워 넣으면 모두 `InvalidTokenError`로 통일해 던집니다(실패 이유를 구체적으로 노출하지 않음).
- **`rotate_refresh_token(refresh_token)`**: refresh 토큰으로 "새 입장권 묶음"을 발급받는 기능입니다. JWT 서명/만료 확인 → DB에 저장된 해시와 대조(존재하는지, 이미 취소(revoked)됐는지, DB 기준 만료되지 않았는지) → 통과하면 기존 토큰을 즉시 `revoked=True`로 바꾸고 새 access/refresh 쌍을 발급합니다. 이미 한 번 쓴 표를 재사용하려 들면(재사용 탐지) 바로 거부되므로, 탈취된 refresh 토큰이 반복 사용되는 것을 막습니다.

작업 중 실제 버그를 하나 발견해 함께 고쳤습니다: 같은 사용자에게 1초 안에 토큰을 두 번 발급하면(특히 회전 시 "취소 1개 + 발급 1개"가 거의 동시에 일어남) 기존 `utils/jwt.py`가 만드는 JWT 내용(sub·type·만료시각)이 완전히 똑같아져 해시도 똑같아지고, DB의 `UNIQUE(token_hash)` 제약을 위반해 에러가 났습니다. 표마다 고유 번호(`jti`, JWT 표준 클레임)를 추가해 토큰이 항상 서로 다르게 만들어지도록 T012 유틸리티를 보강했습니다.

## 변경 파일
- `backend/src/services/auth/token_service.py` (신규 생성)
- `backend/src/services/auth/exceptions.py` (수정: `InvalidTokenError` 추가)
- `backend/src/utils/jwt.py` (수정: `create_access_token`/`create_refresh_token`에 `jti` 클레임 추가 — 토큰 중복 생성 버그 수정)
- `backend/tests/integration/test_token_service.py` (신규 생성: 12개 테스트)
- `specs/001-ai-code-learning-platform/tasks.md` (T026 완료 체크)

## TDD 결과
- **RED**: `TokenService`/`InvalidTokenError`가 없는 상태에서 테스트를 먼저 작성 → `ImportError: cannot import name 'InvalidTokenError'`로 수집 단계 실패 확인.
- **GREEN**: `InvalidTokenError`, `TokenService` 구현 후 재실행 → 처음엔 "같은 초 안에 발급된 토큰 해시 충돌"로 회전 테스트 3개가 실패했고, 원인을 찾아 `jti` 클레임을 추가해 전부 통과시켰습니다.
  - 커버리지: `token_service.py` 100%, `exceptions.py` 100%(신규 `InvalidTokenError` 포함).
  - 발급: access/refresh 토큰 유효성, DB에 해시만 저장(평문 미저장) 확인
  - 검증: 정상 토큰 통과, refresh 토큰을 access 자리에 넣으면 거부, 깨진 토큰 거부, 만료된 토큰 거부
  - 회전: 새 토큰 쌍 발급, 기존 토큰 revoked 처리, 이미 취소된 토큰 재사용 거부, 모르는(DB에 없는) 토큰 거부, DB 기준 만료된 토큰 거부
- 백엔드 전체 테스트(27개, 기존 T025 포함) 재실행 → 전부 통과, 회귀 없음 확인.
- `ruff check`, `black --check` 모두 통과.
- 저장소가 git 초기화 전이라 RED/GREEN 커밋은 생성하지 않았습니다(T025와 동일).

## 기술 결정
- **발급/회전 시 하나의 DB 트랜잭션으로 처리**: `rotate_refresh_token`은 "기존 토큰 취소 + 새 토큰 저장"을 한 번의 `commit()`으로 묶었습니다. 둘을 따로 커밋하면 중간에 서버가 죽었을 때 "취소는 됐는데 새 토큰은 없는" 상태가 생길 수 있기 때문입니다.
- **실패 이유를 하나의 예외(`InvalidTokenError`)로 통일**: 서명 오류·만료·회전·존재하지 않음을 구분하지 않고 전부 같은 예외로 던집니다. `UserService.login`과 동일한 설계 원칙(T025 보고서 참고)으로, 공격자가 오류 메시지로 토큰 상태를 추측하지 못하게 합니다.
- **`jti` 클레임 추가(T012 보강)**: 토큰 내용이 완전히 같으면 해시도 같아져 DB `UNIQUE` 제약과 충돌하는 실제 버그를 발견했습니다. 토큰마다 무작위 고유값을 넣는 것은 JWT 표준 관행(RFC 7519 "jti")이라 범위를 벗어나지 않는 선에서 바로잡았습니다.
- **DB 만료 시각을 JWT `exp`와 별도로 검사**: JWT 자체의 서명 만료 외에도 DB의 `expires_at`을 한 번 더 확인합니다. 두 값은 발급 시 동일하게 맞춰지지만, 운영 중 DB 레코드만 강제로 무효화(예: 보안 사고 대응)해야 하는 경우를 대비한 이중 안전장치입니다.

## 비고
- T027(인증 의존성)과 T028~T031(API 엔드포인트)이 이 `TokenService`를 그대로 가져다 쓸 수 있습니다. 로그인/회원가입 성공 후 `issue_tokens(user.id)`를 호출하고, 보호된 라우트에서는 `verify_access_token`을, 토큰 재발급 엔드포인트에서는 `rotate_refresh_token`을 사용하면 됩니다.
- 레이트 리밋이나 "여러 기기 동시 로그인" 정책은 이번 범위 밖입니다(요구사항에 명시되지 않음).
