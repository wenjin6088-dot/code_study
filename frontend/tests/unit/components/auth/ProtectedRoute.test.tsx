import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

// ProtectedRoute (T037) does not exist yet — frontend/src/components/auth/ProtectedRoute.tsx
//
// Expected contract:
//   <ProtectedRoute><SomeChild /></ProtectedRoute>
//   - Reads { isAuthenticated, isLoading } from useAuth() (T038 hook, mocked
//     here at the module boundary) to decide what to render.
//   - While isLoading is true: renders a loading indicator (role="status",
//     or text matching /loading/i) and does NOT render children, does NOT
//     redirect.
//   - Once isLoading is false and isAuthenticated is true: renders children.
//   - Once isLoading is false and isAuthenticated is false: redirects
//     (react-router <Navigate>) to /login, passing the current location in
//     navigation state as `state.from` so Login can send the user back
//     after signing in.
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import * as useAuthHook from '@/hooks/useAuth'

vi.mock('@/hooks/useAuth')

const mockedUseAuth = useAuthHook.useAuth as unknown as ReturnType<typeof vi.fn>

function renderProtected(initialEntry = '/dashboard') {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <div>Secret Dashboard</div>
            </ProtectedRoute>
          }
        />
        <Route path="/login" element={<div>Login Page</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('ProtectedRoute', () => {
  it('should render children when the user is authenticated', () => {
    mockedUseAuth.mockReturnValue({ isAuthenticated: true, isLoading: false, user: { id: '1' } })

    renderProtected()

    expect(screen.getByText('Secret Dashboard')).toBeInTheDocument()
  })

  it('should show a loading indicator and not render children while auth state is loading', () => {
    mockedUseAuth.mockReturnValue({ isAuthenticated: false, isLoading: true, user: null })

    renderProtected()

    expect(screen.queryByText('Secret Dashboard')).not.toBeInTheDocument()
    expect(screen.queryByText('Login Page')).not.toBeInTheDocument()
    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })

  it('should redirect to /login when the user is not authenticated', () => {
    mockedUseAuth.mockReturnValue({ isAuthenticated: false, isLoading: false, user: null })

    renderProtected()

    expect(screen.getByText('Login Page')).toBeInTheDocument()
    expect(screen.queryByText('Secret Dashboard')).not.toBeInTheDocument()
  })

  it('should pass the attempted location in navigation state so Login can redirect back', () => {
    mockedUseAuth.mockReturnValue({ isAuthenticated: false, isLoading: false, user: null })

    function LoginWithState() {
      const location = useLocation()
      const from = (location.state as { from?: { pathname: string } } | null)?.from
      return <div>Login Page{from ? ` from:${from.pathname}` : ''}</div>
    }

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Routes>
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <div>Secret Dashboard</div>
              </ProtectedRoute>
            }
          />
          <Route path="/login" element={<LoginWithState />} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText('Login Page from:/dashboard')).toBeInTheDocument()
  })
})
