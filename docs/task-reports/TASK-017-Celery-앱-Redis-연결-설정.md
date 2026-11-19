# TASK-017. Celery 앱 및 Redis 연결 설정

## 상태
완료

## 날짜
2026-11-02

## 작업 요약
AI로 7챕터짜리 학습 문서를 만드는 작업은 최대 3분까지 걸릴 수 있습니다(research.md). 사용자가 "업로드" 버튼을 누르고 3분 동안 화면이 멈춰있으면 안 되니까, 이런 "시간이 오래 걸리는 일"은 별도의 "일꾼(Celery worker)"에게 맡기고, 웹 서버는 곧바로 "작업을 접수했습니다"라고 응답합니다. Celery가 바로 이 "일꾼에게 일을 전달하고 결과를 받아오는" 시스템이고, Redis는 그 일을 전달하는 "우편함" 역할을 합니다.

`backend/src/tasks/celery_app.py`에 Celery 앱을 설정했습니다.

1. **`celery_app = Celery("code_study", broker=REDIS_URL, backend=REDIS_URL)`**: `REDIS_URL`(`.env.example`에 정의됨)을 통해 Redis를 "일 전달함"(broker)과 "결과 보관함"(backend) 양쪽으로 사용합니다.
2. **4개의 큐(queue) 분리**: constitution(III장)에 명시된 대로 `default`, `document_generation`, `practice_generation`, `cleanup` 큐를 미리 나눠뒀습니다. 문서 생성 작업과 연습문제 생성 작업이 서로 다른 줄에 서도록 해서, 한쪽이 밀려도 다른 쪽이 영향을 받지 않게 하기 위함입니다.
3. **`task_time_limit=300`**: 태스크 하나가 5분(300초)을 넘기면 강제로 중단시킵니다 (constitution III장 "태스크 타임아웃: 300초").

## 변경 파일
- `backend/src/tasks/celery_app.py` (신규 생성)

## TDD 결과
- Celery 설정은 "앱 객체를 만드는" 작업이라 비즈니스 로직 테스트는 의미가 없지만, "진짜로 Redis에 연결되고, 작업을 보내면 실제로 처리되는가"는 반드시 실제로 확인해야 하는 부분이라 아래와 같이 end-to-end로 검증했습니다.
  - `ruff check`, `black --check` 통과
  - **설정값 확인**: `broker_url`, `result_backend`가 둘 다 `redis://localhost:6379/0`로 정확히 설정됨, `task_time_limit=300`, `task_routes`에 3개 큐 매핑 모두 정확히 반영됨을 확인
  - **브로커 연결 확인**: `celery_app.connection().ensure_connection()`으로 실제 Redis 서버에 연결 성공
  - **전체 라운드트립 검증(가장 중요)**: 임시로 간단한 테스트 태스크(`_verify_tmp_add(a, b)`)를 추가하고, 실제로 `celery -A src.tasks.celery_app worker --pool=solo`로 워커를 띄운 뒤, `.delay(2, 3)`으로 태스크를 전송 → `.get(timeout=10)`으로 결과(`5`)를 정확히 받아옴을 확인. 워커 로그에도 `Task _verify_tmp_add[...] succeeded in 0.0s: 5`로 동일하게 기록됨을 확인했습니다. 즉 브로커 연결뿐 아니라 "전송 → 워커가 받음 → 실행 → 결과 저장 → 결과 조회"까지 전체 경로가 실제로 동작함을 증명했습니다.
  - 검증 후 임시 테스트 태스크(`_verify_tmp_add`)는 제거하고 원래 설정만 남겼습니다.
  - **중간에 발견한 환경 이슈**: 검증 시작 시 Docker Desktop이 다시 꺼져 있었습니다(이전 세션들에서 반복적으로 발생). Docker Desktop을 재실행하고 엔진 기동을 기다린 뒤 `docker compose up -d`로 PostgreSQL/Redis 컨테이너를 복구했습니다.
  - **(추가 검증, 2026-11-02) 실제 병렬 처리 확인**: 사용자 요청으로, Redis 상태 확인 → 10초 소요되는 임시 테스트 작업(`_verify_tmp_sleep(job_id, seconds=10)`) 추가 → 워커 실행 → 5개 작업 동시 전송의 4단계를 추가로 검증했습니다.
    - Redis 컨테이너 `PONG` 응답으로 정상 확인
    - 워커를 `--pool=threads --concurrency=5`로 띄움 (Windows에서 `--pool=solo`는 동시성 1로 순차 처리되므로, 진짜 병렬 처리를 보려면 스레드 풀이 필요)
    - `_verify_tmp_sleep.delay(i, 10)`을 5번 연속 호출해 작업 5개를 동시 전송, 각각의 `AsyncResult.get(timeout=30)`으로 결과 수집
    - **결과**: 전체 소요 시간 12.24초 (순차 처리였다면 5×10=50초가 걸렸어야 함). 5개 작업 모두 시작 시각이 0.12~0.14초 사이, 종료 시각이 10.13~10.14초 사이로 거의 완전히 겹침 — 워커 로그의 `received`/`succeeded` 타임스탬프에서도 동일하게 확인(5개 모두 11:25:08.45~08.48에 수신, 11:25:18.52~18.55에 완료)
    - 검증 후 `_verify_tmp_sleep` 임시 태스크는 제거하고 `celery_app.py`를 원래 상태로 복원
