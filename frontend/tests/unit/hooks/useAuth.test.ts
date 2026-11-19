import { act, renderHook, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

// useAuth (T038) does not exist yet — frontend/src/hooks/useAuth.ts
//
// Expected contract, built on top of the existing useAuthStore
// (frontend/src/stores/auth-store.ts) and auth-service (T034, mocked here):
//
//   const { user, isAuthenticated, isLoading, login, logout } = useAuth()
//
//   - On mount: isLoading starts true. Calls authService.getCurrentUser()
//     to hydrate the session from the auth cookies.
//       * success -> useAuthStore.setUser(user), isLoading becomes false.
//       * failure -> tries authService.refreshToken() once:
//           - refresh succeeds -> calls getCurrentUser() again and sets the
//             user, isLoading becomes false.
//           - refresh fails -> useAuthStore.clearAuth(), isLoading false.
//   - While authenticated, schedules a recurring authService.refreshToken()
//     call (silent background refresh) so the session does not expire.
//   - login(email, password) calls authService.login and stores the
//     resulting user via useAuthStore.setUser.
//   - logout() calls authService.logout(), then useAuthStore.clearAuth(),
//     and stops the recurring refresh.
import { useAuth } from '@/hooks/useAuth'
import * as authService from '@/services/auth-service'
import { useAuthStore } from '@/stores/auth-store'

vi.mock('@/services/auth-service')

const mockedGetCurrentUser = authService.getCurrentUser as unknown as ReturnType<typeof vi.fn>
const mockedRefreshToken = authService.refreshToken as unknown as ReturnType<typeof vi.fn>
const mockedLogin = authService.login as unknown as ReturnType<typeof vi.fn>
const mockedLogout = authService.logout as unknown as ReturnType<typeof vi.fn>

const mockUser = { id: 'user-1', email: 'test@example.com', skillLevel: 'Complete Beginner' }

describe('useAuth', () => {
  beforeEach(() => {
    mockedGetCurrentUser.mockReset()
    mockedRefreshToken.mockReset()
    mockedLogin.mockReset()
    mockedLogout.mockReset()
    act(() => {
      useAuthStore.getState().clearAuth()
    })
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should start with isLoading true, then hydrate the session on mount via getCurrentUser', async () => {
    mockedGetCurrentUser.mockResolvedValueOnce(mockUser)

    const { result } = renderHook(() => useAuth())

    expect(result.current.isLoading).toBe(true)

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(mockedGetCurrentUser).toHaveBeenCalledTimes(1)
    expect(result.current.isAuthenticated).toBe(true)
    expect(result.current.user).toEqual(mockUser)
  })

  it('should retry via refreshToken then getCurrentUser when the initial session check fails', async () => {
    mockedGetCurrentUser.mockRejectedValueOnce(new Error('인증이 필요합니다'))
    mockedRefreshToken.mockResolvedValueOnce(undefined)
    mockedGetCurrentUser.mockResolvedValueOnce(mockUser)

    const { result } = renderHook(() => useAuth())

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(mockedRefreshToken).toHaveBeenCalledTimes(1)
    expect(mockedGetCurrentUser).toHaveBeenCalledTimes(2)
    expect(result.current.isAuthenticated).toBe(true)
    expect(result.current.user).toEqual(mockUser)
  })

  it('should clear auth and finish loading when both getCurrentUser and refreshToken fail', async () => {
    mockedGetCurrentUser.mockRejectedValueOnce(new Error('인증이 필요합니다'))
    mockedRefreshToken.mockRejectedValueOnce(new Error('세션이 만료되었습니다'))

    const { result } = renderHook(() => useAuth())

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(result.current.isAuthenticated).toBe(false)
    expect(result.current.user).toBeNull()
  })

  it('should schedule a recurring background token refresh while authenticated', async () => {
    vi.useFakeTimers()
    mockedGetCurrentUser.mockResolvedValueOnce(mockUser)
    mockedRefreshToken.mockResolvedValue(undefined)

    const { result } = renderHook(() => useAuth())

    await vi.waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(mockedRefreshToken).not.toHaveBeenCalled()

    await act(async () => {
      await vi.advanceTimersByTimeAsync(15 * 60 * 1000)
    })

    expect(mockedRefreshToken).toHaveBeenCalled()
  })

  it('should update the store with the returned user when login() succeeds', async () => {
    mockedGetCurrentUser.mockRejectedValueOnce(new Error('인증이 필요합니다'))
    mockedRefreshToken.mockRejectedValueOnce(new Error('세션이 만료되었습니다'))
    const { result } = renderHook(() => useAuth())
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    mockedLogin.mockResolvedValueOnce(mockUser)

    await act(async () => {
      await result.current.login('test@example.com', 'password123')
    })

    expect(mockedLogin).toHaveBeenCalledWith('test@example.com', 'password123')
    expect(result.current.isAuthenticated).toBe(true)
    expect(result.current.user).toEqual(mockUser)
  })

  it('should clear the store and stop the refresh timer when logout() is called', async () => {
    vi.useFakeTimers()
    mockedGetCurrentUser.mockResolvedValueOnce(mockUser)
    mockedRefreshToken.mockResolvedValue(undefined)
    mockedLogout.mockResolvedValueOnce(undefined)

    const { result } = renderHook(() => useAuth())
    await vi.waitFor(() => expect(result.current.isLoading).toBe(false))

    await act(async () => {
      await result.current.logout()
    })

    expect(mockedLogout).toHaveBeenCalledTimes(1)
    expect(result.current.isAuthenticated).toBe(false)
    expect(result.current.user).toBeNull()

    const callsAtLogout = mockedRefreshToken.mock.calls.length
    await act(async () => {
      await vi.advanceTimersByTimeAsync(30 * 60 * 1000)
    })
    expect(mockedRefreshToken.mock.calls.length).toBe(callsAtLogout)
  })
})
