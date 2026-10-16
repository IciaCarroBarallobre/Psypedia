import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import ChatPanel from '../ChatPanel.vue'

const fetchMock = vi.fn()
const answerResponse = (answer: string) => ({ ok: true, json: async () => ({ answer }) })

beforeEach(() => {
  fetchMock.mockReset()
  vi.stubGlobal('fetch', fetchMock)
})

async function submit(chat: ReturnType<typeof mount>, question: string) {
  await chat.get('textarea').setValue(question)
  await chat.get('form').trigger('submit')
  await flushPromises()
}

describe('ChatPanel API integration', () => {
  it('shows the empty state and explains responses are mocked', () => {
    const chat = mount(ChatPanel)
    expect(chat.get('h1').text()).toBe('Explore psychotherapy knowledge')
    expect(chat.text()).toContain('Responses come from a mock')
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('posts questions and displays the returned answers in order', async () => {
    fetchMock.mockResolvedValueOnce(answerResponse('First returned answer'))
      .mockResolvedValueOnce(answerResponse('Second returned answer'))
    const chat = mount(ChatPanel)
    await submit(chat, '  First question  ')
    await submit(chat, 'Second question')
    expect(fetchMock).toHaveBeenNthCalledWith(1, '/api/chat', expect.objectContaining({
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: 'First question' }),
    }))
    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(chat.findAll('[aria-label="Your message"]').map(message => message.text()))
      .toEqual([expect.stringContaining('First question'), expect.stringContaining('Second question')])
    expect(chat.findAll('[aria-label="Assistant message"]').map(message => message.text()))
      .toEqual([expect.stringContaining('First returned answer'), expect.stringContaining('Second returned answer')])
  })

  it('blocks duplicate requests while waiting and clears the pending state', async () => {
    let resolve!: (response: ReturnType<typeof answerResponse>) => void
    fetchMock.mockReturnValue(new Promise(done => { resolve = done }))
    const chat = mount(ChatPanel)
    await chat.get('textarea').setValue('Question')
    await chat.get('form').trigger('submit')
    expect(chat.get('[role="status"]').text()).toContain('Waiting')
    await chat.get('textarea').setValue('Another question')
    await chat.get('form').trigger('submit')
    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(chat.get('button[type="submit"]').attributes('disabled')).toBeDefined()
    resolve(answerResponse('Answer'))
    await flushPromises()
    expect(chat.find('[role="status"]').exists()).toBe(false)
    expect(chat.get('textarea').element.value).toBe('Another question')
    expect(chat.get('button[type="submit"]').attributes('disabled')).toBeUndefined()
  })

  it.each([
    { name: 'network failure', response: () => Promise.reject(new TypeError('Failed to fetch')), text: 'Check your connection' },
    { name: 'API error', response: () => Promise.resolve({ ok: false, status: 500 }), text: 'HTTP 500' },
    { name: 'invalid JSON', response: () => Promise.resolve({ ok: true, json: async () => { throw new SyntaxError() } }), text: 'invalid response' },
    { name: 'missing answer', response: () => Promise.resolve({ ok: true, json: async () => ({}) }), text: 'invalid response' },
    { name: 'blank answer', response: () => Promise.resolve(answerResponse(' ')), text: 'invalid response' },
  ])('shows $name and allows a later submission', async ({ response, text }) => {
    fetchMock.mockImplementationOnce(response)
    const chat = mount(ChatPanel)
    await submit(chat, 'Question')
    expect(chat.get('[role="alert"]').text()).toContain(text)
    expect(chat.find('[aria-label="Assistant message"]').exists()).toBe(false)
    expect(chat.find('[role="status"]').exists()).toBe(false)
    expect(chat.get('[aria-label="Your message"]').text()).toContain('Question')
    fetchMock.mockResolvedValueOnce(answerResponse('Recovered answer'))
    await submit(chat, 'Try again')
    expect(chat.find('[role="alert"]').exists()).toBe(false)
    expect(chat.get('[aria-label="Assistant message"]').text()).toContain('Recovered answer')
  })

  it('renders submitted and returned HTML as plain text', async () => {
    const markup = '<img src=x onerror=alert(1)>'
    fetchMock.mockResolvedValueOnce(answerResponse(markup))
    const chat = mount(ChatPanel)
    await submit(chat, markup)
    for (const role of ['Your message', 'Assistant message']) {
      const message = chat.get(`[aria-label="${role}"]`)
      expect(message.find('img').exists()).toBe(false)
      expect(message.text()).toContain(markup)
    }
  })
})
