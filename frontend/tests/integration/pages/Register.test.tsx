import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

// Register page (T035) does not exist yet — frontend/src/pages/Register.tsx
//
// Expected contract:
//   - Renders the real RegisterForm (T032) inside the page.
//   - On successful registration (RegisterForm's onSuccess), navigates to
//     /login (registration does not log the user in — only /auth/login
//     sets the auth cookies per the backend contract).
//   - On a failed registration, stays on /register and shows the error
//     (delegated to RegisterForm, which is NOT mocked in this integration
//     test — only the underlying auth-service call is mocked).
import Register from '@/pages/Register'
import * as authService from '@/services/auth-service'

vi.mock('@/services/auth-service')

const mockedRegister = authService.register as unknown as ReturnType<typeof vi.fn>

function renderRegisterPage() {
  return render(
    <MemoryRouter initialEntries={['/register']}>
      <Routes>
        <Route path="/register" element={<Register />} />
        <Route path="/login" element={<div>Login Page</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

function fillForm(email: string, password: string, confirmPassword: string) {
  fireEvent.change(screen.getByLabelText(/^email$/i), { target: { value: email } })
  fireEvent.change(screen.getByLabelText(/^password$/i), { target: { value: password } })
  fireEvent.change(screen.getByLabelText(/confirm password/i), {
    target: { value: confirmPassword },
  })
}

describe('Register page', () => {
  beforeEach(() => {
    mockedRegister.mockReset()
  })

  it('should render the registration form', () => {
    renderRegisterPage()

    expect(screen.getByLabelText(/^email$/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /register/i })).toBeInTheDocument()
  })

  it('should navigate to /login after a successful registration', async () => {
    mockedRegister.mockResolvedValueOnce({
      id: 'user-1',
      email: 'new@example.com',
      skillLevel: 'Complete Beginner',
    })
    renderRegisterPage()

    fillForm('new@example.com', 'password123', 'password123')
    fireEvent.click(screen.getByRole('button', { name: /register/i }))

    await waitFor(() => expect(screen.getByText('Login Page')).toBeInTheDocument())
  })

  it('should stay on the register page and show the server error when registration fails', async () => {
    mockedRegister.mockRejectedValueOnce(new Error('이미 등록된 이메일입니다'))
    renderRegisterPage()

    fillForm('dup@example.com', 'password123', 'password123')
    fireEvent.click(screen.getByRole('button', { name: /register/i }))

    expect(await screen.findByText('이미 등록된 이메일입니다')).toBeInTheDocument()
    expect(screen.queryByText('Login Page')).not.toBeInTheDocument()
  })
})
