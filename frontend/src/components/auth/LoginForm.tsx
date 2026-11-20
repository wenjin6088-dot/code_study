import { useState } from 'react'

import { Button } from '../ui/button'
import { Input } from '../ui/input'
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
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-1.5">
        <label htmlFor="login-email" className="text-sm font-medium leading-none">
          Email
        </label>
        <Input
          id="login-email"
          type="text"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </div>
      <div className="space-y-1.5">
        <label htmlFor="login-password" className="text-sm font-medium leading-none">
          Password
        </label>
        <Input
          id="login-password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </div>
      {error && (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      )}
      <Button type="submit" disabled={isSubmitting} className="w-full">
        Login
      </Button>
    </form>
  )
}
