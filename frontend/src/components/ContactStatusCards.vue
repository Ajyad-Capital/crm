<template>
  <div class="mx-3 grid grid-cols-2 gap-3 sm:mx-5 sm:grid-cols-4">
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
  approved: { type: Number, default: 0 },
  rejected: { type: Number, default: 0 },
  pending: { type: Number, default: 0 },
  blocked: { type: Number, default: 0 },
})

const cards = computed(() => [
  { label: __('Approved'), value: props.approved },
  { label: __('Rejected'), value: props.rejected },
  { label: __('Pending'), value: props.pending },
  { label: __('Blocked'), value: props.blocked },
])
</script>
