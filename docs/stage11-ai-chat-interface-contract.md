# 阶段 11 AI 对话接口契约

## 1. 当前入口

前端 AI 客服页调用：

```text
POST /api/ai/chat
```

这个接口位于 `projects/ai-service`，当前底层复用已有 `tool_chat` 链路。这样前端不直接依赖历史学习路由 `/tool-chat`，后续如果切换成 LangGraph Agent、SSE 流式输出或更完整的 RAG + Tool Calling 链路，可以优先保持前端契约不变。

## 2. 请求格式

```json
{
  "message": "A1001 物流一直没更新，帮我看看应该怎么处理",
  "conversation_id": "conv-ui-001",
  "history": [
    {
      "role": "user",
      "content": "我的订单有问题"
    },
    {
      "role": "assistant",
      "content": "请提供订单号。"
    }
  ]
}
```

说明：

- `message`：当前用户本次发送的消息。
- `conversation_id`：前端会话 id，可选；不传时后端会生成本地会话 id。
- `history`：历史消息，只允许 `user` 和 `assistant`，不允许前端传 `system`。

## 3. 响应格式

```json
{
  "reply": "订单 A1001 已发货，预计 2 天内送达。",
  "conversation_id": "conv-ui-001",
  "trace_id": "trace-console-ai-chat",
  "mode": "tool_chat"
}
```

说明：

- `reply`：返回给前端展示的最终回答。
- `conversation_id`：本轮对话归属的会话 id。
- `trace_id`：排查前端、Python、Java 调用链问题时使用。
- `mode`：当前后端使用的 AI 路由，当前为 `tool_chat`。

## 4. 当前边界

当前已具备：

- 前端真实调用 Python AI 服务。
- Python 对用户输入做 Prompt Injection 基础拦截。
- Python 对模型输出做敏感信息脱敏。
- 自动测试使用 fake service，不真实调用大模型。

当前暂未完成：

- SSE 流式输出接入前端。
- 前端会话持久化。
- LangGraph Agent 作为最终统一入口。
- 前端 token 在 Python 侧做强鉴权。

## 5. 验证

```text
uv run pytest tests/test_chat_api.py tests/test_chat_schema.py -q
64 passed

npm run build
vue-tsc -b && vite build 通过
```
