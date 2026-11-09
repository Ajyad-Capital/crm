<template>
  <div class="mx-3 flex flex-wrap items-center gap-2 sm:mx-5">
    <div class="w-44">
      <FormControl
        v-model="period"
        class="[&_select]:cursor-pointer"
        type="select"
        :options="periodOptions"
      />
    </div>
    <template v-if="period === 'custom'">
      <DatePicker
        v-model="dateFrom"
        class="w-40"
        :placeholder="__('From')"
        :format="getFormat('', '', true, false, false)"
      />
      <DatePicker
        v-model="dateTo"
        class="w-40"
        :placeholder="__('To')"
        :format="getFormat('', '', true, false, false)"
      />
    </template>
  </div>
</template>

<script setup>
import { FormControl, DatePicker } from 'frappe-ui'
import { getFormat } from '@/utils'

const period = defineModel('period', { type: String, default: 'today' })
const dateFrom = defineModel('dateFrom', { type: String, default: '' })
const dateTo = defineModel('dateTo', { type: String, default: '' })

const periodOptions = [
  { label: __('Today'), value: 'today' },
  { label: __('Yesterday'), value: 'yesterday' },
  { label: __('Last 7 days'), value: 'last_7_days' },
  { label: __('Last 30 days'), value: 'last_30_days' },
  { label: __('This month'), value: 'this_month' },
  { label: __('All time'), value: 'all' },
  { label: __('Custom range'), value: 'custom' },
]
</script>
