<script setup lang="ts">
import { dashboardMetrics, ticketRows } from '../services/mockData'
</script>

<template>
  <section class="page-grid">
    <el-card v-for="metric in dashboardMetrics" :key="metric.label" class="metric-card" shadow="never">
      <p>{{ metric.label }}</p>
      <div>
        <strong>{{ metric.value }}</strong>
        <el-tag size="small" :type="metric.tone === 'red' ? 'danger' : metric.tone === 'amber' ? 'warning' : 'success'">
          {{ metric.trend }}
        </el-tag>
      </div>
    </el-card>
  </section>

  <section class="content-grid two-columns">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>今日主链路</span>
          <el-tag type="info">静态骨架</el-tag>
        </div>
      </template>
      <el-timeline>
        <el-timeline-item timestamp="前端工作台" type="primary">
          Vue3 页面、路由、Pinia 和 Axios 基础已经建立。
        </el-timeline-item>
        <el-timeline-item timestamp="Java 业务服务" type="success">
          后续接入登录、订单、工单和权限 API。
        </el-timeline-item>
        <el-timeline-item timestamp="Python AI 服务" type="warning">
          后续接入真实 LLM、RAG、Tool Calling 和 Agent。
        </el-timeline-item>
      </el-timeline>
    </el-card>

    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>待处理工单</span>
          <el-button size="small" text>查看全部</el-button>
        </div>
      </template>
      <el-table :data="ticketRows" size="small">
        <el-table-column prop="ticketNo" label="工单号" min-width="132" />
        <el-table-column prop="title" label="标题" min-width="180" />
        <el-table-column prop="status" label="状态" width="120" />
      </el-table>
    </el-card>
  </section>
</template>
