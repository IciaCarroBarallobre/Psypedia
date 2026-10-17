import { ref } from 'vue'
import type { Message } from '@/types/chat'
import { sendChatMessage } from '@/services/chatApi'

export function useChat() {
  const messages = ref<Message[]>([{
    id: 0,
    role: 'assistant',
    content: '¡Hola! Estoy aquí para ayudarte con preguntas sobre psicología. ¿Qué te gustaría saber?',
  }])
  const isSending = ref(false)
  const error = ref<string | null>(null)
  let nextId = 1

  async function sendQuestion(question: string): Promise<void> {
    const content = question.trim()
    if (!content || isSending.value) return
    // Snapshot prior turns before adding the current question; sources stay in Vue.
    const history = messages.value.filter(message => message.id !== 0).slice(-12).map(({ role, content }) => ({
      role, content: content.slice(0, 4000),
    }))
    messages.value.push({ id: nextId++, role: 'user', content })
    error.value = null
    isSending.value = true
    try {
      const reply = await sendChatMessage(content, history)
      messages.value.push({ id: nextId++, role: 'assistant', content: reply.content, sources: reply.sources })
    } catch (cause) {
      error.value = cause instanceof Error ? cause.message : 'Se ha producido un error. Inténtalo de nuevo.'
    } finally {
      isSending.value = false
    }
  }

  return { messages, sendQuestion, isSending, error }
}
