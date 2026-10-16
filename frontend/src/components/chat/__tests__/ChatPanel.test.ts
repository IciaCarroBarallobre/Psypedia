import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import ChatPanel from '../ChatPanel.vue'

describe('ChatPanel conversation', () => {
  it('shows the empty state and explains the assistant is disconnected', () => {
    const chat = mount(ChatPanel)
    expect(chat.get('h1').text()).toBe('Explore psychotherapy knowledge')
    expect(chat.text()).toContain('not connected yet')
    expect(chat.find('[role="log"]').exists()).toBe(false)
  })

  it('keeps submitted questions in order and labels the assistant separately', async () => {
    const chat = mount(ChatPanel)
    for (const question of ['First question', 'Second question']) {
      await chat.get('textarea').setValue(question)
      await chat.get('form').trigger('submit')
    }
    expect(chat.findAll('[aria-label="Your message"]').map(message => message.text()))
      .toEqual([expect.stringContaining('First question'), expect.stringContaining('Second question')])
    expect(chat.findAll('[aria-label="Assistant message"]')).toHaveLength(2)
    expect(chat.get('[aria-label="Assistant message"]').text()).toContain('not connected yet')
    expect(chat.find('h1').exists()).toBe(false)
  })

  it('renders submitted HTML as plain text', async () => {
    const chat = mount(ChatPanel)
    const markup = '<img src=x onerror=alert(1)>'
    await chat.get('textarea').setValue(markup)
    await chat.get('form').trigger('submit')
    const message = chat.get('[aria-label="Your message"]')
    expect(message.find('img').exists()).toBe(false)
    expect(message.text()).toContain(markup)
  })
})
