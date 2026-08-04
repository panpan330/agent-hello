# 阶段 11 第 14 节：项目总验收与补洞收口

## 本节完成内容

- 将阶段 11 原计划中的 Docker Compose 小节后移到后续“部署与上线专题”。
- 本节改为项目总验收与补洞，优先保证当前项目完整、可运行、可演示。
- 检查前端主要页面真实程度：
  - 订单页已接 Java 真实 API。
  - 工单页已接 Java 真实 API。
  - 工单工作台已接 Java 详情、状态流转和事件流水。
  - 知识库页已接 Java 文档元数据和 Python 入库接口。
  - AI 评估页已接 Python 评估与 bad case 看板接口。
- 补齐首页最大缺口：Dashboard 从静态 mock 数据改为真实接口聚合概览。

## 本节补的关键缺口

首页现在会从真实接口聚合：

- Java 订单列表。
- Java 工单列表。
- Java 知识库文档列表。
- Python AI 评估看板。

首页展示内容包括：

- 可见订单数。
- 待处理工单数。
- 知识库文档数。
- 评估通过率。
- 项目运行链路。
- 最近工单。
- 当前评估快照。

## 验证结果

```text
projects/customer-service-console:
npm run build
通过：vue-tsc + vite build

projects/java-business-service:
mvn test
通过：36 tests

projects/ai-service:
uv run pytest -q
通过：1258 tests
```

## 当前结论

阶段 11 的核心项目化目标已经达成：

```text
Vue3 前端
-> Java Spring Boot 业务服务
-> MySQL / Redis
-> Python FastAPI AI 服务
-> 真实 LLM / embedding / rerank / Qdrant RAG
-> 工单工作台
-> 评估与 bad case 看板
```

当前项目已经具备“完整项目”的主体结构，可以继续进入作品化打磨、部署专题或新技术专题。

## 后续可选方向

- 上传 GitHub 前做敏感信息扫描、提交和推送。
- 手动启动完整真实链路，按 `docs/local-run-and-demo.md` 做一次浏览器验收。
- 后续阶段系统学习 Dockerfile / Docker Compose / 部署上线。
- 继续补更饱满的业务功能，例如工单分配、工单备注、用户侧工单详情、知识库上传、运营统计图表。
