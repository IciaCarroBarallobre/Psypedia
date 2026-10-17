<script setup lang="ts">
import ChatComposer from './ChatComposer.vue'
import MessageList from './MessageList.vue'
import { useChat } from '@/composables/useChat'
const { messages, sendQuestion, isSending, error } = useChat()
</script>

<template>
  <section aria-label="Mensajes del chat" class="min-h-0 min-w-0 flex-1"><MessageList :messages="messages" /></section>
  <div class="shrink-0 bg-background pb-[max(0.5rem,env(safe-area-inset-bottom))] pt-2">
    <p v-if="isSending" role="status" class="mb-2 text-xs text-muted-foreground">
      Generando respuesta<span aria-hidden="true" class="loading-dots">...</span><span class="sr-only">…</span>
      La respuesta puede tardar unos minutos.
    </p>
    <p v-if="error" role="alert" class="mb-2 rounded-control border border-negative/30 bg-negative-bg p-3 text-sm text-negative">{{ error }}</p>
    <ChatComposer :busy="isSending" @send="sendQuestion" />
    <aside aria-label="Aviso de uso profesional y privacidad" class="mt-2 text-xs leading-5 text-muted-foreground">
      <p>IA educativa: verifica las respuestas. No introduzcas datos de pacientes.</p>
    </aside>
  </div>
</template>

<style scoped>
.loading-dots {
  display: inline-block;
  width: 3ch;
  font-family: monospace;
  animation: loading-dots 1.5s step-end infinite;
}

@keyframes loading-dots {
  0%, 100% { clip-path: inset(0 66.666% 0 0); }
  33.333% { clip-path: inset(0 33.333% 0 0); }
  66.666% { clip-path: inset(0); }
}

@media (prefers-reduced-motion: reduce) {
  .loading-dots { animation: none; }
}
</style>
