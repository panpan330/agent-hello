from pathlib import Path

import json
import logging

from fastapi import APIRouter, Depends, Header

from app.agents.bad_case_analysis import analyze_agent_eval_bad_cases
from app.agents.eval_suite import AgentEvalRunReport, run_agent_eval_suites
from app.core.config import PROJECT_ROOT
from app.core.exceptions import AppException
from app.core.trace import get_trace_id
from app.evaluation.bad_case_registry import (
    BadCaseRecord,
    BadCaseRegistry,
    ProductionRegressionSpec,
    build_bad_case_record_from_analysis_item,
    build_bad_case_id,
    build_regression_case_draft,
    build_bad_case_registry_summary,
)
from app.evaluation.production_bad_case_registry import append_production_bad_case
from app.evaluation.case_writer import write_bad_case_to_agent_cases
from app.evaluation.production_regression import (
    ProductionRegressionRun,
    run_production_bad_case_regression,
)
from app.evaluation.production_regression_history import (
    append_production_regression_run,
    load_latest_production_regression_run,
)
from app.evaluation.eval_platform import (
    EvalDatasetManifest,
    EvalRunContext,
    EvalRunSnapshot,
    build_agent_eval_run_snapshot,
    compare_eval_run_snapshots,
    find_eval_dataset_manifest,
    load_eval_dataset_registry,
)
from app.evaluation.snapshot_store import SnapshotStore
from app.schemas.evaluation import (
    BadCaseItemView,
    BadCaseSummaryView,
    EvaluationDatasetView,
    EvaluationMetricView,
    EvaluationOverviewResponse,
    EvaluationRunOverview,
    EvaluationSuiteView,
    ProductionRegressionCaseResultView,
    ProductionRegressionRunView,
    ProductionFeedbackContextView,
    PromoteProductionFeedbackRequest,
    PromoteProductionFeedbackResponse,
    ReviewProductionFeedbackRequest,
)
from app.services.console_agent_service import ConsoleAgentActor, JavaConsoleAgentActorResolver
from app.services.java_feedback_client import JavaFeedbackClient, JavaFeedbackContext
from app.core.business_context import reset_business_context, set_business_context
from app.core.config import Settings, get_settings


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/ai/evaluation", tags=["evaluation"])
EVALUATION_REGISTRY_PATH = PROJECT_ROOT / "data" / "evaluation" / "datasets.json"
BAD_CASE_REGISTRY_PATH = PROJECT_ROOT / "data" / "evaluation" / "bad_cases.json"
PRODUCTION_REGRESSION_HISTORY_PATH = (
    PROJECT_ROOT / "data" / "evaluation" / "production_regression_runs.json"
)
EVAL_SNAPSHOT_STORE_PATH = PROJECT_ROOT / "data" / "evaluation" / "agent_eval_snapshots.json"
# agent_eval 数据集路径与 datasets.json manifest 中 cases_path="data/agent_eval/agent_cases.json" 一致
AGENT_CASES_PATH = PROJECT_ROOT / "data" / "agent_eval" / "agent_cases.json"


def get_evaluation_registry_path() -> Path:
    return EVALUATION_REGISTRY_PATH


def get_bad_case_registry_path() -> Path:
    return BAD_CASE_REGISTRY_PATH


def get_production_regression_history_path() -> Path:
    return PRODUCTION_REGRESSION_HISTORY_PATH


def get_eval_snapshot_store_path() -> Path:
    return EVAL_SNAPSHOT_STORE_PATH


def get_agent_cases_path() -> Path:
    return AGENT_CASES_PATH


