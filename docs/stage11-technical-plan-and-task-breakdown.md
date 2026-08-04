# 阶段 11：技术方案与任务拆分

## 1. 文档目的

上一节已经确定了阶段 11 的项目范围和真实化标准：

```text
docs/stage11-product-scope-and-realization-standards.md
```

这一节继续回答更具体的问题：

- 项目最终由哪些服务组成。
- 每个服务负责什么。
- 代码应该放在哪些目录。
- 前端、Java、Python、MySQL、Redis、Qdrant、真实模型按什么顺序接入。
- 哪些任务应该先做，哪些任务不能提前做。
- 每个阶段需要用户准备什么真实资源。
- 每个小阶段怎么验收。

这个文档会作为阶段 11 的实施路线。

## 2. 总体技术架构

阶段 11 的目标架构：

```text
Browser Frontend
  |
  |-- calls Java public APIs
  |       |
  |       |-- MySQL
  |       |-- Redis
  |
  |-- calls Python AI public APIs
          |
          |-- LLM API
          |-- Embedding API
          |-- Rerank API
          |-- Qdrant
          |-- Java internal APIs
                    |
                    |-- MySQL
                    |-- Redis
```

更具体地说：

```text
projects/customer-service-console      前端项目
projects/java-business-service         Java Spring Boot 业务服务
projects/ai-service                    Python FastAPI AI 服务
MySQL                                  业务数据库
Redis                                  缓存、幂等、限流、会话辅助
Qdrant                                 向量数据库
LLM / embedding / rerank provider      真实模型服务
```

阶段 11 不把所有东西塞进一个服务。

原因是边界要清楚：

- Java 管传统业务事实。
- Python 管 AI 能力。
- 前端管交互体验。
- MySQL 管结构化业务数据。
- Redis 管短期状态和高频访问。
- Qdrant 管语义检索向量。
- 模型服务负责生成、向量化、重排。

## 3. 服务职责拆分

### 3.1 前端服务

建议目录：

```text
projects/customer-service-console
```

前端职责：

- 登录页。
- 工作台布局。
- 客户 AI 对话页。
- 我的订单页。
- 我的工单页。
- 客服工单工作台。
- 工单详情页。
- 知识库管理页。
- AI 评估 / bad case 页面。
- 调用 Java API 和 Python AI API。

前端不负责：

- 保存 API Key。
- 直接连接 MySQL。
- 直接连接 Qdrant。
- 判断订单归属的最终权限。
- 自己构造模型 tool call。

固定技术选型：

```text
Vue3 + TypeScript + Vite + Element Plus
Vue Router + Pinia + Axios
```

理由：

- 你对 Vue3 体系更熟悉，后续学习和开发效率更高。
- Element Plus 很适合后台工作台，表格、表单、弹窗、菜单、分页、Tabs、Drawer 等组件现成。
- Vite 本地启动快，项目结构清楚，适合阶段 11 快速搭建真实前端。
- TypeScript 能把用户、订单、工单、AI 消息、接口响应这些类型管理清楚。
- Vue Router 负责页面路由，Pinia 负责登录用户、权限和必要全局状态，Axios 负责 API 调用封装。

UI 风格：

```text
工作台型，不做营销首页。
```

也就是：

- 左侧导航。
- 顶部用户信息。
- 中间业务内容。
- 表格、详情、表单、对话窗口。
- 简洁清晰，不做花哨动效。

### 3.2 Java 业务服务

已有目录：

```text
projects/java-business-service
```

Java 职责：

- 用户。
- 角色。
- 登录。
- 订单。
- 工单。
- 工单事件。
- 工单分配。
- 知识库文档元信息。
- 权限校验。
- MySQL 持久化。
- Redis 缓存、幂等、限流。
- 面向前端的 public API。
- 面向 Python AI 服务的 internal API。

Java 是业务事实来源。

这句话非常关键：

```text
订单和工单是否存在、归谁、状态是什么、能不能操作，以 Java + MySQL 为准。
```

Python AI 服务不能绕过 Java 直接写业务库。

### 3.3 Python AI 服务

已有目录：

```text
projects/ai-service
```

Python 职责：

