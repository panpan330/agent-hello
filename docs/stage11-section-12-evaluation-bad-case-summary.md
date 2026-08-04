# 阶段 11 第 12 节：AI 评估与 bad case 页面收口

## 本节完成内容

- Python AI 服务新增 `GET /api/ai/evaluation/overview`。
- 该接口读取本地评估集 registry，并运行本地规则评估生成最新评估快照。
- 当 `data/evaluation/bad_cases.json` 为空时，接口会基于最新本地评估结果即时生成 bad case 展示数据。
- Vue3 前端新增评估 API client。
- AI 评估页面从静态骨架升级为真实看板，支持查看评估集、最新运行、套件状态、bad case 分布、bad case 列表和详情。

## 验证结果

```text
projects/ai-service:
uv run pytest tests/test_evaluation_api.py -q
通过：2 tests

projects/ai-service:
uv run pytest tests/test_evaluation_api.py tests/test_eval_platform.py tests/test_bad_case_registry.py tests/test_agent_eval_suite.py tests/test_bad_case_analysis.py -q
通过：30 tests

projects/ai-service:
uv run pytest -q
通过：1258 tests

projects/customer-service-console:
npm run build
通过：vue-tsc + vite build
```

## 下一节

阶段 11 第 13 节：生产化配置与本地运行说明。

这一节会整理完整项目的运行方式、环境变量、服务依赖和本地联调顺序。按当前安排会以代码完整和可运行为主，文档只写必要的运行说明。
