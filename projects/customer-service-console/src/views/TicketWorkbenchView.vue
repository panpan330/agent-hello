<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { listTickets } from '../services/businessApi'
import type { TicketListItem } from '../services/businessApi'

type QueueFilter = 'all' | 'created' | 'in_progress' | 'waiting_user'

const tickets = ref<TicketListItem[]>([])
const selectedTicketId = ref('')
const loading = ref(false)
const queueFilter = ref<QueueFilter>('all')

const statusLabels: Record<string, string> = {
  created: '待处理',
  open: '待处理',
  in_progress: '处理中',
  waiting_user: '待用户补充',
  resolved: '已解决',
}

const priorityLabels: Record<string, string> = {
  low: '低',
  normal: '普通',
  high: '高',
}

const filterOptions = [
  { label: '全部', value: 'all' },
  { label: '待处理', value: 'created' },
  { label: '处理中', value: 'in_progress' },
  { label: '待用户', value: 'waiting_user' },
]

const visibleTickets = computed(() => {
  if (queueFilter.value === 'all') {
    return tickets.value
  }
  return tickets.value.filter((ticket) => ticket.ticket_status === queueFilter.value)
})

const selectedTicket = computed(() => {
  return tickets.value.find((ticket) => ticket.ticket_id === selectedTicketId.value) || visibleTickets.value[0]
})

async function loadTickets() {
  loading.value = true
  try {
    tickets.value = await listTickets()
    selectedTicketId.value = tickets.value[0]?.ticket_id || ''
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '工单队列加载失败')
  } finally {
    loading.value = false
  }
}

function selectTicket(ticket: TicketListItem) {
  selectedTicketId.value = ticket.ticket_id
}

function formatDate(value: string) {
  return value ? value.replace('T', ' ').slice(0, 19) : '-'
}

onMounted(loadTickets)
</script>

<template>
  <section class="content-grid two-columns">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>工单队列</span>
          <div class="toolbar-actions">
            <el-segmented v-model="queueFilter" :options="filterOptions" />
            <el-button type="primary" plain :loading="loading" @click="loadTickets">刷新</el-button>
          </div>
        </div>
      </template>
      <el-table
        v-loading="loading"
        :data="visibleTickets"
        height="420"
        highlight-current-row
        @row-click="selectTicket"
      >
        <el-table-column prop="ticket_id" label="工单号" width="160" />
        <el-table-column prop="title" label="标题" min-width="220" show-overflow-tooltip />
        <el-table-column prop="requester_user_id" label="用户" width="120" />
        <el-table-column label="状态" width="110">
          <template #default="{ row }">{{ statusLabels[row.ticket_status] || row.ticket_status }}</template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && visibleTickets.length === 0" description="当前队列暂无工单" />
    </el-card>

    <el-card shadow="never">
      <template #header>处理面板</template>

      <el-empty v-if="!selectedTicket" description="请选择一个工单" />
      <div v-else class="ticket-detail">
        <h2>{{ selectedTicket.title }}</h2>
        <dl class="detail-list">
          <div>
            <dt>工单号</dt>
            <dd>{{ selectedTicket.ticket_id }}</dd>
          </div>
          <div>
            <dt>关联订单</dt>
            <dd>{{ selectedTicket.related_order_id || '-' }}</dd>
          </div>
          <div>
            <dt>当前状态</dt>
            <dd>{{ statusLabels[selectedTicket.ticket_status] || selectedTicket.ticket_status }}</dd>
          </div>
          <div>
            <dt>优先级</dt>
            <dd>{{ priorityLabels[selectedTicket.priority] || selectedTicket.priority }}</dd>
          </div>
          <div>
            <dt>来源</dt>
            <dd>{{ selectedTicket.source }}</dd>
          </div>
          <div>
            <dt>更新时间</dt>
            <dd>{{ formatDate(selectedTicket.updated_at) }}</dd>
          </div>
        </dl>
        <el-alert
          type="info"
          :closable="false"
          title="本节先接入真实工单队列读接口，状态流转和处理备注会在客服工作台增强节补齐。"
        />
      </div>
    </el-card>
  </section>
</template>
