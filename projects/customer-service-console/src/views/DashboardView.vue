<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { listKnowledgeDocuments, listOrders, listTickets } from '../services/businessApi'
import { getEvaluationOverview } from '../services/evaluationApi'
import type { OrderListItem, TicketListItem } from '../services/businessApi'
import type { EvaluationOverview } from '../services/evaluationApi'

const orders = ref<OrderListItem[]>([])
const tickets = ref<TicketListItem[]>([])
const knowledgeDocumentCount = ref(0)
const evaluationOverview = ref<EvaluationOverview | null>(null)
const loading = ref(false)

const openTicketCount = computed(() => {
  return tickets.value.filter((ticket) =>
    ['created', 'in_progress', 'waiting_user'].includes(ticket.ticket_status),
  ).length
})

const recentTickets = computed(() => tickets.value.slice(0, 6))

const metrics = computed(() => [
  {
    label: '可见订单',
    value: String(orders.value.length),
    tag: '真实 Java',
    type: 'success' as const,
  },
  {
    label: '待处理工单',
    value: String(openTicketCount.value),
    tag: `${tickets.value.length} total`,
    type: openTicketCount.value > 0 ? ('warning' as const) : ('success' as const),
  },
  {
    label: '知识库文档',
    value: String(knowledgeDocumentCount.value),
    tag: 'Java + AI',
    type: 'info' as const,
  },
  {
    label: '评估通过率',
    value:
      evaluationOverview.value?.latest_run.metrics.find((metric) => metric.name === 'check_pass_rate')
        ?.display_value || '-',
    tag: evaluationOverview.value?.latest_run.passed ? '通过' : '有失败',
    type: evaluationOverview.value?.latest_run.passed ? ('success' as const) : ('danger' as const),
  },
])

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

async function loadDashboard() {
  loading.value = true
  try {
    const [orderList, ticketList, knowledgeDocuments, evaluation] = await Promise.all([
      listOrders(),
      listTickets(),
      listKnowledgeDocuments(),
      getEvaluationOverview(),
    ])
    orders.value = orderList
    tickets.value = ticketList
    knowledgeDocumentCount.value = knowledgeDocuments.length
    evaluationOverview.value = evaluation
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '运营概览加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void loadDashboard()
})
</script>

<template>
  <section v-loading="loading" class="dashboard-page">
    <section class="page-grid">
      <el-card v-for="metric in metrics" :key="metric.label" class="metric-card" shadow="never">
        <p>{{ metric.label }}</p>
        <div>
          <strong>{{ metric.value }}</strong>
          <el-tag size="small" :type="metric.type">{{ metric.tag }}</el-tag>
        </div>
      </el-card>
    </section>

    <section class="content-grid two-columns">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span>项目运行链路</span>
            <el-button type="primary" plain :loading="loading" @click="loadDashboard">刷新</el-button>
          </div>
        </template>
        <el-timeline>
          <el-timeline-item timestamp="前端控制台" type="primary">
            Vue3 页面已接入 Java public API 和 Python AI API。
          </el-timeline-item>
          <el-timeline-item timestamp="Java 业务服务" type="success">
            登录、订单、工单、知识库元数据、工单状态流转均来自 Spring Boot + MyBatis。
          </el-timeline-item>
          <el-timeline-item timestamp="Python AI 服务" type="warning">
            AI 对话、RAG 问答、知识库入库、评估与 bad case 看板均由 FastAPI 提供。
          </el-timeline-item>
          <el-timeline-item timestamp="真实依赖" type="info">
            MySQL 保存业务数据，Redis 支撑缓存/幂等/限流，Qdrant 支撑真实 RAG 检索。
          </el-timeline-item>
        </el-timeline>
      </el-card>

      <el-card shadow="never">
        <template #header>最近工单</template>
        <el-table :data="recentTickets" size="small" height="300">
          <el-table-column prop="ticket_id" label="工单号" width="150" />
          <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
          <el-table-column label="状态" width="110">
            <template #default="{ row }">
              <el-tag effect="light">{{ statusLabels[row.ticket_status] || row.ticket_status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="优先级" width="90">
            <template #default="{ row }">{{ priorityLabels[row.priority] || row.priority }}</template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!loading && recentTickets.length === 0" description="暂无可见工单" />
      </el-card>
    </section>

    <el-card shadow="never">
      <template #header>当前评估快照</template>
      <el-descriptions v-if="evaluationOverview" :column="4" border>
        <el-descriptions-item label="run_id">{{ evaluationOverview.latest_run.run_id }}</el-descriptions-item>
        <el-descriptions-item label="数据集">
          {{ evaluationOverview.latest_run.dataset_name }}:{{ evaluationOverview.latest_run.dataset_version }}
        </el-descriptions-item>
        <el-descriptions-item label="检查项">{{ evaluationOverview.latest_run.evaluated_check_count }}</el-descriptions-item>
        <el-descriptions-item label="失败项">{{ evaluationOverview.latest_run.failed_check_count }}</el-descriptions-item>
      </el-descriptions>
    </el-card>
  </section>
</template>

<style scoped>
.dashboard-page {
  display: grid;
  gap: 16px;
}
</style>
