# TASK-093. DocumentGenerationService 재시도 로직 구현

## 상태
완료

## 날짜
2026-11-18

## 작업 요약
`backend/src/services/document/document_generation_service.py`에 `DocumentGenerationService`를 구현했습니다. T092 `build_document_prompt(...)`로 프롬프트를 만들고 T091 `GeminiClient.generate_json(...)`을 호출해 7챕터 JSON 문서를 받아오며, FR-090("AI 요청 실패 시 지수 백오프로 최대 3회 자동 재시도")을 만족하는 재시도 로직을 담당합니다. T094(Celery 비동기 태스크)가 DB/파일 I/O를 맡고, 이 서비스는 순수하게 "코드 파일 목록 → 검증된 문서 dict" 변환과 재시도만 책임지도록 분리했습니다.

- **공개 API**: `generate_document(files: list[CodeFileInput], *, detected_language: str, complexity_level: str) -> dict[str, Any]`. 내부 DB 세션이나 파일시스템에 의존하지 않아 단위 테스트가 순수 로직만으로 가능.
- **재시도 대상**:
  - `GeminiAPIError`인데 `retryable=True`인 경우(408/429/500/502/503/504) — 재시도.
  - `GeminiAPIError`인데 `retryable=False`인 경우(그 외 4xx) — 즉시 예외 전파, 재시도하지 않음.
  - `GeminiResponseError`(빈 응답/JSON 파싱 실패) — 모델이 다시 시도하면 유효한 JSON을 낼 수 있으므로 재시도.
  - `InvalidDocumentStructureError`(이 서비스가 새로 정의) — 응답 JSON에 `chapter1~7` 키가 모두 있는지 T092 `CHAPTER_KEYS` 기준으로 검증하고, 누락 시 재시도.
  - `GeminiConfigurationError`(API 키 누락 등 설정 오류)는 재시도 대상에서 **제외** — 재시도해도 동일하게 실패할 구조적 오류이므로 즉시 전파.
- **지수 백오프**: `initial_delay_seconds * (backoff_multiplier ** attempt)`. 기본값 `max_retries=3`, `initial_delay_seconds=1.0`, `backoff_multiplier=2.0` → 1초, 2초, 4초 순으로 대기하며 최대 4회 시도(최초 1회 + 재시도 3회).
- **테스트 용이성**: `sleep: Callable[[float], Awaitable[None]] = asyncio.sleep`을 생성자 주입으로 받아, 테스트에서는 실제로 대기하지 않는 `FakeSleep`으로 대체해 지연을 기록·검증.

## 변경 파일
- `backend/src/services/document/document_generation_service.py` (신규 생성)
- `backend/tests/unit/test_document_generation_service.py` (신규 생성)
- `specs/001-ai-code-learning-platform/tasks.md` (T093 `[X]` 체크)
- `docs/task-reports/TASK-093-DocumentGenerationService-재시도로직-구현.md` (본 보고서)

## TDD 결과
- RED 커밋: 해당 없음 — 작업 디렉토리가 git 저장소가 아니어서 커밋 불가(`check-prerequisites.ps1` 실행 시 "Git repository not detected" 경고로 확인). 대신 `pytest` 실행으로 RED 확인: `ModuleNotFoundError: No module named 'src.services.document.document_generation_service'`.
- GREEN 커밋: 해당 없음(동일 사유). 구현 후 테스트 13개 전부 통과.
- REFACTOR 커밋: 해당 없음(동일 사유). `ruff check` E501(라인 95자) 1건을 `except` 튜플과 백오프 계산식 줄바꿈으로 정리 후 재통과, 전체 단위 테스트 152개 재통과.
- 테스트 커버리지: `src/services/document/document_generation_service.py` **100%** (38 stmts, 0 miss).
- MyPy: 이 가상환경에 `mypy`가 설치되어 있지 않아 실행 불가(`No module named mypy`). 타입 힌트는 constructor/메서드 시그니처 전체에 부여했으며, 추후 MyPy 설치 시 재검증 필요.

