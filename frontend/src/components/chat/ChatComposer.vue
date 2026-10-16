<script setup lang="ts">
import { computed, ref } from 'vue'
import { ArrowUp } from '@lucide/vue'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
const emit = defineEmits<{ send: [question: string] }>()
const draft = ref('')
const canSend = computed(() => draft.value.trim().length > 0)
function submit() {
  if (!canSend.value) return
  emit('send', draft.value.trim())
  draft.value = ''
}
function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
    event.preventDefault()
    submit()
  }
}
</script>

<template>
  <form @submit.prevent="submit" class="rounded-card border bg-surface p-3 shadow-card">
    <label for="question" class="sr-only">Your question</label>
    <Textarea id="question" v-model="draft" placeholder="Ask a question about therapeutic approaches…" rows="3"
      aria-describedby="composer-hint" class="min-h-24 resize-none overflow-x-hidden whitespace-pre-wrap break-words border-0 bg-transparent shadow-none focus-visible:ring-2 focus-visible:ring-ring/40" @keydown="onKeydown" />
    <div class="flex items-center justify-between gap-3 px-2 pt-2">
      <p id="composer-hint" class="text-xs leading-5 text-muted-foreground">Enter to send · Shift + Enter for a new line</p>
      <Button type="submit" :disabled="!canSend" size="icon" aria-label="Send question" class="size-11 shrink-0 rounded-control"><ArrowUp aria-hidden="true" class="size-5" /></Button>
    </div>
  </form>
</template>
