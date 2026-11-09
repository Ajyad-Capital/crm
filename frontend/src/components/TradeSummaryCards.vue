<template>
  <div class="mx-3 grid grid-cols-1 gap-3 sm:mx-5 sm:grid-cols-3">
    <div
      class="rounded-lg border border-outline-gray-2 bg-surface-white px-4 py-3"
    >
      <div class="text-sm text-ink-gray-5">{{ __('Total Trades') }}</div>
      <div class="mt-1 text-2xl-medium text-ink-gray-9">{{ totalTrades }}</div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  totalTrades: { type: Number, required: true },
})
</script>
