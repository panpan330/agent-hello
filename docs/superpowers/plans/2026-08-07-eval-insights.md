# 评测深化后续（趋势图 / 报告导出 / CI 定时回归）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 补全评测体系后续三方向——评测趋势图（echarts 折线图）、报告导出 API + 前端下载、CI cron 定时回归，让评测闭环具备可观测性与自动化。

**Architecture:** 三块独立衔接的改造：①后端数据层（EvalRunContext 加 started_at、SnapshotStore.load_all、新 history 端点）→ 前端 echarts 趋势图；②报告生成器（新增 build_production_regression_markdown_report）+ 新 reports 端点 → 前端下载按钮；③CI workflow 加 schedule cron + 新增 scripts/production_regression.py CLI。评测纯本地（规则分类器 + run_ticket_agent），CI 可跑。

**Tech Stack:** Python 3.12 + FastAPI + Pydantic + LangGraph；Vue 3 + Element Plus + echarts；GitHub Actions；pytest。

## Global Constraints

- 自动测试不调用真实模型、不命中真实 Embedding/Rerank API、不写入真实业务数据、不依赖真实 Redis。
- 现有测试套件保持绿色：Python `uv run pytest -q` = 1484 passed；前端 `npm run build` 通过。
- **echarts 是唯一允许新增的第三方依赖**（用户明确选择引入，突破"不新增第三方依赖"约束）；锁定版本 `echarts@^5`。
- 评测套件用 fake/规则依赖，不依赖真实模型服务。
- snapshot 落盘原子写（.tmp + replace，参考 production_bad_case_registry.py:12-23）；保留最近 50 条。
- 生产回归历史保留最近 30 条（production_regression_history.py:12 的 MAX_STORED_RUNS）。
- history 端点读取用既有 `get_production_regression_history_path`（evaluation.py:89-90）与 `get_eval_snapshot_store_path`（:93）依赖。
- CI cron：`'0 2 * * *'`（每日 UTC 02:00 = 北京时间 10:00）；保留 workflow_dispatch。
- 报告导出响应：JSON 包 `{report: "...", type, generated_at}`（跟随现有 ApiResponse 模式）；无数据 404。
- 本地 git commit；不推送 GitHub。

---

### Task 1: 后端数据层（started_at + load_all + history 端点）

**Files:**
- Modify: `projects/ai-service/app/evaluation/eval_platform.py`（EvalRunContext 加 started_at；build_agent_eval_run_snapshot 填时间戳）
- Modify: `projects/ai-service/app/evaluation/snapshot_store.py`（_load_all 提升为公开 load_all）
- Modify: `projects/ai-service/app/routers/evaluation.py`（新增 GET /history 端点）
- Modify: `projects/ai-service/app/schemas/evaluation.py`（加 history 响应 schema）
- Test: `projects/ai-service/tests/test_eval_platform.py` + `tests/test_evaluation_api.py`

**Interfaces:**
- Consumes: `SnapshotStore`（load_latest/save）、`EvalRunContext`、`build_agent_eval_run_snapshot`、`get_eval_snapshot_store_path`/`get_production_regression_history_path`、`load_latest_production_regression_run`
- Produces: `EvalRunContext.started_at: datetime | None`；`SnapshotStore.load_all() -> list[EvalRunSnapshot]`；`GET /api/ai/evaluation/history` 返回 `{agent_eval: [{started_at, check_pass_rate}], production_regression: [{started_at, passed, total, pass_rate}]}`（Task 3 前端消费）

- [ ] **Step 1: 写失败测试**

```python
# test_eval_platform.py 追加
def test_eval_run_context_carries_started_at():
    # build_agent_eval_run_snapshot 后 context.started_at 非 None（datetime UTC）
def test_snapshot_store_load_all_returns_ordered_snapshots():
    # save 3 条 → load_all() 返回 3 条按保存顺序（时间升序）
# test_evaluation_api.py 追加
def test_history_returns_agent_and_regression_sequences():
    # 造 snapshot（2 条）+ 回归历史（1 条）→ GET /history → agent_eval 2 点 + production_regression 1 点
def test_history_returns_empty_arrays_when_no_data():
    # 无 snapshot 无回归历史 → 200 + 空数组
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd projects/ai-service && uv run pytest tests/test_eval_platform.py tests/test_evaluation_api.py -q`
Expected: 新 4 测试失败

