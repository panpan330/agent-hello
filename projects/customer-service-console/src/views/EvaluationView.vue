<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getEvaluationOverview } from '../services/evaluationApi'
import type { BadCaseItem, EvaluationOverview } from '../services/evaluationApi'

const overview = ref<EvaluationOverview | null>(null)
const loading = ref(false)
const selectedBadCaseId = ref('')

const selectedBadCase = computed(() => {
  return overview.value?.bad_cases.find((item) => item.id === selectedBadCaseId.value) || null
})

const metricMap = computed(() => {
  const metrics = overview.value?.latest_run.metrics || []
  return Object.fromEntries(metrics.map((metric) => [metric.name, metric.display_value]))
})

const sortedLayerCounts = computed(() => {
  const counts = overview.value?.bad_case_summary.layer_counts || {}
  return Object.entries(counts).sort((left, right) => right[1] - left[1])
})

const statusTypeMap: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
  open: 'danger',
  triaged: 'warning',
  fixed: 'success',
  regression_added: 'success',
  closed: 'info',
}

const severityTypeMap: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
  critical: 'danger',
  high: 'danger',
  medium: 'warning',
  low: 'info',
}

async function loadOverview() {
  loading.value = true
  try {
    overview.value = await getEvaluationOverview()
    selectedBadCaseId.value = overview.value.bad_cases[0]?.id || ''
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : 'AI 评估看板加载失败')
  } finally {
    loading.value = false
  }
}

function selectBadCase(item: BadCaseItem) {
  selectedBadCaseId.value = item.id
}

onMounted(() => {
  void loadOverview()
})
</script>

