from typing import Literal

from pydantic import BaseModel, Field


class EvaluationDatasetView(BaseModel):
    name: str
    version: str
    task_type: str
    description: str
    frozen: bool
    baseline_run_id: str | None = None
    tags: list[str] = Field(default_factory=list)


class EvaluationMetricView(BaseModel):
    name: str
    value: float
    direction: Literal["higher_is_better", "lower_is_better"]
    display_value: str


class EvaluationSuiteView(BaseModel):
    name: str
    title: str
    case_count: int
    failed_case_count: int
    passed: bool


class EvaluationRunOverview(BaseModel):
    run_id: str
    dataset_name: str
    dataset_version: str
    candidate_version: str
    model_name: str
    selected_case_count: int
    evaluated_check_count: int
    passed_check_count: int
    failed_check_count: int
    passed: bool
    metrics: list[EvaluationMetricView] = Field(default_factory=list)
    suites: list[EvaluationSuiteView] = Field(default_factory=list)


class BadCaseSummaryView(BaseModel):
    record_count: int
    open_count: int
    regression_added_count: int
    severity_counts: dict[str, int] = Field(default_factory=dict)
    status_counts: dict[str, int] = Field(default_factory=dict)
    layer_counts: dict[str, int] = Field(default_factory=dict)


class BadCaseItemView(BaseModel):
    id: str
    title: str
    source: str
    task_type: str
    severity: str
    status: str
    failure_layer: str
    failure_category: str
    expected_behavior: str
    actual_behavior: str
    root_cause: str
    recommended_action: str
    regression_action: str
    evidence_summary: str
    tags: list[str] = Field(default_factory=list)


class EvaluationOverviewResponse(BaseModel):
    registry_version: str
    datasets: list[EvaluationDatasetView] = Field(default_factory=list)
    latest_run: EvaluationRunOverview
    bad_case_summary: BadCaseSummaryView
    bad_cases: list[BadCaseItemView] = Field(default_factory=list)
    generated_from_latest_run: bool
    trace_id: str
