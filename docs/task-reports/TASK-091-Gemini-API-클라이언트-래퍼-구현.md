# TASK-091. Gemini API 클라이언트 래퍼 구현

## 상태
완료

## 날짜
2026-11-17

## 작업 요약
`backend/src/services/ai/gemini_client.py`에 Google Gemini API 호출을 감싸는 `GeminiClient`를 구현했습니다. 상위 서비스(T092 프롬프트, T093 DocumentGenerationService, 이후 Q&A)가 SDK 세부사항을 몰라도 되도록 다음을 캡슐화합니다.

- **설정**: `GOOGLE_API_KEY` 환경변수(`.env`와 동일 키 이름) 또는 생성자 인자로 API 키 주입. 키가 없으면 `GeminiConfigurationError`. 기본 모델 `gemini-3-flash-preview`(research.md 결정), API 버전 `v1beta` 고정.
- **`generate_text(prompt, system_instruction, temperature, max_output_tokens)`**: 일반 텍스트 생성.
- **`generate_json(...)`**: `response_mime_type="application/json"`(JSON 모드)로 요청하고 응답을 `dict`로 파싱. 마크다운 코드펜스(```json ... ```) 제거, 비JSON/비객체 응답은 `GeminiResponseError`.
- **에러 변환**: SDK의 `APIError`를 `GeminiAPIError(status_code, retryable)`로 변환. 408/429/5xx는 `retryable=True`, 그 외 4xx는 `False` — T093의 지수 백오프 재시도 로직이 이 플래그만 보고 판단할 수 있도록 함. 빈 응답은 `GeminiResponseError`.
- **테스트 용이성**: 생성자에 SDK 클라이언트 객체를 주입할 수 있어 단위 테스트는 네트워크 없이 Fake로 수행.

테스트는 `backend/tests/unit/test_gemini_client.py`에 21개(초기화/텍스트 생성/JSON 생성/에러 변환) 작성했으며, 추가로 `.env`의 실제 키로 1회 라이브 스모크 호출을 수행해 `generate_json`이 `{'status': 'ok', 'model_check': True}`를 정상 반환함을 확인했습니다.

## 변경 파일
- `backend/src/services/ai/gemini_client.py` (신규 생성)
- `backend/tests/unit/test_gemini_client.py` (신규 생성)
- `backend/requirements.txt` (`google-generativeai==0.3.0` → `google-genai==3.4.0`)
- `specs/001-ai-code-learning-platform/tasks.md` (T091 `[X]` 체크)

## TDD 결과
- RED 커밋: 해당 없음 — 현재 작업 디렉토리가 git 저장소가 아니어서(`git rev-parse` 실패) 커밋 불가. RED 상태는 `pytest`로 확인함(1차: `ModuleNotFoundError: src.services.ai.gemini_client`, 2차: `API_VERSION` 미존재 ImportError).
- GREEN 커밋: 해당 없음(동일 사유). 구현 후 `tests/unit/test_gemini_client.py` 21개 통과, 전체 단위 테스트 120개 통과.
- REFACTOR 커밋: 해당 없음(동일 사유). 테스트 파일 E501 2건 정리(패치 경로 상수화) 후 `ruff check` 통과, 테스트 재통과.
- 테스트 커버리지: `src/services/ai/gemini_client.py` **100%** (61 stmts, 0 miss)

TDD 사이클은 두 번 돌았습니다. ① 래퍼 전체(RED→GREEN→REFACTOR). ② 라이브 스모크에서 `404 models/gemini-3-flash-preview is not found for API version v1`을 발견 → `v1beta` 고정 테스트를 먼저 추가(RED) → `http_options=HttpOptions(api_version="v1beta")` 구현(GREEN) → 스모크 재호출 성공.

## 기술 결정
1. **SDK 교체: `google-generativeai==0.3.0` → `google-genai==3.4.0`**
   - 기존 고정 버전은 2023년 말 레거시 SDK로 `system_instruction`과 JSON 모드(`response_mime_type`)를 지원하지 않으며 현재 deprecated. research.md가 요구하는 "시스템 인스트럭션 + JSON 모드 7챕터 구조화 출력"을 구현하려면 공식 후속 SDK가 필요함.
   - `src/` 내 레거시 SDK 참조는 없었으므로 다른 코드 영향 없음. `httpx==0.25.0` 핀은 그대로 유지됨(의존성 충돌 없음).
   - 신규 `.venv`에서 `pip install -r requirements.txt` 재실행 필요.
2. **API 버전 `v1beta` 고정**
   - 실제 키로 모델 목록을 조회한 결과 `gemini-3-flash-preview`는 `v1beta`에만 존재(v1 목록에는 없음). SDK 기본값(v1)으로는 404. 프리뷰 모델 사용이 스펙 결정이므로 클라이언트에서 고정하고 코드 주석으로 이유를 남김.
3. **재시도 로직은 클라이언트에 넣지 않음**
   - tasks.md가 재시도(지수 백오프, 최대 3회)를 T093 `DocumentGenerationService` 책임으로 명시. 이중 재시도를 피하기 위해 클라이언트는 `GeminiAPIError.retryable` 분류만 제공하고 실제 재시도는 T093에서 구현.
4. **에러 계층**: `GeminiError` 베이스 아래 `GeminiConfigurationError` / `GeminiResponseError` / `GeminiAPIError` — `services/auth/exceptions.py`의 기존 예외 계층 스타일과 동일.
5. **코드펜스 제거**: JSON 모드에서도 모델이 간혹 ```json 펜스를 붙이는 경우에 대비한 방어 로직(파싱 실패로 인한 불필요한 재시도 방지).

## 비고
- API 키는 `.env`의 `GOOGLE_API_KEY`를 사용하며, 코드·테스트·보고서 어디에도 키 값을 기록하지 않음. 라이브 스모크 스크립트는 레포 밖 임시 디렉토리에서 실행 후 커밋 대상 아님.
- 스모크 호출 중 `max_output_tokens=32~64`로 제한하면 gemini-3 계열의 thinking 토큰 때문에 출력이 잘리는 현상을 관찰함. T092/T093에서 7챕터 문서 생성 시 `max_output_tokens`를 작게 두지 말 것.