def get_evaluation_actor(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> ConsoleAgentActor:
    return JavaConsoleAgentActorResolver(settings).resolve(authorization)


def require_evaluation_supervisor(actor: ConsoleAgentActor) -> None:
    if not set(actor.roles).intersection({"supervisor", "admin"}):
        raise AppException(
            code="EVALUATION_ACCESS_DENIED",
            message="Only supervisors can review production AI feedback.",
            status_code=403,
        )


def _load_feedback_context(
    *,
    feedback_id: int,
    actor: ConsoleAgentActor,
    settings: Settings,
) -> JavaFeedbackContext:
    tokens = set_business_context(user_id=actor.user_id, tenant_id=actor.tenant_id)
    try:
        return JavaFeedbackClient.from_settings(settings).get_context(feedback_id)
    finally:
        reset_business_context(tokens)


@router.get(
    "/feedback-candidates/{feedback_id}",
    response_model=ProductionFeedbackContextView,
)
def production_feedback_context(
    feedback_id: int,
    actor: ConsoleAgentActor = Depends(get_evaluation_actor),
    settings: Settings = Depends(get_settings),
) -> ProductionFeedbackContextView:
    require_evaluation_supervisor(actor)
    return _feedback_context_view(_load_feedback_context(feedback_id=feedback_id, actor=actor, settings=settings))


@router.post(
    "/feedback-candidates/{feedback_id}/promote",
    response_model=PromoteProductionFeedbackResponse,
)
def promote_production_feedback(
    feedback_id: int,
    request: PromoteProductionFeedbackRequest,
    actor: ConsoleAgentActor = Depends(get_evaluation_actor),
    settings: Settings = Depends(get_settings),
    bad_case_registry_path: Path = Depends(get_bad_case_registry_path),
    agent_cases_path: Path = Depends(get_agent_cases_path),
) -> PromoteProductionFeedbackResponse:
    require_evaluation_supervisor(actor)
    context = _load_feedback_context(feedback_id=feedback_id, actor=actor, settings=settings)
    if context.review_status == "regression_added" and context.bad_case_id:
        existing = _find_bad_case_by_id(bad_case_registry_path, context.bad_case_id)
        if existing is not None:
            return _promotion_response(existing)

    record = _build_production_bad_case(context, request)
    stored_record = append_production_bad_case(bad_case_registry_path, record)
    tokens = set_business_context(user_id=actor.user_id, tenant_id=actor.tenant_id)
    try:
        JavaFeedbackClient.from_settings(settings).mark_promoted(
            feedback_id,
            bad_case_id=stored_record.id,
        )
    finally:
        reset_business_context(tokens)
    # 反馈→用例闭环：把 bad case 写回 agent_cases.json 生成正式评测用例。
    # 写回是附属数据：失败只降级为告警日志，不阻断 promote 主流程（registry + Java 已写入）。
    try:
        written_case = write_bad_case_to_agent_cases(
            stored_record,
            cases_path=agent_cases_path,
        )
    except (OSError, ValueError) as exc:
        logger.warning(
            "agent_case_writeback_failed path=%s bad_case_id=%s error=%s",
            agent_cases_path,
            stored_record.id,
            exc,
        )
        written_case = None
    return _promotion_response(
        stored_record,
        written_case_id=written_case.id if written_case is not None else None,
    )


@router.post(
    "/feedback-candidates/{feedback_id}/review",
    response_model=ProductionFeedbackContextView,
)
def review_production_feedback(
    feedback_id: int,
    request: ReviewProductionFeedbackRequest,
    actor: ConsoleAgentActor = Depends(get_evaluation_actor),
    settings: Settings = Depends(get_settings),
) -> ProductionFeedbackContextView:
    require_evaluation_supervisor(actor)
    tokens = set_business_context(user_id=actor.user_id, tenant_id=actor.tenant_id)
    try:
        context = JavaFeedbackClient.from_settings(settings).mark_reviewed(
            feedback_id,
            review_status=request.review_status,
            review_note=request.review_note,
        )
    finally:
        reset_business_context(tokens)
    return _feedback_context_view(context)


@router.post(
    "/runs/production-regression",
    response_model=ProductionRegressionRunView,
)
def run_production_regression(
    actor: ConsoleAgentActor = Depends(get_evaluation_actor),
    bad_case_registry_path: Path = Depends(get_bad_case_registry_path),
    history_path: Path = Depends(get_production_regression_history_path),
) -> ProductionRegressionRunView:
    require_evaluation_supervisor(actor)
    registry = BadCaseRegistry.model_validate_json(
        bad_case_registry_path.read_text(encoding="utf-8")
    )
    run = run_production_bad_case_regression(registry.records)
    append_production_regression_run(history_path, run)
    return _production_regression_run_view(run)


@router.get("/overview", response_model=EvaluationOverviewResponse)
def evaluation_overview(
    registry_path: Path = Depends(get_evaluation_registry_path),
    bad_case_registry_path: Path = Depends(get_bad_case_registry_path),
    production_regression_history_path: Path = Depends(get_production_regression_history_path),
    snapshot_store_path: Path = Depends(get_eval_snapshot_store_path),
) -> EvaluationOverviewResponse:
    try:
        registry = load_eval_dataset_registry(registry_path)
        agent_dataset = find_eval_dataset_manifest(
            registry,
            name="agent_eval",
            version="stage6-v1",
        )
        run_report = run_agent_eval_suites(PROJECT_ROOT / agent_dataset.cases_path)
        snapshot = build_agent_eval_run_snapshot(
            run_report,
            context=EvalRunContext(
                run_id="local-agent-eval-latest",
                dataset_name=agent_dataset.name,
                dataset_version=agent_dataset.version,
                candidate_version="local-working-tree",
                baseline_run_id=agent_dataset.baseline_run_id,
                model_name="fake_or_rule_based",
                prompt_version="local",
                code_version="local-working-tree",
            ),
        )
        bad_cases, generated_from_latest_run = _load_or_generate_bad_cases(
            bad_case_registry_path,
            run_report=run_report,
            dataset=agent_dataset,
        )
    except FileNotFoundError as exc:
        raise AppException(
            code="EVALUATION_DATA_NOT_FOUND",
            message="本地评估数据文件不存在，无法生成评估看板。",
            status_code=500,
        ) from exc
    except ValueError as exc:
        raise AppException(
            code="EVALUATION_DATA_INVALID",
            message=str(exc),
            status_code=500,
        ) from exc

    # 基线语义：自动取最近一次保存的快照（先 load_latest 得 baseline，再保存本次）。
    # 只有 dataset/version 一致才做回归对比，否则跳过对比，避免陈旧快照让看板 500。
    # 快照是附属数据：历史快照损坏（JSON 解析/model_validate 失败）只降级为告警，
    # 本次跳过基线对比，看板仍正常返回。
    snapshot_store = SnapshotStore(snapshot_store_path)
    try:
        baseline = snapshot_store.load_latest()
    except (OSError, ValueError) as exc:
        logger.warning("snapshot_load_failed path=%s error=%s", snapshot_store_path, exc)
        baseline = None
    baseline_comparison = (
        compare_eval_run_snapshots(baseline, snapshot)
        if baseline is not None
        and baseline.context.dataset_name == snapshot.context.dataset_name
        and baseline.context.dataset_version == snapshot.context.dataset_version
        else None
    )
    # 快照是附属数据：写盘失败（含读历史损坏文件失败）只降级为告警日志，不影响看板响应。
    try:
        snapshot_store.save(snapshot)
    except (OSError, ValueError) as exc:
        logger.warning("snapshot_save_failed path=%s error=%s", snapshot_store_path, exc)

    bad_case_registry = BadCaseRegistry(
        schema_version="stage11.bad_case_registry.view",
        records=bad_cases,
    )
    bad_case_summary = build_bad_case_registry_summary(bad_case_registry)

    return EvaluationOverviewResponse(
        registry_version=registry.registry_version,
        datasets=[_dataset_view(dataset) for dataset in registry.datasets],
        latest_run=_run_overview(snapshot, run_report),
        bad_case_summary=BadCaseSummaryView.model_validate(
            bad_case_summary.model_dump()
        ),
        bad_cases=[_bad_case_view(record) for record in bad_cases],
        generated_from_latest_run=generated_from_latest_run,
        latest_production_regression_run=_optional_production_regression_run_view(
            load_latest_production_regression_run(production_regression_history_path)
        ),
        baseline_comparison=baseline_comparison,
        trace_id=get_trace_id(),
    )


def _load_or_generate_bad_cases(
    bad_case_registry_path: Path,
    *,
    run_report: AgentEvalRunReport,
    dataset: EvalDatasetManifest,
) -> tuple[list[BadCaseRecord], bool]:
    bad_case_registry = BadCaseRegistry.model_validate_json(
        bad_case_registry_path.read_text(encoding="utf-8")
    )
    production_records = [record for record in bad_case_registry.records if record.source == "production"]
    if bad_case_registry.records and not production_records:
        return bad_case_registry.records, False

    analysis_report = analyze_agent_eval_bad_cases(run_report)
    generated_records = [
        build_bad_case_record_from_analysis_item(
            item,
            discovered_run_id="local-agent-eval-latest",
            dataset_name=dataset.name,
            dataset_version=dataset.version,
        )
        for item in analysis_report.items
    ]
    merged_records = {record.id: record for record in generated_records}
    for record in bad_case_registry.records:
        merged_records[record.id] = record
    return list(merged_records.values()), True


def _dataset_view(dataset: EvalDatasetManifest) -> EvaluationDatasetView:
    return EvaluationDatasetView(
        name=dataset.name,
        version=dataset.version,
        task_type=dataset.task_type,
        description=dataset.description,
        frozen=dataset.frozen,
        baseline_run_id=dataset.baseline_run_id,
        tags=dataset.tags,
    )


def _run_overview(
    snapshot: EvalRunSnapshot,
    run_report: AgentEvalRunReport,
) -> EvaluationRunOverview:
    return EvaluationRunOverview(
        run_id=snapshot.context.run_id,
        dataset_name=snapshot.context.dataset_name,
        dataset_version=snapshot.context.dataset_version,
        candidate_version=snapshot.context.candidate_version,
        model_name=snapshot.context.model_name,
        selected_case_count=run_report.selected_case_count,
        evaluated_check_count=snapshot.evaluated_check_count,
        passed_check_count=snapshot.passed_check_count,
        failed_check_count=snapshot.failed_check_count,
        passed=snapshot.passed,
        metrics=[
            EvaluationMetricView(
                name=metric.name,
                value=metric.value,
                direction=metric.direction,
                display_value=_format_metric_value(metric.name, metric.value),
            )
            for metric in snapshot.metrics
        ],
        suites=[
            EvaluationSuiteView(
                name=suite.name,
                title=suite.title,
                case_count=suite.case_count,
                failed_case_count=suite.failed_case_count,
                passed=suite.passed,
            )
            for suite in run_report.suite_reports
        ],
    )


def _bad_case_view(record: BadCaseRecord) -> BadCaseItemView:
    return BadCaseItemView(
        id=record.id,
        title=record.title,
        source=record.source,
        task_type=record.task_type,
        severity=record.severity,
        status=record.status,
        failure_layer=record.failure_layer,
        failure_category=record.failure_category,
        expected_behavior=record.expected_behavior,
        actual_behavior=record.actual_behavior,
        root_cause=record.root_cause,
        recommended_action=record.recommended_action,
        regression_action=record.regression_action,
        evidence_summary=record.evidence_summary,
        tags=record.tags,
    )


def _format_metric_value(name: str, value: float) -> str:
    if name.endswith("_rate"):
        return f"{value * 100:.1f}%"
    if value.is_integer():
        return str(int(value))
    return f"{value:.4f}"


def _feedback_context_view(context: JavaFeedbackContext) -> ProductionFeedbackContextView:
    return ProductionFeedbackContextView(
        feedback_id=context.feedback_id,
        conversation_id=context.conversation_id,
        trace_id=context.trace_id,
        reason=context.reason,
        agent_route=context.agent_route,
        citation_count=context.citation_count,
        human_handoff_suggested=context.human_handoff_suggested,
        user_message_excerpt=context.user_message_excerpt,
        assistant_answer_excerpt=context.assistant_answer_excerpt,
        citation_summary=_parse_citation_summary(context.citation_summary_json),
        review_status=context.review_status,
        bad_case_id=context.bad_case_id,
        review_note=context.review_note,
    )


def _build_production_bad_case(
    context: JavaFeedbackContext,
    request: PromoteProductionFeedbackRequest,
) -> BadCaseRecord:
    failure_layer = request.failure_layer
    bad_case_id = build_bad_case_id(
        dataset_name="production_feedback",
        dataset_version="stage11",
        source_case_id=f"feedback_{context.feedback_id}",
        failure_layer=failure_layer,
    )
    user_message = context.user_message_excerpt or "The original customer request was unavailable."
    answer = context.assistant_answer_excerpt or "The original AI answer was unavailable."
    citations = _parse_citation_summary(context.citation_summary_json)
    citation_evidence = ", ".join(
        item.get("source") or item.get("title") or "unknown source" for item in citations
    ) or "no citations"
    return BadCaseRecord(
        id=bad_case_id,
        title=f"Production feedback {context.feedback_id}: {request.failure_category.strip()}",
        source="production",
        task_type="rag" if failure_layer in {"rag_retrieval", "rag_citation"} else "agent",
        severity=request.severity,
        status="regression_added",
        source_case_id=f"feedback_{context.feedback_id}",
        failure_layer=failure_layer,
        failure_category=request.failure_category.strip(),
        expected_behavior=request.expected_behavior.strip(),
        actual_behavior=f"Customer request: {user_message}\n\nAI answer: {answer}",
        root_cause=request.review_note.strip(),
        recommended_action=request.recommended_action.strip(),
        regression_action=request.regression_action.strip(),
        regression_dataset_name="agent_eval",
        regression_case_id=f"feedback_{context.feedback_id}_regression_{failure_layer}",
        production_regression=ProductionRegressionSpec(
            message=request.regression_message,
            assertion=request.regression_assertion,
            expected_intent=request.regression_expected_intent,
            expected_tool=request.regression_expected_tool,
            must_ask_fields=request.regression_must_ask_fields,
            must_not_reveal_terms=request.regression_must_not_reveal_terms,
        ),
        evidence_summary=(
            f"production_feedback_id={context.feedback_id}; trace_id={context.trace_id}; "
            f"reason={context.reason or 'unspecified'}; route={context.agent_route}; citations={citation_evidence}"
        ),
        tags=[
            "bad_case",
            "production_feedback",
            "regression_added",
            failure_layer,
            request.severity,
            *( [context.reason] if context.reason else [] ),
        ],
    )


def _promotion_response(
    record: BadCaseRecord,
    *,
    written_case_id: str | None = None,
) -> PromoteProductionFeedbackResponse:
    return PromoteProductionFeedbackResponse(
        bad_case=_bad_case_view(record),
        regression_draft=build_regression_case_draft(record).model_dump(mode="json"),
        written_case_id=written_case_id,
    )


def _optional_production_regression_run_view(
    run: ProductionRegressionRun | None,
) -> ProductionRegressionRunView | None:
    return _production_regression_run_view(run) if run is not None else None


def _production_regression_run_view(run: ProductionRegressionRun) -> ProductionRegressionRunView:
    return ProductionRegressionRunView(
        run_id=run.run_id,
        started_at=run.started_at.isoformat(),
        completed_at=run.completed_at.isoformat(),
        total_case_count=run.total_case_count,
        passed_case_count=run.passed_case_count,
        failed_case_count=run.failed_case_count,
        not_ready_case_count=run.not_ready_case_count,
        error_case_count=run.error_case_count,
        passed=run.passed,
        results=[
            ProductionRegressionCaseResultView(
                bad_case_id=result.bad_case_id,
                title=result.title,
                outcome=result.outcome,
                assertion=result.assertion,
                expected=result.expected,
                actual=result.actual,
                detail=result.detail,
            )
            for result in run.results
        ],
    )


def _find_bad_case_by_id(path: Path, bad_case_id: str) -> BadCaseRecord | None:
    registry = BadCaseRegistry.model_validate_json(path.read_text(encoding="utf-8"))
    return next((record for record in registry.records if record.id == bad_case_id), None)


def _parse_citation_summary(raw: str | None) -> list[dict[str, str | None]]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(value, list):
        return []
    results: list[dict[str, str | None]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        results.append(
            {
                "source": _optional_string(item.get("source")),
                "title": _optional_string(item.get("title")),
                "chunk_id": _optional_string(item.get("chunk_id")),
            }
        )
    return results


def _optional_string(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None
