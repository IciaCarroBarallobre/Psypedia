<script setup lang="ts">
import { BookOpen } from '@lucide/vue'
</script>

<template>
  <div class="flex min-h-dvh min-w-0 flex-col bg-background">
    <a href="#main-content" class="sr-only z-20 rounded-control bg-surface p-3 focus:not-sr-only focus:fixed focus:left-3 focus:top-3">Skip to conversation</a>
    <header class="border-b bg-surface">
      <div class="mx-auto flex w-full max-w-5xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6 sm:py-4">
        <a href="/" class="flex min-h-11 items-center gap-3 rounded-control text-brand-950" aria-label="PsyPedia home">
          <span class="flex size-10 items-center justify-center rounded-control bg-brand-950 text-surface"><BookOpen aria-hidden="true" class="size-5" /></span>
          <span><span class="block text-lg font-semibold tracking-tight">PsyPedia</span><span class="block text-xs text-muted-foreground">AI knowledge assistant</span></span>
        </a>
        <span class="hidden rounded-full bg-brand-50 sm:inline-flex px-3 py-1.5 text-xs font-medium text-brand-900">Research preview</span>
      </div>
    </header>
    <main id="main-content" tabindex="-1" class="mx-auto flex w-full min-w-0 max-w-[840px] flex-1 flex-col px-4 pt-6 sm:px-6 sm:pt-10">
      <slot />
    </main>
  </div>
</template>
