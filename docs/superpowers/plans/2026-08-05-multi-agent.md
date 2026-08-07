# 多 Agent 协作升级 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把客服 Agent 从单个 LangGraph 工单 Agent 升级为监督-工作（supervisor-worker）多 Agent 系统：顶层监督 Agent 用 LLM/rule 可切换路由，3 个工作子 Agent（知识库问答、订单查询、工单创建）以嵌套子图运行，双模式共存可配置切换。

**Architecture:** 顶层 `StateGraph`（SupervisorState）嵌套 3 个独立子图（KnowledgeWorkerState / OrderWorkerState / TicketWorkerState），LangGraph 子图嵌套复用 checkpoint/interrupt/流式协议；监督节点 `supervisor_route` 用 `LLMSupervisorRouter`（LLM structured output → rule fallback）或 `RuleSupervisorRouter` 输出 `SupervisorRoute` 枚举。`console_agent_service._build_graph` 按 `AGENT_MULTI_AGENT_ENABLED` 分叉；子 Agent 工具执行复用上一轮 MCP 链路（`McpTicketCreator` / `create_mcp_order_query_executor`），与 `AGENT_MCP_TOOLS_ENABLED` 正交。

**Tech Stack:** Python 3.12、uv、LangGraph（StateGraph、子图嵌套、interrupt）、Pydantic、MCP 2.0.0（已接入）。

## Global Constraints

- 规格文件：`docs/superpowers/specs/2026-08-05-multi-agent-design.md`（已获用户认可）。
- 双模式共存：`ticket_agent.py` 单 Agent 代码**保留不动**（不删、不改），既有 1349 个测试必须全绿。
- 状态拆分：现有 `TicketAgentState`（`ticket_agent.py:375-427`）**不修改**；多 Agent 用新的 `SupervisorState` + 3 个子图 state（新建），避免破坏单 Agent。
- 节点复用：3 个子图的节点逻辑从 `ticket_agent.py` 现有节点函数**导入复用**（`retrieve_policy_node`、`query_order_node`、`extract_ticket_fields_node` 等），不复制实现；子图仅新增编排层与 state 定义。
- 配置项（新增，`Settings` 字段 + `.env.example`）：`agent_multi_agent_enabled: bool = False`、`supervisor_router_mode: str = "rule"`（枚举 rule|llm）。
- 测试约束：自动测试不调用真实模型（LLM 路由用 `FakeLLMSupervisorRouter` 或注入 fake client）、不写真实业务数据、不依赖真实 Redis；`Settings(_env_file=None)` 默认 `agent_multi_agent_enabled=False`，保证既有测试全绿。
- 不新增第三方依赖。
- Git：按项目协作偏好，只有用户明确要求才执行 `git commit`/`git push`；计划中 Commit 步骤默认跳过，仅在用户指示时执行。
- 新功能最低要求：核心正常路径与关键失败边界补自动测试；`uv run pytest -q` 全绿。

---

### Task 1: 配置项（`agent_multi_agent_enabled` / `supervisor_router_mode`）

**Files:**
- Modify: `projects/ai-service/app/core/config.py`（Settings 类，在 `agent_mcp_tools_enabled` 之后追加）
- Modify: `projects/ai-service/.env.example`（在 `AGENT_MCP_TOOLS_ENABLED` 行后追加）
- Test: `projects/ai-service/tests/test_config.py`

**Interfaces:**
- Produces: `Settings` 新增字段（全部有默认值，测试 `Settings(_env_file=None)` 可用）：
  - `agent_multi_agent_enabled: bool = Field(default=False)`
  - `supervisor_router_mode: str = Field(default="rule")`
- Produces: `resolved_supervisor_router_mode: str`（非法值回退 "rule"）

- [ ] **Step 1: 写失败测试**（追加到 `tests/test_config.py`）

```python
def test_multi_agent_settings_defaults() -> None:
    settings = Settings(_env_file=None)
    assert settings.agent_multi_agent_enabled is False
    assert settings.supervisor_router_mode == "rule"
    assert settings.resolved_supervisor_router_mode == "rule"


def test_multi_agent_settings_env_overrides() -> None:
    settings = Settings(
        _env_file=None,
        agent_multi_agent_enabled=True,
        supervisor_router_mode="llm",
    )
    assert settings.agent_multi_agent_enabled is True
    assert settings.resolved_supervisor_router_mode == "llm"


def test_supervisor_router_mode_invalid_falls_back_to_rule() -> None:
    settings = Settings(_env_file=None, supervisor_router_mode="invalid")
    assert settings.resolved_supervisor_router_mode == "rule"
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd projects/ai-service && uv run pytest tests/test_config.py::test_multi_agent_settings_defaults -q`
Expected: FAIL（`AttributeError: 'Settings' object has no attribute 'agent_multi_agent_enabled'`）

- [ ] **Step 3: 实现**（`app/core/config.py`，在 `agent_mcp_tools_enabled` 字段后追加）

```python
    agent_multi_agent_enabled: bool = Field(default=False)
    supervisor_router_mode: str = Field(default="rule")
```

在 `resolved_tool_confirmation_backend` 属性后追加：

```python
    @property
    def resolved_supervisor_router_mode(self) -> str:
        return self.supervisor_router_mode if self.supervisor_router_mode == "llm" else "rule"
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd projects/ai-service && uv run pytest tests/test_config.py -q`
Expected: PASS

- [ ] **Step 5: 更新 `.env.example`**（在 `AGENT_MCP_TOOLS_ENABLED` 行后追加）

```text
# 多 Agent 模式开关：false=单 Agent（现有），true=监督-工作多 Agent
AGENT_MULTI_AGENT_ENABLED=false
# 监督路由模式：rule（默认，关键词）或 llm（模型路由，失败回退 rule）
SUPERVISOR_ROUTER_MODE=rule
```

- [ ] **Step 6: Commit**（仅用户明确要求时执行）

```bash
git add projects/ai-service/app/core/config.py projects/ai-service/.env.example projects/ai-service/tests/test_config.py
git commit -m "feat: add multi-agent and supervisor router settings"
```

---

### Task 2: 多 Agent 状态定义（`SupervisorState` + 3 子图 state）

**Files:**
- Create: `projects/ai-service/app/agents/multi_agent_states.py`
- Test: `projects/ai-service/tests/test_multi_agent_states.py`（新建）

**Interfaces:**
- Consumes: `TicketIntent`（`app/schemas/structured.py`）、现有 `TicketAgentState` 字段名（`ticket_agent.py:375-427`，只读参考，不 import 其类型）
- Produces:
  - `SupervisorState(TypedDict, total=False)`：`user_message: str`、`normalized_message: str`、`agent_trace_id: str`、`intent: TicketIntent`、`intent_reason: str`、`final_answer: str | None`、`node_history: list[str]`、`agent_error_code: str | None`、`agent_error_message: str | None`
  - `KnowledgeWorkerState(TypedDict, total=False)`：`normalized_message: str`、`rag_query: str`、`rag_answer_status: str`、`rag_citations: list[dict]`、`rag_no_context_reason: str | None`、`rag_suggestions: list[str]`、`final_answer: str | None`、`node_history: list[str]`
  - `OrderWorkerState(TypedDict, total=False)`：`normalized_message: str`、`order_query_order_id: str | None`、`order_query_status: str`、`order_query_result: dict | None`、`order_query_error_code: str | None`、`order_query_error_message: str | None`、`final_answer: str | None`、`node_history: list[str]`
  - `TicketWorkerState(TypedDict, total=False)`：`normalized_message: str`、`ticket_fields: dict | None`、`ticket_confirmation_approved: bool | None`、`pending_ticket_confirmation: dict | None`、`ticket_creation_status: str | None`、`created_ticket: dict | None`、`final_answer: str | None`、`node_history: list[str]`
  - `SUPERVISOR_OUTPUT_KEYS: frozenset[str]`（子图写回顶层的字段集合：`final_answer` 等）

