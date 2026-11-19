# TASK-035. Register 페이지 구현

## 상태
완료

## 날짜
2026-11-09

## 작업 요약
회원가입 라우트(`/register`)에서 보여줄 페이지를 `frontend/src/pages/Register.tsx`에 만들었습니다. 내용은 단순합니다 — T032에서 만든 `RegisterForm`을 그대로 렌더링하고, 가입이 성공하면(`onSuccess` 콜백) `react-router-dom`의 `useNavigate`로 `/login`으로 이동시킵니다. 실패했을 때 처리는 전부 `RegisterForm` 내부가 알아서 하므로(에러 문구 표시, 버튼 재활성화) 이 페이지는 아무것도 하지 않고 그 자리에 머뭅니다.

"가입 성공 후 로그인 페이지로 보낸다"는 동작은 백엔드 계약을 그대로 반영한 것입니다 — `/auth/register`는 사용자 계정만 만들 뿐 로그인 쿠키를 심어주지 않기 때문에, 가입 직후에도 사용자는 아직 비로그인 상태입니다. 그래서 대시보드(`/`)로 보내지 않고 로그인을 한 번 더 하도록 `/login`으로 보냅니다.

## 변경 파일
- `frontend/src/pages/Register.tsx` (신규 생성)

## TDD 결과
- `frontend/tests/integration/pages/Register.test.tsx`(3개 테스트, RED 상태)를 먼저 읽었습니다. 이 테스트는 `RegisterForm`을 모킹하지 않고 실제로 렌더링하며, `authService`만 모킹해서 "폼이 보이는지", "성공 시 `/login` 라우트로 이동하는지", "실패 시 `/register`에 머물며 에러가 보이는지"를 검증합니다.
- GREEN 확인: 3개 테스트 전부 통과. `MemoryRouter`로 감싼 테스트 환경에서 실제 네비게이션까지 확인했습니다.
- Git 저장소가 아직 초기화되지 않아 커밋은 생략했습니다.

## 기술 결정
- **페이지 자체에는 로직을 거의 두지 않음**: 유효성 검사·서버 호출·에러 표시는 전부 T032 `RegisterForm`이 담당하므로, 이 페이지는 "성공 후 어디로 갈지"라는 라우팅 결정 하나만 가집니다. 책임을 분리해 두면 나중에 RegisterForm을 다른 곳(예: 모달)에서 재사용하기도 쉽습니다.
- **`navigate('/login')`에 `replace` 옵션을 쓰지 않음**: 테스트가 요구하지 않았고, 가입 완료 후 뒤로가기로 가입 페이지에 돌아가는 것이 사용자에게 특별히 해로운 흐름은 아니라고 판단해 기본 동작(push)을 그대로 두었습니다.

## 비고
- 이 페이지는 `useAuthStore`를 전혀 참조하지 않습니다. 가입은 로그인이 아니므로 전역 인증 상태를 바꿀 이유가 없기 때문입니다.
- `frontend/src/App.tsx`의 `/register` 라우트를 이 페이지로 교체했습니다(기존에는 placeholder `Register` 함수가 inline으로 있었습니다).
