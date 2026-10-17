import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import MessageList from '../MessageList.vue'
import type { Message } from '@/types/chat'

const first: Message = { id: 1, role: 'assistant', content: 'Primera respuesta' }
const second: Message = { id: 2, role: 'assistant', content: 'Nueva respuesta' }
let resize: () => void
const disconnect = vi.fn()

beforeEach(() => {
  vi.stubGlobal('ResizeObserver', class {
    constructor(callback: () => void) { resize = callback }
    observe() {}
    disconnect = disconnect
  })
})

function conversation() {
  const wrapper = mount(MessageList, { props: { messages: [first] } })
  const viewport = wrapper.get('[role="log"]').element as HTMLElement
  let height = 500
  Object.defineProperty(viewport, 'scrollHeight', { get: () => height })
  Object.defineProperty(viewport, 'clientHeight', { value: 200 })
  return { wrapper, viewport, grow: () => { height += 200 } }
}

describe('Conversation scroll', () => {
  it('follows new messages and layout changes when the reader stays at the end', async () => {
    const { wrapper, viewport, grow } = conversation()
    await wrapper.setProps({ messages: [first, second] })
    expect(viewport.scrollTop).toBe(500)
    grow()
    resize()
    expect(viewport.scrollTop).toBe(700)
  })

  it('preserves the reading position when scrolled up, including on resize', async () => {
    const { wrapper, viewport, grow } = conversation()
    viewport.scrollTop = 80
    await wrapper.get('[role="log"]').trigger('scroll')
    grow()
    await wrapper.setProps({ messages: [first, second] })
    resize()
    expect(viewport.scrollTop).toBe(80)
    expect(wrapper.get('button').text()).toContain('Volver al final')
  })

  it('resumes following when the reader returns to the bottom', async () => {
    const { wrapper, viewport, grow } = conversation()
    viewport.scrollTop = 0
    await wrapper.get('[role="log"]').trigger('scroll')
    viewport.scrollTop = 300
    await wrapper.get('[role="log"]').trigger('scroll')
    grow()
    await wrapper.setProps({ messages: [first, second] })
    expect(viewport.scrollTop).toBe(700)
    expect(wrapper.find('button').exists()).toBe(false)
  })

  it('offers explicit return to the latest message and releases the observer', async () => {
    const { wrapper, viewport } = conversation()
    viewport.scrollTop = 0
    await wrapper.get('[role="log"]').trigger('scroll')
    await wrapper.get('button').trigger('click')
    await nextTick()
    expect(viewport.scrollTop).toBe(500)
    expect(wrapper.find('button').exists()).toBe(false)
    wrapper.unmount()
    expect(disconnect).toHaveBeenCalledOnce()
  })
})
