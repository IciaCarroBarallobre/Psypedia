<script setup lang="ts">
import ChatComposer from './ChatComposer.vue'
import MessageList from './MessageList.vue'
import { Sparkles } from '@lucide/vue'
import { useChat } from '@/composables/useChat'
const { messages, sendQuestion } = useChat()
</script>

<template>
  <section v-if="!messages.length" aria-labelledby="welcome" class="flex flex-1 flex-col justify-center py-6 sm:py-16">
    <span class="mb-5 flex size-12 items-center justify-center rounded-card bg-brand-100 text-primary"><Sparkles aria-hidden="true" class="size-6" /></span>
    <h1 id="welcome" class="max-w-lg text-2xl font-semibold leading-tight tracking-tight text-brand-950 sm:text-[28px]">Explore psychotherapy knowledge</h1>
    <p class="mt-3 max-w-lg text-base leading-7 text-muted-foreground">A space for your questions about therapeutic approaches. Start a conversation below.</p>
  </section>
  <section v-else aria-label="Chat messages" class="min-w-0 flex-1 pb-6"><MessageList :messages="messages" /></section>
  <div :class="messages.length ? 'sticky bottom-0' : 'relative'" class="mt-auto min-w-0 bg-background pb-[max(1rem,env(safe-area-inset-bottom))] pt-3 sm:pt-4">
    <p class="mb-3 text-xs leading-5 text-muted-foreground">Interface preview · Assistant responses are not connected yet.</p>
    <ChatComposer @send="sendQuestion" />
    <aside aria-label="Clinical and privacy notice" class="mt-3 text-xs leading-5 text-muted-foreground">
    <p>AI prototype for educational reference; does not replace professional judgment.</p>
    <p>Do not enter identifiable patient information. Conversations are not saved after a page refresh.</p>
  </aside>
  </div>
</template>
