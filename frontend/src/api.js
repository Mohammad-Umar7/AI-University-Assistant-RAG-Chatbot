const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const RETRYABLE_STATUS = new Set([502, 503, 504])

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

async function parseError(response) {
  try {
    const body = await response.json()
    return body?.detail || `${response.status}`
  } catch {
    return `${response.status}`
  }
}

export async function getHealth() {
  const response = await fetch(`${API_URL}/health`, {
    cache: 'no-store',
  })
  if (!response.ok) throw new Error(await parseError(response))
  return response.json()
}

export async function waitForReady({ timeoutMs = 120000, intervalMs = 2500 } = {}) {
  const deadline = Date.now() + timeoutMs

  while (Date.now() < deadline) {
    try {
      const health = await getHealth()
      if (health.status === 'ready') return true
      if (health.status === 'error') {
        throw new Error(health.detail || 'Backend failed to initialize')
      }
    } catch (err) {
      if (Date.now() + intervalMs >= deadline) throw err
    }

    await sleep(intervalMs)
  }

  throw new Error('Backend is still warming up')
}

async function requestChat(message, history) {
  const response = await fetch(`${API_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history }),
  })

  if (!response.ok) {
    const error = new Error(await parseError(response))
    error.status = response.status
    throw error
  }

  return response.json()
}

export async function sendMessage(message, history) {
  try {
    return await requestChat(message, history)
  } catch (err) {
    if (!RETRYABLE_STATUS.has(err.status)) throw err
    await waitForReady()
    return requestChat(message, history)
  }
}
