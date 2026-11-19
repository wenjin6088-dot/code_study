import { beforeEach, describe, expect, it, vi } from 'vitest'

// auth-service.ts (T034) does not exist yet — this import will fail until it is
// created at frontend/src/services/auth-service.ts.
//
// Expected contract (designed against the existing apiClient in
// frontend/src/services/api-client.ts, which is cookie-based: withCredentials
// true, no Authorization header):
//
//   register(email, password) -> POST /auth/register {email,password} -> AuthUser
//   login(email, password)    -> POST /auth/login    {email,password} -> AuthUser
//   logout()                  -> POST /auth/logout
//   getCurrentUser()          -> GET  /auth/me        -> AuthUser
//   refreshToken()            -> POST /auth/refresh
//
// All calls go through the shared `apiClient` so cookies are sent and the
// response interceptor's error normalization (Error(message)) applies.
import * as authService from '@/services/auth-service'
import { apiClient } from '@/services/api-client'

vi.mock('@/services/api-client', () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
  },
}))

const mockedPost = apiClient.post as unknown as ReturnType<typeof vi.fn>
const mockedGet = apiClient.get as unknown as ReturnType<typeof vi.fn>

const mockUser = { id: 'user-1', email: 'test@example.com', skillLevel: 'Complete Beginner' }

describe('auth-service', () => {
  beforeEach(() => {
    mockedPost.mockReset()
    mockedGet.mockReset()
  })

  describe('register', () => {
    it('should POST to /auth/register with email and password when registering', async () => {
      mockedPost.mockResolvedValueOnce({ data: mockUser })

      const result = await authService.register('test@example.com', 'password123')

      expect(mockedPost).toHaveBeenCalledWith('/auth/register', {
        email: 'test@example.com',
        password: 'password123',
      })
      expect(result).toEqual(mockUser)
    })

    it('should propagate the error when registration fails (e.g. duplicate email)', async () => {
      mockedPost.mockRejectedValueOnce(new Error('이미 등록된 이메일입니다'))

      await expect(authService.register('dup@example.com', 'password123')).rejects.toThrow(
        '이미 등록된 이메일입니다',
      )
    })
  })

  describe('login', () => {
    it('should POST to /auth/login with email and password and return the user', async () => {
      mockedPost.mockResolvedValueOnce({ data: mockUser })

      const result = await authService.login('test@example.com', 'password123')

      expect(mockedPost).toHaveBeenCalledWith('/auth/login', {
        email: 'test@example.com',
        password: 'password123',
      })
      expect(result).toEqual(mockUser)
    })

    it('should propagate the error when credentials are invalid', async () => {
      mockedPost.mockRejectedValueOnce(new Error('이메일 또는 비밀번호가 올바르지 않습니다'))

      await expect(authService.login('test@example.com', 'wrongpass')).rejects.toThrow(
        '이메일 또는 비밀번호가 올바르지 않습니다',
      )
    })
  })

  describe('logout', () => {
    it('should POST to /auth/logout with no body', async () => {
      mockedPost.mockResolvedValueOnce({ data: undefined })

      await authService.logout()

      expect(mockedPost).toHaveBeenCalledWith('/auth/logout')
    })

    it('should propagate the error when logout fails', async () => {
      mockedPost.mockRejectedValueOnce(new Error('로그아웃에 실패했습니다'))

      await expect(authService.logout()).rejects.toThrow('로그아웃에 실패했습니다')
    })
  })

  describe('getCurrentUser', () => {
    it('should GET /auth/me and return the current user', async () => {
      mockedGet.mockResolvedValueOnce({ data: mockUser })

      const result = await authService.getCurrentUser()

      expect(mockedGet).toHaveBeenCalledWith('/auth/me')
      expect(result).toEqual(mockUser)
    })

    it('should propagate the error when the session is unauthenticated (401)', async () => {
      mockedGet.mockRejectedValueOnce(new Error('인증이 필요합니다'))

      await expect(authService.getCurrentUser()).rejects.toThrow('인증이 필요합니다')
    })
  })

  describe('refreshToken', () => {
    it('should POST to /auth/refresh to rotate the auth cookies', async () => {
      mockedPost.mockResolvedValueOnce({ data: undefined })

      await authService.refreshToken()

      expect(mockedPost).toHaveBeenCalledWith('/auth/refresh')
    })

    it('should propagate the error when the refresh token is expired/invalid', async () => {
      mockedPost.mockRejectedValueOnce(new Error('세션이 만료되었습니다'))

      await expect(authService.refreshToken()).rejects.toThrow('세션이 만료되었습니다')
    })
  })
})
