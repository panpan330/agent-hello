<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getEvaluationOverview, runProductionRegression } from '../services/evaluationApi'
import {
  getAiResponseFeedbackOverview,
  getProductionFeedbackContext,
  promoteProductionFeedback,
  reviewProductionFeedback,
} from '../services/aiFeedbackApi'
import type { BadCaseItem, EvaluationOverview } from '../services/evaluationApi'
import type {
  AiFeedbackRegressionCandidate,
  AiResponseFeedbackOverview,
  ProductionFeedbackContext,
} from '../services/aiFeedbackApi'

const overview = ref<EvaluationOverview | null>(null)
const loading = ref(false)
const selectedBadCaseId = ref('')
const feedbackOverview = ref<AiResponseFeedbackOverview | null>(null)
const feedbackReviewVisible = ref(false)
const feedbackReviewLoading = ref(false)
const feedbackPromotionSubmitting = ref(false)
const productionRegressionRunning = ref(false)
const selectedFeedbackContext = ref<ProductionFeedbackContext | null>(null)
const feedbackPromotionForm = reactive({
  failure_layer: 'agent_decision',
  severity: 'medium',
  failure_category: '',
  expected_behavior: '',
  recommended_action: '',
  regression_action: '',
  review_note: '',
  regression_message: '',
  regression_assertion: 'intent' as 'intent' | 'citation_present' | 'ticket_confirmation_required',
  regression_expected_intent: null as 'policy_question' | 'order_query' | 'ticket_request' | 'smalltalk' | 'unsupported' | 'unclear' | null,
})

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
    const [evaluation, feedback] = await Promise.all([
      getEvaluationOverview(),
      getAiResponseFeedbackOverview(),
    ])
    overview.value = evaluation
    feedbackOverview.value = feedback
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

async function openFeedbackReview(candidate: AiFeedbackRegressionCandidate) {
  feedbackReviewVisible.value = true
  feedbackReviewLoading.value = true
  selectedFeedbackContext.value = null
  feedbackPromotionForm.failure_layer = 'agent_decision'
  feedbackPromotionForm.severity = 'medium'
  feedbackPromotionForm.failure_category = ''
  feedbackPromotionForm.expected_behavior = ''
  feedbackPromotionForm.recommended_action = ''
  feedbackPromotionForm.regression_action = ''
  feedbackPromotionForm.review_note = ''
  feedbackPromotionForm.regression_message = ''
  feedbackPromotionForm.regression_assertion = 'intent'
  feedbackPromotionForm.regression_expected_intent = null
  try {
    selectedFeedbackContext.value = await getProductionFeedbackContext(candidate.feedback_id)
    feedbackPromotionForm.regression_message = selectedFeedbackContext.value.user_message_excerpt || ''
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '反馈上下文加载失败')
    feedbackReviewVisible.value = false
  } finally {
    feedbackReviewLoading.value = false
  }
}

async function promoteSelectedFeedback() {
  const context = selectedFeedbackContext.value
  if (!context || feedbackPromotionSubmitting.value) {
    return
  }
  const requiredValues = [
    feedbackPromotionForm.failure_category,
    feedbackPromotionForm.expected_behavior,
    feedbackPromotionForm.recommended_action,
    feedbackPromotionForm.regression_action,
    feedbackPromotionForm.regression_message,
  ]
  if (requiredValues.some((value) => !value.trim()) || (
    feedbackPromotionForm.regression_assertion === 'intent' && !feedbackPromotionForm.regression_expected_intent
  )) {
    ElMessage.warning('请完成坏案例审核字段')
    return
  }
  feedbackPromotionSubmitting.value = true
  try {
    const response = await promoteProductionFeedback(context.feedback_id, { ...feedbackPromotionForm })
    ElMessage.success(`已登记 ${response.bad_case.id}`)
    feedbackReviewVisible.value = false
    await loadOverview()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '坏案例登记失败')
  } finally {
    feedbackPromotionSubmitting.value = false
  }
}

async function runFormalProductionRegression() {
  if (productionRegressionRunning.value) {
    return
  }
  productionRegressionRunning.value = true
  try {
    const run = await runProductionRegression()
    if (overview.value) {
      overview.value.latest_production_regression_run = run
    }
    ElMessage.success(run.passed ? '正式 Bad Case 回归评测通过' : '正式 Bad Case 回归评测需要处理')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '正式 Bad Case 回归评测执行失败')
  } finally {
    productionRegressionRunning.value = false
  }
}

