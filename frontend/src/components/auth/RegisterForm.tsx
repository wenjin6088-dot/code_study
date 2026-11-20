import { useState } from 'react'

import { Button } from '../ui/button'
import { Input } from '../ui/input'
import { register, type AuthUser } from '../../services/auth-service'

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export interface RegisterFormProps {
  onSuccess?: (user: AuthUser) => void
}

export function RegisterForm({ onSuccess }: RegisterFormProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()

    if (!EMAIL_REGEX.test(email)) {
      setError('유효한 이메일 주소를 입력해 주세요 (valid email required)')
      return
    }

    if (password.length < 8) {
      setError('비밀번호는 8 characters 이상이어야 합니다')
      return
    }

    if (password !== confirmPassword) {
      setError('비밀번호가 일치하지 않습니다 (passwords do not match)')
      return
    }

    setError(null)
    setIsSubmitting(true)
    try {
      const user = await register(email, password)
      onSuccess?.(user)
    } catch (err) {
      setError(err instanceof Error ? err.message : '회원가입에 실패했습니다')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-1.5">
        <label htmlFor="register-email" className="text-sm font-medium leading-none">
          Email
        </label>
        <Input
          id="register-email"
          type="text"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </div>
      <div className="space-y-1.5">
        <label htmlFor="register-password" className="text-sm font-medium leading-none">
          Password
        </label>
        <Input
          id="register-password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </div>
      <div className="space-y-1.5">
        <label htmlFor="register-confirm-password" className="text-sm font-medium leading-none">
          Confirm Password
        </label>
        <Input
          id="register-confirm-password"
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
        />
      </div>
      {error && (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      )}
      <Button type="submit" disabled={isSubmitting} className="w-full">
        Register
      </Button>
    </form>
  )
}
