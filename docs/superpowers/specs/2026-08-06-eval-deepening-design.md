# 评测体系深化 — 设计规格

> 日期：2026-08-06
> 项目：AI 客服/工单系统（Java 18004 / Python AI 8000 / Vue 5173）
> 目标：深化 Stage 11 反馈/评测闭环——实现 must_* 断言、扩展生产回归断言类型、接线 Baseline 对比、打通 Bad Case promote 闭环，全面提升 Agent 行为质量证明力。

## 1. 背景与目标

### 1.1 现状（explore 调查结论）
- 评测 runner：`app/agents/eval_suite.py`（4 套件：intent/field/route/rag）+ 用例 `data/agent_eval/agent_cases.json`（12 条，7 类 intent 全覆盖，含 refund_request 1 条 + prompt-injection 2 条）
- 断言：4 套件为字段+比较逻辑式；生产回归有正式枚举 `ProductionRegressionAssertion`（bad_case_registry.py:37-41）仅 3 种：intent/citation_present/ticket_confirmation_required
- Bad Case：`BadCaseRecord`（source∈{eval,production,manual}）+ promote 只返回文本 draft（`build_regression_case_draft` bad_case_registry.py:249-283），**不写回 agent_cases.json**；bad_cases.json 当前 records 为空
- Baseline：`compare_eval_run_snapshots`（eval_platform.py:238-278）已实现但仅被测试调用；/overview 每次重跑本地评测但不落盘、无基线对比
- 前端 EvaluationView：5 指标卡 + 反馈候选表 + 回归评测 + 套件表 + 数据集表 + Bad Case 列表 + 反馈审核 dialog

### 1.2 缺口清单（按深化价值/成本，用户确认范围）
1. **must_ask_for / must_not_reveal 断言未实现**（schema 有字段 intent_evaluation.py:36-37，但 4 个评估器均未校验；prompt-injection 用例的 must_not_reveal 期望形同虚设）
2. **生产回归断言类型仅 3 种且 intent 枚举缺 refund_request**（bad_case_registry.py:37-41 + schemas/evaluation.py:135-140）
3. **Baseline 回归对比未接线**（compare 已实现，/overview 无对比、无变差标记）
4. **Bad Case promote 不写回评测用例**（只返回文本 draft）

### 1.3 目标（用户确认的决策）
- **三缺口一次闭环**：must_* 断言实现 + 回归断言扩类 + Baseline 对比接线
- **顺带做 promote 闭环**：promote 时写回 agent_cases.json
- **前端展示**：EvaluationView 概览区展示基线对比
- 评测套件用 fake/规则依赖，不依赖真实模型服务（已确认 `run_agent_eval_suites` 走规则分类器）

## 2. 架构与数据流

```
用户反馈 → Java ai_response_feedback → 候选 → supervisor promote
    → BadCaseRecord（source=production）→ [新增] 写回 agent_cases.json（AgentEvalCase）
    → 生产回归执行（断言：intent/citation/ticket_confirmation/tool_called/must_ask_for/must_not_reveal）
    → 结果落 production_regression_runs.json

本地评测 run → [新增] 落盘 snapshot（agent_eval_snapshots.json）
    → /overview 与最近基线对比（compare_eval_run_snapshots）→ 前端基线对比卡片（变差标红）
```

## 3. 变更设计

### 3.1 must_ask_for / must_not_reveal 断言实现

**语义**：
- `must_ask_for: list[str]`：Agent 回复中必须包含对指定字段的追问（如 `["order_id"]` 表示必须追问订单号）。判定：回复文本明确询问该字段（字段名或其中文别名）。
- `must_not_reveal: list[str]`：Agent 回复文本不得包含指定敏感内容（如系统提示词片段、密钥、内部配置）。判定：子串/关键词匹配，任一命中即失败。

**实现位置**：
- `app/agents/intent_evaluation.py`（或新建 `app/agents/must_check.py`——跟随现有代码组织，若评估器结构分散则独立模块供 4 套件复用）新增：
  - `check_must_ask_for(reply: str, fields: list[str]) -> list[str]`（返回未追问的字段）
  - `check_must_not_reveal(reply: str, terms: list[str]) -> list[str]`（返回被泄露的 term）
- 4 个评估器（intent/field/route/rag）在生成结果时统一附加这两类检查（在现有评估函数里合并进 AgentEvalResult，跟随现有失败收集结构）
- 失败进入 bad case 分析（`bad_case_analysis.py` 分类），failure_layer 用现有 12 种（如 security/model_output）

**用例**：
- agent_cases.json 现有 prompt-injection 用例的 must_not_reveal 期望真正生效
- 新增/调整：order_query 缺订单号用例加 must_ask_for=["order_id"]（验证追问）

### 3.2 生产回归断言扩类

**`ProductionRegressionAssertion` 扩展**（bad_case_registry.py:37-41）：
```python
ProductionRegressionAssertion = Literal[
    "intent",
    "citation_present",
    "ticket_confirmation_required",
    "tool_called",       # 新增：指定工具被调用
    "must_ask_for",      # 新增：必须追问指定字段
    "must_not_reveal",   # 新增：不得泄露指定内容
]
```

**`ProductionRegressionSpec` 字段扩展**（bad_case_registry.py）：
- `expected_intent` Literal 补 `"refund_request"`
- 新增可选字段：
  - `expected_tool: str | None`（tool_called 用，如 "refund_order"/"query_order"）
  - `must_ask_fields: list[str]`（must_ask_for 用）
  - `must_not_reveal_terms: list[str]`（must_not_reveal 用）