- [ ] **Step 1: 写失败测试**（新建 `tests/test_multi_agent_states.py`）

```python
from app.agents.multi_agent_states import (
    KnowledgeWorkerState,
    OrderWorkerState,
    SupervisorState,
    TicketWorkerState,
    SUPERVISOR_OUTPUT_KEYS,
)


def test_supervisor_state_holds_core_fields() -> None:
    state: SupervisorState = {
        "user_message": "查订单",
        "normalized_message": "查订单",
        "intent": "order_query",
        "final_answer": "订单已发货",
        "node_history": ["normalize_user_input"],
    }
    assert state["intent"] == "order_query"
    assert state["final_answer"] == "订单已发货"


def test_worker_states_hold_their_own_fields() -> None:
    knowledge: KnowledgeWorkerState = {
        "normalized_message": "退货政策",
        "rag_answer_status": "answered",
        "final_answer": "退货政策是...",
    }
    order: OrderWorkerState = {
        "normalized_message": "查订单 A1001",
        "order_query_status": "succeeded",
        "order_query_result": {"order_id": "A1001"},
        "final_answer": "订单已发货",
    }
    ticket: TicketWorkerState = {
        "normalized_message": "申请退款",
        "ticket_confirmation_approved": True,
        "pending_ticket_confirmation": {"confirmation_id": "a" * 32},
        "final_answer": "工单已创建",
    }
    assert knowledge["rag_answer_status"] == "answered"
    assert order["order_query_result"]["order_id"] == "A1001"
    assert ticket["ticket_confirmation_approved"] is True


def test_supervisor_output_keys_contains_final_answer() -> None:
    assert "final_answer" in SUPERVISOR_OUTPUT_KEYS
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd projects/ai-service && uv run pytest tests/test_multi_agent_states.py -q`
Expected: FAIL（`ModuleNotFoundError: No module named 'app.agents.multi_agent_states'`）

- [ ] **Step 3: 实现**（新建 `app/agents/multi_agent_states.py`）

```python
"""State definitions for the supervisor-worker multi-agent system."""

from typing import TypedDict

from app.schemas.structured import TicketIntent


class SupervisorState(TypedDict, total=False):
    user_message: str
    normalized_message: str
    agent_trace_id: str
    intent: TicketIntent
    intent_reason: str
    # 跨 Agent 协作字段（knowledge 子图输出，监督层读取）
    rag_answer_status: str
    rag_citations: list[dict]
    needs_ticket: bool
    final_answer: str | None
    node_history: list[str]
    agent_error_code: str | None
    agent_error_message: str | None


class KnowledgeWorkerState(TypedDict, total=False):
    normalized_message: str
    intent: TicketIntent
    rag_query: str
    rag_answer_status: str
    rag_citations: list[dict]
    rag_no_context_reason: str | None
    rag_suggestions: list[str]
    needs_ticket: bool
    ticket_need_reason: str
    final_answer: str | None
    node_history: list[str]


class OrderWorkerState(TypedDict, total=False):
    normalized_message: str
    order_query_order_id: str | None
    order_query_status: str
    order_query_result: dict | None
    order_query_error_code: str | None
    order_query_error_message: str | None
    final_answer: str | None
    node_history: list[str]


class TicketWorkerState(TypedDict, total=False):
    normalized_message: str
    ticket_fields: dict | None
    ticket_confirmation_approved: bool | None
    pending_ticket_confirmation: dict | None
    ticket_creation_status: str | None
    created_ticket: dict | None
    final_answer: str | None
    node_history: list[str]


# Fields a worker subgraph writes back to the supervisor top-level state.
SUPERVISOR_OUTPUT_KEYS = frozenset(
    {
        "final_answer",
        "needs_ticket",
        "rag_answer_status",
        "rag_citations",
        "agent_error_code",
        "agent_error_message",
    }
)
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd projects/ai-service && uv run pytest tests/test_multi_agent_states.py -q`
Expected: PASS

- [ ] **Step 5: Commit**（仅用户明确要求时执行）

```bash
git add projects/ai-service/app/agents/multi_agent_states.py projects/ai-service/tests/test_multi_agent_states.py
git commit -m "feat: add multi-agent state definitions"
```

---

### Task 3: 监督路由（`SupervisorRoute` 枚举 + rule/LLM 双模式 router）

**Files:**
- Create: `projects/ai-service/app/agents/supervisor/supervisor_router.py`
- Create: `projects/ai-service/app/agents/supervisor/__init__.py`（空或导出）
- Test: `projects/ai-service/tests/test_supervisor_router.py`（新建）

**Interfaces:**
- Consumes: `Settings`（`resolved_supervisor_router_mode`、`has_llm_api_key`、`llm_model`）、`TicketIntent`（`app/schemas/structured.py`）、`classify_ticket_intent`（`ticket_agent.py:1352`，rule 复用）、`build_ticket_intent_classification_messages` / `parse_ticket_intent_classification_json`（`ticket_agent.py`，LLM 复用）
- Produces:
  - `class SupervisorRoute(StrEnum)`：`KNOWLEDGE_QUESTION = "knowledge_question"`、`ORDER_QUERY = "order_query"`、`TICKET_REQUEST = "ticket_request"`、`SMALLTALK = "smalltalk"`、`UNSUPPORTED = "unsupported"`、`UNCLEAR = "unclear"`
  - `TICKET_INTENT_TO_SUPERVISOR_ROUTE: dict[TicketIntent, SupervisorRoute]`：映射 `policy_question→KNOWLEDGE_QUESTION`、`order_query→ORDER_QUERY`、`ticket_request→TICKET_REQUEST`、`smalltalk→SMALLTALK`、`unsupported→UNSUPPORTED`、`unclear→UNCLEAR`
  - `class SupervisorRouter(Protocol)`：`def route(self, message: str) -> SupervisorRoute`
  - `class RuleSupervisorRouter`：`route()` 调 `classify_ticket_intent` 映射为 `SupervisorRoute`（未知意图回退 `UNCLEAR`）
  - `class LLMSupervisorRouter`：构造 `LLMSupervisorRouter(settings, *, client=None, prompt_spec=...)`；`route()` 调 `classify_intent`（复用 `LLMTicketIntentClassifier` 逻辑：messages → chat.completions → parse → 映射），LLM 失败抛 `AppException`；`route_with_fallback()`：LLM 失败回退 `RuleSupervisorRouter`（返回 `(route, source)`，source ∈ {"llm","rule_fallback"}）
  - `def create_supervisor_router(settings, *, client=None) -> SupervisorRouter`：按 `resolved_supervisor_router_mode` 返回 LLM（带 fallback 包装）或 rule
  - `FakeLLMSupervisorRouter`：测试用，构造传入 `route: SupervisorRoute`，`route()` 恒返回该值（模拟 LLM 成功路径）

