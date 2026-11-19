import { useState } from 'react'

import { apiClient } from '../../services/api-client'
import { AuthStoreTest } from './AuthStoreTest'
import { TailwindShadcnTest } from './TailwindShadcnTest'

export function DevTest() {
  const [response, setResponse] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleClick() {
    setLoading(true)
    setResponse(null)
    setError(null)
    try {
      const res = await apiClient.get('/health')
      setResponse(JSON.stringify(res.data))
    } catch (e) {
      setError(e instanceof Error ? e.message : '알 수 없는 오류')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <section>
        <h2>API 클라이언트 테스트</h2>
        <button onClick={handleClick} disabled={loading}>
          API 호출
        </button>
        <div data-testid="dev-test-response">
          {loading
            ? '요청 중...'
            : error
              ? `에러: ${error}`
              : response
                ? `응답: ${response}`
                : '대기 중'}
        </div>
      </section>
      <AuthStoreTest />
      <TailwindShadcnTest />
    </div>
  )
}
