import { QueryClient } from '@tanstack/react-query'

/**
 * Test-only helper (no precedent existed in frontend/src/lib/queryClient.ts —
 * that one is the real app's singleton with staleTime: 60s, retry: 1, which
 * is unsuitable for tests: retries slow down failure-path assertions and a
 * shared singleton leaks cached data between tests).
 *
 * Integration tests for pages that use TanStack Query (Dashboard, ProjectDetail)
 * must create a FRESH QueryClient per test via this helper and wrap the
 * rendered tree in <QueryClientProvider client={createTestQueryClient()}>,
 * alongside <MemoryRouter>. There is no shared renderWithProviders wrapper —
 * each integration test file wraps manually so it stays free to vary the
 * <Routes> it declares (needed to assert navigation).
 */
export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  })
}