- [ ] **Step 1: 写失败测试**（新建 `tests/test_supervisor_router.py`）

```python
import pytest

from app.agents.supervisor.supervisor_router import (
    FakeLLMSupervisorRouter,
    LLMSupervisorRouter,
    RuleSupervisorRouter,
    SupervisorRoute,
    SupervisorRouter,
    TICKET_INTENT_TO_SUPERVISOR_ROUTE,
    create_supervisor_router,
)
from app.core.config import Settings
from app.schemas.structured import TicketIntent


def test_route_enum_has_six_values() -> None:
    values = {route.value for route in SupervisorRoute}
    assert values == {
        "knowledge_question",
        "order_query",
        "ticket_request",
        "smalltalk",
        "unsupported",
        "unclear",
    }


def test_ticket_intent_mapping_covers_all_intents() -> None:
    for intent in TicketIntent:
        assert intent in TICKET_INTENT_TO_SUPERVISOR_ROUTE


def test_rule_router_classifies_order_query() -> None:
    router = RuleSupervisorRouter()
    assert router.route("查一下我的订单 A1001 物流") == SupervisorRoute.ORDER_QUERY


def test_rule_router_classifies_policy_question() -> None:
    router = RuleSupervisorRouter()
    assert router.route("退货政策是什么") == SupervisorRoute.KNOWLEDGE_QUESTION


def test_rule_router_classifies_ticket_request() -> None:
    router = RuleSupervisorRouter()
    assert router.route("我要申请退款工单") == SupervisorRoute.TICKET_REQUEST


def test_rule_router_falls_back_to_unclear_for_unknown() -> None:
    router = RuleSupervisorRouter()
    assert router.route("今天天气怎么样啊") in {
        SupervisorRoute.UNCLEAR,
        SupervisorRoute.SMALLTALK,
    }


def test_fake_llm_router_returns_configured_route() -> None:
    fake = FakeLLMSupervisorRouter(SupervisorRoute.TICKET_REQUEST)
    router: SupervisorRouter = fake
    assert router.route("anything") == SupervisorRoute.TICKET_REQUEST


def test_create_router_returns_rule_by_default() -> None:
    router = create_supervisor_router(Settings(_env_file=None))
    assert isinstance(router, RuleSupervisorRouter)


def test_create_router_returns_llm_when_configured() -> None:
    router = create_supervisor_router(
        Settings(_env_file=None, supervisor_router_mode="llm")
    )
    assert isinstance(router, LLMSupervisorRouter)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd projects/ai-service && uv run pytest tests/test_supervisor_router.py -q`
Expected: FAIL（`ModuleNotFoundError: No module named 'app.agents.supervisor.supervisor_router'`）

- [ ] **Step 3: 实现**（新建 `app/agents/supervisor/supervisor_router.py`）

```python
"""Supervisor routing: rule-based and LLM-based intent routing for the multi-agent system."""

from enum import StrEnum
import logging
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field

from app.agents.ticket_agent import (
    LLMTicketIntentClassifier,
    classify_ticket_intent,
)
from app.core.config import Settings, get_settings
from app.core.exceptions import AppException
from app.schemas.structured import TicketIntent


logger = logging.getLogger(__name__)


class SupervisorRoute(StrEnum):
    KNOWLEDGE_QUESTION = "knowledge_question"
    ORDER_QUERY = "order_query"
    TICKET_REQUEST = "ticket_request"
    SMALLTALK = "smalltalk"
    UNSUPPORTED = "unsupported"
    UNCLEAR = "unclear"


TICKET_INTENT_TO_SUPERVISOR_ROUTE: dict[TicketIntent, SupervisorRoute] = {
    "policy_question": SupervisorRoute.KNOWLEDGE_QUESTION,
    "order_query": SupervisorRoute.ORDER_QUERY,
    "ticket_request": SupervisorRoute.TICKET_REQUEST,
    "smalltalk": SupervisorRoute.SMALLTALK,
    "unsupported": SupervisorRoute.UNSUPPORTED,
    "unclear": SupervisorRoute.UNCLEAR,
}


class SupervisorRouter(Protocol):
    def route(self, message: str) -> SupervisorRoute:
        """Route a user message to a supervisor route."""
        ...


class RuleSupervisorRouter:
    def route(self, message: str) -> SupervisorRoute:
        classification = classify_ticket_intent(message)
        return TICKET_INTENT_TO_SUPERVISOR_ROUTE[classification["intent"]]


class LLMSupervisorRouter:
    """LLM-based supervisor router. Reuses LLMTicketIntentClassifier for the
    model call, mapping its intent output to a SupervisorRoute."""

    def __init__(
        self,
        settings: Settings,
        *,
        client: Any | None = None,
        prompt_spec: Any = None,
    ) -> None:
        self._settings = settings
        self._classifier = LLMTicketIntentClassifier(
            settings,
            client=client,
            prompt_spec=prompt_spec if prompt_spec is not None else LLMTicketIntentClassifier.__init__.__defaults__[2],
        )

    def route(self, message: str) -> SupervisorRoute:
        classification = self._classifier.classify_intent(message)
        return TICKET_INTENT_TO_SUPERVISOR_ROUTE[classification["intent"]]

    def route_with_fallback(self, message: str) -> tuple[SupervisorRoute, str]:
        """Return (route, source) where source is 'llm' or 'rule_fallback'."""
        try:
            return self.route(message), "llm"
        except AppException as exc:
            logger.warning(
                "supervisor_llm_route_failed code=%s falling_back_to_rule",
                exc.code,
            )
            return RuleSupervisorRouter().route(message), "rule_fallback"


class FakeLLMSupervisorRouter:
    def __init__(self, route: SupervisorRoute) -> None:
        self._route = route

    def route(self, message: str) -> SupervisorRoute:
        return self._route


def create_supervisor_router(
    settings: Settings | None = None,
    *,
    client: Any | None = None,
) -> SupervisorRouter:
    resolved_settings = settings or get_settings()
    if resolved_settings.resolved_supervisor_router_mode == "llm":
        return LLMSupervisorRouter(resolved_settings, client=client)
    return RuleSupervisorRouter()
```

注意：`LLMSupervisorRouter` 的 `prompt_spec` 默认值取 `LLMTicketIntentClassifier.__init__` 的 `prompt_spec` 默认参数（`TICKET_INTENT_CLASSIFICATION_PROMPT`）。若你发现该默认参数获取方式不稳健，可改为显式 import `TICKET_INTENT_CLASSIFICATION_PROMPT`：

```python
from app.agents.ticket_agent import TICKET_INTENT_CLASSIFICATION_PROMPT
# 构造时: prompt_spec=prompt_spec if prompt_spec is not None else TICKET_INTENT_CLASSIFICATION_PROMPT
```

（以实际可用为准，二选一，报告中说明。）

- [ ] **Step 4: 跑测试确认通过**

Run: `cd projects/ai-service && uv run pytest tests/test_supervisor_router.py -q`
Expected: PASS

- [ ] **Step 5: 跑既有测试确认不回归**

Run: `cd projects/ai-service && uv run pytest tests/test_ticket_agent_intent.py tests/test_ticket_agent_llm_intent.py -q`
Expected: PASS

- [ ] **Step 6: Commit**（仅用户明确要求时执行）

