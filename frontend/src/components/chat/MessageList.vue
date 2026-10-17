<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ArrowDown } from '@lucide/vue'
import ChatMessage from './ChatMessage.vue'
import type { Message } from '@/types/chat'
const props = defineProps<{ messages: Message[] }>()
const viewport = ref<HTMLElement | null>(null)
const content = ref<HTMLElement | null>(null)
const following = ref(true)
let observer: ResizeObserver | undefined

function scrollToEnd() {
  if (following.value && viewport.value) {
    viewport.value.scrollTop = viewport.value.scrollHeight
  }
}

function onScroll() {
  const element = viewport.value
  if (element) {
    following.value = element.scrollHeight - element.clientHeight - element.scrollTop <= 48
  }
}

async function resume() {
  following.value = true
  await nextTick()
  scrollToEnd()
}

onMounted(() => {
  scrollToEnd()
  // Also follow layout changes, such as wrapping text or the mobile keyboard.
  if (typeof ResizeObserver !== 'undefined') {
    observer = new ResizeObserver(scrollToEnd)
    if (content.value) observer.observe(content.value)
    if (viewport.value) observer.observe(viewport.value)
  }
})
onBeforeUnmount(() => observer?.disconnect())
watch(() => props.messages.map(message => [message.id, message.content, message.sources]), scrollToEnd, { deep: true, flush: 'post' })
</script>

<template>
  <div class="relative flex h-full min-h-0 flex-col">
    <div ref="viewport" role="log" aria-label="Conversación" aria-live="polite" aria-relevant="additions"
      class="min-h-0 flex-1 overflow-y-auto overscroll-contain [overflow-anchor:none]" @scroll="onScroll">
      <div ref="content" class="space-y-5 pb-5 pr-1">
        <ChatMessage v-for="message in messages" :key="message.id" :message="message" />
      </div>
    </div>
    <button v-if="!following" type="button" @click="resume"
      class="absolute bottom-3 right-3 inline-flex min-h-11 items-center gap-2 rounded-full border border-border bg-surface px-4 text-sm font-medium text-primary shadow-card">
      <ArrowDown aria-hidden="true" class="size-4" />Volver al final
    </button>
  </div>
</template>
