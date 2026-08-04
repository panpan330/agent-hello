# 阶段 11 第 11 节：客服工单工作台收口

## 本节完成内容

- Java public API 新增 `GET /api/tickets/{ticketId}`，用于读取工单详情和事件流水。
- Java public API 新增 `PATCH /api/tickets/{ticketId}/status`，用于客服更新工单状态。
- 工单状态从基础 `created / processing / closed` 扩展为 `created / in_progress / waiting_user / resolved / closed`。
- 状态更新会写入 `ticket_events`，保留处理人、trace_id、处理说明和目标状态。
- Vue3 客服工单工作台已接真实 Java API，支持队列筛选、详情查看、处理说明、状态流转和事件流水展示。

## 验证结果

```text
projects/java-business-service:
mvn test -Dtest=PublicOrderTicketControllerTest
通过：7 tests

projects/java-business-service:
mvn test
通过：36 tests

projects/customer-service-console:
npm run build
通过：vue-tsc + vite build
```

## 下一节

阶段 11 第 12 节：AI 评估与 bad case 页面。

这一节会把前面已经学过的评估数据、bad case、回归样例等能力做成项目里可展示、可查看的页面，不要求提前打开 Qdrant；如果需要真实服务，我会在开始前单独提醒。
