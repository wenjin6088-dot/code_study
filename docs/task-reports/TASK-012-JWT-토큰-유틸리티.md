# TASK-012. JWT 토큰 유틸리티 (발급/검증/디코드)

## 상태
완료

## 날짜
2026-10-30

## 작업 요약
로그인을 하면 서버가 "이 사람이 누구인지 증명하는 신분증"을 발급해줘야 합니다. 그 신분증이 JWT(JSON Web Token)입니다. 신분증 앞면에는 "누구인지(sub)", "언제까지 유효한지(exp)", "어떤 용도인지(type)"가 암호학적으로 서명되어 찍혀 있어서, 아무나 위조할 수 없습니다.

이번 Task에서는 이 신분증을 **만들고(발급)**, **진짜인지 확인하고(검증)**, **내용을 읽는(디코드)** 기능을 `backend/src/utils/jwt.py`에 만들었습니다.

1. **`create_access_token(subject)`**: 15분짜리 "임시 출입증"을 만듭니다. API 요청마다 이 토큰을 들고 다니며 "나 로그인한 사람이야"를 증명합니다.
2. **`create_refresh_token(subject)`**: 7일짜리 "재발급 카드"를 만듭니다. 임시 출입증이 만료되면, 이 카드로 새 임시 출입증을 다시 발급받습니다.
3. **`decode_access_token(token)` / `decode_refresh_token(token)`**: 받은 토큰이 진짜인지(서명 확인), 아직 유효한지(만료 확인), 그리고 "출입증을 재발급 카드로 쓰려는" 것처럼 용도를 혼동해서 쓰려는 건 아닌지까지 확인하고, 안에 담긴 내용(누구인지 등)을 꺼내줍니다.

두 종류의 토큰은 **서로 다른 비밀키**(`JWT_SECRET_KEY`, `JWT_REFRESH_SECRET` — T005에서 만든 `.env.example`에 이미 정의되어 있음)로 서명하고, 토큰 안에 `"type": "access"` 또는 `"type": "refresh"`라는 표시를 넣어서, 출입증을 재발급 카드로 몰래 바꿔 쓰는 공격(토큰 타입 혼동 공격)을 막았습니다.

## 변경 파일
- `backend/src/utils/jwt.py` (신규 생성)

## TDD 결과
- JWT 유틸은 암호학적 서명/만료/타입 검증이 핵심이라, 이런 "보안 관련 분기"는 반드시 공격 시나리오를 흉내 낸 실제 실행으로 검증해야 의미가 있습니다. RED-GREEN-REFACTOR 형식의 pytest 파일 작성 대신(추후 서비스 계층에서 통합될 때 함께 작성될 예정), 아래 4가지 시나리오를 직접 실행해 확인했습니다.
  - `ruff check`(최초 `datetime.UTC` 사용 권고 2건을 `--fix`로 자동 수정), `black --check` 통과
  - **정상 발급/검증**: `create_access_token`/`create_refresh_token`으로 토큰 생성 → `decode_access_token`/`decode_refresh_token`으로 정확히 `sub`, `type`, `exp`가 담긴 payload를 꺼냄
  - **토큰 타입 혼동 방지**: access 토큰을 `decode_refresh_token()`에 넣음 → `JWTError`(서명 검증 실패)로 정확히 거부됨
  - **위조 토큰 거부**: 다른(잘못된) 비밀키로 서명한 토큰을 `decode_access_token()`에 넣음 → `JWTError: Signature verification failed`로 정확히 거부됨
  - **만료 토큰 거부**: 만료 시각을 1분 전으로 설정한 토큰을 디코드 시도 → `ExpiredSignatureError`로 정확히 거부됨
- 저장소가 아직 git으로 초기화되지 않아 관련 커밋은 생성하지 않았습니다.
- 테스트 커버리지: 해당 없음 (pytest 자동화 테스트는 T025 UserService/T026 TokenService 등 실제 사용처와 함께 작성될 예정이며, 이번에는 수동 스크립트로 핵심 보안 분기를 검증했습니다.)

## 기술 결정
- **access/refresh에 서로 다른 비밀키 사용**: data-model.md의 RefreshToken 엔티티나 research.md 어디에도 "같은 키를 써도 된다"는 언급이 없고, `.env.example`(T005)에 이미 `JWT_SECRET_KEY`와 `JWT_REFRESH_SECRET`이 별도로 정의되어 있어 이를 그대로 활용했습니다. 키를 분리하면, 한쪽 키가 유출되어도 다른 쪽 토큰 체계는 안전합니다.
- **payload에 `"type"` 클레임 추가**: JWT 표준 클레임(`sub`, `exp`)만으로는 "이 토큰이 access용인지 refresh용인지" 구분할 방법이 없습니다. 서로 다른 비밀키를 쓰기 때문에 사실상 교차 사용은 서명 단계에서 이미 막히지만, 혹시 두 비밀키가 같은 값으로 잘못 설정되는 운영 실수가 있어도 `type` 체크가 2차 방어선이 되도록 했습니다 (심층 방어).
- **`os.environ[...]`로 필수 환경변수 처리 (fallback 기본값 없음)**: T010(`session.py`)의 `DATABASE_URL`은 로컬 개발 편의를 위해 기본값을 뒀지만, JWT 서명 비밀키는 절대 하드코딩된 기본값을 두면 안 되는 보안 값이라 판단해 `os.environ["JWT_SECRET_KEY"]` 형태로 작성했습니다. 환경변수가 없으면 `KeyError`로 즉시 실패하며, 이는 "토큰 비밀키 없이 조용히 안전하지 않은 기본값으로 동작"하는 것보다 훨씬 안전한 실패 방식입니다.
- **만료 검증을 python-jose에 위임**: `jwt.decode()`는 `exp` 클레임을 자동으로 확인해 만료 시 `ExpiredSignatureError`(JWTError의 하위 클래스)를 발생시킵니다. 직접 만료 시각을 비교하는 코드를 따로 작성하지 않고 라이브러리의 검증된 구현을 그대로 사용했습니다(YAGNI + 보안 모범사례).
- **`timezone.utc` 대신 `datetime.UTC` 사용**: ruff(UP017)가 Python 3.11+에서 추가된 `datetime.UTC` alias 사용을 권고해 그대로 반영했습니다. 동작은 동일합니다.

## 비고
- 이 모듈은 아직 실제 사용자 DB나 API와 연결되어 있지 않습니다. 실제 로그인 흐름에서의 사용은 T025(UserService)/T026(TokenService)/T028-031(인증 API 엔드포인트)에서 이뤄질 예정입니다.
- `decode_access_token`/`decode_refresh_token`이 던지는 예외(`JWTError`)를 HTTP 401 응답으로 변환하는 처리는 이번 Task 범위가 아니며, T027(인증 의존성) 또는 T016(에러 핸들링 미들웨어)에서 다뤄질 것으로 예상됩니다.
