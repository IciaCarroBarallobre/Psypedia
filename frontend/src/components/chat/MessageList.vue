<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import ChatMessage from './ChatMessage.vue'
import type { Message } from '@/types/chat'
const props = defineProps<{ messages: Message[] }>()
const end = ref<HTMLElement | null>(null)
watch(() => props.messages.length, async () => {
  await nextTick()
  end.value?.scrollIntoView({ block: 'nearest', behavior: 'instant' })
})
</script>

<template>
  <div role="log" aria-label="Conversation" aria-live="polite" aria-relevant="additions" class="space-y-5">
    <ChatMessage v-for="message in messages" :key="message.id" :message="message" />
    <div ref="end" />
  </div>
</template>
