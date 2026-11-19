import { useCallback, useEffect, useRef, useState } from 'react'

import * as authService from '../services/auth-service'
import { useAuthStore } from '../stores/auth-store'

const REFRESH_INTERVAL_MS = 15 * 60 * 1000

export function useAuth() {
  const [isLoading, setIsLoading] = useState(true)
  const user = useAuthStore((state) => state.user)
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const setUser = useAuthStore((state) => state.setUser)
  const clearAuth = useAuthStore((state) => state.clearAuth)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const stopRefreshTimer = useCallback(() => {
    if (timerRef.current !== null) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
  }, [])

  const startRefreshTimer = useCallback(() => {
    stopRefreshTimer()
    timerRef.current = setInterval(() => {
      authService.refreshToken().catch(() => {})
    }, REFRESH_INTERVAL_MS)
  }, [stopRefreshTimer])

  useEffect(() => {
    let isMounted = true

    async function hydrate() {
      try {
        const currentUser = await authService.getCurrentUser()
        if (!isMounted) return
        setUser(currentUser)
        startRefreshTimer()
      } catch {
        try {
          await authService.refreshToken()
          const currentUser = await authService.getCurrentUser()
          if (!isMounted) return
          setUser(currentUser)
          startRefreshTimer()
        } catch {
          if (!isMounted) return
          clearAuth()
        }
      } finally {
        if (isMounted) setIsLoading(false)
      }
    }

    hydrate()

    return () => {
      isMounted = false
      stopRefreshTimer()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const login = useCallback(
    async (email: string, password: string) => {
      const loggedInUser = await authService.login(email, password)
      setUser(loggedInUser)
      startRefreshTimer()
      return loggedInUser
    },
    [setUser, startRefreshTimer],
  )

  const logout = useCallback(async () => {
    await authService.logout()
    clearAuth()
    stopRefreshTimer()
  }, [clearAuth, stopRefreshTimer])

  return { user, isAuthenticated, isLoading, login, logout }
}
