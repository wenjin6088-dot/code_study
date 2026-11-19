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
    <div>
      <LoginForm onSuccess={handleSuccess} />
    </div>
  )
}
