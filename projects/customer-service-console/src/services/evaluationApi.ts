import { aiApi } from './http'

export interface EvaluationDataset {
  name: string
  version: string
  task_type: string
  description: string
  frozen: boolean
  baseline_run_id: string | null
  tags: string[]
}

export interface EvaluationMetric {
  name: string
  value: number
  direction: 'higher_is_better' | 'lower_is_better'
  display_value: string
}

export interface EvaluationSuite {
  name: string
  title: string
  case_count: number
  failed_case_count: number
  passed: boolean
}

export interface EvaluationRunOverview {
  run_id: string
  dataset_name: string
  dataset_version: string
  candidate_version: string
  model_name: string
  selected_case_count: number
  evaluated_check_count: number
  passed_check_count: number
  failed_check_count: number
  passed: boolean
  metrics: EvaluationMetric[]
  suites: EvaluationSuite[]
}

export interface ProductionRegressionCaseResult {
  bad_case_id: string
  title: string
  outcome: 'passed' | 'failed' | 'not_ready' | 'error'
  assertion: string | null
  expected: string | null
  actual: string | null
  detail: string
}

export interface ProductionRegressionRun {
  run_id: string
  started_at: string
  completed_at: string
  total_case_count: number
  passed_case_count: number
  failed_case_count: number
  not_ready_case_count: number
  error_case_count: number
  passed: boolean
  results: ProductionRegressionCaseResult[]
}

export interface BadCaseSummary {
  record_count: number
  open_count: number
  regression_added_count: number
  severity_counts: Record<string, number>
  status_counts: Record<string, number>
  layer_counts: Record<string, number>
}

export interface BadCaseItem {
  id: string
  title: string
  source: string
  task_type: string
  severity: string
  status: string
  failure_layer: string
  failure_category: string
  expected_behavior: string
  actual_behavior: string
  root_cause: string
  recommended_action: string
  regression_action: string
  evidence_summary: string
  tags: string[]
}

export interface EvaluationOverview {
  registry_version: string
  datasets: EvaluationDataset[]
  latest_run: EvaluationRunOverview
  bad_case_summary: BadCaseSummary
  bad_cases: BadCaseItem[]
  generated_from_latest_run: boolean
  latest_production_regression_run: ProductionRegressionRun | null
  trace_id: string
}

interface AiServiceErrorBody {
  code?: string
  message?: string
  trace_id?: string
}

export async function getEvaluationOverview() {
  try {
    const response = await aiApi.get<EvaluationOverview>('/api/ai/evaluation/overview')
    return response.data
  } catch (error: any) {
    const data = error?.response?.data as AiServiceErrorBody | undefined
    throw new Error(data?.message || 'AI 评估看板加载失败')
  }
}

export async function runProductionRegression() {
  try {
    const response = await aiApi.post<ProductionRegressionRun>('/api/ai/evaluation/runs/production-regression')
    return response.data
  } catch (error: any) {
    const data = error?.response?.data as AiServiceErrorBody | undefined
    throw new Error(data?.message || 'Production regression run failed')
  }
}