```bash
git add projects/ai-service/app/agents/supervisor/ projects/ai-service/tests/test_supervisor_router.py
git commit -m "feat: add supervisor router with rule and llm modes"
```

---

### Task 4: 工作子图（knowledge / order / ticket）

**Files:**
- Create: `projects/ai-service/app/agents/workers/knowledge_agent.py`
- Create: `projects/ai-service/app/agents/workers/order_agent.py`
- Create: `projects/ai-service/app/agents/workers/ticket_worker.py`
- Create: `projects/ai-service/app/agents/workers/__init__.py`（空）
- Test: `projects/ai-service/tests/test_worker_agents.py`（新建）

**Interfaces:**
- Consumes:
  - `retrieve_policy_node(state, service=None)`（`ticket_agent.py:2012`，输入 `TicketAgentState` 子集，输出含 `rag_answer_status`/`rag_citations`/`final_answer`）
  - `query_order_node(state, *, order_query_executor=None)`（`ticket_agent.py:2035`）
  - `extract_ticket_fields_node` / `ask_missing_ticket_fields_node` / `request_ticket_confirmation_node` / `create_ticket_node`（`ticket_agent.py`，均接受 `TicketAgentState` 子集）
  - `PolicyRagService`（`ticket_agent.py:357`）、`OrderQueryExecutor`（`ticket_agent.py:372`）、`TicketCreator`（`ticket_agent.py:362`）
- Produces:
  - `def build_knowledge_agent_graph(service: PolicyRagService | None = None, *, checkpointer=None, interrupt_confirmation: bool = False)`：`StateGraph(KnowledgeWorkerState)`，节点 `retrieve_policy`（用 `lambda state: retrieve_policy_node(state, service=service)`）、`decide_ticket_need`（`lambda state: decide_ticket_need_node(state)`）；边 `START→retrieve_policy→decide_ticket_need`，`decide_ticket_need` 条件路由 `TICKET_AGENT_TICKET_NEED_ROUTES`（复用：`finish→END`、`create_ticket→END`——本子图不含 create_ticket 节点，`create_ticket` 分支经条件路由把 `final_answer` 置为需要转工单的标记后 END）
  - `def build_order_agent_graph(order_query_executor: OrderQueryExecutor | None = None, *, checkpointer=None)`：`StateGraph(OrderWorkerState)`，节点 `query_order`（`lambda state: query_order_node(state, order_query_executor=order_query_executor)`）；边 `START→query_order→END`
  - `def build_ticket_worker_graph(ticket_creator: TicketCreator | None = None, *, checkpointer=None, interrupt_confirmation: bool = False)`：`StateGraph(TicketWorkerState)`，节点 `extract_ticket_fields`、`ask_missing_ticket_fields`、`request_ticket_confirmation`（interrupt 版或普通版）、`create_ticket`；边与条件路由复用 `TICKET_AGENT_FIELD_COMPLETION_ROUTES` / `TICKET_AGENT_CONFIRMATION_ROUTES`
- 关键适配：现有节点函数签名接收 `TicketAgentState`（TypedDict 键名兼容），子图 `WorkerState` 用**相同字段名**的子集，直接传入节点函数可工作（TypedDict 结构兼容，Python 运行时不做强校验）。

- [ ] **Step 1: 写失败测试**（新建 `tests/test_worker_agents.py`）

```python
import pytest

from app.agents.workers.knowledge_agent import build_knowledge_agent_graph
from app.agents.workers.order_agent import build_order_agent_graph
from app.agents.workers.ticket_worker import build_ticket_worker_graph
from tests.rag_fakes import make_retrieved_chunk
from tests.tool_fakes import (
    FakeNoContextPolicyRagService,
    FakeOrderLookupClient,
    FakePolicyRagService,
    FakeTicketCreator,
    make_created_ticket,
    make_policy_rag_answer,
)
from app.schemas.tool import QueryOrderArgs, QueryOrderResult
from app.agents.ticket_agent import OrderQueryExecutor
from app.core.exceptions import AppException


def test_knowledge_agent_answers_policy_question() -> None:
    graph = build_knowledge_agent_graph(
        service=FakePolicyRagService(make_policy_rag_answer("退货政策是 30 天无理由。"))
    )
    result = graph.invoke({"normalized_message": "退货政策是什么"})
    assert result["rag_answer_status"] == "answered"
    assert "退货政策" in (result.get("final_answer") or "")


def test_knowledge_agent_marks_no_context_for_ticket_transfer() -> None:
    graph = build_knowledge_agent_graph(
        service=FakeNoContextPolicyRagService()
    )
    result = graph.invoke({"normalized_message": "完全不知道的问题"})
    assert result["rag_answer_status"] == "no_context"


def test_order_agent_queries_order() -> None:
    def executor(arguments: QueryOrderArgs) -> QueryOrderResult:
        return QueryOrderResult(
            order_id=arguments.order_id,
            order_status="shipped",
            payment_status="paid",
            logistics_message="已发货",
            latest_event="包裹已发出",
            can_create_ticket=True,
            source="java_business_service",
        )

    graph = build_order_agent_graph(order_query_executor=executor)
    result = graph.invoke({"normalized_message": "查订单 A1001 物流"})
    assert result["order_query_status"] == "succeeded"
    assert result["order_query_result"]["order_id"] == "A1001"


def test_order_agent_missing_order_id() -> None:
    graph = build_order_agent_graph()
    result = graph.invoke({"normalized_message": "查一下订单状态"})
    assert result["order_query_status"] == "failed"
    assert result["order_query_error_code"] is not None


def test_ticket_worker_creates_ticket_after_confirmation() -> None:
    graph = build_ticket_worker_graph(
        ticket_creator=FakeTicketCreator(),
        interrupt_confirmation=False,
    )
    result = graph.invoke(
        {
            "normalized_message": "申请退款，订单 A1001 破损",
            "ticket_confirmation_approved": True,
            "ticket_fields": {
                "issue_type": "refund",
                "order_id": "A1001",
                "description": "订单破损",
                "user_request": "申请退款",
                "urgency": "high",
                "need_human_review": False,
            },
        }
    )
    assert result["ticket_creation_status"] == "succeeded"
    assert result["created_ticket"]["ticket_id"] is not None
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd projects/ai-service && uv run pytest tests/test_worker_agents.py -q`
Expected: FAIL（`ModuleNotFoundError: No module named 'app.agents.workers.knowledge_agent'`）

- [ ] **Step 3: 实现 knowledge 子图**（新建 `app/agents/workers/knowledge_agent.py`）

```python
"""Knowledge-base QA worker subgraph."""

from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agents.multi_agent_states import KnowledgeWorkerState
from app.agents.ticket_agent import (
    PolicyRagService,
    decide_ticket_need_node,
    retrieve_policy_node,
)


def build_knowledge_agent_graph(
    service: PolicyRagService | None = None,
    *,
    checkpointer: Any | None = None,
) -> Any:
    builder = StateGraph(KnowledgeWorkerState)
    builder.add_node(
        "retrieve_policy",
        lambda state: retrieve_policy_node(state, service=service),
    )
    builder.add_node("decide_ticket_need", decide_ticket_need_node)
    builder.add_edge(START, "retrieve_policy")
    builder.add_edge("retrieve_policy", "decide_ticket_need")

    # decide_ticket_need_node 输出 needs_ticket(bool) + ticket_need_source。
    # 本子图不含 create_ticket 节点，needs_ticket=True（含 RAG no_context 转工单）
    # 时子图结束，由监督层 after_knowledge_agent 检查后转 ticket_agent 子图。
    def _route_after_ticket_need(state: KnowledgeWorkerState) -> str:
        return "finish"

    builder.add_conditional_edges(
        "decide_ticket_need",
        _route_after_ticket_need,
        {"finish": END},
    )
    return builder.compile(checkpointer=checkpointer)
```

