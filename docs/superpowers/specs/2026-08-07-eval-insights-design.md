# 评测深化后续（趋势图 / 报告导出 / CI 定时回归）— 设计规格

> 日期：2026-08-07
> 项目：AI 客服/工单系统（Java 18004 / Python AI 8000 / Vue 5173）
> 目标：补全评测体系后续三方向——评测趋势图（echarts）、报告导出 API + 前端下载、CI cron 定时回归，让评测闭环具备可观测性与自动化。

## 1. 背景与目标

### 1.1 现状（explore 调查结论）
- 生产回归历史 `production_regression_history.py`：30 条上限，每条 run 含 started_at/completed_at（UTC）+ 四类计数 + passed + results[]（per-case assertion/expected/actual）——**可直接支撑通过率时间序列**；`data/evaluation/production_regression_runs.json` 当前不存在（从未跑过）
- agent eval snapshot `snapshot_store.py`：50 条上限，`SnapshotStore` 只有 load_latest/save，`_load_all` 私有；`EvalRunContext`（eval_platform.py:70-101）**无时间戳字段**；snapshot 有 `check_pass_rate` 等 4 指标
- 无任何定时机制（grep apscheduler/scheduler/cron/BackgroundTasks 无命中）；CI workflow（.github/workflows/ci.yml）只有 push/PR + workflow_dispatch，只跑 pytest，**不跑评测 CLI**
- 报告生成器 `eval_report.py` 完整（build_agent_eval_markdown_report :6-54），CLI 支持 --report-path；**无报告导出 API**、前端无下载入口
- 前端 EvaluationView：无图表库（package.json 无 echarts/chart.js）、回归评测卡片只渲染单次 run、无历史列表
- overview 接口（EvaluationOverviewResponse）无历史/趋势字段

### 1.2 目标（用户确认的决策）
- **三方向一次闭环**：趋势图（echarts）+ 报告导出 API + 前端下载 + CI cron 定时回归
- **图表用 echarts**（用户选择引入，突破"不新增第三方依赖"约束——本规格明确允许 echarts）
- **定时用 CI cron**（GitHub Actions schedule，零常驻进程）
- **报告导出 API + 前端下载按钮**（agent/regression 两种类型）

## 2. 架构与数据流

```
用户查看评测趋势
  → GET /api/ai/evaluation/history
  → 后端读 agent_eval_snapshots.json（load_all）+ production_regression_runs.json
  → 返回两序列 [{started_at, check_pass_rate}] / [{started_at, passed, total, pass_rate}]
  → 前端 echarts 折线图展示

用户下载报告
  → GET /api/ai/evaluation/reports/latest?type=agent|regression
  → agent: build_agent_eval_markdown_report(最近 run_report)
  → regression: build_production_regression_markdown_report(最近 run)
  → 前端 Blob 下载 .md

定时回归（CI）
  → GitHub Actions schedule cron 每日触发
  → uv run python scripts/agent_eval.py --regression --report-path ...
  → uv run python scripts/production_regression.py --report-path ...
  → 上传报告 artifact
```

## 3. 变更设计

### 3.1 趋势图（echarts）

**后端数据准备**：
- `EvalRunContext`（eval_platform.py:70-101）加字段：`started_at: datetime | None = None`（build_agent_eval_run_snapshot 时填 `datetime.now(timezone.utc)`）
- `SnapshotStore`（snapshot_store.py）加公开 `load_all() -> list[EvalRunSnapshot]`（把现有私有 `_load_all`（:58-60）提升为公开，或新增公开方法调用私有实现——跟随最小侵入）
- 新增端点 `GET /api/ai/evaluation/history`（routers/evaluation.py）：
  - agent eval 序列：从 snapshot load_all 取，`[{started_at, check_pass_rate}]`（按时间升序）
  - 生产回归序列：从 production_regression_runs.json 取全部，`[{started_at, passed, total, pass_rate}]`
  - 响应：`{agent_eval: [...], production_regression: [...]}`（无数据时空数组）
  - 生产回归读取用新依赖 `get_production_regression_history_path`（routers/evaluation.py 已有常量 `PRODUCTION_REGRESSION_HISTORY_PATH`，需包装为依赖注入函数供 history 端点使用，仿 get_bad_case_registry_path 模式）

**前端**：
- 引入 echarts（package.json 加依赖 + npm install）
- EvaluationView 加"评测趋势"卡片：echarts 折线图，两条序列（agent 通过率 / 回归通过率），x 轴时间（started_at 格式化）
- 无历史数据时显示空态提示
- 数据来自新 `evaluationApi.getEvaluationHistory()`

### 3.2 报告导出 API + 前端下载

