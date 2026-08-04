<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listKnowledgeDocuments } from '../services/businessApi'
import type { KnowledgeDocumentItem } from '../services/businessApi'
import {
  getKnowledgeBaseStatus,
  ingestKnowledgeBase,
} from '../services/knowledgeBaseApi'
import type {
  KnowledgeBaseDocumentStatus,
  KnowledgeBaseEmbeddingMode,
  KnowledgeBaseIngestResponse,
  KnowledgeBaseStatusResponse,
} from '../services/knowledgeBaseApi'

const documents = ref<KnowledgeDocumentItem[]>([])
const kbStatus = ref<KnowledgeBaseStatusResponse>()
const lastIngestResult = ref<KnowledgeBaseIngestResponse>()
const loading = ref(false)
const ingestingMode = ref<KnowledgeBaseEmbeddingMode | null>(null)

const localDocumentBySource = computed(() => {
  const result = new Map<string, KnowledgeBaseDocumentStatus>()
  for (const document of kbStatus.value?.documents || []) {
    result.set(document.source, document)
  }
  return result
})

const statusTagType: Record<string, 'success' | 'warning' | 'info' | 'danger'> = {
  active: 'success',
  draft: 'warning',
  disabled: 'info',
  failed: 'danger',
}

const domainLabels: Record<string, string> = {
  logistics: '物流',
  refund: '退款',
  account: '账号',
  order: '订单',
  general: '通用',
}

const permissionLabels: Record<string, string> = {
  public: '公开',
  customer: '客户可见',
  customer_service: '客服可见',
  internal: '内部',
}

async function loadPageData() {
  loading.value = true
  try {
    const [businessDocuments, status] = await Promise.all([
      listKnowledgeDocuments(),
      getKnowledgeBaseStatus(),
    ])
    documents.value = businessDocuments
    kbStatus.value = status
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '知识库加载失败')
  } finally {
    loading.value = false
  }
}

async function runIngest(mode: KnowledgeBaseEmbeddingMode) {
  if (mode === 'real') {
    await ElMessageBox.confirm(
      '真实入库会调用真实 embedding 模型并消耗 API 额度，确认继续吗？',
      '确认真实入库',
      {
        confirmButtonText: '确认入库',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )
  }

  ingestingMode.value = mode
  try {
    const result = await ingestKnowledgeBase({
      embedding_mode: mode,
      refresh: true,
      wait: true,
      include_readme: false,
      chunk_size: 500,
      chunk_overlap: 80,
    })
    lastIngestResult.value = result
    ElMessage.success(`入库完成：${result.chunk_count} 个 chunk，${result.vector_count} 条向量`)
    await loadPageData()
  } catch (error) {
    if (error === 'cancel' || error === 'close') {
      return
    }
    if (error instanceof Error && error.message.includes('cancel')) {
      return
    }
    ElMessage.error(error instanceof Error ? error.message : '知识库入库失败')
  } finally {
    ingestingMode.value = null
  }
}

function hasLocalFile(row: KnowledgeDocumentItem) {
  return localDocumentBySource.value.has(row.source_file_name)
}

function formatDate(value: string) {
  return value ? value.replace('T', ' ').slice(0, 19) : '-'
}

function labelOf(value: string, labels: Record<string, string>) {
  return labels[value] || value
}

onMounted(loadPageData)
</script>

<template>
  <section class="knowledge-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>知识库管理</span>
          <div class="toolbar-actions">
            <el-button plain :loading="loading" @click="loadPageData">刷新状态</el-button>
            <el-button
              type="primary"
              plain
              :loading="ingestingMode === 'fake'"
              :disabled="Boolean(ingestingMode)"
              @click="runIngest('fake')"
            >
              Fake 入库
            </el-button>
            <el-button
              type="primary"
              :loading="ingestingMode === 'real'"
              :disabled="Boolean(ingestingMode) || !kbStatus?.real_embedding_configured"
              @click="runIngest('real')"
            >
              真实入库
            </el-button>
          </div>
        </div>
      </template>

      <div class="kb-summary">
        <el-statistic title="业务文档" :value="documents.length" />
        <el-statistic title="本地知识文件" :value="kbStatus?.document_count || 0" />
        <el-statistic title="Fake 向量维度" :value="kbStatus?.fake_embedding_dimension || 0" />
        <el-statistic title="最近入库向量" :value="lastIngestResult?.vector_count || 0" />
      </div>

      <el-alert
        v-if="kbStatus && !kbStatus.real_embedding_configured"
        class="page-alert"
        type="warning"
        :closable="false"
        title="当前未配置真实 embedding API Key，只能使用 Fake 入库验证 Qdrant 链路。"
      />

      <el-descriptions v-if="kbStatus" class="page-alert" :column="3" border>
        <el-descriptions-item label="Qdrant 地址">{{ kbStatus.qdrant_base_url }}</el-descriptions-item>
        <el-descriptions-item label="Collection">{{ kbStatus.collection_name }}</el-descriptions-item>
        <el-descriptions-item label="trace_id">{{ kbStatus.trace_id }}</el-descriptions-item>
      </el-descriptions>

      <el-table v-loading="loading" :data="documents" stripe>
        <el-table-column prop="title" label="文档名称" min-width="220" show-overflow-tooltip />
        <el-table-column label="业务域" width="120">
          <template #default="{ row }">
            {{ labelOf(row.business_domain, domainLabels) }}
          </template>
        </el-table-column>
        <el-table-column label="权限组" width="130">
          <template #default="{ row }">
            {{ labelOf(row.permission_group, permissionLabels) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="statusTagType[row.status] || 'info'" effect="light">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="chunk_count" label="Chunks" width="100" />
        <el-table-column prop="source_file_name" label="源文件" min-width="190" show-overflow-tooltip />
        <el-table-column label="本地文件" width="110">
          <template #default="{ row }">
            <el-tag :type="hasLocalFile(row) ? 'success' : 'danger'" effect="light">
              {{ hasLocalFile(row) ? '已匹配' : '缺失' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="更新时间" width="180">
          <template #default="{ row }">{{ formatDate(row.updated_at) }}</template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && documents.length === 0" description="暂无可见知识文档" />
    </el-card>
  </section>
</template>

<style scoped>
.knowledge-page {
  display: grid;
  gap: 16px;
}

.kb-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.kb-summary :deep(.el-statistic) {
  min-height: 88px;
  border: 1px solid #dce3ee;
  border-radius: 8px;
  padding: 14px 16px;
  background: #f8fafc;
}

@media (max-width: 1100px) {
  .kb-summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .kb-summary {
    grid-template-columns: 1fr;
  }
}
</style>
