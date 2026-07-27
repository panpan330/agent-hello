# M6 第 4 节：本地运行说明和演示脚本

## 本节定位

这一节是 M6 快速作品化阶段的第四节。

前面已经完成：

```text
M6 第 1 节：项目定位和作品化目标
M6 第 2 节：整理 GitHub 首页 README
M6 第 3 节：架构图和核心流程图
```

现在项目已经能用文字和图说明：

```text
它是什么。
它有什么能力。
它的架构是什么。
RAG、Agent、工具调用安全怎么流转。
```

但作品项目还差一个关键问题：

```text
别人怎么运行？
你怎么演示？
```

这一节解决的就是：

```text
本地运行说明 + 项目演示脚本
```

运行说明告诉别人：

```text
怎么把服务跑起来。
```

演示脚本告诉你：

```text
给别人展示时，按什么顺序讲、按什么命令演示、每一步证明什么能力。
```

---

## 一、本节学习目标

学完本节，你要能讲清楚：

1. 运行说明是什么。
2. 演示脚本是什么。
3. 运行说明和演示脚本有什么区别。
4. 为什么作品项目必须有运行说明。
5. 为什么演示要分成最小演示和可选演示。
6. 当前项目在 Windows 本地怎么启动两个服务。
7. Java mock service 怎么启动和验证。
8. Python ai-service 怎么启动和验证。
9. `.env.example` 和 `.env` 的关系。
10. 为什么不要把真实 `.env` 上传 GitHub。
11. 哪些演示不需要模型 API Key。
12. 哪些演示需要模型 API Key。
13. 哪些演示需要打开 VMware Ubuntu 里的 Docker。
14. 为什么 PowerShell 里优先用 `Invoke-RestMethod`。
15. 怎么跑统一回归脚本。
16. 常见启动问题怎么排查。

---

## 二、本节先不做什么

这一节不做这些事：

1. 不新增业务功能。
2. 不真实启动长期服务。
3. 不真实调用大模型。
4. 不强制打开虚拟机。
5. 不真实跑 Qdrant/Milvus 入库。
6. 不把运行说明写成生产部署文档。
7. 不写最终简历和面试问答。

原因是：

```text
本节是作品化运行说明，不是部署上线阶段。
```

生产部署、Dockerfile、Nginx、HTTPS、云服务器、监控告警，后续阶段再学。

---

## 三、基础知识铺垫

### 1. 什么是运行说明

运行说明回答：

```text
我拿到这个仓库后，怎么把项目跑起来？
```

它通常包括：

```text
需要什么环境
进入哪个目录
安装依赖用什么命令
配置文件怎么准备
服务怎么启动
启动后怎么验证
出错时怎么排查
```

运行说明不是讲原理。

运行说明要尽量具体。

比如不要只写：

```text
启动 ai-service。
```

要写：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv sync
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

这样读者才能照着做。

### 2. 什么是演示脚本

演示脚本回答：

```text
我给别人展示这个项目时，按什么顺序演示？
```

演示脚本不只是命令列表。

它还要说明：

```text
这一步证明什么能力。
这一步预期看到什么结果。
如果没有模型 API Key，哪些步骤跳过。
如果虚拟机没开，哪些步骤跳过。
```

比如：

```text
第一步演示 /health，证明服务进程正常。
第二步演示 /ready，证明当前配置满足接收请求条件。
第三步演示 Java mock /orders/A1001，证明业务服务能返回订单。
第四步演示 ai-service /tools/query-order，证明 Python AI 服务能通过受控工具调用 Java 服务。
```

这才是演示脚本。

### 3. 运行说明和演示脚本的区别

可以这样区分：

| 类型 | 目标 | 关注点 |
| --- | --- | --- |
| 运行说明 | 让项目跑起来 | 环境、命令、端口、配置、验证 |
| 演示脚本 | 让别人看懂项目能力 | 演示顺序、说明话术、预期结果、能力证明 |

运行说明更偏操作。

演示脚本更偏展示。

作品项目两者都需要。

### 4. 为什么要分最小演示和完整演示

当前项目有几类能力：

```text
不需要模型 API Key 的能力
需要模型 API Key 的能力
需要 Qdrant/Milvus 的能力
需要 VMware Ubuntu Docker 的能力
```

如果把所有能力混在一起，演示会很容易卡住。

所以要分层：

```text
最小演示：不需要模型 API Key，不需要虚拟机。
AI 演示：需要模型 API Key。
向量库演示：需要 VMware Ubuntu Docker 启动 Qdrant 或 Milvus。
回归演示：直接跑统一回归脚本。
```

这样做的好处是：

```text
就算没有 API Key 或虚拟机没开，也能演示项目的基础工程能力。
```

### 5. 当前项目推荐的最小演示

当前最推荐的最小演示是：

```text
Windows 本地启动 Java mock service
Windows 本地启动 Python ai-service
验证两个服务 /health 和 /ready
直接查 Java mock 订单
通过 ai-service /tools/query-order 调用 Java 订单服务
运行统一回归脚本
```

