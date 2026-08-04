# 阶段 11 第 13 节：生产化配置与本地运行说明收口

## 本节完成内容

- 重写 `docs/local-run-and-demo.md`，对齐阶段 11 当前真实项目结构。
- 明确前端、Java business service、Python AI service、MySQL、Redis、Qdrant 的本地端口和启动顺序。
- 补齐 MySQL、Redis、Qdrant、真实 LLM、embedding、rerank 的配置说明。
- 新增 `projects/java-business-service/.env.example`，集中记录 Java 服务本地环境变量。
- 更新 `projects/ai-service/.env.example` 的 Qdrant 真实 embedding 集合、向量维度和 rerank 示例配置。
- 保留 PowerShell 常见问题说明，包括 `curl.exe`、中文显示、JSON 引号和 `ModuleNotFoundError`。

## 验证结果

```text
projects/ai-service:
uv run python -c "from pathlib import Path; from app.core.config import Settings; s=Settings(_env_file=Path('.env.example')); print(s.qdrant_collection_name, s.qdrant_vector_size, s.rerank_model)"
通过：learning_rag_chunks_v4_1024 1024 qwen3-rerank

projects/customer-service-console:
npm run build
通过：vue-tsc + vite build
```

## 下一节

阶段 11 第 14 节：Docker Compose 本地部署。

这一节会把当前多个服务的启动方式进一步整理为本地编排方案。开始前需要确认你希望 Docker Compose 主要跑在 Windows 侧，还是继续依赖 VMware Ubuntu 里的 Docker。