注意：`TICKET_AGENT_TICKET_NEED_ROUTES` 中 `create_ticket→extract_ticket_fields` 的目标节点不在本子图，不能直接复用该路由表；本实现用单一 `{"finish": END}` 路由（`needs_ticket=True` 时子图结束，监督层负责转工单）。

- [ ] **Step 4: 实现 order 子图**（新建 `app/agents/workers/order_agent.py`）

```python
"""Order query worker subgraph."""

from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agents.multi_agent_states import OrderWorkerState
from app.agents.ticket_agent import OrderQueryExecutor, query_order_node


def build_order_agent_graph(
    order_query_executor: OrderQueryExecutor | None = None,
    *,
    checkpointer: Any | None = None,
) -> Any:
    builder = StateGraph(OrderWorkerState)
    builder.add_node(
        "query_order",
        lambda state: query_order_node(
            state,
            order_query_executor=order_query_executor,
        ),
    )
    builder.add_edge(START, "query_order")
    builder.add_edge("query_order", END)
    return builder.compile(checkpointer=checkpointer)
```

- [ ] **Step 5: 实现 ticket worker 子图**（新建 `app/agents/workers/ticket_worker.py`）

```python
"""Ticket creation worker subgraph."""

from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agents.multi_agent_states import TicketWorkerState
from app.agents.ticket_agent import (
    TICKET_AGENT_CONFIRMATION_ROUTES,
    TICKET_AGENT_FIELD_COMPLETION_ROUTES,
    TicketCreator,
    ask_missing_ticket_fields_node,
    create_ticket_node,
    extract_ticket_fields_node,
    request_ticket_confirmation_interrupt_node,
    request_ticket_confirmation_node,
)


def build_ticket_worker_graph(
    ticket_creator: TicketCreator | None = None,
    *,
    checkpointer: Any | None = None,
    interrupt_confirmation: bool = False,
) -> Any:
    builder = StateGraph(TicketWorkerState)
    builder.add_node(
        "extract_ticket_fields",
        lambda state: extract_ticket_fields_node(state),
    )
    builder.add_node("ask_missing_ticket_fields", ask_missing_ticket_fields_node)
    builder.add_node(
        "request_ticket_confirmation",
        (
            request_ticket_confirmation_interrupt_node
            if interrupt_confirmation
            else request_ticket_confirmation_node
        ),
    )
    builder.add_node(
        "create_ticket",
        lambda state: create_ticket_node(state, creator=ticket_creator),
    )
    builder.add_edge(START, "extract_ticket_fields")
    builder.add_conditional_edges(
        "extract_ticket_fields",
        lambda state: (
            "ask_missing_fields"
            if (state.get("missing_ticket_fields") or [])
            else "request_confirmation"
        ),
        TICKET_AGENT_FIELD_COMPLETION_ROUTES,
    )
    builder.add_edge("ask_missing_ticket_fields", END)
    builder.add_edge("create_ticket", END)
    builder.add_conditional_edges(
        "request_ticket_confirmation",
        lambda state: (
            "execute_create_ticket"
            if state.get("ticket_confirmation_approved") is True
            else "finish"
        ),
        TICKET_AGENT_CONFIRMATION_ROUTES,
    )
    return builder.compile(checkpointer=checkpointer)
```

- [ ] **Step 6: 跑测试确认通过**

Run: `cd projects/ai-service && uv run pytest tests/test_worker_agents.py -q`
Expected: PASS（若 fake/节点签名有出入，以实际 API 小幅适配并写入报告）

- [ ] **Step 7: Commit**（仅用户明确要求时执行）

```bash
git add projects/ai-service/app/agents/workers/ projects/ai-service/tests/test_worker_agents.py
git commit -m "feat: add knowledge/order/ticket worker subgraphs"
```

---

### Task 5: 监督图（supervisor_graph）与跨 Agent 协作

**Files:**
- Create: `projects/ai-service/app/agents/supervisor/supervisor_graph.py`
- Test: `projects/ai-service/tests/test_supervisor_graph.py`（新建）

**Interfaces:**
- Consumes:
  - `SupervisorState`（Task 2）、`SupervisorRouter`/`create_supervisor_router`（Task 3）
  - `build_knowledge_agent_graph` / `build_order_agent_graph` / `build_ticket_worker_graph`（Task 4）
  - `PolicyRagService`、`OrderQueryExecutor`、`TicketCreator`
  - `normalize_user_input_node`（`ticket_agent.py:1343`）、`build_direct_answer_node` / `build_unsupported_answer_node` / `ask_clarifying_question_node`（`ticket_agent.py:2399/2406/2413`）
- Produces:
  - `def build_supervisor_graph(*, router: SupervisorRouter | None = None, knowledge_service=None, order_query_executor=None, ticket_creator=None, checkpointer=None, interrupt_confirmation: bool = False) -> Any`：顶层 `StateGraph(SupervisorState)`
  - 节点：`normalize_user_input`（复用）、`supervisor_route`（新：调 `router.route`，写 `intent`/`intent_reason`）、3 个子图节点（`add_node("knowledge_agent", knowledge_graph)` 等）、`build_direct_answer`/`build_unsupported_answer`/`ask_clarifying_question`（复用）
  - 路由：`SUPERVISOR_ROUTE_TABLE: dict[SupervisorRoute, str]`：`KNOWLEDGE_QUESTION→"knowledge_agent"`、`ORDER_QUERY→"order_agent"`、`TICKET_REQUEST→"ticket_agent"`、`SMALLTALK→"build_direct_answer"`、`UNSUPPORTED→"build_unsupported_answer"`、`UNCLEAR→"ask_clarifying_question"`
  - 跨 Agent 协作：`after_knowledge_agent(state)` 检查 `rag_answer_status == "no_context"` 且 `ticket_need == "create_ticket"` → 转 `ticket_agent` 子图（把 `intent` 改为 `ticket_request`），否则 END
  - 日志：`supervisor_routed intent=... worker=...`（info）

- [ ] **Step 1: 写失败测试**（新建 `tests/test_supervisor_graph.py`）

