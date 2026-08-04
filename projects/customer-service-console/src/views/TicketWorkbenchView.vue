<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getTicketDetail,
  listTickets,
  updateTicketStatus,
} from '../services/businessApi'
import type {
  TicketDetail,
  TicketEventItem,
  TicketListItem,
  UpdateTicketStatusPayload,
} from '../services/businessApi'

type QueueFilter = 'all' | 'created' | 'in_progress' | 'waiting_user' | 'resolved'
type TargetStatus = UpdateTicketStatusPayload['target_status']

const tickets = ref<TicketListItem[]>([])
const ticketDetail = ref<TicketDetail | null>(null)
const selectedTicketId = ref('')
const loading = ref(false)
const detailLoading = ref(false)
const statusSubmitting = ref(false)
const queueFilter = ref<QueueFilter>('all')
const statusNote = ref('')

const statusLabels: Record<string, string> = {
  created: '待处理',
  in_progress: '处理中',
  waiting_user: '待用户补充',
  resolved: '已解决',
  closed: '已关闭',
}

const priorityLabels: Record<string, string> = {
  low: '低',
  normal: '普通',
  high: '高',
}

const actionLabels: Record<TargetStatus, string> = {
  in_progress: '开始处理',
  waiting_user: '等待用户补充',
  resolved: '标记已解决',
  closed: '关闭工单',
}

const filterOptions = [
  { label: '全部', value: 'all' },
  { label: '待处理', value: 'created' },
  { label: '处理中', value: 'in_progress' },
  { label: '待用户', value: 'waiting_user' },
  { label: '已解决', value: 'resolved' },
]

const visibleTickets = computed(() => {
  if (queueFilter.value === 'all') {
    return tickets.value
  }
  return tickets.value.filter((ticket) => ticket.ticket_status === queueFilter.value)
})

const availableActions = computed<TargetStatus[]>(() => {
  const status = ticketDetail.value?.ticket_status
  if (status === 'created') {
    return ['in_progress', 'waiting_user', 'resolved', 'closed']
  }
  if (status === 'in_progress') {
    return ['waiting_user', 'resolved', 'closed']
  }
  if (status === 'waiting_user') {
    return ['in_progress', 'resolved', 'closed']
  }
  if (status === 'resolved') {
    return ['closed', 'in_progress']
  }
  return []
})

async function loadTickets(preserveSelection = false) {
  loading.value = true
  try {
    tickets.value = await listTickets()
    const selectedStillVisible =
      preserveSelection &&
      visibleTickets.value.some((ticket) => ticket.ticket_id === selectedTicketId.value)
    const targetTicket = selectedStillVisible
      ? selectedTicketId.value
      : visibleTickets.value[0]?.ticket_id || ''

    if (targetTicket) {
      await openTicket(targetTicket)
    } else {
      selectedTicketId.value = ''
      ticketDetail.value = null
    }
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '工单队列加载失败')
  } finally {
    loading.value = false
  }
}

async function openTicket(ticketId: string) {
  selectedTicketId.value = ticketId
  detailLoading.value = true
  try {
    ticketDetail.value = await getTicketDetail(ticketId)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '工单详情加载失败')
  } finally {
    detailLoading.value = false
  }
}

function selectTicket(ticket: TicketListItem) {
  void openTicket(ticket.ticket_id)
}

async function submitStatus(targetStatus: TargetStatus) {
  if (!ticketDetail.value) {
    return
  }

  statusSubmitting.value = true
  try {
    await updateTicketStatus(ticketDetail.value.ticket_id, {
      target_status: targetStatus,
      note: statusNote.value.trim() || undefined,
    })
    statusNote.value = ''
    ElMessage.success('工单状态已更新')
    await loadTickets(true)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '工单状态更新失败')
  } finally {
    statusSubmitting.value = false
  }
}

function formatDate(value: string) {
  return value ? value.replace('T', ' ').slice(0, 19) : '-'
}

function eventSummary(event: TicketEventItem) {
  if (!event.event_payload) {
    return '-'
  }
  try {
    const payload = JSON.parse(event.event_payload) as Record<string, unknown>
    if (typeof payload.target_status === 'string') {
      const status = statusLabels[payload.target_status] || payload.target_status
      const note = typeof payload.note === 'string' && payload.note ? `，备注：${payload.note}` : ''
      return `状态变为 ${status}${note}`
    }
    if (typeof payload.title === 'string') {
      return payload.title
    }
  } catch {
    return event.event_payload
  }
  return event.event_payload
}

watch(queueFilter, () => {
  const firstVisibleTicketId = visibleTickets.value[0]?.ticket_id || ''
  if (!visibleTickets.value.some((ticket) => ticket.ticket_id === selectedTicketId.value)) {
    if (firstVisibleTicketId) {
      void openTicket(firstVisibleTicketId)
    } else {
      selectedTicketId.value = ''
      ticketDetail.value = null
    }
  }
})

