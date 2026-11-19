# TASK-014. FastAPI 앱 초기화 및 CORS 설정

## 상태
완료

## 날짜
2026-10-30

## 작업 요약
지금까지 만든 DB 연결, JWT, 비밀번호 해싱 같은 "부품"들을 실제로 움직이게 할 "본체"를 만들었습니다. `backend/src/main.py`가 바로 그 본체로, 웹 서버(FastAPI 앱)를 켜는 시작점입니다.

여기에 추가로 **CORS(Cross-Origin Resource Sharing)** 설정을 넣었습니다. 브라우저는 보안상 "다른 주소(origin)에서 온 요청"을 기본적으로 차단합니다. 우리 프론트엔드(`http://localhost:5173`)와 백엔드(`http://localhost:8000`)는 포트가 달라서 브라우저 입장에서는 "서로 다른 사이트"로 취급됩니다. CORS 설정은 "이 주소에서 오는 요청은 허락해도 된다"고 백엔드가 브라우저에게 미리 알려주는 허가증입니다.

## 변경 파일
- `backend/src/main.py` (신규 생성)

## TDD 결과
- FastAPI 앱 초기화 자체는 테스트할 비즈니스 로직 함수가 아니라, "서버가 실제로 뜨고, CORS가 설계대로 동작하는가"가 유일한 의미 있는 검증이라, 실제로 `uvicorn`으로 서버를 띄워서 확인했습니다.
  - `ruff check`, `black --check` 통과
  - `uvicorn src.main:app`으로 실제 서버 기동 → "Application startup complete" 로그로 정상 기동 확인
  - `GET /openapi.json` → `200 OK` (FastAPI가 라우트 없이도 자동 제공하는 스키마 엔드포인트로, 앱이 정상 동작 중임을 확인하는 용도)
  - **허용된 origin**(`http://localhost:5173`, `.env.example`의 `ALLOWED_ORIGINS` 기본값)에서 CORS preflight(`OPTIONS`) 요청 → `200 OK`, 응답 헤더에 `access-control-allow-origin: http://localhost:5173`, `access-control-allow-credentials: true` 정확히 포함됨을 확인
  - **허용되지 않은 origin**(`http://evil.example.com`)에서 같은 요청 → `400 Bad Request`, `Disallowed CORS origin`으로 정확히 차단됨을 확인
  - 검증 후 백그라운드로 띄워둔 서버 프로세스는 정리(종료)했습니다.
- 저장소가 아직 git으로 초기화되지 않아 관련 커밋은 생성하지 않았습니다.
- 테스트 커버리지: 해당 없음 (앱 초기화 코드, 아직 비즈니스 로직 엔드포인트 없음)

## 기술 결정
- **`ALLOWED_ORIGINS`를 쉼표로 구분된 문자열로 읽어 리스트로 변환**: `.env.example`(T005)에 이미 `ALLOWED_ORIGINS=http://localhost:5173` 형태로 정의되어 있어 그 형식을 그대로 썼습니다. 여러 origin을 허용해야 할 경우(예: 운영 도메인 추가) `ALLOWED_ORIGINS=http://a.com,http://b.com`처럼 쉼표로 이어 쓰면 되도록 `.split(",")`를 사용했습니다.
- **`allow_credentials=True`**: research.md의 인증 방식(HTTPOnly 쿠키 기반 JWT)이 쿠키를 주고받으려면 브라우저가 자격 증명(쿠키)을 포함한 요청을 허용해야 합니다. 이 옵션이 꺼져 있으면 쿠키 기반 인증 자체가 동작하지 않습니다.
- **커스텀 엔드포인트(헬스체크 등)를 추가하지 않음**: T014의 범위를 "앱 초기화 + CORS + 미들웨어"로 좁게 해석했습니다. 실제 라우트 구조(`/api/v1` 등)는 T015(API 라우터 구조), 에러 핸들링은 T016의 몫이라 이번에는 건드리지 않았습니다. 검증은 FastAPI가 기본 제공하는 `/openapi.json`으로 충분히 가능했습니다.
- **에러 핸들링 미들웨어 미포함**: T014 제목에 "middleware"가 있지만, tasks.md에 "에러 핸들링 미들웨어"가 T016으로 명시적으로 분리되어 있어, 이번 Task의 "middleware"는 CORS 미들웨어를 가리키는 것으로 해석했습니다.

## 비고
- 서버가 실제로 DB(T010/T011)나 JWT/비밀번호 유틸(T012/T013)을 아직 사용하지 않습니다 — 아직 API 라우트가 없기 때문입니다. 이 부품들이 실제로 연결되는 것은 T015(라우터) 이후, 특히 T025-T031(인증 서비스/엔드포인트)에서부터입니다.
- `uvicorn src.main:app` 실행은 반드시 `backend/` 디렉토리에서 해야 합니다(quickstart.md에도 동일하게 안내되어 있음) — `src` 패키지를 찾을 수 있는 기준 경로이기 때문입니다.