<template>
  <section v-loading="loading" class="evaluation-page">
    <el-alert
      v-if="overview?.generated_from_latest_run"
      class="page-alert"
      type="info"
      :closable="false"
      title="当前 bad case 由本地评估结果即时生成；当 bad_cases.json 有正式记录后，页面会优先展示正式登记记录。"
    />

    <div class="page-grid">
      <el-card shadow="never" class="metric-card">
        <p>评估集</p>
        <div>
          <strong>{{ overview?.datasets.length || 0 }}</strong>
          <el-tag type="info">{{ overview?.registry_version || '-' }}</el-tag>
        </div>
      </el-card>
      <el-card shadow="never" class="metric-card">
        <p>检查项</p>
        <div>
          <strong>{{ overview?.latest_run.evaluated_check_count || 0 }}</strong>
          <el-tag :type="overview?.latest_run.passed ? 'success' : 'danger'">
            {{ overview?.latest_run.passed ? '通过' : '有失败' }}
          </el-tag>
        </div>
      </el-card>
      <el-card shadow="never" class="metric-card">
        <p>通过率</p>
        <div>
          <strong>{{ metricMap.check_pass_rate || '-' }}</strong>
          <el-tag type="success">{{ overview?.latest_run.passed_check_count || 0 }} passed</el-tag>
        </div>
      </el-card>
      <el-card shadow="never" class="metric-card">
        <p>Bad Case</p>
        <div>
          <strong>{{ overview?.bad_case_summary.record_count || 0 }}</strong>
          <el-tag type="danger">{{ overview?.bad_case_summary.open_count || 0 }} open</el-tag>
        </div>
      </el-card>
    </div>

    <section class="content-grid two-columns">
      <div class="content-grid">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>本地评估运行</span>
              <el-button type="primary" plain :loading="loading" @click="loadOverview">刷新</el-button>
            </div>
          </template>
          <el-descriptions v-if="overview" :column="2" border>
            <el-descriptions-item label="run_id">{{ overview.latest_run.run_id }}</el-descriptions-item>
            <el-descriptions-item label="数据集">
              {{ overview.latest_run.dataset_name }}:{{ overview.latest_run.dataset_version }}
            </el-descriptions-item>
            <el-descriptions-item label="候选版本">{{ overview.latest_run.candidate_version }}</el-descriptions-item>
            <el-descriptions-item label="模型">{{ overview.latest_run.model_name }}</el-descriptions-item>
            <el-descriptions-item label="样例数">{{ overview.latest_run.selected_case_count }}</el-descriptions-item>
            <el-descriptions-item label="trace_id">{{ overview.trace_id }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card shadow="never">
          <template #header>评估套件</template>
          <el-table :data="overview?.latest_run.suites || []" height="260">
            <el-table-column prop="name" label="套件" width="110" />
            <el-table-column prop="title" label="说明" min-width="210" show-overflow-tooltip />
            <el-table-column prop="case_count" label="样例" width="80" />
            <el-table-column prop="failed_case_count" label="失败" width="80" />
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="row.passed ? 'success' : 'danger'">
                  {{ row.passed ? '通过' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-card shadow="never">
          <template #header>评估集登记</template>
          <el-table :data="overview?.datasets || []" height="260">
            <el-table-column prop="name" label="名称" width="170" />
            <el-table-column prop="version" label="版本" width="120" />
            <el-table-column prop="task_type" label="类型" width="130" />
            <el-table-column prop="description" label="说明" min-width="260" show-overflow-tooltip />
            <el-table-column label="冻结" width="80">
              <template #default="{ row }">
                <el-tag :type="row.frozen ? 'success' : 'warning'">{{ row.frozen ? '是' : '否' }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>

      <div class="content-grid">
        <el-card shadow="never">
          <template #header>失败层分布</template>
          <div v-if="sortedLayerCounts.length" class="layer-list">
            <div v-for="[layer, count] in sortedLayerCounts" :key="layer" class="layer-row">
              <span>{{ layer }}</span>
              <el-progress :percentage="Math.min(100, count * 20)" :format="() => `${count}`" />
            </div>
          </div>
          <el-empty v-else description="暂无失败层统计" />
        </el-card>

        <el-card shadow="never">
          <template #header>Bad Case 列表</template>
          <el-table
            :data="overview?.bad_cases || []"
            height="300"
            highlight-current-row
            row-key="id"
            @row-click="selectBadCase"
          >
            <el-table-column prop="failure_layer" label="层" width="120" />
            <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
            <el-table-column label="级别" width="86">
              <template #default="{ row }">
                <el-tag :type="severityTypeMap[row.severity] || 'info'">{{ row.severity }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="statusTypeMap[row.status] || 'info'">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="overview && overview.bad_cases.length === 0" description="暂无 bad case" />
        </el-card>

        <el-card shadow="never">
          <template #header>Bad Case 详情</template>
          <el-empty v-if="!selectedBadCase" description="请选择一个 bad case" />
          <div v-else class="bad-case-detail">
            <h2>{{ selectedBadCase.title }}</h2>
            <dl class="detail-list">
              <div>
                <dt>ID</dt>
                <dd>{{ selectedBadCase.id }}</dd>
              </div>
              <div>
                <dt>失败层</dt>
                <dd>{{ selectedBadCase.failure_layer }}</dd>
              </div>
              <div>
                <dt>分类</dt>
                <dd>{{ selectedBadCase.failure_category }}</dd>
              </div>
              <div>
                <dt>任务</dt>
                <dd>{{ selectedBadCase.task_type }}</dd>
              </div>
            </dl>
            <section>
              <h3>期望行为</h3>
              <p>{{ selectedBadCase.expected_behavior }}</p>
            </section>
            <section>
              <h3>实际问题</h3>
              <p>{{ selectedBadCase.actual_behavior }}</p>
            </section>
            <section>
              <h3>建议动作</h3>
              <p>{{ selectedBadCase.recommended_action }}</p>
            </section>
            <section>
              <h3>回归策略</h3>
              <p>{{ selectedBadCase.regression_action }}</p>
            </section>
            <section>
              <h3>证据摘要</h3>
              <p>{{ selectedBadCase.evidence_summary }}</p>
            </section>
          </div>
        </el-card>
      </div>
    </section>
  </section>
</template>

<style scoped>
.evaluation-page {
  min-height: 520px;
}

.layer-list {
  display: grid;
  gap: 12px;
}

.layer-row {
  display: grid;
  grid-template-columns: 140px minmax(0, 1fr);
  gap: 12px;
  align-items: center;
}

.layer-row span {
  color: #344054;
  font-size: 13px;
  overflow-wrap: anywhere;
}

.bad-case-detail h2 {
  margin: 0 0 16px;
  color: #101828;
  font-size: 18px;
  line-height: 1.4;
}

.bad-case-detail section {
  border-top: 1px solid #e5e7eb;
  padding-top: 12px;
  margin-top: 12px;
}

.bad-case-detail h3 {
  margin: 0 0 6px;
  color: #344054;
  font-size: 14px;
}

.bad-case-detail p {
  margin: 0;
  color: #101828;
  line-height: 1.7;
  overflow-wrap: anywhere;
}

@media (max-width: 900px) {
  .layer-row {
    grid-template-columns: 1fr;
  }
}
</style>