- 普通 AI 对话。
- RAG 问答。
- Tool Calling。
- Agent 编排。
- 真实 LLM 调用。
- 真实 embedding。
- 真实 rerank。
- Qdrant 检索。
- 引用来源整理。
- Prompt Injection 防护。
- AI 输出脱敏。
- 调 Java internal API。
- AI 评估和 bad case。

Python 是 AI 能力编排层。

它可以理解用户意图、组织上下文、调用模型、调用工具，但不能成为业务数据的最终裁判。

### 3.4 MySQL

MySQL 职责：

- 保存结构化业务数据。
- 保证订单、工单、用户、权限、知识库文档元信息可查询、可更新、可事务处理。

推荐优先补齐的表：

- `users`
- `roles`
- `user_roles`
- `orders`
- `order_items`
- `tickets`
- `ticket_events`
- `ticket_assignments`
- `knowledge_documents`
- `ai_conversations`
- `ai_messages`

MySQL 不负责语义检索。

### 3.5 Redis

Redis 职责：

- 登录会话或 token 辅助状态。
- 工单创建幂等。
- 订单详情缓存。
- 接口限流。
- AI 请求短期状态。

Redis 不负责长期业务事实。

也就是说：

```text
Redis 可以丢，但 MySQL 不能丢。
```

### 3.6 Qdrant

Qdrant 职责：

- 保存文档 chunk 的向量。
- 根据 query vector 检索相关 chunks。
- 支持 metadata filter。

Qdrant 不负责：

- 保存订单。
- 保存工单。
- 保存用户权限。
- 作为业务数据库。

Qdrant 只解决语义检索问题。

### 3.7 真实模型服务

阶段 11 要用真实：

- LLM。
- embedding。
- rerank。

模型职责：

- LLM：理解问题、生成回答、总结工具结果、辅助字段提取。
- embedding：把文档和问题变成向量。
- rerank：对召回文档重新排序，提高上下文质量。

模型不负责：

- 权限判断。
- 业务数据写入。
- 幂等控制。
- 密钥保存。
- 最终业务状态裁决。

## 4. API 边界设计

阶段 11 最关键的边界是：

```text
前端 API
Python AI API
Java public API
Java internal API
```

### 4.1 前端调用 Java public API

适合放在 Java public API 的能力：

- 登录。
- 获取当前用户。
- 查询我的订单。
- 查询我的工单。
- 客服查询工单工作台。
- 客服更新工单状态。
- 管理知识库文档元信息。

示例：

```text
POST /api/auth/login
GET  /api/me
GET  /api/orders
GET  /api/orders/{orderNo}
GET  /api/tickets
POST /api/tickets
GET  /api/tickets/{ticketNo}
PATCH /api/tickets/{ticketNo}/status
GET  /api/knowledge-documents
```

### 4.2 前端调用 Python AI API

适合放在 Python AI API 的能力：

- AI 对话。
- RAG 问答。
- AI 查询订单入口。
- AI 创建工单入口。
- 知识库入库触发。
- AI 评估摘要。

示例：

```text
POST /api/ai/chat
POST /api/ai/chat/stream
POST /api/ai/rag/ask
POST /api/ai/agent/ticket
POST /api/ai/knowledge/ingest
GET  /api/ai/evaluation/runs
GET  /api/ai/bad-cases
```

具体路由是否带 `/api/ai` 前缀，可以后续按现有 `ai-service` 结构调整。

### 4.3 Python 调 Java internal API

Python 调 Java 的接口必须是 internal API。

原因：

- 调用方是受信任服务。
- 需要 internal token。
- 需要传递真实用户身份。
- 返回字段要白名单。
- 错误码要稳定。

示例：

```text
GET  /internal/orders/{orderNo}
POST /internal/tickets
GET  /internal/tickets/{ticketNo}
```

Header 必须包含：

```text
X-Trace-Id
X-Caller
X-User-Id
X-Tenant-Id
X-Internal-Token
Idempotency-Key      写操作需要
```

## 5. 数据流顺序

### 5.1 普通业务数据流

```text
前端
-> Java public API
-> Java Service
-> MyBatis Mapper
-> MySQL / Redis
-> Java 返回 DTO
-> 前端展示
```

### 5.2 AI 知识问答数据流

