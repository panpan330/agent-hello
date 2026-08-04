<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { listOrders } from '../services/businessApi'
import type { OrderListItem } from '../services/businessApi'

const orders = ref<OrderListItem[]>([])
const loading = ref(false)

const orderStatusLabels: Record<string, string> = {
  shipped: '运输中',
  waiting_shipment: '待发货',
  delivered: '已签收',
}

const paymentStatusLabels: Record<string, string> = {
  paid: '已支付',
  unpaid: '未支付',
  refunded: '已退款',
}

async function loadOrders() {
  loading.value = true
  try {
    orders.value = await listOrders()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '订单加载失败')
  } finally {
    loading.value = false
  }
}

function formatDate(value: string) {
  return value ? value.replace('T', ' ').slice(0, 19) : '-'
}

onMounted(loadOrders)
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <div class="card-header">
        <span>我的订单</span>
        <el-button type="primary" plain :loading="loading" @click="loadOrders">刷新订单</el-button>
      </div>
    </template>

    <el-table v-loading="loading" :data="orders" stripe>
      <el-table-column prop="order_id" label="订单号" width="140" />
      <el-table-column prop="owner_user_id" label="用户" width="120" />
      <el-table-column label="订单状态" width="120">
        <template #default="{ row }">
          <el-tag effect="light">{{ orderStatusLabels[row.order_status] || row.order_status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="支付状态" width="120">
        <template #default="{ row }">
          {{ paymentStatusLabels[row.payment_status] || row.payment_status }}
        </template>
      </el-table-column>
      <el-table-column prop="logistics_message" label="物流状态" min-width="220" show-overflow-tooltip />
      <el-table-column prop="latest_event" label="最新事件" min-width="220" show-overflow-tooltip />
      <el-table-column label="可建工单" width="100">
        <template #default="{ row }">
          <el-tag :type="row.can_create_ticket ? 'success' : 'info'" effect="light">
            {{ row.can_create_ticket ? '可以' : '不可' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="更新时间" width="180">
        <template #default="{ row }">{{ formatDate(row.updated_at) }}</template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!loading && orders.length === 0" description="暂无可见订单" />
  </el-card>
</template>