- [ ] **Step 3: EvalRunContext 加 started_at + build 填时间戳**

`eval_platform.py`：
```python
class EvalRunContext(BaseModel):
    run_id: str = Field(min_length=1)
    # ... 现有字段 ...
    started_at: datetime | None = None
```
`build_agent_eval_run_snapshot` 构造 context 时 `started_at=datetime.now(timezone.utc)`（或由调用方传，跟随现有签名最小侵入）。

- [ ] **Step 4: SnapshotStore.load_all 公开化**

`snapshot_store.py`：`_load_all` 改为公开 `load_all`（或保留私有 + 加公开包装——跟随最小侵入）。

- [ ] **Step 5: history 端点**

`routers/evaluation.py` 新增：
```python
@router.get("/api/ai/evaluation/history", response_model=EvaluationHistoryView)
def get_evaluation_history(
    snapshot_store_path: Path = Depends(get_eval_snapshot_store_path),
    regression_history_path: Path = Depends(get_production_regression_history_path),
) -> EvaluationHistoryView:
    # agent_eval: SnapshotStore(path).load_all() → [{started_at, check_pass_rate}]（metric_map()["check_pass_rate"]）
    # production_regression: load_latest_production_regression_run 的历史（runs 列表）
    #   需要读全量 runs（load_latest 只取最后一条）——实现时用 append 的反向：读 JSON runs 列表
    # 响应 {agent_eval: [...], production_regression: [...]}（无数据空数组）
```
`schemas/evaluation.py` 加 `EvaluationHistoryPoint`（started_at/passed/total/pass_rate 可选）+ `EvaluationHistoryView`（agent_eval/production_regression 列表）。

- [ ] **Step 6: 跑测试确认通过 + 相关套件**

Run: `cd projects/ai-service && uv run pytest tests/test_eval_platform.py tests/test_evaluation_api.py -q`
Expected: 4 新测试 + 原有全过

- [ ] **Step 7: 全量 pytest + Commit**

Run: `cd projects/ai-service && uv run pytest -q`
```bash
git add projects/ai-service/
git commit -m "feat: add eval history endpoint with started_at timestamps"
```

---

### Task 2: 生产回归报告生成器 + reports 导出端点

**Files:**
- Create: `projects/ai-service/app/evaluation/report_generator.py`（build_production_regression_markdown_report）
- Modify: `projects/ai-service/app/routers/evaluation.py`（新增 GET /reports/latest）
- Modify: `projects/ai-service/app/schemas/evaluation.py`（加 EvaluationReportView）
- Test: `projects/ai-service/tests/test_evaluation_api.py` + 新 `tests/test_report_generator.py`

**Interfaces:**
- Consumes: `ProductionRegressionRun`（含 results[]）、`build_agent_eval_markdown_report`（eval_report.py:6）、`run_agent_eval_suites`、`load_latest_production_regression_run`、`SnapshotStore.load_latest`
- Produces: `build_production_regression_markdown_report(run: ProductionRegressionRun) -> str`（Task 3 CLI 复用）；`GET /api/ai/evaluation/reports/latest?type=agent|regression` 返回 `EvaluationReportView{report, type, generated_at}`

- [ ] **Step 1: 写失败测试**