async function updateSelectedFeedbackReview(reviewStatus: 'triaged' | 'closed') {
  const context = selectedFeedbackContext.value
  if (!context || feedbackPromotionSubmitting.value) {
    return
  }
  feedbackPromotionSubmitting.value = true
  try {
    selectedFeedbackContext.value = await reviewProductionFeedback(context.feedback_id, {
      review_status: reviewStatus,
      review_note: feedbackPromotionForm.review_note,
    })
    ElMessage.success(reviewStatus === 'triaged' ? '审核状态已暂存' : '候选已关闭')
    await loadOverview()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '审核状态更新失败')
  } finally {
    feedbackPromotionSubmitting.value = false
  }
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
        <p>线上负反馈</p>
        <div>
          <strong>{{ feedbackOverview?.unhelpful_count || 0 }}</strong>
          <el-tag type="warning">{{ ((feedbackOverview?.unhelpful_rate || 0) * 100).toFixed(1) }}%</el-tag>
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
          <template #header>线上反馈与回归候选</template>
          <el-descriptions :column="3" border>
            <el-descriptions-item label="总反馈">{{ feedbackOverview?.total_count || 0 }}</el-descriptions-item>
            <el-descriptions-item label="有帮助">{{ feedbackOverview?.helpful_count || 0 }}</el-descriptions-item>
            <el-descriptions-item label="无帮助">{{ feedbackOverview?.unhelpful_count || 0 }}</el-descriptions-item>
          </el-descriptions>
          <el-table class="feedback-candidate-table" :data="feedbackOverview?.regression_candidates || []" height="240">
            <el-table-column prop="reason" label="原因" width="150" />
            <el-table-column prop="agent_route" label="链路" width="150" />
            <el-table-column prop="citation_count" label="引用数" width="90" />
            <el-table-column label="人工转接" width="110">
              <template #default="{ row }">
                <el-tag :type="row.human_handoff_suggested ? 'warning' : 'info'">
                  {{ row.human_handoff_suggested ? '建议过' : '未建议' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="review_status" label="状态" width="130" />
            <el-table-column prop="trace_id" label="trace_id" min-width="180" show-overflow-tooltip />
            <el-table-column label="操作" width="90" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="openFeedbackReview(row)">
                  {{ row.review_status === 'regression_added' ? '查看' : '审核' }}
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty
            v-if="feedbackOverview && feedbackOverview.regression_candidates.length === 0"
            :image-size="52"
            description="暂无线上负反馈候选"
          />
        </el-card>

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
          <template #header>
            <div class="card-header">
              <span>正式 Bad Case 回归评测</span>
              <el-button type="primary" :loading="productionRegressionRunning" @click="runFormalProductionRegression">
                运行回归
              </el-button>
            </div>
          </template>
          <el-empty
            v-if="!overview?.latest_production_regression_run"
            :image-size="52"
            description="尚未运行正式 Bad Case 回归评测"
          />
          <template v-else>
            <el-descriptions :column="3" border>
              <el-descriptions-item label="运行 ID">{{ overview.latest_production_regression_run.run_id }}</el-descriptions-item>
              <el-descriptions-item label="通过">{{ overview.latest_production_regression_run.passed_case_count }}</el-descriptions-item>
              <el-descriptions-item label="失败">{{ overview.latest_production_regression_run.failed_case_count }}</el-descriptions-item>
              <el-descriptions-item label="待补充">{{ overview.latest_production_regression_run.not_ready_case_count }}</el-descriptions-item>
              <el-descriptions-item label="执行异常">{{ overview.latest_production_regression_run.error_case_count }}</el-descriptions-item>
              <el-descriptions-item label="结论">
                <el-tag :type="overview.latest_production_regression_run.passed ? 'success' : 'warning'">
                  {{ overview.latest_production_regression_run.passed ? '通过' : '需要处理' }}
                </el-tag>
              </el-descriptions-item>
            </el-descriptions>
            <el-table :data="overview.latest_production_regression_run.results" height="260" class="feedback-candidate-table">
              <el-table-column prop="title" label="Bad Case" min-width="180" show-overflow-tooltip />
              <el-table-column prop="assertion" label="断言" width="180" />
              <el-table-column prop="expected" label="期望" width="130" />
              <el-table-column prop="actual" label="实际" width="130" />
              <el-table-column label="结果" width="110">
                <template #default="{ row }">
                  <el-tag :type="row.outcome === 'passed' ? 'success' : row.outcome === 'failed' ? 'danger' : 'warning'">
                    {{ row.outcome }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="detail" label="说明" min-width="220" show-overflow-tooltip />
            </el-table>
          </template>
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

    <el-dialog v-model="feedbackReviewVisible" title="线上反馈审核" width="min(860px, 92vw)" destroy-on-close>
      <div v-loading="feedbackReviewLoading" class="feedback-review-dialog">
        <template v-if="selectedFeedbackContext">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="反馈原因">{{ selectedFeedbackContext.reason || '未填写' }}</el-descriptions-item>
            <el-descriptions-item label="Agent 路由">{{ selectedFeedbackContext.agent_route }}</el-descriptions-item>
            <el-descriptions-item label="trace_id" :span="2">{{ selectedFeedbackContext.trace_id }}</el-descriptions-item>
          </el-descriptions>
          <section class="feedback-context-block">
            <h3>用户问题</h3>
            <p>{{ selectedFeedbackContext.user_message_excerpt || '历史问题已过期或不可用' }}</p>
          </section>
          <section class="feedback-context-block">
            <h3>AI 最终回答</h3>
            <p>{{ selectedFeedbackContext.assistant_answer_excerpt || '历史回答已过期或不可用' }}</p>
          </section>
          <section v-if="selectedFeedbackContext.citation_summary.length" class="feedback-context-block">
            <h3>引用摘要</h3>
            <p v-for="citation in selectedFeedbackContext.citation_summary" :key="citation.chunk_id || citation.source || citation.title || 'citation'">
              {{ citation.title || citation.source }}
            </p>
          </section>
          <el-form class="feedback-review-form" label-position="top">
            <el-form-item label="失败层">
              <el-select v-model="feedbackPromotionForm.failure_layer">
                <el-option label="意图识别" value="intent" />
                <el-option label="路由" value="routing" />
                <el-option label="RAG 检索" value="rag_retrieval" />
                <el-option label="RAG 引用" value="rag_citation" />
                <el-option label="Agent 决策" value="agent_decision" />
                <el-option label="工具调用" value="tool_calling" />
                <el-option label="权限" value="permission" />
                <el-option label="安全" value="security" />
                <el-option label="模型输出" value="model_output" />
              </el-select>
            </el-form-item>
            <el-form-item label="严重程度">
              <el-select v-model="feedbackPromotionForm.severity">
                <el-option label="低" value="low" />
                <el-option label="中" value="medium" />
                <el-option label="高" value="high" />
                <el-option label="严重" value="critical" />
              </el-select>
            </el-form-item>
            <el-form-item label="失败分类"><el-input v-model="feedbackPromotionForm.failure_category" maxlength="120" /></el-form-item>
            <el-form-item label="预期行为"><el-input v-model="feedbackPromotionForm.expected_behavior" type="textarea" :rows="2" maxlength="1000" /></el-form-item>
            <el-form-item label="建议改动"><el-input v-model="feedbackPromotionForm.recommended_action" type="textarea" :rows="2" maxlength="1000" /></el-form-item>
            <el-form-item label="回归策略"><el-input v-model="feedbackPromotionForm.regression_action" type="textarea" :rows="2" maxlength="1000" /></el-form-item>
            <el-form-item label="审核备注"><el-input v-model="feedbackPromotionForm.review_note" type="textarea" :rows="2" maxlength="1000" /></el-form-item>
            <el-form-item label="回归输入">
              <el-input v-model="feedbackPromotionForm.regression_message" type="textarea" :rows="2" maxlength="4000" />
            </el-form-item>
            <el-form-item label="自动断言">
              <el-select v-model="feedbackPromotionForm.regression_assertion">
                <el-option label="意图必须正确" value="intent" />
                <el-option label="必须返回引用" value="citation_present" />
                <el-option label="必须进入工单确认" value="ticket_confirmation_required" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="feedbackPromotionForm.regression_assertion === 'intent'" label="期望意图">
              <el-select v-model="feedbackPromotionForm.regression_expected_intent">
                <el-option label="政策问答" value="policy_question" />
                <el-option label="订单查询" value="order_query" />
                <el-option label="工单请求" value="ticket_request" />
                <el-option label="闲聊" value="smalltalk" />
                <el-option label="不支持" value="unsupported" />
                <el-option label="不明确" value="unclear" />
              </el-select>
            </el-form-item>
          </el-form>
        </template>
      </div>
      <template #footer>
        <el-button @click="feedbackReviewVisible = false">取消</el-button>
        <el-button :disabled="feedbackPromotionSubmitting" @click="updateSelectedFeedbackReview('closed')">关闭候选</el-button>
        <el-button :disabled="feedbackPromotionSubmitting" @click="updateSelectedFeedbackReview('triaged')">暂存审核</el-button>
        <el-button type="primary" :loading="feedbackPromotionSubmitting" @click="promoteSelectedFeedback">登记为 Bad Case</el-button>
      </template>
    </el-dialog>
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

.feedback-candidate-table {
  margin-top: 16px;
}

.feedback-review-dialog {
  display: grid;
  gap: 16px;
}

.feedback-context-block {
  border-top: 1px solid var(--el-border-color);
  padding-top: 12px;
}

.feedback-context-block h3 {
  margin: 0 0 6px;
  font-size: 14px;
}

.feedback-context-block p {
  margin: 4px 0;
  line-height: 1.65;
  white-space: pre-wrap;
}

.feedback-review-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 12px;
}

.feedback-review-form :deep(.el-form-item:nth-child(n + 3)) {
  grid-column: 1 / -1;
}

@media (max-width: 900px) {
  .layer-row {
    grid-template-columns: 1fr;
  }
  .feedback-review-form { grid-template-columns: 1fr; }
}
</style>
