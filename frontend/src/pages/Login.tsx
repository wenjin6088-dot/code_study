import { useLocation, useNavigate } from 'react-router-dom'

import { LoginForm } from '../components/auth/LoginForm'
import type { AuthUser } from '../services/auth-service'
import { useAuthStore } from '../stores/auth-store'

export default function Login() {
  const navigate = useNavigate()
  const location = useLocation()
  const setUser = useAuthStore((state) => state.setUser)

  function handleSuccess(user: AuthUser) {
    setUser(user)
    const from = (location.state as { from?: { pathname: string } } | null)?.from
    navigate(from?.pathname ?? '/', { replace: true })
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm space-y-6 rounded-lg border border-border bg-card p-6 shadow-sm">
        <h1 className="text-xl font-semibold text-card-foreground">Login</h1>
        <LoginForm onSuccess={handleSuccess} />
      </div>
    </div>
  )
}