```python
# test_report_generator.py（新文件）
def test_build_production_regression_markdown_report_includes_overview_and_assertions():
    # 造 ProductionRegressionRun（含 intent/tool_called 两类结果）→ 报告含 "Production Regression Report" 标题、
    #   Overall 表（passed/total）、断言分布（intent: 1 passed 等）、per-case 明细（bad_case_id/assertion/outcome）
# test_evaluation_api.py 追加
def test_reports_latest_agent_returns_markdown():
    # GET /reports/latest?type=agent → 200 + report 含 "Agent Evaluation Report" + Overall 表
def test_reports_latest_regression_returns_markdown():
    # 造回归历史 → GET /reports/latest?type=regression → report 含 "Production Regression Report"
def test_reports_latest_not_found_when_no_data():
    # 无任何历史 → 404 REPORT_NOT_FOUND
def test_reports_latest_rejects_unknown_type():
    # type=foo → 422
```

- [ ] **Step 2: 跑测试确认失败**

- [ ] **Step 3: 实现 build_production_regression_markdown_report**

`report_generator.py`（仿 eval_report.py 风格）：
```python
def build_production_regression_markdown_report(run: ProductionRegressionRun) -> str:
    # 标题 "# Production Regression Report"
    # "## Overall" 表：Status/run_id/started_at/completed_at/total/passed/failed/not_ready/error/passed%
    # "## Assertion distribution" 表：按 assertion 聚合（count passed/failed/not_ready）
    # "## Case details" 表或列表：每 case bad_case_id/title/assertion/expected/actual/outcome/detail
```

- [ ] **Step 4: reports 端点**

`routers/evaluation.py`：
```python
@router.get("/api/ai/evaluation/reports/latest", response_model=EvaluationReportView)
def get_latest_evaluation_report(
    type: Literal["agent", "regression"] = Query("agent"),
    cases_path: Path = Depends(get_agent_cases_path),
    snapshot_store_path: Path = Depends(get_eval_snapshot_store_path),
    regression_history_path: Path = Depends(get_production_regression_history_path),
) -> EvaluationReportView:
    # type=agent: run_agent_eval_suites(cases_path) → build_agent_eval_markdown_report(run_report)
    # type=regression: 读回归历史最后一条 → build_production_regression_markdown_report(run)
    # 无数据 → AppException REPORT_NOT_FOUND(404)
    # 返回 EvaluationReportView(report=..., type=type, generated_at=now)
```
`schemas/evaluation.py` 加 `EvaluationReportView`（report: str, type: str, generated_at: datetime）。

- [ ] **Step 5: 跑测试确认通过 + 相关套件**

- [ ] **Step 6: 全量 pytest + Commit**

Run: `cd projects/ai-service && uv run pytest -q`
```bash
git add projects/ai-service/
git commit -m "feat: add evaluation report export endpoint"
```

---

### Task 3: 前端 echarts 趋势图 + 报告下载按钮

**Files:**
- Modify: `projects/customer-service-console/package.json`（加 echarts）
- Modify: `projects/customer-service-console/src/services/evaluationApi.ts`（getEvaluationHistory/getLatestReport）
- Modify: `projects/customer-service-console/src/views/EvaluationView.vue`（趋势图卡片 + 下载按钮）
- Test: 前端 `npm run build`

**Interfaces:**
- Consumes: Task 1 的 `GET /history`（agent_eval/production_regression 序列）、Task 2 的 `GET /reports/latest`
- Produces: 前端趋势图（echarts 折线，两条序列）+ "下载报告"下拉按钮

- [ ] **Step 1: 安装 echarts**

Run: `cd projects/customer-service-console && npm install echarts@^5`
Expected: package.json + package-lock.json 更新

- [ ] **Step 2: evaluationApi.ts 加方法**

```ts
export function getEvaluationHistory(): Promise<EvaluationHistory>  // GET /api/ai/evaluation/history
export function getLatestReport(type: 'agent' | 'regression'): Promise<EvaluationReport>  // GET /api/ai/evaluation/reports/latest?type=...
// 加类型：EvaluationHistoryPoint/EvaluationHistory/EvaluationReport
```

- [ ] **Step 3: EvaluationView.vue 趋势图卡片**