**后端**：
- 新增 `GET /api/ai/evaluation/reports/latest?type=agent|regression`（routers/evaluation.py）：
  - `type=agent`：复用 `build_agent_eval_markdown_report(run_report)`（最近一次本地评测 run_report——overview 已跑，需从 /overview 逻辑取或重跑；实现时定：重跑一次 run_agent_eval_suites 最简单）→ 返回 Markdown
  - `type=regression`：新增 `build_production_regression_markdown_report(run)`（app/evaluation/ 下新文件或并入 eval_report.py——选并入 `app/evaluation/report_generator.py` 或 `eval_report.py`，跟随现有组织）→ 含 run 概览表 + 每 case 断言分布 + 结果明细（仿 eval_report.py 风格）
  - 响应：JSON 包 `{report: "markdown文本", type, generated_at}`（跟随现有 ApiResponse JSON 模式，前端转 Blob）
  - 无数据时返回 404（AppException REPORT_NOT_FOUND）
- schema：`schemas/evaluation.py` 加 `EvaluationReportView`（report/type/generated_at）

**前端**：
- EvaluationView 加"下载报告"按钮（el-dropdown：Agent 评测报告 / 生产回归报告）
- 点击 → 调 `evaluationApi.getLatestReport(type)` → 拿 Markdown 文本 → 转 Blob 触发下载 `.md` 文件（文件名如 `agent-eval-report-YYYYMMDD.md`）
- `evaluationApi.ts` 加 `getEvaluationHistory()` 与 `getLatestReport(type)`

### 3.3 CI cron 定时回归

**GitHub Actions**（.github/workflows/ci.yml）：
- `on` 加 `schedule: cron: '0 2 * * *'`（每日 UTC 02:00 = 北京时间 10:00）+ 保留 workflow_dispatch
- 新增 job `eval-regression`（runs-on ubuntu-latest，复用现有 setup steps）：
  - `uv run python scripts/agent_eval.py --regression --report-path data/agent_eval/reports/ci-agent-report.md`
  - `uv run python scripts/production_regression.py --report-path data/agent_eval/reports/ci-regression-report.md`
  - `actions/upload-artifact@v4` 上传 `data/agent_eval/reports/*.md`
- 现有 pytest job 不动

**新增 CLI 脚本 `scripts/production_regression.py`**：
- 参数：`--bad-cases-path`（默认 data/evaluation/bad_cases.json）、`--history-path`（默认 data/evaluation/production_regression_runs.json）、`--report-path`（默认 data/agent_eval/reports/production_regression_report.md）
- 逻辑：读 bad_cases registry → `run_production_bad_case_regression(records)` → append 历史（原子写）→ `build_production_regression_markdown_report` 写盘
- 本地可跑、CI 可跑

## 4. 测试与验收

### 4.1 单元测试（Python 基线 1484 passed）
| 模块 | 测试 |
| --- | --- |
| 趋势图后端 | history 端点（有数据返回两序列、无数据空数组）；SnapshotStore.load_all；EvalRunContext.started_at 落盘（build snapshot 后 context.started_at 非 None） |
| 报告导出 | reports 端点（agent 类型含 Overall 表、regression 类型含断言分布、无数据 404）；build_production_regression_markdown_report 单测 |
| CLI | scripts/production_regression.py 冒烟（参数解析 + 跑一次 + 写报告） |

### 4.2 前端
- echarts 引入 + 趋势图卡片 + 下载按钮
- `npm run build` 通过（echarts 类型检查）

### 4.3 全量回归
- Python `uv run pytest -q`（1484 + 新增全过）；前端 build；Java 无改动

### 4.4 真实验收（启动 Python 8000）
- **场景 1（趋势图数据）**：跑两次 /overview（生成 2 条 snapshot）→ GET /history → agent_eval 序列 2 点（started_at + check_pass_rate）；跑一次生产回归 → history 含回归序列
- **场景 2（报告导出）**：GET /reports/latest?type=agent → Markdown 含 Overall 表；type=regression → 含断言分布；前端下载按钮触发下载 .md
- **场景 3（CI 配置）**：本地跑 scripts/production_regression.py --report-path 确认输出；CI workflow YAML 结构审查（本地无法跑 GitHub Actions，验证语法 + 文档说明）

## 5. 范围外（YAGNI）
- 评测报告前端预览（只做下载按钮）
- 回归历史趋势的断言分布图（只做通过率折线）
- 服务内定时 scheduler（用 CI cron 替代）
- 更多报告类型（bad case 分析报告已有 CLI，不加 API）

## 6. 风险与开放点
- **echarts 引入突破"不新增第三方依赖"约束**：用户明确选择，本规格允许；锁定版本（echarts ^5.x）
- **history 端点生产回归读取**：routers/evaluation.py 已有 `PRODUCTION_REGRESSION_HISTORY_PATH` 常量，需包装为依赖注入函数（仿 get_bad_case_registry_path 模式）供 history 端点用
- **reports 端点 agent 类型重跑评测**：每次请求重跑 run_agent_eval_suites（与 overview 一致，评测快 ~30s，可接受）——或复用 overview 的缓存，实现时定最小方案
- **CI 本地无法验证**：workflow 语法靠结构审查 + 文档说明；CLI 脚本本地冒烟
- **production_regression_runs.json 当前不存在**：首次跑生成