onMounted(() => {
  void loadTickets()
})
</script>

<template>
  <section class="content-grid two-columns">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>工单队列</span>
          <div class="toolbar-actions">
            <el-segmented v-model="queueFilter" :options="filterOptions" />
            <el-button type="primary" plain :loading="loading" @click="loadTickets(true)">刷新</el-button>
          </div>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="visibleTickets"
        height="420"
        highlight-current-row
        :current-row-key="selectedTicketId"
        row-key="ticket_id"
        @row-click="selectTicket"
      >
        <el-table-column prop="ticket_id" label="工单号" width="150" />
        <el-table-column prop="title" label="标题" min-width="220" show-overflow-tooltip />
        <el-table-column prop="requester_user_id" label="用户" width="110" />
        <el-table-column label="状态" width="110">
          <template #default="{ row }">{{ statusLabels[row.ticket_status] || row.ticket_status }}</template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && visibleTickets.length === 0" description="当前队列暂无工单" />
    </el-card>

    <el-card shadow="never">
      <template #header>处理面板</template>

      <el-empty v-if="!ticketDetail && !detailLoading" description="请选择一个工单" />
      <div v-else v-loading="detailLoading" class="ticket-detail">
        <template v-if="ticketDetail">
          <div class="detail-title">
            <h2>{{ ticketDetail.title }}</h2>
            <el-tag>{{ statusLabels[ticketDetail.ticket_status] || ticketDetail.ticket_status }}</el-tag>
          </div>

          <dl class="detail-list">
            <div>
              <dt>工单号</dt>
              <dd>{{ ticketDetail.ticket_id }}</dd>
            </div>
            <div>
              <dt>关联订单</dt>
              <dd>{{ ticketDetail.related_order_id || '-' }}</dd>
            </div>
            <div>
              <dt>用户</dt>
              <dd>{{ ticketDetail.requester_user_id }}</dd>
            </div>
            <div>
              <dt>优先级</dt>
              <dd>{{ priorityLabels[ticketDetail.priority] || ticketDetail.priority }}</dd>
            </div>
            <div>
              <dt>来源</dt>
              <dd>{{ ticketDetail.source }}</dd>
            </div>
            <div>
              <dt>更新时间</dt>
              <dd>{{ formatDate(ticketDetail.updated_at) }}</dd>
            </div>
          </dl>

          <section class="detail-section">
            <h3>用户问题</h3>
            <p>{{ ticketDetail.description }}</p>
          </section>

          <section class="detail-section">
            <h3>处理动作</h3>
            <el-input
              v-model="statusNote"
              type="textarea"
              :rows="3"
              maxlength="500"
              show-word-limit
              placeholder="填写本次处理说明，可留空"
            />
            <div class="action-row">
              <el-button
                v-for="action in availableActions"
                :key="action"
                type="primary"
                :loading="statusSubmitting"
                @click="submitStatus(action)"
              >
                {{ actionLabels[action] }}
              </el-button>
              <el-tag v-if="availableActions.length === 0" type="info">当前状态不可继续流转</el-tag>
            </div>
          </section>

          <section class="detail-section">
            <h3>事件流水</h3>
            <el-timeline>
              <el-timeline-item
                v-for="event in ticketDetail.events"
                :key="event.event_id"
                :timestamp="formatDate(event.created_at)"
              >
                <div class="event-card">
                  <strong>{{ event.event_type }}</strong>
                  <p>{{ eventSummary(event) }}</p>
                  <small>{{ event.operator_type }} / {{ event.operator_id }} / {{ event.trace_id }}</small>
                </div>
              </el-timeline-item>
            </el-timeline>
            <el-empty v-if="ticketDetail.events.length === 0" description="暂无事件流水" />
          </section>
        </template>
      </div>
    </el-card>
  </section>
</template>

<style scoped>
.ticket-detail {
  min-height: 420px;
}

.detail-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.detail-title h2 {
  margin: 0;
  font-size: 20px;
  line-height: 1.35;
}

.detail-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px 20px;
  margin: 0 0 18px;
}

.detail-list div {
  min-width: 0;
}

.detail-list dt {
  color: #6b7280;
  font-size: 12px;
  margin-bottom: 4px;
}

.detail-list dd {
  margin: 0;
  overflow-wrap: anywhere;
}

.detail-section {
  border-top: 1px solid #e5e7eb;
  padding-top: 16px;
  margin-top: 16px;
}

.detail-section h3 {
  margin: 0 0 10px;
  font-size: 15px;
}

.detail-section p {
  margin: 0;
  line-height: 1.7;
}

.action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 12px;
}

.event-card {
  display: grid;
  gap: 4px;
}

.event-card small {
  color: #6b7280;
  overflow-wrap: anywhere;
}

@media (max-width: 900px) {
  .detail-list {
    grid-template-columns: 1fr;
  }
}
</style>
