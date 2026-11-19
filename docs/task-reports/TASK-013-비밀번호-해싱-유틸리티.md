# TASK-013. 비밀번호 해싱 유틸리티 (bcrypt)

## 상태
완료

## 날짜
2026-10-30

## 작업 요약
비밀번호를 데이터베이스에 그대로 저장하면, DB가 유출되는 순간 모든 사용자의 비밀번호가 그대로 노출됩니다. 그래서 비밀번호를 "원래대로 되돌릴 수 없는 암호화된 형태"로 바꿔서 저장합니다. 이걸 "해싱"이라고 하고, bcrypt는 그중에서도 가장 널리 쓰이는 방식입니다. 비유하자면, 비밀번호를 "완전히 섞은 뒤 다시는 못 풀게 만드는 분쇄기"에 넣는 것과 비슷한데, 같은 비밀번호를 넣어도 매번 다른 "섞인 결과"가 나오게 해서(salt), 두 사람이 같은 비밀번호를 쓰더라도 저장된 값은 서로 달라집니다.

`backend/src/utils/security.py`에 두 함수를 만들었습니다.

1. **`hash_password(password)`**: 평문 비밀번호를 bcrypt로 해싱합니다 (cost factor 12 — constitution에 명시된 값).
2. **`verify_password(plain_password, hashed_password)`**: 로그인 시 입력한 평문 비밀번호가, 저장된 해시와 같은 원본에서 나온 것인지 확인합니다 (해시를 다시 평문으로 되돌리는 게 아니라, 같은 방식으로 다시 섞어봤을 때 결과가 일치하는지 비교하는 방식입니다).

## 변경 파일
- `backend/src/utils/security.py` (신규 생성)
- `backend/requirements.txt` (수정: `bcrypt==4.0.1` 명시적 고정 추가 — 아래 "기술 결정" 참고)

## TDD 결과
- 해싱 유틸도 보안 관련 동작이라, 실제 값으로 직접 실행해 검증했습니다.
  - **(최초 실행 시 실패 발견)** `ruff check`/`black --check`는 통과했지만, 실제로 `hash_password()`를 호출하자 `AttributeError: module 'bcrypt' has no attribute '__about__'` → `ValueError: password cannot be longer than 72 bytes`라는 에러로 완전히 실패했습니다. 아래 "기술 결정"에 원인과 조치를 기록합니다.
  - **원인 수정 후 재검증**:
    - 올바른 비밀번호로 `verify_password()` → `True`
    - 틀린 비밀번호로 `verify_password()` → `False`
    - 같은 비밀번호를 두 번 해싱 → 매번 다른 해시값 생성(salt 랜덤화 확인), 그런데도 둘 다 원래 비밀번호로 검증 성공
    - 72바이트를 초과하는 비밀번호(100자) → 에러 없이 정상 처리됨 (passlib가 내부적으로 bcrypt의 72바이트 제한에 맞춰 처리)
    - 생성된 해시가 `$2b$12$...` 형식 → bcrypt 변형 `2b`, cost factor `12`로 정확히 생성됨을 확인
- 저장소가 아직 git으로 초기화되지 않아 관련 커밋은 생성하지 않았습니다.
- 테스트 커버리지: 해당 없음 (pytest 자동화 테스트는 T025 UserService 등 실제 사용처에서 함께 작성될 예정)

## 기술 결정
- **`bcrypt==4.0.1` 명시적 버전 고정 (중요 버그 수정)**: T002에서 `requirements.txt`에 `passlib[bcrypt]==1.7.4`만 적어뒀는데, 이 extra는 `bcrypt`의 버전을 못박지 않아서 pip가 최신 버전(`bcrypt==5.0.0`)을 설치했습니다. 그런데 **passlib 1.7.4(2020년 출시)는 bcrypt 4.1 이후 버전과 호환되지 않는 알려진 문제**가 있습니다 — bcrypt 4.1부터 `bcrypt.__about__` 모듈이 제거됐는데, passlib가 내부적으로 이 속성을 읽어서 버전을 확인하려다 실패하고, 그 결과 passlib의 내부 자가진단 로직(72바이트 처리 버그 감지)이 오동작해서 실제 해싱 자체가 `ValueError`로 깨지는 것을 발견했습니다. passlib는 2020년 이후 업데이트가 거의 없는 프로젝트라 상위 호환 수정이 나올 가능성이 낮아, `bcrypt`를 passlib 1.7.4와 호환되는 `4.0.1`로 고정하는 방식으로 해결했습니다. (T002에서 celery/redis 버전 충돌을 고친 것과 같은 종류의 조치입니다.) 두 가상환경(`venv`, `.venv`) 모두에 재설치해 반영했습니다.
- **`bcrypt__rounds=12`**: constitution(V장, Security)과 data-model.md("bcrypt hashed password (cost factor 12)") 양쪽에 명시된 값을 그대로 사용했습니다.
- **`passlib.context.CryptContext` 사용**: bcrypt 라이브러리를 직접 쓰는 대신 passlib로 감싼 이유는, 향후 해싱 알고리즘을 교체하거나(예: argon2 추가) 여러 스킴을 점진적으로 마이그레이션해야 할 때 `CryptContext`가 "저장된 해시가 어떤 알고리즘으로 만들어졌는지"를 자동으로 인식해 처리해주기 때문입니다. (단, 이번 버그 때문에 passlib의 "오래된 프로젝트"라는 리스크가 실제로 드러났다는 점은 비고에 남깁니다.)

## 비고
- **passlib + 최신 bcrypt 비호환 이슈는 알려진 미해결 문제**입니다. 만약 나중에 `pip install -r requirements.txt`를 다시 실행하거나 다른 패키지가 `bcrypt`를 더 최신 버전으로 끌어올리면 이 버그가 재발할 수 있습니다. `requirements.txt`에 `bcrypt==4.0.1`을 명시적으로 고정해뒀으니, 이 줄을 지우지 않도록 주의가 필요합니다.
- 72바이트를 초과하는 비밀번호는 bcrypt 알고리즘 자체의 한계로 뒷부분이 잘려서 처리됩니다. 사용자가 72바이트보다 긴 비밀번호를 설정해도 에러 없이 동작하지만, 실질적으로는 앞 72바이트만 비교에 사용됩니다. 회원가입 폼(T032, 추후 Task)에서 비밀번호 길이 제한을 안내하는 것을 고려할 수 있습니다.
- `password_hash` 컬럼은 data-model.md에서 `VARCHAR(255)`로 정의되어 있고, bcrypt 해시 결과는 항상 60자 고정 길이라 컬럼 크기 문제는 없습니다.
