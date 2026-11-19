import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

// Login page (T036) does not exist yet — frontend/src/pages/Login.tsx
//
// Expected contract:
//   - Renders the real LoginForm (T033) inside the page.
//   - On successful login (LoginForm's onSuccess), stores the returned user
//     in useAuthStore (frontend/src/stores/auth-store.ts) and navigates:
//       * to location.state.from.pathname when the router sent the user
//         here from a ProtectedRoute redirect,
//       * otherwise to "/" (dashboard).
//   - On a failed login, stays on /login and shows the error (delegated to
//     LoginForm, which is NOT mocked here — only auth-service is mocked).
import Login from '@/pages/Login'
import * as authService from '@/services/auth-service'
import { useAuthStore } from '@/stores/auth-store'

vi.mock('@/services/auth-service')

const mockedLogin = authService.login as unknown as ReturnType<typeof vi.fn>

function fillForm(email: string, password: string) {
  fireEvent.change(screen.getByLabelText(/^email$/i), { target: { value: email } })
  fireEvent.change(screen.getByLabelText(/^password$/i), { target: { value: password } })
}

describe('Login page', () => {
  beforeEach(() => {
    mockedLogin.mockReset()
    act(() => {
      useAuthStore.getState().clearAuth()
    })
  })

  it('should render the login form', () => {
    render(
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route path="/login" element={<Login />} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByLabelText(/^email$/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument()
  })

  it('should store the user and navigate to "/" after a successful login with no prior location', async () => {
    const loggedInUser = { id: 'user-1', email: 'test@example.com', skillLevel: 'Complete Beginner' }
    mockedLogin.mockResolvedValueOnce(loggedInUser)

    render(
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<div>Dashboard Page</div>} />
        </Routes>
      </MemoryRouter>,
    )

    fillForm('test@example.com', 'password123')
    fireEvent.click(screen.getByRole('button', { name: /login/i }))

    await waitFor(() => expect(screen.getByText('Dashboard Page')).toBeInTheDocument())
    expect(useAuthStore.getState().user).toEqual(loggedInUser)
    expect(useAuthStore.getState().isAuthenticated).toBe(true)
  })

  it('should navigate back to the originally requested page after login', async () => {
    const loggedInUser = { id: 'user-1', email: 'test@example.com', skillLevel: 'Complete Beginner' }
    mockedLogin.mockResolvedValueOnce(loggedInUser)

    render(
      <MemoryRouter
        initialEntries={[
          { pathname: '/login', state: { from: { pathname: '/projects/123' } } },
        ]}
      >
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/projects/:projectId" element={<div>Project Page</div>} />
        </Routes>
      </MemoryRouter>,
    )

    fillForm('test@example.com', 'password123')
    fireEvent.click(screen.getByRole('button', { name: /login/i }))

    await waitFor(() => expect(screen.getByText('Project Page')).toBeInTheDocument())
  })

  it('should stay on the login page and show the error when login fails', async () => {
    mockedLogin.mockRejectedValueOnce(new Error('이메일 또는 비밀번호가 올바르지 않습니다'))

    render(
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<div>Dashboard Page</div>} />
        </Routes>
      </MemoryRouter>,
    )

    fillForm('test@example.com', 'wrongpassword')
    fireEvent.click(screen.getByRole('button', { name: /login/i }))

    expect(await screen.findByText('이메일 또는 비밀번호가 올바르지 않습니다')).toBeInTheDocument()
    expect(screen.queryByText('Dashboard Page')).not.toBeInTheDocument()
    expect(useAuthStore.getState().isAuthenticated).toBe(false)
  })
})