```text
前端
-> Python AI API
-> 安全检查
-> query rewrite / route
-> embedding
-> Qdrant search
-> rerank
-> context build
-> LLM answer
-> citation check
-> 前端展示答案和引用
```

### 5.3 AI 工具调用数据流

```text
前端
-> Python AI API
-> LLM 判断是否需要工具
-> Python 校验工具名和参数
-> Python 调 Java internal API
-> Java 校验权限和业务规则
-> Java 查/写 MySQL
-> Java 返回白名单结果
-> Python 把工具结果交给模型总结
-> 前端展示用户可读答案
```

### 5.4 工单创建确认数据流

```text
前端输入问题
-> Python Agent 提取工单字段
-> 字段不足则追问
-> 字段完整则生成草稿
-> 前端展示确认
-> 用户点击确认
-> Python 调 Java 创建工单
-> Java 幂等写入 MySQL
-> 前端展示工单编号和状态
```

## 6. 实施顺序

阶段 11 不建议一上来就接真实模型和向量库。

更稳的顺序是：

```text
1. 先定架构和任务拆分。
2. 建前端骨架。
3. 打通登录和角色。
4. 补 Java 业务数据模型。
5. 做订单和工单页面。
6. 整理 Python AI API。
7. 接知识库管理和真实入库。
8. 接真实模型链路。
9. 做端到端联调。
10. 做客服工作台。
11. 做评估和 bad case 展示。
12. 整理运行部署和演示。
```

理由：

- 前端骨架先做，后续功能才有展示入口。
- 登录和角色先做，后续权限边界才不乱。
- Java 业务模型先补齐，AI 工具调用才有真实业务来源。
- Python AI API 对齐前端之后，再接真实模型更稳。
- 真实模型和 Qdrant 放在业务骨架之后，避免一开始就被外部依赖拖慢。

## 7. 阶段 11 任务拆分

### 7.1 第 1 组：项目蓝图

包含：

- 第 1 节：项目产品范围与真实化标准。
- 第 2 节：技术方案与任务拆分。

目标：

- 固定项目边界。
- 固定技术路线。
- 固定实施顺序。
- 明确资源准备点。

当前状态：

```text
第 1 节已完成。
第 2 节正在完成。
```

### 7.2 第 2 组：前端与基础身份

包含：

- 第 3 节：前端技术选型与项目骨架。
- 第 4 节：登录与用户角色最小闭环。

目标：

- 创建真实前端项目。
- 建立工作台布局。
- 建立 API client。
- 支持登录。
- 支持当前用户。
- 支持角色菜单。

需要准备：

```text
Node.js
npm / pnpm
```

开始第 3 节前，我会先检查本机 Node.js 环境。

### 7.3 第 3 组：Java 业务底座补全

包含：

- 第 5 节：Java 业务数据模型补全（已完成：用户/角色/知识库/AI 会话表，本地登录 API，知识库文档列表 API）。
- 第 6 节：前端订单与工单基础页面（已完成：Java public 订单/工单列表 API，前端登录接 Java，本地订单/工单页面接真实接口）。
- 第 7 节：Python AI 对话接口真实化整理（已完成：新增 `/api/ai/chat` 前端稳定入口，前端 AI 客服页接 Python AI 服务）。

目标：

- 补齐用户、角色、订单、工单、工单事件、知识库文档表。
- 补齐 Java public API。
- 让前端能展示订单和工单。

需要准备：

```text
MySQL
Redis
Java business service
```

你的环境里已经有 MySQL / Redis 使用经验。到这组开始时，我会提醒你是否需要启动 VMware Ubuntu 或 Windows MySQL。

### 7.4 第 4 组：AI API 与 RAG 真实化

包含：

- 第 7 节：Python AI 对话接口真实化整理（已完成：新增 `/api/ai/chat` 前端稳定入口，前端 AI 客服页接 Python AI 服务）。
- 第 8 节：知识库管理与真实入库（已完成：新增 Python 知识库状态/入库接口，前端知识库页接 Java 文档列表与 Python 入库状态，Fake embedding 已真实写入 Qdrant）。
- 第 9 节：真实 LLM + embedding + rerank 链路验收（已完成：新增 `/api/ai/rag/ask`，真实 `text-embedding-v4 -> Qdrant -> qwen3-rerank -> qwen3.7-plus` 链路验收通过）。