- 概览区（基线对比卡片后）加"评测趋势"卡片
- `onMounted` 时 `getEvaluationHistory()` → echarts 折线图（两条序列：agent 通过率 / 回归通过率，x 轴时间）
- 引入 `echarts`：`import * as echarts from 'echarts'`，在卡片 div 上 init + setOption
- 无数据时空态提示
- `beforeUnmount` 时 dispose

- [ ] **Step 4: EvaluationView.vue 下载按钮**

- 本地评估运行信息卡片（约 L410-427）加"下载报告"el-dropdown（Agent 评测报告 / 生产回归报告）
- 点击 → `getLatestReport(type)` → 拿 report 文本 → Blob 下载 `.md` 文件（文件名 `agent-eval-report-YYYYMMDD.md` / `production-regression-report-YYYYMMDD.md`）
- 404 时 ElMessage 提示"暂无报告数据"

- [ ] **Step 5: 前端构建验证**

Run: `cd projects/customer-service-console && npm run build`
Expected: 构建成功（echarts 类型检查通过）

- [ ] **Step 6: Commit**

```bash
git add projects/customer-service-console/
git commit -m "feat: add eval trend chart and report download to evaluation view"
```

---

### Task 4: CI cron 定时回归 + production_regression CLI

**Files:**
- Create: `projects/ai-service/scripts/production_regression.py`（CLI）
- Modify: `.github/workflows/ci.yml`（schedule cron + eval-regression job）
- Test: CLI 冒烟（本地跑一次）

**Interfaces:**
- Consumes: Task 2 的 `build_production_regression_markdown_report`；`run_production_bad_case_regression`（production_regression.py:41）、`append_production_regression_run`（production_regression_history.py:27）
- Produces: `scripts/production_regression.py`（--bad-cases-path/--history-path/--report-path）；CI eval-regression job

- [ ] **Step 1: 写 CLI 脚本**

`scripts/production_regression.py`：
```python
"""Run production bad-case regression and write a Markdown report.

Usage:
    uv run python scripts/production_regression.py \
        --report-path data/agent_eval/reports/production_regression_report.md
"""
import argparse
from pathlib import Path

from app.evaluation.bad_case_registry import BadCaseRegistry, load...  # 读 bad_cases.json
from app.evaluation.production_regression import run_production_bad_case_regression
from app.evaluation.production_regression_history import append_production_regression_run
from app.evaluation.report_generator import build_production_regression_markdown_report

def main() -> int:
    parser = argparse.ArgumentParser(...)
    parser.add_argument("--bad-cases-path", default="data/evaluation/bad_cases.json")
    parser.add_argument("--history-path", default="data/evaluation/production_regression_runs.json")
    parser.add_argument("--report-path", default="data/agent_eval/reports/production_regression_report.md")
    args = parser.parse_args()
    # 1. 读 registry records
    # 2. run_production_bad_case_regression(records)（只跑 source=production + regression_added）
    # 3. append_production_regression_run(history_path, run)
    # 4. build_production_regression_markdown_report(run) → 写 report_path（建目录）
    # 5. print 摘要（passed/total）→ return 0
if __name__ == "__main__":
    raise SystemExit(main())
```
（读 bad_cases.json 用现有 BadCaseRegistry 加载函数——实现时读 bad_case_registry.py 确认加载入口。）

- [ ] **Step 2: 本地冒烟测试**

Run: `cd projects/ai-service && uv run python scripts/production_regression.py --report-path data/agent_eval/reports/production_regression_report.md`
Expected: 打印摘要；报告文件生成（bad_cases.json 为空时跑 0 条，报告含 Overall 表但无 case）

- [ ] **Step 3: CI workflow 扩展**

`.github/workflows/ci.yml`：
```yaml
on:
  push: { branches: [main] }
  pull_request: { branches: [main] }
  schedule:
    - cron: '0 2 * * *'
  workflow_dispatch:

jobs:
  # ... 现有 regression job 不动 ...
  eval-regression:
    name: Eval regression (daily)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with: { enable-cache: true }
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - name: Install dependencies
        run: uv sync --frozen
      - name: Run agent eval regression
        run: uv run python scripts/agent_eval.py --regression --report-path data/agent_eval/reports/ci-agent-report.md
      - name: Run production regression
        run: uv run python scripts/production_regression.py --report-path data/agent_eval/reports/ci-regression-report.md
      - name: Upload reports
        uses: actions/upload-artifact@v4
        with:
          name: eval-reports
          path: data/agent_eval/reports/*.md
```

