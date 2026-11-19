import { useNavigate } from 'react-router-dom'

import { RegisterForm } from '../components/auth/RegisterForm'

export default function Register() {
  const navigate = useNavigate()

  return (
    <div>
      <RegisterForm onSuccess={() => navigate('/login')} />
    </div>
  )
}
