<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  addTicketMessage,
  assignTicket,
  claimTicket,
  getTicketDetail,
  listStaffUsers,
  listTickets,
  resolveTicket,
  updateTicketStatus,
} from '../services/businessApi'
import type {
  StaffUserItem,
  TicketMessageItem,
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
const assignmentSubmitting = ref(false)
const messageSubmitting = ref(false)
const resolutionSubmitting = ref(false)
const queueFilter = ref<QueueFilter>('all')
const statusNote = ref('')
const assignmentNote = ref('')
const targetAssigneeUserId = ref('')
const staffUsers = ref<StaffUserItem[]>([])
const messageVisibility = ref<'public' | 'internal'>('public')
const messageContent = ref('')
const resolutionContent = ref('')

type TimelineItem =
  | { kind: 'event'; createdAt: string; key: string; event: TicketEventItem }
  | { kind: 'message'; createdAt: string; key: string; message: TicketMessageItem }

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
    return ['in_progress', 'waiting_user']
  }
  if (status === 'in_progress') {
    return ['waiting_user']
  }
  if (status === 'waiting_user') {
    return ['in_progress']
  }
  if (status === 'resolved') {
    return ['closed']
  }
  return []
})

const canClaimSelectedTicket = computed(() => {
  return Boolean(ticketDetail.value && !ticketDetail.value.assignee_user_id)
})

const canResolveSelectedTicket = computed(() => {
  const status = ticketDetail.value?.ticket_status
  return status === 'in_progress' || status === 'waiting_user'
})

const selectedAssigneeLabel = computed(() => {
  if (!ticketDetail.value?.assignee_user_id) {
    return '未分配'
  }
  return ticketDetail.value.assignee_display_name || ticketDetail.value.assignee_user_id
})

const timelineItems = computed<TimelineItem[]>(() => {
  if (!ticketDetail.value) {
    return []
  }
  return [
    ...ticketDetail.value.events.map((event) => ({
      kind: 'event' as const,
      createdAt: event.created_at,
      key: `event-${event.event_id}`,
      event,
    })),
    ...(ticketDetail.value.messages ?? []).map((message) => ({
      kind: 'message' as const,
      createdAt: message.created_at,
      key: `message-${message.message_id}`,
      message,
    })),
  ].sort((left, right) => left.createdAt.localeCompare(right.createdAt))
})

async function loadStaffUsers() {
  try {
    staffUsers.value = await listStaffUsers()
    if (!targetAssigneeUserId.value && staffUsers.value.length > 0) {
      targetAssigneeUserId.value = staffUsers.value[0].user_id
    }
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '客服人员列表加载失败')
  }
}

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
    const detail = await getTicketDetail(ticketId)
    ticketDetail.value = detail
    targetAssigneeUserId.value = detail.assignee_user_id || staffUsers.value[0]?.user_id || ''
    assignmentNote.value = ''
    messageContent.value = ''
    resolutionContent.value = ''
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '工单详情加载失败')
  } finally {
    detailLoading.value = false
  }
}

async function submitResolution() {
  if (!ticketDetail.value) {
    return
  }
  const content = resolutionContent.value.trim()
  if (!content) {
    ElMessage.warning('请填写用户可见的解决说明')
    return
  }

  resolutionSubmitting.value = true
  try {
    await resolveTicket(ticketDetail.value.ticket_id, { content })
    resolutionContent.value = ''
    ElMessage.success('已向用户发送解决说明并标记工单为已解决')
    await loadTickets(true)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '工单解决操作失败')
  } finally {
    resolutionSubmitting.value = false
  }
}

async function submitMessage() {
  if (!ticketDetail.value) {
    return
  }
  const content = messageContent.value.trim()
  if (!content) {
    ElMessage.warning('请输入回复或内部备注')
    return
  }

  messageSubmitting.value = true
  try {
    await addTicketMessage(ticketDetail.value.ticket_id, {
      visibility: messageVisibility.value,
      content,
    })
    messageContent.value = ''
    ElMessage.success(messageVisibility.value === 'public' ? '已回复用户' : '内部备注已保存')
    await loadTickets(true)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '工单留言提交失败')
  } finally {
    messageSubmitting.value = false
  }
}

function selectTicket(ticket: TicketListItem) {
  void openTicket(ticket.ticket_id)
}

async function submitClaim() {
  if (!ticketDetail.value) {
    return
  }

  assignmentSubmitting.value = true
  try {
    await claimTicket(ticketDetail.value.ticket_id)
    ElMessage.success('工单已认领')
    await loadTickets(true)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '工单认领失败')
  } finally {
    assignmentSubmitting.value = false
  }
}

