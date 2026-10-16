import { afterEach, vi } from 'vitest'
import { enableAutoUnmount } from '@vue/test-utils'

enableAutoUnmount(afterEach)

// jsdom has no layout or native scrolling.
Element.prototype.scrollIntoView = vi.fn()
afterEach(() => vi.clearAllMocks())