这个演示不需要：

```text
真实模型 API Key
Qdrant
Milvus
VMware Ubuntu
Docker
```

它能证明：

```text
两个服务能跑。
Python AI 服务能调用 Java 业务服务。
工具参数和结果能被校验。
项目有自动化回归。
```

这已经足够作为基础演示。

### 6. 哪些功能需要模型 API Key

这些通常需要模型 API Key：

```text
/chat
/stream-chat
/extract-ticket
/tool-decision
/tool-chat
/tickets/plans
真实 LLM 意图识别 smoke
真实 LLM 字段提取 smoke
真实 embedding 入库
```

原因是：

```text
这些能力要调用真实 OpenAI-compatible 模型。
```

如果 `.env` 没有配置 `LLM_API_KEY`，这些接口会返回类似：

```text
LLM_API_KEY_MISSING
```

这是预期行为，不是项目坏了。

### 7. 哪些功能需要 VMware Ubuntu Docker

这些需要打开虚拟机：

```text
Qdrant 实机检索演示
Milvus 实机检索演示
Docker Compose 编排演示
```

原因是：

```text
你的 Docker 安装在 VMware Ubuntu 里，不在 Windows 本机。
```

所以如果只是做基础运行和工具调用演示：

```text
不需要开虚拟机。
```

如果要演示 Qdrant/Milvus：

```text
需要开 VMware Ubuntu。
```

### 8. `.env.example` 和 `.env` 的关系

`.env.example` 是示例配置。

它可以提交到 GitHub。

`.env` 是本机真实配置。

它不应该提交到 GitHub。

当前 ai-service 的 `.env.example` 里有：

```text
LLM_MODEL
LLM_BASE_URL
LLM_API_KEY
JAVA_MOCK_SERVICE_BASE_URL
QDRANT_BASE_URL
MILVUS_URI
TICKET_AGENT_MODEL_MODE
```

使用方式是：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

然后你只在本机 `.env` 里填真实 API Key。

不要把真实 `.env` 上传。

### 9. 为什么 PowerShell 里优先用 Invoke-RestMethod

在 PowerShell 里，`curl` 经常不是你以为的 curl。

它可能是：

```text
Invoke-WebRequest 的别名
```

这会导致：

```text
JSON 引号不好写
中文显示混乱
弹出脚本安全提示
参数行为和 Linux curl 不一样
```

所以 Windows PowerShell 演示时，优先用：

```powershell
Invoke-RestMethod
```

如果你一定要用真正 curl，要写：

```powershell
curl.exe
```

本节文档优先给 `Invoke-RestMethod` 示例。

### 10. 为什么运行说明要写常见问题

运行项目时常见错误包括：

```text
端口被占用
没有进入正确目录
没有安装依赖
.env 缺失
API Key 缺失
Java mock service 没启动
Qdrant/Milvus 虚拟机没开
PowerShell curl 引号问题
```

如果 README 或运行说明提前写清楚这些问题，后续学习会顺很多。

---

## 四、本节主题系统讲解

### 1. 本节新增的运行说明文档

本节新增：

```text
docs/local-run-and-demo.md
```

它是项目本地运行和演示脚本入口。

里面包含：

```text
运行范围说明
前置条件
Windows 本地最小运行
健康检查
工具调用演示
真实模型演示
Qdrant/Milvus 可选演示
统一回归
常见问题
演示话术
```

### 2. 为什么不把完整运行说明直接塞进 README

README 已经承担很多职责：

```text
项目定位
核心能力
技术栈
目录结构
快速入口
学习索引
```

如果再把所有运行步骤都放进 README，会太长。

所以 README 只放入口：

```text
本地运行和演示脚本：docs/local-run-and-demo.md
```

详细步骤放到单独文档。

### 3. Windows 本地最小运行链路

最小运行需要两个终端：

```text
终端 1：启动 Java mock service，端口 8001
终端 2：启动 Python ai-service，端口 8000
```

启动顺序建议：

```text
先启动 Java mock service。
再启动 ai-service。
```

原因是：

```text
ai-service 的工具调用会访问 Java mock service。
```

### 4. 最小演示证明什么

最小演示包括：

```text
java-mock-service /health
java-mock-service /ready
ai-service /health
ai-service /ready
java-mock-service /orders/A1001
ai-service /tools/query-order
python scripts/run_regression.py
```

它证明：

```text
Java mock 业务服务可用。
Python AI 服务可用。
Python 能通过工具调用 Java。
项目测试和回归能跑。
```

这比只演示聊天更能体现后端工程能力。

### 5. 为什么 `/chat` 不放进最小演示

`/chat` 是真实模型调用接口。

它需要：

```text
LLM_API_KEY
LLM_BASE_URL
LLM_MODEL
```

如果没有配置真实模型，它会返回 `LLM_API_KEY_MISSING`。

这不是 bug。

所以 `/chat` 放到：

```text
可选真实模型演示
```

这样最小演示不会被 API Key 卡住。

