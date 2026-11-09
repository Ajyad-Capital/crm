<template>
  <ListView
    :class="$attrs.class"
    :columns="columns"
    :rows="rows"
    :options="{
      selectable: false,
      showTooltip: false,
      resizeColumn: false,
    }"
    row-key="name"
  >
    <ListHeader class="sm:mx-5 mx-3">
      <ListHeaderItem
        v-for="column in columns"
        :key="column.key"
        :item="column"
      />
    </ListHeader>
    <ListRows v-slot="{ column, item }" :rows="rows">
      <ListRowItem :item="item" :align="column.align" />
    </ListRows>
  </ListView>
  <ListFooter
    v-model="pageLength"
    class="border-t px-3 py-2 sm:px-5"
    :options="{ rowCount: rows.length, totalCount }"
    @loadMore="emit('loadMore')"
  />
</template>

<script setup>
import ListRows from '@/components/ListViews/ListRows.vue'
import {
  ListView,
  ListHeader,
  ListHeaderItem,
  ListRowItem,
  ListFooter,
} from 'frappe-ui/experimental'

defineProps({
  rows: { type: Array, required: true },
  columns: { type: Array, required: true },
  totalCount: { type: Number, default: 0 },
})
const pageLength = defineModel('pageLength', { type: Number, default: 20 })
const emit = defineEmits(['loadMore'])
</script>
