<template>
  <ListView
    :columns="columns"
    :rows="rows"
    :options="{
      selectable: options.selectable,
      showTooltip: options.showTooltip,
      resizeColumn: options.resizeColumn,
    }"
    row-key="name"
    v-bind="$attrs"
    @update:selections="(selections) => emit('selectionsChanged', selections)"
  >
    <ListHeader
      class="sm:mx-5 mx-3"
      @columnWidthUpdated="emit('columnWidthUpdated')"
    >
      <ListHeaderItem
        v-for="column in columns"
        :key="column.key"
        :item="column"
        @columnWidthUpdated="(e) => onColumnWidthUpdated(e, column)"
      />
    </ListHeader>
    <ListRows
      v-slot="{ idx, column, item }"
      class="mx-3 sm:mx-5"
      :rows="rows"
      :doctype="doctype"
    >
      <ListRowItem :item="item" :align="column.align" class="overflow-hidden">
        <template #default="{ label }">
          <div
            v-if="column.type === 'Datetime'"
            class="truncate text-base"
            @click="(event) => applyFilter(event, idx, column, item)"
          >
            <Tooltip :text="item.label">
              <div>{{ item.timeAgo }}</div>
            </Tooltip>
          </div>
          <div
            v-else-if="label"
            class="truncate text-base"
            @click="(event) => applyFilter(event, idx, column, item)"
          >
            {{ label }}
          </div>
        </template>
      </ListRowItem>
    </ListRows>
    <ListSelectBanner>
      <template #actions="{ selections, unselectAll }">
        <Dropdown
          :options="listBulkActionsRef?.bulkActions(selections, unselectAll)"
        >
          <Button icon="lucide-more-horizontal" variant="ghost" />
        </Dropdown>
      </template>
    </ListSelectBanner>
  </ListView>
  <ListFooter
    v-model="pageLengthCount"
    class="border-t sm:px-5 px-3 py-2"
    :options="{
      rowCount: options.rowCount,
      totalCount: options.totalCount,
    }"
    @loadMore="emit('loadMore')"
  />
  <ListBulkActions
    ref="listBulkActionsRef"
    v-model="list"
    :doctype="doctype"
    :options="{ hideEdit: true, hideAssign: true }"
  />
</template>

<script setup>
import ListBulkActions from '@/components/ListBulkActions.vue'
import ListRows from '@/components/ListViews/ListRows.vue'
import { Tooltip, Dropdown } from 'frappe-ui'
import {
  ListView,
  ListHeader,
  ListHeaderItem,
  ListSelectBanner,
  ListRowItem,
  ListFooter,
} from 'frappe-ui/experimental'
import { ref, computed, watch } from 'vue'

// A read-only list of one doctype's records, with the standard CRM list tools
const props = defineProps({
  doctype: { type: String, required: true },
  rows: { type: Array, required: true },
  columns: { type: Array, required: true },
  options: {
    type: Object,
    default: () => ({
      selectable: true,
      showTooltip: true,
      resizeColumn: false,
      totalCount: 0,
      rowCount: 0,
    }),
  },
})

const emit = defineEmits([
  'loadMore',
  'updatePageCount',
  'columnWidthUpdated',
  'applyFilter',
  'selectionsChanged',
])

const pageLengthCount = defineModel({ type: Number, required: true })
const list = defineModel('list', { type: Object, required: true })

function onColumnWidthUpdated({ width, save }, column) {
  column.width = width
  if (save) emit('columnWidthUpdated', column)
}

function applyFilter(event, idx, column, item) {
  emit('applyFilter', {
    event,
    idx,
    column,
    item,
    firstColumn: props.columns[0],
  })
}

watch(pageLengthCount, (val, old_value) => {
  if (val === old_value) return
  emit('updatePageCount', val)
})

const listBulkActionsRef = ref(null)

defineExpose({
  customListActions: computed(
    () => listBulkActionsRef.value?.customListActions,
  ),
})
</script>
