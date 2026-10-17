<script setup lang="ts">
import { BookOpen } from '@lucide/vue'
</script>

<template>
  <div class="flex h-dvh min-h-0 min-w-0 flex-col overflow-hidden bg-background">
    <a href="#main-content" class="sr-only z-20 rounded-control bg-surface p-3 focus:not-sr-only focus:fixed focus:left-3 focus:top-3">Ir a la conversación</a>
    <header class="sticky top-0 z-10 shrink-0 border-b bg-surface">
      <div class="mx-auto flex w-full max-w-5xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6 sm:py-4">
        <a href="/" class="flex min-h-11 items-center gap-3 rounded-control text-brand-950" aria-label="Inicio de PsyPedia">
          <span class="flex size-10 items-center justify-center rounded-control bg-brand-950 text-surface"><BookOpen aria-hidden="true" class="size-5" /></span>
          <span><span class="block text-lg font-semibold tracking-tight">PsyPedia</span><span class="block text-xs text-muted-foreground">Asistente de consulta sobre psicología</span></span>
        </a>
        <span class="hidden rounded-full bg-brand-50 sm:inline-flex px-3 py-1.5 text-xs font-medium text-brand-900">Prototipo</span>
      </div>
    </header>
    <main id="main-content" tabindex="-1" class="mx-auto flex w-full min-w-0 max-w-[840px] min-h-0 flex-1 flex-col overflow-hidden px-4 pt-4 sm:px-6 sm:pt-6">
      <slot />
    </main>
  </div>
</template>