## 기술 결정
1. **서비스를 DB/Celery/파일시스템과 완전히 분리**: `generate_document`는 이미 메모리에 올라온 `CodeFileInput` 목록만 받는다. T094(Celery 태스크)가 `CodeFile.storage_path`에서 실제 파일을 읽어 `CodeFileInput`으로 변환하고, 결과를 `LearningDocument.content`에 저장하는 역할을 맡는다. 이렇게 분리해야 이 서비스를 DB 없이 순수 단위 테스트할 수 있고, 모듈별 단일 책임(헌법 III. Modular Monolith — "서비스 레이어가 비즈니스 로직을 캡슐화") 원칙에 맞음.
2. **재시도 판단을 예외 타입으로 분기**: `GeminiAPIError.retryable` 플래그(T091에서 상태 코드로 이미 분류됨)를 그대로 신뢰하고, 추가로 "응답은 받았지만 구조가 틀린 경우"(`GeminiResponseError`, `InvalidDocumentStructureError`)도 재시도 대상에 포함시켰다. AI 생성형 API는 같은 입력에도 매번 다른 출력을 내므로, 한 번의 JSON 파싱 실패나 챕터 누락이 영구적 실패를 의미하지 않는다고 판단.
3. **`InvalidDocumentStructureError`를 서비스 자체 예외로 신설**: data-model.md의 `valid_content_structure` CHECK 제약(7개 챕터 키 필수)을 DB insert 시점이 아니라 생성 직후 애플리케이션 레벨에서 먼저 검증해, DB 제약 위반으로 실패하기 전에 재시도 기회를 준다. `GeminiError` 계열에 억지로 끼워 넣지 않고 이 서비스의 `DocumentGenerationError` 계열로 별도 정의해 책임 경계를 명확히 함.
4. **지연 함수(`sleep`)를 생성자 주입으로 설계**: `asyncio.sleep`을 기본값으로 쓰되 테스트에서 교체 가능하게 해, 실제로 1+2+4초를 기다리지 않고도 백오프 수열을 검증(FR-090의 "지수 백오프"를 수치로 증명). `max_retries`/`initial_delay_seconds`/`backoff_multiplier`도 모두 생성자 옵션으로 노출해 T094/T095에서 재시도 정책을 조정할 수 있게 함.
5. **재시도 횟수 "최대 3회"를 "최초 시도 포함 최대 4회 호출"로 해석**: FR-090 문구("최대 3회 자동 재시도")를 "최초 시도 1회 + 재시도 3회"로 해석했다. 테스트(`test_default_max_retries_is_three`)로 이 해석을 명시적으로 고정해 두었으니, 다른 해석이 필요하면 이 테스트부터 수정.

## 비고
- Celery 태스크(T094)에서 이 서비스를 호출할 때는 `LearningDocument.generation_status`를 `in_progress` → `completed`/`failed`로, 실패 시 `generation_error`에 마지막 예외 메시지를 기록해야 함(FR-094: "3회 재시도 실패 후 명확한 에러 메시지 + 수동 재시도 옵션").
- Q&A 쪽 재시도(FR-093 "Response delayed, retrying...")는 별도 서비스(T122 전후 예정)에서 다루며, 이 서비스의 백오프 파라미터 기본값을 재사용할 수 있음.

## 검증 메모 (2026-11-18 추가)
Docker(PostgreSQL 15 + Redis)를 기동하고 `alembic upgrade head`로 실 스키마를 적용한 뒤, 실제 Gemini API로 35줄짜리 Python 샘플(`BankAccount` 클래스)에 대해 수동 검증 스크립트(레포 밖, 임시 스크래치패드에 작성·실행 후 폐기)로 아래를 확인했습니다. 이 스크립트는 `task_id` 조회·상태 전환 등 T094가 맡을 오케스트레이션을 임시로 흉내 낸 것일 뿐, 운영 코드에는 반영하지 않았습니다.

- **상태 전환**: `pending` → `in_progress` → `completed` 정상 전환 확인.
- **7챕터 저장**: 생성된 `LearningDocument.content`에 `chapter1~7` 모두 존재(O), 챕터별 본문 길이 112~3642자.
- **존재하지 않는 task_id**: 조회 시 명확한 한국어 메시지("Task를 찾을 수 없습니다 (task_id=...)")와 함께 예외 발생을 확인. 단, 이는 스크립트 자체 정의 예외일 뿐 실제 API의 404 응답은 아직 없음(T097에서 구현 예정).
- **DB 제약 관련 발견(T094에 전달 필요)**: `learning_documents.valid_content_structure` CHECK 제약이 `content`에 `chapter1~7` 키가 항상 존재해야 한다고 강제하므로, `generation_status='pending'`으로 행을 먼저 만들 때도 content를 완전히 비워 둘 수 없음. 검증 스크립트는 `{"chapter1": {}, ..., "chapter7": {}}` 형태의 플레이스홀더로 삽입 후 완료 시 실제 내용으로 덮어쓰는 방식을 택했으며, T094도 동일한 방식(또는 제약 자체 재검토)이 필요함.
- 테스트에 사용한 DB 행/스토리지 파일은 검증 후 삭제해 원래 상태로 되돌렸음.
