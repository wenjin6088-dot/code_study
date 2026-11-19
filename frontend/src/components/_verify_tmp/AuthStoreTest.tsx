import { useAuthStore } from '../../stores/auth-store'

function UserDisplay() {
  const user = useAuthStore((state) => state.user)
  return <div data-testid="user-display">user: {user ? JSON.stringify(user) : 'null'}</div>
}

function AuthStatusDisplay() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  return <div data-testid="auth-status-display">isAuthenticated: {String(isAuthenticated)}</div>
}

export function AuthStoreTest() {
  const setUser = useAuthStore((state) => state.setUser)
  const clearAuth = useAuthStore((state) => state.clearAuth)

  return (
    <div>
      <h2>Zustand Auth Store 테스트</h2>
      <UserDisplay />
      <AuthStatusDisplay />
      <button
        onClick={() =>
          setUser({ id: 'test-user-1', email: 'test@example.com', skillLevel: 'Complete Beginner' })
        }
      >
        사용자 설정
      </button>
      <button onClick={() => clearAuth()}>인증 초기화</button>
    </div>
  )
}
