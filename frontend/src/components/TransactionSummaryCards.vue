<template>
  <div class="mx-3 grid grid-cols-1 gap-3 sm:mx-5 sm:grid-cols-3">
    <div
      v-for="card in cards"
      :key="card.label"
      class="rounded-lg border border-outline-gray-2 bg-surface-white px-4 py-3"
    >
      <div class="text-sm text-ink-gray-5">{{ card.label }}</div>
      <div class="mt-1 text-2xl-medium text-ink-gray-9">{{ card.value }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  deposits: { type: String, required: true },
  withdrawals: { type: String, required: true },
  aum: { type: String, required: true },
})

const cards = computed(() => [
  { label: __('Deposits'), value: props.deposits },
  { label: __('Withdrawals'), value: props.withdrawals },
  { label: __('AUM'), value: props.aum },
])
</script>
