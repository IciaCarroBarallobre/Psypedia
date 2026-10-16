/** HTTP boundary for the Flask chat contract. */
export async function sendChatMessage(message: string): Promise<string> {
  let response: Response
  try {
    response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
      signal: AbortSignal.timeout(30_000),
    })
  } catch {
    throw new Error('Could not reach the assistant. Check your connection and try again.')
  }

  if (!response.ok) {
    throw new Error(`The server could not answer (HTTP ${response.status}). Please try again.`)
  }

  let payload: unknown
  try {
    payload = await response.json()
  } catch {
    throw new Error('The server returned an invalid response. Please try again.')
  }
  if (
    typeof payload !== 'object' || payload === null ||
    !('answer' in payload) || typeof payload.answer !== 'string' || !payload.answer.trim()
  ) {
    throw new Error('The server returned an invalid response. Please try again.')
  }
  return payload.answer
}