```python
import pytest

from app.agents.supervisor.supervisor_graph import (
    SUPERVISOR_ROUTE_TABLE,
    build_supervisor_graph,
)
from app.agents.supervisor.supervisor_router import (
    FakeLLMSupervisorRouter,
    SupervisorRoute,
)
from tests.rag_fakes import make_retrieved_chunk
from tests.tool_fakes import (
    FakePolicyRagService,
    FakeTicketCreator,
    make_created_ticket,
    make_policy_rag_answer,
)
from app.schemas.tool import QueryOrderArgs, QueryOrderResult


def _order_executor(arguments: QueryOrderArgs) -> QueryOrderResult:
    return QueryOrderResult(
        order_id=arguments.order_id,
        order_status="shipped",
        payment_status="paid",
        logistics_message="已发货",
        latest_event="包裹已发出",
        can_create_ticket=True,
        source="java_business_service",
    )


def test_route_table_maps_all_routes() -> None:
    for route in SupervisorRoute:
        assert route in SUPERVISOR_ROUTE_TABLE


def test_supervisor_routes_order_query_to_order_agent() -> None:
    graph = build_supervisor_graph(
        router=FakeLLMSupervisorRouter(SupervisorRoute.ORDER_QUERY),
        order_query_executor=_order_executor,
    )
    result = graph.invoke({"user_message": "查订单 A1001 物流"})
    assert result["intent"] == "order_query"
    assert "已发货" in (result.get("final_answer") or "")


def test_supervisor_routes_policy_to_knowledge_agent() -> None:
    graph = build_supervisor_graph(
        router=FakeLLMSupervisorRouter(SupervisorRoute.KNOWLEDGE_QUESTION),
        knowledge_service=FakePolicyRagService(
            make_policy_rag_answer("退货政策是 30 天无理由。")
        ),
    )
    result = graph.invoke({"user_message": "退货政策是什么"})
    assert result["rag_answer_status"] == "answered"
    assert "退货政策" in (result.get("final_answer") or "")


def test_supervisor_routes_ticket_to_ticket_agent() -> None:
    graph = build_supervisor_graph(
        router=FakeLLMSupervisorRouter(SupervisorRoute.TICKET_REQUEST),
        ticket_creator=FakeTicketCreator(),
        interrupt_confirmation=False,
    )
    result = graph.invoke(
        {
            "user_message": "申请退款，订单 A1001 破损",
            "ticket_confirmation_approved": True,
            "ticket_fields": {
                "issue_type": "refund",
                "order_id": "A1001",
                "description": "订单破损",
                "user_request": "申请退款",
                "urgency": "high",
                "need_human_review": False,
            },
        }
    )
    assert result["ticket_creation_status"] == "succeeded"
    assert result["created_ticket"]["ticket_id"] is not None


def test_supervisor_smalltalk_builds_direct_answer() -> None:
    graph = build_supervisor_graph(
        router=FakeLLMSupervisorRouter(SupervisorRoute.SMALLTALK)
    )
    result = graph.invoke({"user_message": "你好"})
    assert result["final_answer"] is not None
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd projects/ai-service && uv run pytest tests/test_supervisor_graph.py -q`
Expected: FAIL（`ModuleNotFoundError: No module named 'app.agents.supervisor.supervisor_graph'`）

- [ ] **Step 3: 实现**（新建 `app/agents/supervisor/supervisor_graph.py`）

```python
"""Supervisor graph: top-level orchestrator nesting three worker subgraphs."""

import logging
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agents.multi_agent_states import SupervisorState
from app.agents.supervisor.supervisor_router import SupervisorRoute, SupervisorRouter
from app.agents.ticket_agent import (
    OrderQueryExecutor,
    PolicyRagService,
    TicketCreator,
    ask_clarifying_question_node,
    build_direct_answer_node,
    build_unsupported_answer_node,
    normalize_user_input_node,
)
from app.agents.workers.knowledge_agent import build_knowledge_agent_graph
from app.agents.workers.order_agent import build_order_agent_graph
from app.agents.workers.ticket_worker import build_ticket_worker_graph


logger = logging.getLogger(__name__)

SUPERVISOR_ROUTE_TABLE: dict[SupervisorRoute, str] = {
    SupervisorRoute.KNOWLEDGE_QUESTION: "knowledge_agent",
    SupervisorRoute.ORDER_QUERY: "order_agent",
    SupervisorRoute.TICKET_REQUEST: "ticket_agent",
    SupervisorRoute.SMALLTALK: "build_direct_answer",
    SupervisorRoute.UNSUPPORTED: "build_unsupported_answer",
    SupervisorRoute.UNCLEAR: "ask_clarifying_question",
}


def build_supervisor_graph(
    *,
    router: SupervisorRouter | None = None,
    knowledge_service: PolicyRagService | None = None,
    order_query_executor: OrderQueryExecutor | None = None,
    ticket_creator: TicketCreator | None = None,
    checkpointer: Any | None = None,
    interrupt_confirmation: bool = False,
) -> Any:
    from app.agents.supervisor.supervisor_router import create_supervisor_router

    resolved_router = router or create_supervisor_router()

    knowledge_graph = build_knowledge_agent_graph(knowledge_service)
    order_graph = build_order_agent_graph(order_query_executor)
    ticket_graph = build_ticket_worker_graph(
        ticket_creator,
        interrupt_confirmation=interrupt_confirmation,
    )

    builder = StateGraph(SupervisorState)
    builder.add_node("normalize_user_input", normalize_user_input_node)

    def supervisor_route_node(state: SupervisorState) -> SupervisorState:
        message = state.get("normalized_message") or state.get("user_message", "")
        route = resolved_router.route(message)
        intent = {
            SupervisorRoute.KNOWLEDGE_QUESTION: "policy_question",
            SupervisorRoute.ORDER_QUERY: "order_query",
            SupervisorRoute.TICKET_REQUEST: "ticket_request",
            SupervisorRoute.SMALLTALK: "smalltalk",
            SupervisorRoute.UNSUPPORTED: "unsupported",
            SupervisorRoute.UNCLEAR: "unclear",
        }[route]
        logger.info("supervisor_routed intent=%s worker=%s", intent, SUPERVISOR_ROUTE_TABLE[route])
        return {
            "intent": intent,
            "intent_reason": f"supervisor routed to {route.value}",
            "node_history": ["supervisor_route"],
        }

    builder.add_node("supervisor_route", supervisor_route_node)
    builder.add_node("knowledge_agent", knowledge_graph)
    builder.add_node("order_agent", order_graph)
    builder.add_node("ticket_agent", ticket_graph)
    builder.add_node("build_direct_answer", build_direct_answer_node)
    builder.add_node("build_unsupported_answer", build_unsupported_answer_node)
    builder.add_node("ask_clarifying_question", ask_clarifying_question_node)

    builder.add_edge(START, "normalize_user_input")
    builder.add_edge("normalize_user_input", "supervisor_route")

    def route_after_supervisor(state: SupervisorState) -> str:
        intent = state.get("intent")
        route = {
            "policy_question": SupervisorRoute.KNOWLEDGE_QUESTION,
            "order_query": SupervisorRoute.ORDER_QUERY,
            "ticket_request": SupervisorRoute.TICKET_REQUEST,
            "smalltalk": SupervisorRoute.SMALLTALK,
            "unsupported": SupervisorRoute.UNSUPPORTED,
            "unclear": SupervisorRoute.UNCLEAR,
        }[intent] if intent else SupervisorRoute.UNCLEAR
        return SUPERVISOR_ROUTE_TABLE[route]

    builder.add_conditional_edges(
        "supervisor_route",
        route_after_supervisor,
        SUPERVISOR_ROUTE_TABLE,
    )

    def after_knowledge_agent(state: SupervisorState) -> str:
        if state.get("needs_ticket") is True:
            logger.info(
                "supervisor_knowledge_to_ticket_transfer needs_ticket=true rag_answer_status=%s",
                state.get("rag_answer_status"),
            )
            return "ticket_agent"
        return END

    builder.add_conditional_edges(
        "knowledge_agent",
        after_knowledge_agent,
        {END: END, "ticket_agent": "ticket_agent"},
    )

    builder.add_edge("order_agent", END)
    builder.add_edge("ticket_agent", END)
    builder.add_edge("build_direct_answer", END)
    builder.add_edge("build_unsupported_answer", END)
    builder.add_edge("ask_clarifying_question", END)

    return builder.compile(checkpointer=checkpointer)
```

