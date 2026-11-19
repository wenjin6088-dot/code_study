import { useState } from 'react'

import { Button } from '../ui/button'
import { login, type AuthUser } from '../../services/auth-service'

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export interface LoginFormProps {
  onSuccess?: (user: AuthUser) => void
}

export function LoginForm({ onSuccess }: LoginFormProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()

    if (!EMAIL_REGEX.test(email)) {
      setError('유효한 이메일 주소를 입력해 주세요 (valid email required)')
      return
    }

    if (!password) {
      setError('비밀번호를 입력해 주세요 (password required)')
      return
    }

    setError(null)
    setIsSubmitting(true)
    try {
      const user = await login(email, password)
      onSuccess?.(user)
    } catch (err) {
      setError(err instanceof Error ? err.message : '로그인에 실패했습니다')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label htmlFor="login-email">Email</label>
        <input
          id="login-email"
          type="text"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </div>
      <div>
        <label htmlFor="login-password">Password</label>
        <input
          id="login-password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </div>
      {error && <p role="alert">{error}</p>}
      <Button type="submit" disabled={isSubmitting}>
        Login
      </Button>
    </form>
  )
}
