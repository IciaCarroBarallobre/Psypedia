<script setup lang="ts">
import { computed } from 'vue'
import type { Message } from '@/types/chat'
import ChatSources from './ChatSources.vue'
const props = defineProps<{ message: Message }>()

// Keep original content/history; format only paired inline bold from the assistant.
const segments = computed(() => props.message.role === 'assistant'
  ? props.message.content.split(/(\*\*[^*\n]+\*\*)/g)
  : [props.message.content])
</script>

<template>
  <article :aria-label="message.role === 'user' ? 'Tu mensaje' : 'Mensaje del asistente'"
    :class="['min-w-0 max-w-[95%] rounded-card px-4 py-3 sm:max-w-[85%] sm:px-5 sm:py-4', message.role === 'user' ? 'ml-auto bg-brand-100 text-ink' : 'mr-auto border border-border bg-card text-card-foreground']">
    <p class="mb-2 text-xs font-semibold tracking-wide opacity-75">{{ message.role === 'user' ? 'Tú' : 'PsyPedia · Asistente' }}</p>
    <p class="whitespace-pre-wrap break-words text-base leading-7 [overflow-wrap:anywhere]">
      <template v-for="(segment, index) in segments" :key="index">
        <strong v-if="index % 2 === 1">{{ segment.slice(2, -2) }}</strong>
        <template v-else>{{ segment }}</template>
      </template>
    </p>
    <ChatSources v-if="message.role === 'assistant' && message.sources" :sources="message.sources" />
  </article>
</template>
