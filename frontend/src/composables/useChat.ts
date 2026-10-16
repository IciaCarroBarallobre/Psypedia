import { ref } from 'vue'
import type { Message } from '@/types/chat'

export function useChat() {
  const messages = ref<Message[]>([])
  let nextId = 1

  function sendQuestion(question: string): boolean {
    const content = question.trim()
    if (!content) return false
    messages.value.push({ id: nextId++, role: 'user', content })
    messages.value.push({
      id: nextId++,
      role: 'assistant',
      content: 'Your question has been added. The assistant is not connected yet, so no clinical answer has been generated.',
    })
    return true
  }

  return { messages, sendQuestion }
}
