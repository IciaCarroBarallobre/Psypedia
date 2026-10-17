import type { ChatReply, ConversationTurn } from '@/types/chat'
import { parseChatAnswer } from './parseChatAnswer'

/** HTTP boundary for the Flask chat contract. */
export async function sendChatMessage(message: string, history: ConversationTurn[] = []): Promise<ChatReply> {
  let response: Response
  try {
    response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, history }),
      signal: AbortSignal.timeout(150_000),
    })
  } catch {
    throw new Error('No se pudo conectar con el asistente. Comprueba tu conexión e inténtalo de nuevo.')
  }

  if (response.status === 503) {
    throw new Error('El servicio de IA o el modelo configurado no está disponible. Comprueba el servicio e inténtalo de nuevo.')
  }
  if (response.status === 504) {
    throw new Error('El modelo ha tardado demasiado en responder. Inténtalo de nuevo.')
  }
  if (!response.ok) {
    throw new Error(`El servidor no pudo responder (HTTP ${response.status}). Inténtalo de nuevo.`)
  }

  let payload: unknown
  try {
    payload = await response.json()
  } catch {
    throw new Error('El servidor devolvió una respuesta no válida. Inténtalo de nuevo.')
  }
  if (
    typeof payload !== 'object' || payload === null ||
    !('answer' in payload) || typeof payload.answer !== 'string' || !payload.answer.trim()
  ) {
    throw new Error('El servidor devolvió una respuesta no válida. Inténtalo de nuevo.')
  }
  return parseChatAnswer(payload.answer)
}
