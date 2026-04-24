const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function sendMessage(message, history) {
  const response = await fetch(`${API_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history }),
  })
  if (!response.ok) throw new Error('Request failed')
  return response.json()
}
