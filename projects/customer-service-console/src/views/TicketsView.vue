<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { listTickets } from '../services/businessApi'
import type { TicketListItem } from '../services/businessApi'

const tickets = ref<TicketListItem[]>([])
const loading = ref(false)

const statusLabels: Record<string, string> = {
  created: '已创建',
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

async function loadTickets() {
  loading.value = true
  try {
    tickets.value = await listTickets()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '工单加载失败')
  } finally {
    loading.value = false
  }
}

function formatDate(value: string) {
  return value ? value.replace('T', ' ').slice(0, 19) : '-'
}

onMounted(loadTickets)
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <div class="card-header">
        <span>我的工单</span>
        <el-button type="primary" plain :loading="loading" @click="loadTickets">刷新工单</el-button>
      </div>
    </template>

    <el-table v-loading="loading" :data="tickets" stripe>
      <el-table-column prop="ticket_id" label="工单号" width="160" />
      <el-table-column prop="title" label="标题" min-width="240" show-overflow-tooltip />
      <el-table-column prop="related_order_id" label="关联订单" width="140" />
      <el-table-column label="状态" width="120">
        <template #default="{ row }">
          <el-tag effect="light">{{ statusLabels[row.ticket_status] || row.ticket_status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="优先级" width="100">
        <template #default="{ row }">{{ priorityLabels[row.priority] || row.priority }}</template>
      </el-table-column>
      <el-table-column prop="requester_user_id" label="用户" width="120" />
      <el-table-column label="更新时间" width="180">
        <template #default="{ row }">{{ formatDate(row.updated_at) }}</template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!loading && tickets.length === 0" description="暂无可见工单" />
  </el-card>
</template>
