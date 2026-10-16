import { ref } from 'vue'
import type { Message } from '@/types/chat'
import { sendChatMessage } from '@/services/chatApi'

export function useChat() {
  const messages = ref<Message[]>([])
  const isSending = ref(false)
  const error = ref<string | null>(null)
  let nextId = 1

  async function sendQuestion(question: string): Promise<void> {
    const content = question.trim()
    if (!content || isSending.value) return
    messages.value.push({ id: nextId++, role: 'user', content })
    error.value = null
    isSending.value = true
    try {
      const answer = await sendChatMessage(content)
      messages.value.push({ id: nextId++, role: 'assistant', content: answer })
    } catch (cause) {
      error.value = cause instanceof Error ? cause.message : 'Something went wrong. Please try again.'
    } finally {
      isSending.value = false
    }
  }

  return { messages, sendQuestion, isSending, error }
}
