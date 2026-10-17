import { describe, expect, it } from 'vitest'
import { parseChatAnswer } from '../parseChatAnswer'

const heading = '\n\nReferencias de las fichas / Card references:\n'

describe('parseChatAnswer', () => {
  it('preserves answers without a reference footer', () => {
    expect(parseChatAnswer('Hello!')).toEqual({ content: 'Hello!', sources: [] })
  })

  it('extracts multiple references and deduplicates URLs', () => {
    const reply = parseChatAnswer(`Answer${heading}- First: https://example.org/act\n- Second: https://example.org/dbt\n- Duplicate: https://example.org/act`)
    expect(reply).toEqual({ content: 'Answer', sources: [
      { title: 'First', url: 'https://example.org/act' },
      { title: 'Second', url: 'https://example.org/dbt' },
    ] })
  })

  it.each(['javascript:alert(1)', 'data:text/html,hello', 'https://', 'https://user:password@example.org'])('never makes %s clickable', url => {
    const answer = `Answer${heading}- Source: ${url}`
    expect(parseChatAnswer(answer)).toEqual({ content: answer, sources: [] })
  })

  it('preserves malformed footers and HTML as plain text', () => {
    const answer = `<img src=x onerror=alert(1)>${heading}Not a reference`
    expect(parseChatAnswer(answer)).toEqual({ content: answer, sources: [] })
  })
})