目标：

- 整理前端要调用的 AI API。
- 让知识文档能真实入库。
- 使用真实 embedding 写入 Qdrant。
- 使用真实 rerank 提升检索质量。
- 使用真实 LLM 回答问题。

需要准备：

```text
Qdrant
LLM API Key
Embedding API Key
Rerank API Key
```

你之前已经能在 VMware Ubuntu Docker 中启动 Qdrant。第 8 节已完成 Qdrant 连通与 Fake embedding 真实入库；第 9 节如果继续做真实 embedding/rerank/LLM 链路，仍需要打开虚拟机中的 Qdrant。

### 7.5 第 5 组：端到端业务闭环

包含：

- 第 10 节：AI 查询订单和创建工单端到端联调。
- 第 11 节：客服工单工作台。

目标：

- 用户在前端发起 AI 对话。
- Python 使用真实模型判断工具调用。
- Python 调 Java 查询订单或创建工单。
- Java 读写 MySQL / Redis。

第 10 节已完成的收口：

- Python 订单查询工具已从旧 mock 路径切到 Java business-service 的 `GET /internal/orders/{order_id}`。
- Python 创建工单执行器已从旧 mock 路径切到 Java business-service 的 `POST /internal/tickets`。
- Python 调 Java 时会带 `X-Caller`、`X-User-Id`、`X-Tenant-Id`、`X-Internal-Token`、`X-Trace-Id` 和 `Idempotency-Key`。
- Python 客户端会解包 Java 统一响应 `ApiResponse.data`，再做 Pydantic 白名单校验。
- Java 默认本地端口统一为 `18004`，本地 MySQL root 默认密码统一为 `root`，仍可通过环境变量覆盖。
- 已用真实 Windows MySQL、VMware Redis、Java service 完成订单查询和创建工单 smoke。
- 前端展示结果。
- 客服能处理工单。

验收重点：

```text
前端 -> Python AI -> Java -> MySQL/Redis -> Python -> 前端
```

这条链路必须跑通。

### 7.6 第 6 组：质量与运营展示

包含：

- 第 12 节：AI 评估与 bad case 页面。
- 第 13 节：生产化配置和运行说明。

目标：

- 让评估和坏例不只停留在代码里，也能在页面或文档中展示。
- 整理完整本地启动方式。
- 明确环境变量和服务依赖。

### 7.7 第 7 组：部署和作品化

包含：

- 第 14 节：Docker Compose 本地部署。
- 第 15 节：演示脚本和简历材料。
- 第 16 节：阶段 11 总验收和补洞。

目标：

- 尽量一键启动核心服务。
- 做出 5-10 分钟演示路径。
- 整理截图、简历 bullet、面试表达。
- 按完整项目标准查漏补缺。

## 8. 真实资源接入时间表

| 资源 | 不急着用的原因 | 预计接入时机 |
| --- | --- | --- |
| Node.js | 第 1-2 节是文档设计 | 第 3 节 |
| MySQL | 先确定方案和前端骨架 | 第 5 节 |
| Redis | 登录、幂等、限流时才真正需要 | 第 4-5 节 |
| Qdrant | RAG 入库前不需要启动 | 第 8 节 |
| LLM API Key | 前端和业务底座先行 | 第 7 或第 9 节 |
| Embedding API Key | 知识库真实入库时才需要 | 第 8 节 |
| Rerank API Key | 检索候选需要重排时才需要 | 第 9 节 |
| Docker Compose | 单服务联调稳定后再整合 | 第 14 节 |

原则：

```text
不提前注册一堆暂时用不上的东西。
需要什么真实资源，就在对应小节开始前明确告诉用户准备什么。
```

## 9. 代码目录建议

当前仓库根目录：

```text
D:/wendang/java+python+ai
```

建议最终项目目录：

```text
projects/
  ai-service/
  java-business-service/
  customer-service-console/
docs/
  stage11-product-scope-and-realization-standards.md
  stage11-technical-plan-and-task-breakdown.md
  stage11-api-contract.md
  stage11-database-design.md
  stage11-local-runbook.md
  stage11-demo-script.md
notes/
  stage11-*.md
```

说明：

