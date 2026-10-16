import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import ChatComposer from '../ChatComposer.vue'

describe('ChatComposer', () => {
  describe('submission', () => {
    it.each(['', '   ', '\n\t '])('rejects blank input %j', async (input) => {
      const composer = mount(ChatComposer)
      await composer.get('textarea').setValue(input)
      expect(composer.get('button[type="submit"]').attributes('disabled')).toBeDefined()
      await composer.get('form').trigger('submit')
      expect(composer.emitted('send')).toBeUndefined()
    })

    it('sends a trimmed question and clears the input', async () => {
      const composer = mount(ChatComposer)
      await composer.get('textarea').setValue('  What is psychotherapy?  ')
      await composer.get('form').trigger('submit')
      expect(composer.emitted('send')).toEqual([['What is psychotherapy?']])
      expect(composer.get('textarea').element.value).toBe('')
      expect(composer.get('button[type="submit"]').attributes('disabled')).toBeDefined()
    })
  })

  describe('keyboard', () => {
    it('does not duplicate a question when Enter is pressed again', async () => {
      const composer = mount(ChatComposer)
      const input = composer.get('textarea')
      await input.setValue('A question')
      await input.trigger('keydown', { key: 'Enter' })
      await input.trigger('keydown', { key: 'Enter' })
      expect(composer.emitted('send')).toEqual([['A question']])
      expect(input.element.value).toBe('')
    })

    it('preserves internal line breaks when sending a multiline question', async () => {
      const composer = mount(ChatComposer)
      await composer.get('textarea').setValue('  First line\n\nSecond line  ')
      await composer.get('form').trigger('submit')
      expect(composer.emitted('send')).toEqual([['First line\n\nSecond line']])
    })

    it('sends on Enter', async () => {
      const composer = mount(ChatComposer)
      await composer.get('textarea').setValue('A question')
      await composer.get('textarea').trigger('keydown', { key: 'Enter' })
      expect(composer.emitted('send')).toEqual([['A question']])
    })

    it.each([
      { name: 'Shift+Enter', shiftKey: true },
      { name: 'IME composition', isComposing: true },
    ])('does not send during $name', async ({ name: _name, ...modifiers }) => {
      const composer = mount(ChatComposer)
      await composer.get('textarea').setValue('An unfinished question')
      await composer.get('textarea').trigger('keydown', { key: 'Enter', ...modifiers })
      expect(composer.emitted('send')).toBeUndefined()
      expect(composer.get('textarea').element.value).toBe('An unfinished question')
    })
  })
})