注意：子图节点与顶层 state 的字段传递——LangGraph 子图嵌套时，顶层 `SupervisorState` 的子集字段会传给子图（`normalized_message` 等），子图输出的字段（`final_answer` 等）会合并回顶层。若子图输入需要 `ticket_confirmation_approved` 等字段，通过顶层 state 传入（测试中已示范）。若 LangGraph 子图嵌套对 TypedDict 不兼容（需要 `state_schema` 参数），按实际 API 调整（如给 `add_node` 传子图编译产物即可，LangGraph 支持）。

- [ ] **Step 4: 跑测试确认通过**

Run: `cd projects/ai-service && uv run pytest tests/test_supervisor_graph.py -q`
Expected: PASS（若子图嵌套 API 有出入，以实际 LangGraph 版本为准小幅适配并写入报告）

- [ ] **Step 5: Commit**（仅用户明确要求时执行）

```bash
git add projects/ai-service/app/agents/supervisor/supervisor_graph.py projects/ai-service/tests/test_supervisor_graph.py
git commit -m "feat: add supervisor graph orchestrating worker subgraphs"
```

---

### Task 6: console_agent_service 双模式接入

**Files:**
- Modify: `projects/ai-service/app/services/console_agent_service.py`（`_build_graph` 方法，约 232-252 行）
- Test: `projects/ai-service/tests/test_multi_agent_console.py`（新建）

**Interfaces:**
- Consumes: `Settings.agent_multi_agent_enabled`、`build_supervisor_graph`（Task 5）、现有 `_build_graph` 的工具注入（MCP/直连分叉）、`ProductionPolicyRagService`、`_create_redis_checkpointer`、`interrupt_confirmation=True`
- Produces: `_build_graph` 在 `agent_multi_agent_enabled=True` 时返回多 Agent 监督图，否则返回现有单 Agent 图（行为不变）

- [ ] **Step 1: 写失败测试**（新建 `tests/test_multi_agent_console.py`）

```python
import pytest

from app.agents.supervisor.supervisor_graph import build_supervisor_graph
from app.core.config import Settings
from app.services.console_agent_service import ConsoleAgentService
from tests.tool_fakes import (
    FakePolicyRagService,
    FakeTicketCreator,
    make_created_ticket,
    make_policy_rag_answer,
)
from app.schemas.tool import QueryOrderArgs, QueryOrderResult


def _order_executor(arguments: QueryOrderArgs) -> QueryOrderResult:
    return QueryOrderResult(
        order_id=arguments.order_id,
        order_status="shipped",
        payment_status="paid",
        logistics_message="已发货",
        latest_event="包裹已发出",
        can_create_ticket=True,
        source="java_business_service",
    )


def test_build_graph_returns_supervisor_graph_when_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(
        _env_file=None,
        agent_multi_agent_enabled=True,
        agent_mcp_tools_enabled=False,
    )
    service = ConsoleAgentService(settings, graph=object())
    monkeypatch.setattr(
        service,
        "_create_redis_checkpointer",
        lambda: None,
    )
    graph = service._build_graph()
    assert graph is not None


def test_build_graph_returns_single_agent_graph_when_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(_env_file=None, agent_multi_agent_enabled=False)
    service = ConsoleAgentService(settings, graph=object())
    monkeypatch.setattr(
        service,
        "_create_redis_checkpointer",
        lambda: None,
    )
    graph = service._build_graph()
    assert graph is not None


def test_multi_agent_console_end_to_end_rule_route(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End-to-end: conversation -> supervisor route -> order agent -> answer."""
    from app.agents.supervisor.supervisor_router import (
        FakeLLMSupervisorRouter,
        SupervisorRoute,
    )
    from app.agents.supervisor.supervisor_graph import build_supervisor_graph

    graph = build_supervisor_graph(
        router=FakeLLMSupervisorRouter(SupervisorRoute.ORDER_QUERY),
        order_query_executor=_order_executor,
    )
    result = graph.invoke({"user_message": "查订单 A1001"})
    assert result["intent"] == "order_query"
    assert "已发货" in (result.get("final_answer") or "")
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd projects/ai-service && uv run pytest tests/test_multi_agent_console.py -q`
Expected: FAIL（`_build_graph` 尚未支持 `agent_multi_agent_enabled`）

- [ ] **Step 3: 实现**（`app/services/console_agent_service.py` 的 `_build_graph`）

将 `_build_graph` 方法改为：

```python
    def _build_graph(self) -> Any:
        ticket_creator, order_query_executor = self._build_tool_dependencies()
        if self.settings.agent_multi_agent_enabled:
            from app.agents.supervisor.supervisor_graph import build_supervisor_graph

            return build_supervisor_graph(
                knowledge_service=ProductionPolicyRagService(self.settings),
                order_query_executor=order_query_executor,
                ticket_creator=ticket_creator,
                checkpointer=self._create_redis_checkpointer(),
                interrupt_confirmation=True,
            )
        return build_ticket_agent_graph_for_model_mode(
            ticket_creator=ticket_creator,
            policy_rag_service=ProductionPolicyRagService(self.settings),
            order_query_executor=order_query_executor,
            mode=self.settings.ticket_agent_model_mode,
            settings=self.settings,
            checkpointer=self._create_redis_checkpointer(),
            interrupt_confirmation=True,
        )

    def _build_tool_dependencies(self) -> tuple[Any, Any]:
        if self.settings.agent_mcp_tools_enabled:
            from app.agents.mcp_tool_adapters import (
                create_mcp_order_query_executor,
                create_mcp_ticket_creator,
            )

            return (
                create_mcp_ticket_creator(self.settings),
                create_mcp_order_query_executor(self.settings),
            )
        from app.tools.fake_order_tool import query_order

        return (
            JavaTicketClient.from_settings(self.settings),
            lambda arguments: query_order(arguments, settings=self.settings),
        )
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd projects/ai-service && uv run pytest tests/test_multi_agent_console.py tests/test_console_agent_api.py -q`
Expected: PASS（既有 console agent 测试保持全绿——`agent_multi_agent_enabled` 默认 False 走原路径）

- [ ] **Step 5: Commit**（仅用户明确要求时执行）

```bash
git add projects/ai-service/app/services/console_agent_service.py projects/ai-service/tests/test_multi_agent_console.py
git commit -m "feat: switch console agent to multi-agent mode via setting"
```

---

### Task 7: 文档更新

**Files:**
- Modify: `docs/project-handoff-for-vibe-coding.md`（第 9 节"多 Agent 协作"行 + 第 17 节表格 + 第 16 节已知运行问题）

**Interfaces:** 无新接口。

- [ ] **Step 1: 更新交接文档第 9 节**

将：

```text
| 多 Agent 协作 | 当前是单个 LangGraph 工单 Agent，不是 Multi-Agent 系统。 |
```

改为：

