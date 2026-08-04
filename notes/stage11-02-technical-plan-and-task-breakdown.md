# 阶段 11 第 2 节：技术方案与任务拆分

## 本节定位

第 1 节确定了阶段 11 要把智能工单系统做成完整真实项目。

第 2 节继续解决一个更实际的问题：

```text
这么多东西到底按什么顺序做？
```

完整项目不能一上来所有方向同时开工。

如果前端、Java、Python、MySQL、Redis、Qdrant、真实模型、部署文档一起做，很容易变成：

- 哪里都改了一点。
- 哪条链路都没真正跑通。
- 外部依赖一出问题就卡住。
- 项目结构越来越乱。

所以本节的重点是技术方案和任务拆分。

本节主文档：

```text
docs/stage11-technical-plan-and-task-breakdown.md
```

## 本节解决的问题

本节回答：

- 阶段 11 最终由哪些服务组成。
- 前端、Java、Python、MySQL、Redis、Qdrant、模型分别负责什么。
- 前端应该调 Java 还是 Python。
- Python AI 服务什么时候调 Java。
- 哪些真实资源什么时候接入。
- 为什么真实模型和 Qdrant 不应该一开始就接。
- 阶段 11 最小完整闭环是什么。
- 下一节开始前需要准备什么。

## 技术方案核心结论

阶段 11 最终架构是：

```text
前端
-> Java public API
-> MySQL / Redis

前端
-> Python AI API
-> LLM / embedding / rerank / Qdrant
-> Java internal API
-> MySQL / Redis
```

三个核心项目目录：

```text
projects/customer-service-console
projects/java-business-service
projects/ai-service
```

前端固定使用：

```text
Vue3 + TypeScript + Vite + Element Plus
Vue Router + Pinia + Axios
```

原因是你对 Vue3 体系更熟悉，而且这个项目本质是后台工作台 / 客服工作台，Element Plus 的表格、表单、弹窗、菜单、分页、Tabs、Drawer 等组件非常适合这个场景。

其中：

- 前端负责页面和交互。
- Java 负责用户、订单、工单、权限、MySQL、Redis。
- Python 负责 LLM、RAG、Tool Calling、Agent 和 AI 评估。

一句话：

```text
Java 是业务事实来源，Python 是 AI 编排层，前端是用户操作入口。
```

## 为什么按这个顺序推进

阶段 11 推荐顺序：

```text
1. 项目蓝图。
2. 前端骨架。
3. 登录和角色。
4. Java 业务数据模型。
5. 订单和工单页面。
6. Python AI API 整理。
7. 知识库真实入库。
8. 真实模型链路。
9. 端到端联调。
10. 客服工作台。
11. 评估和 bad case 页面。
12. 运行、部署、演示和简历材料。
```

这个顺序的原因：

- 先有前端骨架，后面功能才有展示入口。
- 先有身份和角色，后面权限才不会乱。
- 先有 Java 业务数据，AI 工具调用才有真实目标。
- 先整理 AI API，再接真实模型，避免接口边界反复改。
- 先单服务跑通，再 Docker Compose 整合，排查成本更低。

## 资源准备点

第 2 节本身不需要外部资源。

后续资源准备时间：

- 第 3 节需要检查 Node.js。
- 第 4-5 节可能需要 MySQL / Redis。
- 第 8 节需要 Qdrant。
- 第 8-9 节需要 embedding / rerank / LLM API Key。
- 第 14 节需要 Docker Compose 整合。

以后如果某节需要你打开 VMware、启动 Docker、启动 MySQL/Redis/Qdrant 或准备模型 API Key，我会在开始前明确说。

## 本节练习

### 练习 1：为什么 Java 应该作为业务事实来源？

参考答案：

因为订单、工单、用户、权限、状态流转这些都是结构化业务数据，需要事务、权限、审计、精确查询和稳定接口。Java Spring Boot + MySQL 更适合作为业务事实来源。Python AI 服务可以理解意图和编排工具，但不能绕过 Java 直接决定业务状态。

### 练习 2：为什么 Qdrant 不适合保存订单和工单？

参考答案：

Qdrant 是向量数据库，适合做语义检索，比如根据问题找到相似知识文档。订单和工单需要精确查询、事务、状态流转、权限控制和审计，所以应该保存在 MySQL 中。

### 练习 3：为什么不一开始就接真实 LLM、embedding、rerank？

参考答案：

因为项目骨架、前端、身份、Java 业务模型和 API 边界还没稳定时，提前接真实模型会把精力消耗在外部依赖、费用、网络和调试上。更稳的做法是先把业务骨架和接口定下来，再接真实模型链路。

### 练习 4：阶段 11 最小完整闭环是什么？

参考答案：

用户登录后进入 AI 客服页面，问一个知识库问题，Python 用真实 RAG 回答并展示引用；用户查询自己的订单，Python 通过 Tool 调 Java 查询真实 MySQL 订单；用户确认创建工单，Java 写入真实 MySQL；客服在工作台看到工单并更新状态，用户看到状态变化。

## 自测题

### 自测 1：阶段 11 三个核心项目目录是什么？

答案：

```text
projects/customer-service-console
projects/java-business-service
projects/ai-service
```

### 自测 2：前端应该保存模型 API Key 吗？

答案：

不应该。模型 API Key 属于敏感密钥，只能放在后端环境变量或安全配置中，不能放到浏览器前端。

### 自测 3：Python AI 服务写工单时应该怎么做？

答案：

Python AI 服务不能直接写业务数据库。它应该通过 Java internal API 创建工单，并传递 trace_id、调用方、用户身份、租户、internal token 和幂等键，由 Java 完成权限校验、幂等控制和 MySQL 写入。

### 自测 4：下一节开始前需要优先检查什么环境？

答案：

下一节是前端技术选型与项目骨架，需要优先检查 Node.js 和包管理器环境。

## 本节结论

阶段 11 不能靠随手加功能推进，而要按项目工程顺序推进。

本节已经确定：

- 总体架构。
- 服务职责。
- API 边界。
- 数据流。
- 实施顺序。
- 资源准备点。
- 最小完整闭环。

下一节进入：

```text
阶段 11 第 3 节：前端技术选型与项目骨架
```
