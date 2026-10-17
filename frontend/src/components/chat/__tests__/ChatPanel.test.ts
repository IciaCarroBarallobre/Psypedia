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
  it('opens with one assistant greeting without requesting a model response', () => {
    const chat = mount(ChatPanel)
    const messages = chat.findAll('[aria-label="Mensaje del asistente"]')
    expect(messages).toHaveLength(1)
    expect(messages[0].text()).toContain('¡Hola! Estoy aquí para ayudarte con preguntas sobre psicología. ¿Qué te gustaría saber?')
    expect(chat.find('[aria-label="Tu mensaje"]').exists()).toBe(false)
    expect(chat.text()).toContain('IA educativa: verifica las respuestas.')
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('displays the emergency redirection received from Flask', async () => {
    fetchMock.mockResolvedValueOnce(answerResponse('Siento que estés pasando por esto. Llama al 112 si estás en España o en la UE.'))
    const chat = mount(ChatPanel)
    await submit(chat, 'ME MUERO')
    expect(chat.findAll('[aria-label="Mensaje del asistente"]').at(-1)?.text()).toContain('Siento que estés pasando por esto')
    expect(chat.findAll('[aria-label="Mensaje del asistente"]').at(-1)?.text()).toContain("112")
  })

  it('starts each new chat with its own greeting and no previous messages', async () => {
    fetchMock.mockResolvedValueOnce(answerResponse('Previous answer'))
    const first = mount(ChatPanel)
    await submit(first, 'Previous question')
    first.unmount()
    const fresh = mount(ChatPanel)
    expect(fresh.findAll('[aria-label="Mensaje del asistente"]')).toHaveLength(1)
    expect(fresh.text()).not.toContain('Previous question')
    expect(fresh.text()).not.toContain('Previous answer')
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('posts questions and displays the returned answers in order', async () => {
    fetchMock.mockResolvedValueOnce(answerResponse('First returned answer'))
      .mockResolvedValueOnce(answerResponse('Second returned answer'))
    const chat = mount(ChatPanel)
    await submit(chat, '  First question  ')
    await submit(chat, 'Second question')
    expect(fetchMock).toHaveBeenNthCalledWith(1, '/api/chat', expect.objectContaining({
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: 'First question', history: [] }),
    }))
    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(chat.findAll('[aria-label="Tu mensaje"]').map(message => message.text()))
      .toEqual([expect.stringContaining('First question'), expect.stringContaining('Second question')])
    expect(chat.findAll('[aria-label="Mensaje del asistente"]').map(message => message.text()))
      .toEqual([expect.stringContaining('¡Hola!'), expect.stringContaining('First returned answer'), expect.stringContaining('Second returned answer')])
  })

  it('sends previous turns with a short follow-up without duplicating it', async () => {
    fetchMock.mockResolvedValueOnce(answerResponse('¿Empezamos por ACT?'))
      .mockResolvedValueOnce(answerResponse('ACT explanation'))
    const chat = mount(ChatPanel)
    await submit(chat, 'Ni idea')
    await submit(chat, 'sí')
    const body = JSON.parse(fetchMock.mock.calls[1][1].body)
    expect(body.message).toBe('sí')
    expect(body.history.slice(-2)).toEqual([
      { role: 'user', content: 'Ni idea' },
      { role: 'assistant', content: '¿Empezamos por ACT?' },
    ])
    expect(body.history.every((turn: object) => Object.keys(turn).length === 2)).toBe(true)
    expect(body.history.some((turn: { content: string }) => turn.content === 'sí')).toBe(false)
  })

  it('bounds sent history and does not send link metadata', async () => {
    fetchMock.mockResolvedValue(answerResponse(
      'A'.repeat(4500) + '\n\nReferencias de las fichas / Card references:\n- Source: https://example.org/',
    ))
    const chat = mount(ChatPanel)
    for (let i = 0; i < 8; i++) await submit(chat, `Question ${i}`)
    const body = JSON.parse(fetchMock.mock.calls.at(-1)![1].body)
    expect(body.history).toHaveLength(12)
    expect(body.history.every((turn: { content: string }) => turn.content.length <= 4000)).toBe(true)
    expect(JSON.stringify(body.history)).not.toContain('https://example.org/')
    expect(JSON.stringify(body.history)).not.toContain('sources')
  })

  it('blocks duplicate requests while waiting and clears the pending state', async () => {
    let resolve!: (response: ReturnType<typeof answerResponse>) => void
    fetchMock.mockReturnValue(new Promise(done => { resolve = done }))
    const chat = mount(ChatPanel)
    await chat.get('textarea').setValue('Question')
    await chat.get('form').trigger('submit')
    expect(chat.get('[role="status"]').text()).toContain('Generando')
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
    { name: 'network failure', response: () => Promise.reject(new TypeError('Failed to fetch')), text: 'Comprueba tu conexión' },
    { name: 'API error', response: () => Promise.resolve({ ok: false, status: 500 }), text: 'HTTP 500' },
    { name: 'missing Ollama', response: () => Promise.resolve({ ok: false, status: 503 }), text: 'El servicio de IA o el modelo configurado no está disponible' },
    { name: 'model timeout', response: () => Promise.resolve({ ok: false, status: 504 }), text: 'ha tardado demasiado' },
    { name: 'invalid JSON', response: () => Promise.resolve({ ok: true, json: async () => { throw new SyntaxError() } }), text: 'respuesta no válida' },
    { name: 'missing answer', response: () => Promise.resolve({ ok: true, json: async () => ({}) }), text: 'respuesta no válida' },
    { name: 'blank answer', response: () => Promise.resolve(answerResponse(' ')), text: 'respuesta no válida' },
  ])('shows $name and allows a later submission', async ({ response, text }) => {
    fetchMock.mockImplementationOnce(response)
    const chat = mount(ChatPanel)
    await submit(chat, 'Question')
    expect(chat.get('[role="alert"]').text()).toContain(text)
    expect(chat.findAll('[aria-label="Mensaje del asistente"]')).toHaveLength(1)
    expect(chat.get('[aria-label="Mensaje del asistente"]').text()).toContain('¡Hola!')
    expect(chat.find('[role="status"]').exists()).toBe(false)
    expect(chat.get('[aria-label="Tu mensaje"]').text()).toContain('Question')
    fetchMock.mockResolvedValueOnce(answerResponse('Recovered answer'))
    await submit(chat, 'Try again')
    expect(chat.find('[role="alert"]').exists()).toBe(false)
    expect(chat.findAll('[aria-label="Mensaje del asistente"]').at(-1)?.text()).toContain('Recovered answer')
  })

  it('shows card references as titled links beneath the answer', async () => {
    fetchMock.mockResolvedValueOnce(answerResponse(
      'ACT answer.\n\nReferencias de las fichas / Card references:\n- ACBS — About ACT: https://contextualscience.org/about_act',
    ))
    const chat = mount(ChatPanel)
    await submit(chat, 'What is ACT?')
    const answer = chat.findAll('[aria-label="Mensaje del asistente"]').at(-1)!
    const link = answer.get('a')
    expect(link.text()).toContain('ACBS — About ACT')
    expect(link.attributes('href')).toBe('https://contextualscience.org/about_act')
    expect(link.attributes('target')).toBe('_blank')
    expect(link.attributes('rel')).toContain('noopener')
    expect(answer.text()).toContain('ACT answer.')
    expect(answer.text()).not.toContain('Card references:')
    expect(answer.text()).not.toContain('https://')
    expect(chat.findAll('[aria-label="Fuentes"]')).toHaveLength(1)
  })

  it('renders submitted and returned HTML as plain text', async () => {
    const markup = '<img src=x onerror=alert(1)>'
    fetchMock.mockResolvedValueOnce(answerResponse(markup))
    const chat = mount(ChatPanel)
    await submit(chat, markup)
    for (const role of ['Tu mensaje', 'Mensaje del asistente']) {
      const message = chat.findAll(`[aria-label="${role}"]`).at(-1)!
      expect(message.find('img').exists()).toBe(false)
      expect(message.text()).toContain(markup)
    }
  })

  it('formats assistant bold safely while keeping user text and history unchanged', async () => {
    const answer = 'La **terapia** promueve **flexibilidad psicológica**. **<img src=x onerror=alert(1)>**'
    fetchMock.mockResolvedValue(answerResponse(answer))
    const chat = mount(ChatPanel)
    await submit(chat, '**ACT**')

    const user = chat.get('[aria-label="Tu mensaje"]')
    expect(user.text()).toContain('**ACT**')
    expect(user.find('strong').exists()).toBe(false)
    const reply = chat.findAll('[aria-label="Mensaje del asistente"]').at(-1)!
    expect(reply.findAll('strong').map(element => element.text())).toEqual([
      'terapia', 'flexibilidad psicológica', '<img src=x onerror=alert(1)>',
    ])
    expect(reply.text()).toContain('La terapia promueve flexibilidad psicológica.')
    expect(reply.text()).not.toContain('**')
    expect(reply.find('img').exists()).toBe(false)

    await submit(chat, 'Continúa')
    const body = JSON.parse(fetchMock.mock.calls[1][1].body)
    expect(body.history).toEqual([
      { role: 'user', content: '**ACT**' },
      { role: 'assistant', content: answer },
    ])
  })

  it('preserves literal asterisks and incomplete bold markers', async () => {
    const answer = '2 * 3 = 6. **Un fragmento sin cerrar'
    fetchMock.mockResolvedValueOnce(answerResponse(answer))
    const chat = mount(ChatPanel)
    await submit(chat, 'Pregunta')
    const reply = chat.findAll('[aria-label="Mensaje del asistente"]').at(-1)!
    expect(reply.text()).toContain(answer)
    expect(reply.find('strong').exists()).toBe(false)
  })
})
