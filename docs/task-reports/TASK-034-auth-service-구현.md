# TASK-034. 인증 서비스(auth-service) 구현

## 상태
완료

## 날짜
2026-11-09

## 작업 요약
프론트엔드에서 백엔드 인증 API를 호출하는 얇은 함수 모음을 `frontend/src/services/auth-service.ts`에 만들었습니다. `register`, `login`, `logout`, `getCurrentUser`, `refreshToken` 5개 함수가 있고, 전부 기존에 있던 `frontend/src/services/api-client.ts`의 `apiClient`(axios 인스턴스, `withCredentials: true`로 쿠키 기반 인증을 쓰도록 이미 설정되어 있음)를 통해서만 서버와 통신합니다. 각 함수는 백엔드 라우트 하나씩과 정확히 1:1로 대응합니다.

- `register(email, password)` → `POST /auth/register`, 가입된 사용자 반환
- `login(email, password)` → `POST /auth/login`, 로그인한 사용자 반환
- `logout()` → `POST /auth/logout`, 바디 없음
- `getCurrentUser()` → `GET /auth/me`, 현재 로그인한 사용자 반환
- `refreshToken()` → `POST /auth/refresh`, 바디/반환값 없음(쿠키 갱신만 수행)

Authorization 헤더를 직접 다루는 코드는 전혀 없습니다 — 세션은 전부 HTTPOnly 쿠키로 관리되고, 이미 `apiClient`가 모든 요청에 쿠키를 자동으로 실어 보내기 때문입니다.

## 변경 파일
- `frontend/src/services/auth-service.ts` (신규 생성)

## TDD 결과
- `frontend/tests/unit/services/auth-service.test.ts`(10개 테스트, RED 상태)를 먼저 읽었습니다. 이 테스트는 `apiClient`를 모킹해서 "어떤 경로로, 어떤 바디로 호출했는지", "성공 시 `response.data`를 그대로 반환하는지", "실패 시 에러를 그대로 다시 던지는지(propagate)"를 검증합니다.
- GREEN 확인: 10개 테스트 전부 통과(함수별 성공 케이스 1개 + 실패 전파 케이스 1개, 총 5개 함수 × 2).
- Git 저장소가 아직 초기화되지 않아 커밋은 생략했습니다.

## 기술 결정
- **에러를 별도로 가공하지 않고 그대로 전파**: `apiClient`의 응답 인터셉터(기존 코드, `api-client.ts`)가 이미 서버 에러를 `Error(message)` 형태로 정규화해서 던지기 때문에, `auth-service.ts`에서 다시 try/catch로 감싸거나 메시지를 바꾸지 않았습니다. 그대로 두는 것이 가장 단순하고, 테스트도 "원래 에러 메시지가 그대로 나오는지"를 확인합니다.
- **`logout`/`refreshToken`은 반환값 없음(`void`)**: 테스트가 반환값을 검증하지 않고 호출 여부와 경로만 확인하기 때문에, 응답 바디를 파싱해서 돌려주는 코드를 추가하지 않았습니다.
- **`AuthUser` 타입을 이 파일에서 export**: RegisterForm/LoginForm/useAuth 등 다른 T032~T038 파일들이 이 타입을 `onSuccess` prop 등에서 공유해서 쓸 수 있도록 했습니다. `stores/auth-store.ts`에 있는 `User` 타입과 필드가 동일(`id`, `email`, `skillLevel`)하지만, 이 서비스 계층이 스토어 구현에 의존하지 않도록 별도로 정의했습니다.

## 비고
- 이 서비스는 순수하게 "API 호출"만 책임지고, 어떤 상태 관리(zustand)나 재시도 로직도 포함하지 않습니다. 세션 복구·자동 갱신 같은 로직은 T038 `useAuth` 훅의 책임입니다.
