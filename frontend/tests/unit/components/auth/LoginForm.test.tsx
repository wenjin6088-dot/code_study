import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

// LoginForm (T033) does not exist yet — frontend/src/components/auth/LoginForm.tsx
//
// Expected contract:
//   <LoginForm onSuccess?={(user) => void} />
//   - Fields: "Email", "Password" (accessible via label)
//   - Submit button: "Login"
//   - Client-side validation before calling the service: invalid email
//     format, empty password. In both cases authService.login must NOT be
//     called.
//   - On valid submit, calls authService.login(email, password) from
//     frontend/src/services/auth-service.ts (mocked at that module boundary).
//   - While the request is in-flight, the submit button is disabled.
//   - On success, calls the onSuccess prop with the resolved user.
//   - On failure (wrong credentials), renders the rejected Error's message
//     ("이메일 또는 비밀번호가 올바르지 않습니다") on screen and re-enables the button.
import { LoginForm } from '@/components/auth/LoginForm'
import * as authService from '@/services/auth-service'

vi.mock('@/services/auth-service')

const mockedLogin = authService.login as unknown as ReturnType<typeof vi.fn>

function fillForm(email: string, password: string) {
  fireEvent.change(screen.getByLabelText(/^email$/i), { target: { value: email } })
  fireEvent.change(screen.getByLabelText(/^password$/i), { target: { value: password } })
}

describe('LoginForm', () => {
  beforeEach(() => {
    mockedLogin.mockReset()
  })

  it('should render email and password fields and a submit button', () => {
    render(<LoginForm />)

    expect(screen.getByLabelText(/^email$/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument()
  })

  it('should show a validation error and not call login when email format is invalid', async () => {
    render(<LoginForm />)

    fillForm('not-an-email', 'password123')
    fireEvent.click(screen.getByRole('button', { name: /login/i }))

    expect(await screen.findByText(/valid email/i)).toBeInTheDocument()
    expect(mockedLogin).not.toHaveBeenCalled()
  })

  it('should show a validation error and not call login when password is empty', async () => {
    render(<LoginForm />)

    fireEvent.change(screen.getByLabelText(/^email$/i), {
      target: { value: 'test@example.com' },
    })
    fireEvent.click(screen.getByRole('button', { name: /login/i }))

    expect(await screen.findByText(/password.*required|required/i)).toBeInTheDocument()
    expect(mockedLogin).not.toHaveBeenCalled()
  })

  it('should call authService.login with the entered credentials on valid submit', async () => {
    mockedLogin.mockResolvedValueOnce({
      id: 'user-1',
      email: 'test@example.com',
      skillLevel: 'Complete Beginner',
    })
    render(<LoginForm />)

    fillForm('test@example.com', 'password123')
    fireEvent.click(screen.getByRole('button', { name: /login/i }))

    await waitFor(() =>
      expect(mockedLogin).toHaveBeenCalledWith('test@example.com', 'password123'),
    )
  })

  it('should call onSuccess with the logged in user after a successful submission', async () => {
    const onSuccess = vi.fn()
    const loggedInUser = { id: 'user-1', email: 'test@example.com', skillLevel: 'Complete Beginner' }
    mockedLogin.mockResolvedValueOnce(loggedInUser)
    render(<LoginForm onSuccess={onSuccess} />)

    fillForm('test@example.com', 'password123')
    fireEvent.click(screen.getByRole('button', { name: /login/i }))

    await waitFor(() => expect(onSuccess).toHaveBeenCalledWith(loggedInUser))
  })

  it('should display the "invalid credentials" error message when login fails', async () => {
    mockedLogin.mockRejectedValueOnce(new Error('이메일 또는 비밀번호가 올바르지 않습니다'))
    render(<LoginForm />)

    fillForm('test@example.com', 'wrongpassword')
    fireEvent.click(screen.getByRole('button', { name: /login/i }))

    expect(await screen.findByText('이메일 또는 비밀번호가 올바르지 않습니다')).toBeInTheDocument()
  })

  it('should disable the submit button while the login request is in flight', async () => {
    let resolveLogin: (value: unknown) => void = () => {}
    mockedLogin.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolveLogin = resolve
        }),
    )
    render(<LoginForm />)

    fillForm('test@example.com', 'password123')
    fireEvent.click(screen.getByRole('button', { name: /login/i }))

    await waitFor(() => expect(screen.getByRole('button', { name: /login/i })).toBeDisabled())

    resolveLogin({ id: 'user-1', email: 'test@example.com', skillLevel: 'Complete Beginner' })
    await waitFor(() => expect(screen.getByRole('button', { name: /login/i })).toBeEnabled())
  })
})
