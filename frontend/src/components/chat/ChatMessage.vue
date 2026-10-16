<script setup lang="ts">
import type { Message } from '@/types/chat'
defineProps<{ message: Message }>()
</script>

<template>
  <article :aria-label="message.role === 'user' ? 'Your message' : 'Assistant message'"
    :class="['min-w-0 max-w-[95%] rounded-card px-4 py-3 sm:max-w-[85%] sm:px-5 sm:py-4', message.role === 'user' ? 'ml-auto bg-brand-100 text-ink' : 'mr-auto border border-border bg-card text-card-foreground']">
    <p class="mb-2 text-xs font-semibold tracking-wide opacity-75">{{ message.role === 'user' ? 'You' : 'PsyPedia · Assistant' }}</p>
    <p class="whitespace-pre-wrap break-words text-base leading-7 [overflow-wrap:anywhere]">{{ message.content }}</p>
  </article>
</template>