async function submitAssignment() {
  if (!ticketDetail.value) {
    return
  }
  if (!targetAssigneeUserId.value) {
    ElMessage.warning('请选择处理人')
    return
  }

  assignmentSubmitting.value = true
  try {
    await assignTicket(ticketDetail.value.ticket_id, {
      assignee_user_id: targetAssigneeUserId.value,
      note: assignmentNote.value.trim() || undefined,
    })
    assignmentNote.value = ''
    ElMessage.success('工单处理人已更新')
    await loadTickets(true)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '工单处理人更新失败')
  } finally {
    assignmentSubmitting.value = false
  }
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
  if (event.event_type === 'ticket_resolved') {
    return '客服已发送解决说明并标记工单为已解决'
  }
  if (event.event_type === 'ticket_reopened') {
    return '用户反馈问题未解决，工单已重新进入处理中'
  }
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
    if (typeof payload.assignee_display_name === 'string') {
      const note = typeof payload.note === 'string' && payload.note ? `，备注：${payload.note}` : ''
      return `处理人变为 ${payload.assignee_display_name}${note}`
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
  void loadStaffUsers()
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
        <el-table-column label="处理人" width="130">
          <template #default="{ row }">{{ row.assignee_display_name || '未分配' }}</template>
        </el-table-column>
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
              <dt>当前处理人</dt>
              <dd>{{ selectedAssigneeLabel }}</dd>
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
            <h3>分配处理人</h3>
            <div class="assignment-panel">
              <el-button
                type="success"
                plain
                :disabled="!canClaimSelectedTicket"
                :loading="assignmentSubmitting"
                @click="submitClaim"
              >
                认领工单
              </el-button>
              <el-select v-model="targetAssigneeUserId" placeholder="选择处理人" filterable>
                <el-option
                  v-for="staff in staffUsers"
                  :key="staff.user_id"
                  :label="`${staff.display_name}（${staff.username}）`"
                  :value="staff.user_id"
                />
              </el-select>
              <el-input
                v-model="assignmentNote"
                maxlength="500"
                placeholder="分配/转派说明，可留空"
                show-word-limit
              />
              <el-button type="primary" :loading="assignmentSubmitting" @click="submitAssignment">
                分配 / 转派
              </el-button>
            </div>
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

          <section v-if="canResolveSelectedTicket" class="detail-section">
            <h3>解决工单</h3>
            <el-alert title="解决说明会作为公开回复展示给用户；提交后工单才会进入“已解决”。" type="success" :closable="false" show-icon />
            <div class="message-editor">
              <el-input
                v-model="resolutionContent"
                type="textarea"
                :rows="4"
                maxlength="2000"
                show-word-limit
                placeholder="填写面向用户的解决说明，例如处理结果、后续安排和注意事项"
              />
              <div class="message-actions">
                <el-button type="success" :loading="resolutionSubmitting" @click="submitResolution">
                  解决并回复用户
                </el-button>
              </div>
            </div>
          </section>

          <section class="detail-section">
            <h3>回复与内部备注</h3>
            <el-alert
              :title="messageVisibility === 'public' ? '公开回复会展示给提交该工单的用户。' : '内部备注仅客服、主管和管理员可见。'"
              :type="messageVisibility === 'public' ? 'success' : 'warning'"
              :closable="false"
              show-icon
            />
            <div class="message-editor">
              <el-radio-group v-model="messageVisibility">
                <el-radio-button value="public">回复用户</el-radio-button>
                <el-radio-button value="internal">内部备注</el-radio-button>
              </el-radio-group>
              <el-input
                v-model="messageContent"
                type="textarea"
                :rows="4"
                maxlength="2000"
                show-word-limit
                placeholder="填写本次沟通内容"
              />
              <div class="message-actions">
                <el-button type="primary" :loading="messageSubmitting" @click="submitMessage">
                  {{ messageVisibility === 'public' ? '发送回复' : '保存备注' }}
                </el-button>
              </div>
            </div>
          </section>

          <section class="detail-section">
            <h3>工单时间线</h3>
            <el-timeline>
              <el-timeline-item
                v-for="item in timelineItems"
                :key="item.key"
                :timestamp="formatDate(item.createdAt)"
              >
                <div v-if="item.kind === 'event'" class="event-card">
                  <strong>{{ item.event.event_type }}</strong>
                  <p>{{ eventSummary(item.event) }}</p>
                  <small>{{ item.event.operator_type }} / {{ item.event.operator_id }} / {{ item.event.trace_id }}</small>
                </div>
                <div v-else class="event-card">
                  <strong>{{ item.message.author_type === 'customer' ? '客户补充' : item.message.visibility === 'public' ? '回复用户' : '内部备注' }}</strong>
                  <p class="message-content">{{ item.message.content }}</p>
                  <small>{{ item.message.author_display_name }} / {{ item.message.author_user_id }}</small>
                </div>
              </el-timeline-item>
            </el-timeline>
            <el-empty v-if="timelineItems.length === 0" description="暂无处理记录" />
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

.assignment-panel {
  display: grid;
  grid-template-columns: auto minmax(180px, 240px) minmax(220px, 1fr) auto;
  gap: 10px;
  align-items: center;
}

.message-editor {
  display: grid;
  gap: 10px;
  margin-top: 12px;
}

.message-actions {
  display: flex;
  justify-content: flex-end;
}

.event-card {
  display: grid;
  gap: 4px;
}

.event-card small {
  color: #6b7280;
  overflow-wrap: anywhere;
}

.message-content {
  white-space: pre-wrap;
}

@media (max-width: 900px) {
  .detail-list {
    grid-template-columns: 1fr;
  }

  .assignment-panel {
    grid-template-columns: 1fr;
  }
}
</style>