### 6. 为什么 Qdrant/Milvus 不放进最小演示

Qdrant/Milvus 需要虚拟机 Docker。

如果每次演示都强制打开虚拟机，会增加成本。

M6 是快速作品化。

所以：

```text
基础演示不依赖 Qdrant/Milvus。
向量库能力通过 README、图文档、笔记、测试和可选演示说明。
需要时再打开 VMware Ubuntu。
```

### 7. 统一回归脚本的重要性

统一回归脚本是：

```powershell
python scripts\run_regression.py
```

它会分别进入：

```text
projects/java-mock-service
projects/ai-service
```

并运行：

```text
uv sync --frozen
compileall
pytest
```

这证明：

```text
项目不是只能手动点接口。
它有自动化验证入口。
```

### 8. 演示顺序怎么安排

推荐演示顺序：

```text
1. 先讲项目定位。
2. 打开 README 第一屏。
3. 打开 docs/project-diagrams.md 讲整体架构。
4. 启动 Java mock service。
5. 启动 ai-service。
6. 验证 /health 和 /ready。
7. 演示 Java 订单查询。
8. 演示 ai-service 工具查询订单。
9. 演示统一回归脚本。
10. 如果有 API Key，再演示真实模型能力。
11. 如果虚拟机已开，再演示 Qdrant/Milvus。
```

这样从整体到局部，从低风险到高依赖，比较稳。

### 9. 本节对项目的实际改变

本节新增：

```text
notes/m6-04-local-run-and-demo-script.md
docs/local-run-and-demo.md
```

本节修改：

```text
README.md
docs/learning-progress.md
```

本节没有修改业务代码。

---

## 五、本节练习

### 练习 1：运行说明和演示脚本有什么区别？

参考答案：

```text
运行说明告诉别人怎么把项目跑起来，重点是环境、目录、命令、端口和验证；演示脚本告诉自己怎么展示项目，重点是演示顺序、每一步证明什么能力、预期结果和可选步骤。
```

### 练习 2：为什么最小演示不依赖模型 API Key？

参考答案：

```text
因为真实模型调用受 API Key、网络、费用和模型稳定性影响。最小演示应该优先证明项目基础工程能力，比如两个服务能启动、health/ready 正常、Python 能通过受控工具调用 Java、统一回归能跑。
```

### 练习 3：什么时候需要打开 VMware Ubuntu？

参考答案：

```text
当要演示 Qdrant、Milvus 或 Docker Compose 编排时需要打开 VMware Ubuntu，因为当前 Docker 安装在虚拟机里。只演示 Windows 本地两个 FastAPI 服务和工具调用时不需要开虚拟机。
```

### 练习 4：为什么 Windows PowerShell 优先用 Invoke-RestMethod？

参考答案：

```text
因为 PowerShell 里的 curl 可能是 Invoke-WebRequest 的别名，JSON 引号、中文显示和参数行为容易出问题。Invoke-RestMethod 更适合在 PowerShell 中调用 JSON API。
```

### 练习 5：统一回归脚本证明什么？

参考答案：

```text
统一回归脚本证明项目不是只能手工演示，还能自动验证 Java mock service 和 ai-service 的依赖、语法和测试。它也是本地和 CI 复用的验证入口。
```

---

## 六、自测问题

### 自测 1：基础演示需要启动哪两个服务？

答案：

```text
需要启动 java-mock-service 和 ai-service。java-mock-service 默认端口 8001，ai-service 默认端口 8000。
```

### 自测 2：如果 `/chat` 返回 LLM_API_KEY_MISSING，说明什么？

答案：

```text
说明当前没有配置真实模型 API Key。它不是基础服务坏了，而是接口需要真实 LLM 配置。没有 API Key 时可以跳过 /chat，先演示 health/ready、工具查询和回归脚本。
```

### 自测 3：为什么 ai-service 要先配置 JAVA_MOCK_SERVICE_BASE_URL？

答案：

```text
因为 ai-service 的 query_order 工具会通过 JavaOrderClient 调用 Java mock service。如果 base URL 配错或 Java 服务没启动，工具查询会失败。
```

### 自测 4：如果端口 8000 被占用怎么办？

答案：

```text
可以先查占用端口的进程，或换一个端口启动 ai-service。换端口时健康检查和演示命令里的地址也要同步改。
```

### 自测 5：本节新增的运行说明文档是什么？

答案：

```text
docs/local-run-and-demo.md
```

---

## 七、本节总结

这一节完成了：

```text
本地运行说明
项目演示脚本
常见问题说明
```

你要记住：

```text
作品项目不仅要能写出来，还要能被别人跑起来、看明白、演示清楚。
```

当前推荐最小演示是：

```text
Windows 本地启动 Java mock service
Windows 本地启动 ai-service
验证 health/ready
演示 Java 订单查询
演示 ai-service 通过工具调用 Java
运行统一回归脚本
```

下一节进入：

```text
M6 第 5 节：简历描述、面试讲稿、常见追问
```

那一节会把作品表达整理成简历和面试材料。
