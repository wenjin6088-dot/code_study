import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

// RegisterForm (T032) does not exist yet — frontend/src/components/auth/RegisterForm.tsx
//
// Expected contract:
//   <RegisterForm onSuccess?={(user) => void} />
//   - Fields: "Email", "Password", "Confirm Password" (accessible via label)
//   - Submit button: "Register"
//   - Client-side validation (shown as inline error text) BEFORE calling the
//     service, for: invalid email format, password shorter than 8 chars,
//     confirm-password mismatch. In all these cases authService.register
//     must NOT be called.
//   - On valid submit, calls authService.register(email, password) from
//     frontend/src/services/auth-service.ts (mocked at that module boundary).
//   - While the request is in-flight, the submit button is disabled.
//   - On success, calls the onSuccess prop with the resolved user.
//   - On failure, renders the rejected Error's message on screen and leaves
//     the form usable again (button re-enabled).
import { RegisterForm } from '@/components/auth/RegisterForm'
import * as authService from '@/services/auth-service'

vi.mock('@/services/auth-service')

const mockedRegister = authService.register as unknown as ReturnType<typeof vi.fn>

function fillForm(email: string, password: string, confirmPassword: string) {
  fireEvent.change(screen.getByLabelText(/^email$/i), { target: { value: email } })
  fireEvent.change(screen.getByLabelText(/^password$/i), { target: { value: password } })
  fireEvent.change(screen.getByLabelText(/confirm password/i), {
    target: { value: confirmPassword },
  })
}

describe('RegisterForm', () => {
  beforeEach(() => {
    mockedRegister.mockReset()
  })

  it('should render email, password, confirm password fields and a submit button', () => {
    render(<RegisterForm />)

    expect(screen.getByLabelText(/^email$/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /register/i })).toBeInTheDocument()
  })

  it('should show a validation error and not call register when email format is invalid', async () => {
    render(<RegisterForm />)

    fillForm('not-an-email', 'password123', 'password123')
    fireEvent.click(screen.getByRole('button', { name: /register/i }))

    expect(await screen.findByText(/valid email/i)).toBeInTheDocument()
    expect(mockedRegister).not.toHaveBeenCalled()
  })

  it('should show a validation error and not call register when password is shorter than 8 characters', async () => {
    render(<RegisterForm />)

    fillForm('test@example.com', 'short', 'short')
    fireEvent.click(screen.getByRole('button', { name: /register/i }))

    expect(await screen.findByText(/8 characters/i)).toBeInTheDocument()
    expect(mockedRegister).not.toHaveBeenCalled()
  })

  it('should show a validation error and not call register when passwords do not match', async () => {
    render(<RegisterForm />)

    fillForm('test@example.com', 'password123', 'password456')
    fireEvent.click(screen.getByRole('button', { name: /register/i }))

    expect(await screen.findByText(/do not match|don't match|match/i)).toBeInTheDocument()
    expect(mockedRegister).not.toHaveBeenCalled()
  })

  it('should call authService.register with the entered email and password on valid submit', async () => {
    mockedRegister.mockResolvedValueOnce({
      id: 'user-1',
      email: 'test@example.com',
      skillLevel: 'Complete Beginner',
    })
    render(<RegisterForm />)

    fillForm('test@example.com', 'password123', 'password123')
    fireEvent.click(screen.getByRole('button', { name: /register/i }))

    await waitFor(() =>
      expect(mockedRegister).toHaveBeenCalledWith('test@example.com', 'password123'),
    )
  })

  it('should call onSuccess with the registered user after a successful submission', async () => {
    const onSuccess = vi.fn()
    const registeredUser = { id: 'user-1', email: 'test@example.com', skillLevel: 'Complete Beginner' }
    mockedRegister.mockResolvedValueOnce(registeredUser)
    render(<RegisterForm onSuccess={onSuccess} />)

    fillForm('test@example.com', 'password123', 'password123')
    fireEvent.click(screen.getByRole('button', { name: /register/i }))

    await waitFor(() => expect(onSuccess).toHaveBeenCalledWith(registeredUser))
  })

  it('should display the server error message when registration fails (e.g. duplicate email)', async () => {
    mockedRegister.mockRejectedValueOnce(new Error('이미 등록된 이메일입니다'))
    render(<RegisterForm />)

    fillForm('dup@example.com', 'password123', 'password123')
    fireEvent.click(screen.getByRole('button', { name: /register/i }))

    expect(await screen.findByText('이미 등록된 이메일입니다')).toBeInTheDocument()
  })

  it('should disable the submit button while the registration request is in flight', async () => {
    let resolveRegister: (value: unknown) => void = () => {}
    mockedRegister.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolveRegister = resolve
        }),
    )
    render(<RegisterForm />)

    fillForm('test@example.com', 'password123', 'password123')
    fireEvent.click(screen.getByRole('button', { name: /register/i }))

    await waitFor(() => expect(screen.getByRole('button', { name: /register/i })).toBeDisabled())

    resolveRegister({ id: 'user-1', email: 'test@example.com', skillLevel: 'Complete Beginner' })
    await waitFor(() => expect(screen.getByRole('button', { name: /register/i })).toBeEnabled())
  })
})
