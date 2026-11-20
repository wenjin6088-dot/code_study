import { useNavigate } from 'react-router-dom'

import { RegisterForm } from '../components/auth/RegisterForm'

export default function Register() {
  const navigate = useNavigate()

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm space-y-6 rounded-lg border border-border bg-card p-6 shadow-sm">
        <h1 className="text-xl font-semibold text-card-foreground">Register</h1>
        <RegisterForm onSuccess={() => navigate('/login')} />
      </div>
    </div>
  )
}