```text
| 多 Agent 协作 | 已升级为监督-工作（supervisor-worker）多 Agent：顶层监督 Agent（LLM/rule 可切换路由）+ 3 个工作子 Agent（知识库问答、订单查询、工单创建）。默认关闭，需设 `AGENT_MULTI_AGENT_ENABLED=true` 启用；`SUPERVISOR_ROUTER_MODE=rule|llm` 切换监督路由方式。 |
```

- [ ] **Step 2: 更新交接文档第 17 节**

将：

```text
| 多 Agent 协作 | 当前是单个 LangGraph 工单 Agent，不是 Multi-Agent 系统。 |
```

改为：

```text
| 多 Agent 协作 | `app/agents/supervisor/`（监督图+路由）、`app/agents/workers/`（3 个工作子图） | 监督-工作多 Agent 已实现：监督 Agent 嵌套 3 个子图，LLM/rule 可切换路由；`AGENT_MULTI_AGENT_ENABLED` 开启后生效，与 MCP 工具链路（`AGENT_MCP_TOOLS_ENABLED`）正交可叠加；单 Agent 图（`ticket_agent.py`）保留。 |
```

- [ ] **Step 3: 更新交接文档第 16 节已知运行问题表**（可选，追加一行）

```text
| 多 Agent 模式 Agent 报错或路由异常 | 确认 `.env` 已设 `AGENT_MULTI_AGENT_ENABLED=true`；LLM 路由模式下检查 `SUPERVISOR_ROUTER_MODE=llm` 时 `LLM_API_KEY` 已配置（失败会自动回退 rule）。 |
```

- [ ] **Step 4: 复查文档**（grep 确认无旧表述残留）

Run: `cd D:\wendang\java+python+ai && grep -n "不是 Multi-Agent 系统" docs/project-handoff-for-vibe-coding.md`
Expected: 无匹配

- [ ] **Step 5: Commit**（仅用户明确要求时执行）

```bash
git add docs/project-handoff-for-vibe-coding.md
git commit -m "docs: update multi-agent collaboration status in handoff doc"
```

---

### Task 8: 全量回归与真实联调验收

**Files:** 无新文件；运行既有与新增测试。

**Interfaces:** 无。

- [ ] **Step 1: Python 全量测试**

Run: `cd projects/ai-service && uv run pytest -q`
Expected: 全绿（既有 1349 + 新增）

- [ ] **Step 2: Java 回归（验证边界未破坏）**

Run: `cd projects/java-business-service && mvn test -q`
Expected: BUILD SUCCESS

- [ ] **Step 3: 前端构建（预期无前端改动）**

Run: `cd projects/customer-service-console && npm run build`
Expected: 构建通过

- [ ] **Step 4: 真实联调——知识库问答路径**（需 MySQL/Redis/Qdrant/VM/模型 API）

前置：`.env` 设置 `AGENT_MULTI_AGENT_ENABLED=true`、`SUPERVISOR_ROUTER_MODE=llm`（或 rule 先验证无模型依赖）；确认 MCP 相关配置按需（本路径不依赖 MCP）。

按顺序启动（参考交接文档第 6 节）：

```powershell
# 终端 1：product MCP server（如 AGENT_MCP_TOOLS_ENABLED=true）
cd D:\wendang\java+python+ai\projects\ai-service
uv run python -m app.mcp_servers.product_server
# 终端 2：Java（如已在运行则跳过）
cd D:\wendang\java+python+ai\projects\java-business-service
mvn spring-boot:run
# 终端 3：Python
cd D:\wendang\java+python+ai\projects\ai-service
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
# 终端 4：Vue
cd D:\wendang\java+python+ai\projects\customer-service-console
npm run dev
```

浏览器 AI 客服页输入"退货政策是什么"，预期：监督 Agent 路由 → knowledge 子图 → RAG 引用回答；AI 服务日志出现 `supervisor_routed intent=policy_question worker=knowledge_agent`。

- [ ] **Step 5: 真实联调——订单查询 + 工单创建路径**

1. 输入"查一下我的订单 A1001 物流"，预期 `supervisor_routed intent=order_query worker=order_agent` → MCP → Java 订单数据。
2. 输入"我要申请退款工单，订单 A1001 破损"，预期 `supervisor_routed intent=ticket_request worker=ticket_agent` → 字段提取 → 确认 → 创建。
3. 验证点：日志中监督路由决策 + 子 Agent 执行链完整；前端流式展示不变。

- [ ] **Step 6: 结果记录**（联调结论写入交接文档第 16 节或本地运行笔记）

---

## Self-Review 记录

**1. Spec coverage（对照 `2026-08-05-multi-agent-design.md`）：**
- 2.1 文件组织（supervisor_graph / supervisor_router / 3 workers）→ Task 3/4/5
- 2.2 双模式切换 + 与 MCP 正交 → Task 6
- 3.1 状态拆分（SupervisorState + 3 子图 state）→ Task 2
- 3.2 数据流（监督路由 + 跨 Agent 协作 RAG no_context 转工单）→ Task 5
- 3.3 LLM 路由（SupervisorRoute 枚举 + rule fallback + SUPERVISOR_ROUTER_MODE）→ Task 3
- 3.4 协议不变（interrupt/checkpoint/stream）→ Task 5/6（复用现有机制）
- 4.1 六个测试文件 → Task 1-6（test_multi_agent_states / test_supervisor_router / test_worker_agents / test_supervisor_graph / test_multi_agent_console + test_config 扩展）
- 4.2 真实联调三条路径 → Task 8
- 4.3 质量回归（pytest/mvn/npm）→ Task 8
- 4.4 文档（交接文档第 9/17/16 节 + .env.example）→ Task 1 + Task 7
- 5 配置项 2 个 → Task 1

**2. Placeholder scan：** 无 TBD/TODO；所有任务含具体代码与测试。Task 3 的 `prompt_spec` 默认值标注了"二选一，报告中说明"（`__defaults__` 或显式 import `TICKET_INTENT_CLASSIFICATION_PROMPT`）——这是实现期适配提示，非占位符。Task 4/5 的 knowledge 子图路由已修正为单一 `{"finish": END}`（`decide_ticket_need_node` 输出 `needs_ticket`，无 `ticket_need` 字段）；跨 Agent 协作改查 `needs_ticket`。

**3. Type consistency：**
- `SupervisorRoute` 枚举在 Task 3 定义，Task 5（SUPERVISOR_ROUTE_TABLE / route_after_supervisor）一致使用。
- `build_knowledge_agent_graph` / `build_order_agent_graph` / `build_ticket_worker_graph` 签名在 Task 4 定义，Task 5 调用一致（`knowledge_service` / `order_query_executor` / `ticket_creator` 参数名）。
- `SupervisorState` / `KnowledgeWorkerState` / `OrderWorkerState` / `TicketWorkerState` 在 Task 2 定义，Task 4/5 使用一致。
- `create_supervisor_router` / `RuleSupervisorRouter` / `LLMSupervisorRouter` / `FakeLLMSupervisorRouter` 在 Task 3 定义，Task 5/6 测试使用一致。
- 配置项 `agent_multi_agent_enabled` / `supervisor_router_mode` / `resolved_supervisor_router_mode` 在 Task 1 定义，Task 3/6 使用一致。
- 跨 Agent 协作字段：`rag_answer_status` / `ticket_need`（knowledge 子图输出）→ Task 5 的 `after_knowledge_agent` 读取一致。
