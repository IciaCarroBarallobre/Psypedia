<script setup lang="ts">
import { ExternalLink } from '@lucide/vue'
import type { Source } from '@/types/chat'

defineProps<{ sources: Source[] }>()
</script>

<template>
  <footer v-if="sources.length" aria-label="Fuentes" class="mt-4 border-t border-border pt-3">
    <p class="mb-2 text-xs font-semibold text-muted-foreground">Fuentes</p>
    <ul class="flex flex-col gap-2">
      <li v-for="source in sources" :key="source.url">
        <a :href="source.url" target="_blank" rel="noopener noreferrer"
          class="inline-flex min-h-11 max-w-full items-center gap-2 rounded-control border border-border px-3 py-2 text-sm text-primary underline-offset-4 hover:bg-brand-100 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary">
          <span class="min-w-0 break-words [overflow-wrap:anywhere]">{{ source.title }}</span>
          <ExternalLink aria-hidden="true" class="size-4 shrink-0" />
          <span class="sr-only">(se abre en otra pestaña)</span>
        </a>
      </li>
    </ul>
  </footer>
</template>