- `projects/ai-service` 保留 Python AI 服务。
- `projects/java-business-service` 保留 Java 业务服务。
- `projects/customer-service-console` 新增前端。
- `docs` 存项目级正式文档。
- `notes` 存阶段记录和必要学习说明。

## 10. 接口文档计划

后续需要单独整理：

```text
docs/stage11-api-contract.md
```

它应该包含：

- 前端调用 Java 的 public API。
- 前端调用 Python 的 AI API。
- Python 调 Java 的 internal API。
- 请求字段。
- 响应字段。
- 错误码。
- Header。
- 权限要求。
- 示例请求和响应。

接口文档不建议一次性写完全部。

更合理的方式是：

```text
每做一组接口，就更新对应契约。
```

## 11. 数据库文档计划

后续需要单独整理：

```text
docs/stage11-database-design.md
```

它应该包含：

- 表清单。
- 字段说明。
- 主键。
- 唯一约束。
- 索引。
- 状态流转。
- 初始化演示数据。
- AI 调用业务数据时的权限边界。

数据库文档应主要跟 Java 服务保持一致。

## 12. 运行文档计划

后续需要单独整理：

```text
docs/stage11-local-runbook.md
```

它应该包含：

- 启动 MySQL。
- 启动 Redis。
- 启动 Qdrant。
- 启动 Java 服务。
- 启动 Python AI 服务。
- 启动前端。
- `.env` 配置。
- 常见错误。
- 手动验证命令。

到 Docker Compose 阶段，再补：

```text
docker compose up
```

相关说明。

## 13. 测试策略

阶段 11 仍然保留省 token 约定。

测试原则：

- 代码实现节：补关键测试。
- 纯文档节：不写测试。
- 前端页面节：优先手动验证关键路径，必要时再加自动化。
- Java 业务节：保留单元测试、Controller 测试或集成测试。
- Python AI 节：自动化测试默认不真实调用模型。
- 真实模型链路：用手动 smoke 验证，不把真实 API Key 放进测试。

用户手动跑测试的约定继续有效：

```text
我给出测试命令。
你手动执行。
你把结果贴回来。
我根据结果修复或继续。
```

## 14. 风险和控制

### 14.1 风险：范围膨胀

控制方式：

- 先做最小完整闭环。
- 高级功能放到后续扩展。
- 每节都对照阶段 11 主文档。

### 14.2 风险：外部依赖拖慢进度

控制方式：

- 前几节先做本地项目骨架和业务底座。
- 真实模型、Qdrant、Docker Compose 到对应阶段再接。
- 如果外部服务慢，先保留可切换配置。

### 14.3 风险：前端做成花架子

控制方式：

- 前端按工作台设计。
- 以真实业务操作为核心。
- 不做营销首页。
- 不做无用大屏。

### 14.4 风险：AI 绕过业务边界

控制方式：

- 订单和工单以 Java + MySQL 为准。
- Python 只通过 Java internal API 读写业务。
- 写操作必须确认、幂等、审计。
- 工具输出字段白名单。

### 14.5 风险：密钥泄露

控制方式：

- `.env` 不进 GitHub。
- `.env.example` 只放占位符。
- 前端不保存模型密钥。
- 日志不打印 API Key。

## 15. 阶段 11 最小完整闭环

为了避免项目过大，阶段 11 的最小完整闭环定义为：

```text
用户登录
-> 进入 AI 客服页面
-> 问一个知识库问题
-> Python 用真实 RAG 回答并展示引用
-> 用户查询自己的订单
-> Python 通过 Tool 调 Java 查询真实 MySQL 订单
-> 用户确认创建工单
-> Java 写入真实 MySQL 工单
-> 客服在工作台看到工单并更新状态
-> 用户看到工单状态变化
```

这条链路跑通，就说明项目已经具备完整作品项目的核心价值。

## 16. 本节结论

阶段 11 的实施顺序确定为：

```text
先项目蓝图
再前端骨架
再身份和业务数据
再 AI API
再真实 RAG 和模型
再端到端联调
再运营展示
最后部署和作品化
```

下一节建议进入：

```text
阶段 11 第 3 节：前端技术选型与项目骨架
```

开始第 3 节前，需要先检查本机 Node.js 环境。
