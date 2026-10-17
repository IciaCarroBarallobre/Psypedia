import type { ChatReply, Source } from '@/types/chat'

const referenceHeading = '\n\nReferencias de las fichas / Card references:\n'

/** Separate the backend's reference footer without interpreting arbitrary HTML. */
export function parseChatAnswer(answer: string): ChatReply {
  const start = answer.lastIndexOf(referenceHeading)
  const plain = { content: answer, sources: [] }
  if (start < 0 || !answer.slice(0, start).trim()) return plain

  const sources: Source[] = []
  for (const line of answer.slice(start + referenceHeading.length).trim().split('\n')) {
    const match = /^- (.+): (https?:\/\/\S+)$/.exec(line.trim())
    if (!match) return plain
    try {
      const url = new URL(match[2])
      if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password) return plain
      if (!sources.some(source => source.url === url.href)) {
        sources.push({ title: match[1], url: url.href })
      }
    } catch {
      return plain
    }
  }
  return { content: answer.slice(0, start).trimEnd(), sources }
}