- 저장소가 아직 git으로 초기화되지 않아 관련 커밋은 생성하지 않았습니다.
- 테스트 커버리지: 해당 없음 (앱 설정 파일, 실제 Celery 태스크 로직은 아직 없음)

## 기술 결정
- **Windows에서 `--pool=solo` 사용**: Celery의 기본 워커 풀(prefork)은 `fork()` 시스템 콜에 의존하는데, Windows에는 이 기능이 없어 동작하지 않습니다. 검증을 위해 Windows에서 공식적으로 권장하는 `--pool=solo` 옵션으로 워커를 띄웠습니다. 이는 로컬 개발/테스트용 선택이며, 운영 환경(주로 Linux 컨테이너)에서는 기본 풀을 그대로 쓸 수 있습니다. 이 내용은 quickstart.md의 Celery 실행 안내에 추가하면 Windows 개발자에게 도움이 될 것으로 보입니다.
- **병렬 처리 검증 시에는 `--pool=threads --concurrency=5` 사용**: `--pool=solo`는 이름 그대로 "혼자" 처리하는 풀이라 동시성이 1로 고정되어, 여러 작업을 동시에 보내도 순서대로 하나씩 처리됩니다(진짜 동시 처리 검증에는 적합하지 않음). Windows에서 `prefork`를 쓸 수 없는 대신, `threads` 풀(Python 표준 `ThreadPoolExecutor` 기반)로 동시성 5를 줘서 5개 작업이 실제로 겹쳐서 처리되는지 확인했습니다. I/O 대기가 많은 작업(API 호출, DB 조회, `sleep` 등)에는 스레드 풀로도 충분한 병렬성을 얻을 수 있습니다.
- **`broker_connection_retry_on_startup=True`**: 최신 Celery(5.4+)에서 이 옵션을 명시하지 않으면 "향후 기본값이 바뀐다"는 경고가 뜹니다. 워커가 시작될 때 Redis가 아직 안 떠 있어도(예: `docker compose up` 순서가 늦는 경우) 재시도하도록 명시적으로 켜뒀습니다.
- **큐 이름/태스크 타임아웃은 constitution을 그대로 반영**: 숫자나 이름을 임의로 고르지 않고, my_constitution.md III장에 이미 정해진 값(큐 4종, 타임아웃 300초)을 그대로 사용했습니다.
- **`task_routes`의 대상 모듈이 아직 존재하지 않음**: `src.tasks.document_generation`, `src.tasks.practice_generation`, `src.tasks.trash_cleanup`은 각각 T094, T118, T172에서 만들어질 예정입니다. Celery의 `task_routes`는 문자열 패턴 매칭이라 해당 모듈이 지금 존재하지 않아도 설정 자체에는 문제가 없습니다 — 나중에 그 모듈들이 만들어지고 해당 큐의 워커가 그 모듈을 구독하면 자동으로 올바른 줄로 분배됩니다.

## 비고
- Celery Beat(스케줄러, T172 Trash Cleanup Job이 "매일 새벽 2시 UTC"에 실행되도록 하는 부분)는 이번 Task 범위가 아닙니다. quickstart.md에 `celery -A src.tasks.celery_app beat` 명령이 이미 안내되어 있어, T172에서 스케줄 정의만 추가하면 바로 쓸 수 있는 구조입니다.
- 실제 운영에서 워커를 띄울 때는 `celery -A src.tasks.celery_app worker -Q default,document_generation,practice_generation,cleanup`처럼 어떤 큐를 구독할지 명시해야 합니다(옵션 없이 띄우면 `default` 큐만 구독합니다). 이번 검증에서도 큐 이름을 지정하지 않아 `default` 큐만 구독한 상태로 테스트했고, 이는 의도된 대로였습니다.