- [ ] **Step 4: Commit**

```bash
git add projects/ai-service/scripts/production_regression.py .github/workflows/ci.yml
git commit -m "feat: add daily eval regression cron and production regression CLI"
```

---

### Task 5: 全量回归与真实验收

**Files:**
- Modify: `docs/project-handoff-for-vibe-coding.md`（第 17/18 节更新评测能力）
- 无代码变更（验收）

**Interfaces:**
- Consumes: 全部 Task 1-4 交付

- [ ] **Step 1: Python 全量回归**

Run: `cd projects/ai-service && uv run pytest -q`
Expected: ≥1484 passed（新增测试全过）

- [ ] **Step 2: 前端构建**

Run: `cd projects/customer-service-console && npm run build`
Expected: 构建成功

- [ ] **Step 3: 真实验收（启动 Python 8000）**

启动：`cd projects/ai-service && uv run uvicorn app.main:app --host 127.0.0.1 --port 8000`
- **场景 1（趋势图数据）**：GET /overview 两次（生成 2 条 snapshot）→ GET /history → agent_eval 序列 2 点（started_at + check_pass_rate）；本地跑 scripts/production_regression.py → history 含回归序列
- **场景 2（报告导出）**：GET /reports/latest?type=agent → Markdown 含 Overall 表；type=regression → 含断言分布；type=foo → 422
- **场景 3（CI 配置）**：本地跑 scripts/production_regression.py --report-path 确认输出；CI workflow YAML 结构审查（无法本地跑 GitHub Actions，验证语法 + 文档说明）

- [ ] **Step 4: 更新交接文档**

- 第 17 节评测能力更新（趋势图/报告导出/定时回归）
- 第 18 节"已完成里程碑"加"评测深化后续"
- 候选方向表更新（评测深化后续标记完成；echarts 依赖说明）

- [ ] **Step 5: 最终全分支审查 + Commit**

```bash
git add docs/project-handoff-for-vibe-coding.md
git commit -m "docs: update handoff with eval insights milestone"
```

---

## Self-Review 记录

**1. Spec 覆盖：**
- 3.1 趋势图（started_at + load_all + history 端点 + echarts）→ Task 1 + Task 3 ✅
- 3.2 报告导出（reports 端点 + 生成器 + 前端下载）→ Task 2 + Task 3 ✅
- 3.3 CI cron（schedule + eval-regression job + CLI 脚本）→ Task 4 ✅
- 4 测试与验收 → Task 5 ✅

**2. 占位符扫描：** 无 TBD/TODO；Task 1 Step 5 的"读全量 runs"（load_latest 只取最后一条）给了实现路径（读 JSON runs 列表）；Task 4 Step 1 的 registry 加载入口注明"实现时读 bad_case_registry.py 确认"——不阻塞。

**3. 类型一致性：**
- `build_production_regression_markdown_report(run)` 在 Task 2 定义、Task 4 CLI 复用——签名一致 ✅
- `GET /history` 返回结构（agent_eval/production_regression 序列）在 Task 1 定义、Task 3 前端类型——一致 ✅
- `getLatestReport(type)` 在 Task 3 前端、Task 2 端点——一致 ✅
- started_at 字段在 Task 1 定义、Task 5 验收——一致 ✅

**开放点（实现时按实际代码修正）：**
- build_agent_eval_run_snapshot 的时间戳注入方式（context 构造处或调用方传）
- history 端点生产回归读全量 runs 的具体实现（load_latest 只取最后一条，需读 JSON 列表）
- bad_cases.json 加载入口（bad_case_registry.py 的加载函数名）
- 前端 echarts 引入方式（全量 import vs 按需）