**`schemas/evaluation.py:135-140` 同步** + 前端 EvaluationView 反馈审核 dialog 断言选择（L479-526）加 3 个选项 + 对应条件字段输入。

**回归执行器扩展**（production_regression.py:41-130）：按断言类型分发——intent/citation_present/ticket_confirmation_required 现有；新增 tool_called（Agent 工具调用检测）、must_ask_for、must_not_reveal（复用 3.1 的检查函数）。执行结果结构不变（pass/fail + 详情）。

### 3.3 Baseline 对比接线

**snapshot 落盘**：
- overview 重跑本地评测后，把 `run_agent_eval_suites` 结果写为 snapshot（复用 eval_platform.py 的 `EvalRunSnapshot` 模型）
- 存储：`data/evaluation/agent_eval_snapshots.json`（数组，追加；原子 tmp+replace 写，参考 production_bad_case_registry.py 模式）
- **基线选择**：首次运行无快照 → 本次即基线；之后每次运行与最近一次基线快照对比。前端提供"设为基线"操作（把最近本次标记为基线）——或自动：每次运行后更新基线为本次（简单方案，跟随 YAGNI：**自动取最近一次快照为基线**，不引入手动标记 UI）

**overview 接口**（routers/evaluation.py）：
- `/overview` 增加 `baseline_comparison` 字段：`compare_eval_run_snapshots(baseline, current)` 结果——通过率对比、各套件/断言类型对比、变差用例列表（基线通过但本次失败）
- 变差标记：`regressed: list[case_id]`

**前端 EvaluationView**：
- 概览区新增"基线对比"卡片：本次通过率 vs 基线通过率、变差用例列表（标红）、"设为基线"（若引入手动）——按自动基线方案则只展示对比 + 变差列表
- 复用现有指标卡布局风格

### 3.4 Bad Case promote 闭环

**promote 写回 agent_cases.json**：
- promote 端点（evaluation.py:121-149）在返回 draft 的同时，把 bad case 转为 `AgentEvalCase` 结构（生成 id/inputs{message}/expected{intent 等}/metadata），**追加到 `data/agent_eval/agent_cases.json`**（原子写）
- expected 生成规则（按 failure_layer）：
  - intent 失败 → `expected.intent` = bad case 实际意图（如 refund_request 支持）
  - security/must_not_reveal → `expected.must_not_reveal` = 泄露内容
  - 其他 → 生成基础 expected（intent + 保守断言）
- metadata：`case_type="production_regression"`、`source_bad_case_id`、tags 含 regression

**幂等去重**：
- 写前检查 agent_cases.json 是否已有 `source_bad_case_id` 相同（或同 message）用例，有则跳过
- 新用例 id 生成：`prod_{bad_case_id}_regression` 或 `_slugify`（跟随 build_regression_case_draft 风格）

**测试**：
- promote 端到端：mock bad case → promote → agent_cases.json 出现新用例 → eval suite 可加载新用例
- 去重：重复 promote 不重复写

## 4. 测试与验收

### 4.1 单元测试（Python 基线 1459 passed）
| 模块 | 测试 |
| --- | --- |
| must_* 断言 | test_agent_intent_evaluation.py：must_ask_for 命中/缺失、must_not_reveal 泄露/不泄露、prompt-injection 用例真正失败保护 |
| 回归断言扩类 | test_production_regression.py：tool_called（调用/未调用）、must_ask_for、must_not_reveal、refund_request intent 正/负例 |
| Baseline 对比 | test_eval_platform.py 已有 compare 单测；新增 overview 返回对比 + 变差标记测试 |
| promote 闭环 | 端到端（promote → agent_cases.json → eval suite 可加载）+ 去重测试 |

### 4.2 前端
- EvaluationView 新增基线对比卡片 + 断言选择 3 新选项
- `npm run build` 通过

### 4.3 全量回归
- Python `uv run pytest -q`（1459 + 新增全过）；前端 build；Java 无改动

### 4.4 真实验收（启动 Python 8000 即可，评测不依赖 Java/MCP）
- 场景 1：跑 /overview 两次 → 显示基线对比（本次=基线，无变差）
- 场景 2：构造失败 bad case（prompt-injection 漏防）→ promote → agent_cases.json 增加用例 → 重跑评测该用例失败 → 对比显示变差
- 场景 3：生产回归选 tool_called/must_ask_for/must_not_reveal → 执行 → 结果正确

## 5. 范围外（YAGNI）
- 定时/CI 触发生产回归、release_control 门禁
- 回归历史趋势图（只展示最新对比）
- 反馈候选分页/筛选
- 评测报告导出 API（前端导出）
- RAG 独立评测体系（app/rag/evaluation.py）不动

## 6. 风险与开放点
- **must_not_reveal 的 term 来源**：prompt-injection 用例的 must_not_reveal 具体内容（系统提示词片段）——实现时从现有用例取；若系统提示词含动态部分，用稳定标识符（如 "system prompt" 关键词）
- **snapshot 格式**：EvalRunSnapshot 现有模型字段是否覆盖 run_agent_eval_suites 返回值——实现时按实际结构映射
- **前端"设为基线"**：按自动基线方案不做手动 UI；若用户后续要手动基线再加
- **agent_cases.json 写回**：需保持 schema 严格（schema stage6.agent_eval.v1），写前校验新用例通过 schema
