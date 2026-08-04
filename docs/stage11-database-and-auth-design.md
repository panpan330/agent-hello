# 阶段 11 数据库与本地认证设计

## 1. 当前定位

阶段 11 第 5 节开始把 `java-business-service` 从“AI Agent 可调用的 Java 业务服务”继续推进成“完整项目里的真实 Java 业务后端”。

本节先补数据底座和最小 public API，不引入生产级认证框架。当前登录令牌是本地开发令牌，后续需要替换成 Spring Security + JWT / Session / 网关鉴权中的一种。

## 2. 新增核心表

| 表 | 职责 |
| --- | --- |
| `app_users` | 系统用户。为了避免和数据库保留字冲突，没有直接命名为 `users`。 |
| `app_roles` | 角色字典，目前包含 `customer`、`agent`、`supervisor`、`admin`。 |
| `app_user_roles` | 用户和角色的多对多关系。 |
| `knowledge_documents` | 知识库文档元数据，后续会和 RAG 入库、权限过滤、文档管理页面对齐。 |
| `ai_conversations` | AI 会话主表，预留用户和 Agent 对话持久化。 |
| `ai_messages` | AI 消息明细表，预留会话消息、trace_id 和审计。 |

原有表继续保留：

| 表 | 职责 |
| --- | --- |
| `orders` | 订单业务数据。 |
| `tickets` | 工单业务数据。 |
| `ticket_events` | 工单事件流水和审计。 |

## 3. 当前 public API

| 接口 | 用途 |
| --- | --- |
| `POST /api/auth/login` | 本地开发登录，返回用户信息和本地开发 token。 |
| `GET /api/auth/me` | 根据 `Authorization: Bearer <token>` 返回当前用户。 |
| `GET /api/knowledge-documents` | 根据当前用户角色返回可见知识库文档。 |
| `GET /api/orders` | 根据当前用户角色返回可见订单列表。 |
| `GET /api/tickets` | 根据当前用户角色返回可见工单列表。 |

所有接口仍使用统一响应：

```json
{
  "success": true,
  "code": "OK",
  "message": "OK",
  "data": {},
  "trace_id": "..."
}
```

## 4. 本地开发认证边界

当前 token 形状：

```text
local-dev-token:<tenant_id>:<user_id>
```

它只解决本地项目联调问题，不具备生产安全性：

- 没有签名。
- 没有过期时间。
- 没有刷新机制。
- 没有密码加密存储。
- 没有登录失败次数限制。

后续真实项目增强时，应替换为：

- 密码用 BCrypt 等方式存储。
- token 使用 JWT 或服务端 session。
- 登录、登出、刷新、权限校验统一收口。
- 管理端操作继续保留后端权限兜底，不能只依赖前端菜单隐藏。

## 5. 当前权限规则

知识库文档使用 `permission_group` 做最小权限过滤：

| 角色 | 可见 permission_group |
| --- | --- |
| `customer` | `public`、`customer` |
| `agent` | `public`、`customer_service` |
| `supervisor` | `public`、`customer_service` |
| `admin` | 当前租户全部文档 |

这个设计后续可以直接扩展到 RAG 检索过滤：前端看得到哪些文档，RAG 检索也必须只能检索同一权限范围内的文档。

订单和工单列表使用同一类规则：

| 角色 | 可见范围 |
| --- | --- |
| `customer` | 只看自己的订单和自己提交的工单。 |
| `agent` | 查看当前租户下的订单和工单队列。 |
| `supervisor` | 查看当前租户下的订单和工单队列。 |
| `admin` | 查看当前租户下的订单和工单队列。 |

## 6. 本节已验证

```text
mvn test
Tests run: 29, Failures: 0, Errors: 0, Skipped: 0
```

阶段 11 第 6 节补充验证：

```text
mvn test
Tests run: 33, Failures: 0, Errors: 0, Skipped: 0

npm run build
vue-tsc -b && vite build 通过
```
