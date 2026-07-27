# 阶段 6 第 35 节：health check、readiness 和 CI 自动回归

本节主题：

health check、readiness 和 CI 自动回归。

上一节我们学了 Docker Compose 本地编排。

Compose 能把多个服务启动起来。

但服务“启动了”不等于“可用了”。

一个容器可能已经 running。

但应用还没加载完配置。

数据库还没连上。

依赖还没准备好。

模型 API Key 缺失。

这时候如果系统直接接收流量，就会出现启动即失败。

所以这一节学习：

```text
health check
readiness
CI regression
```

中文可以理解为：

```text
健康检查
就绪检查
持续集成自动回归
```

它们解决三个不同问题：

health check：

服务进程是不是还活着。

readiness：

服务是不是准备好接收流量。

CI regression：

每次代码变更后，能不能自动验证没有破坏已有功能。

---

## 一、本节学习目标

学完本节，你要能讲明白：

1. health check 是什么。
2. liveness 是什么。
3. readiness 是什么。
4. startup probe 是什么。
5. liveness、readiness、startup 的区别。
6. 为什么容器 running 不等于服务 ready。
7. 为什么 `/health` 不应该检查太多外部依赖。
8. 为什么 `/ready` 可以检查当前模式下的必需配置。
9. 为什么 readiness 不一定要真实调用所有外部服务。
10. FastAPI 里怎么实现 `/health` 和 `/ready`。
11. 为什么 readiness 失败时应该返回 503。
12. Compose `healthcheck` 和应用 `/ready` 的关系。
13. GitHub Actions 是什么。
14. CI 是什么。
15. regression test 是什么。
16. 为什么本地和 CI 应该复用同一套回归命令。
17. 为什么真实 API Key 不应该出现在 CI 配置里。
18. 为什么本节新增 `.github/workflows/ci.yml`。
19. 为什么本节新增 `scripts/run_regression.py`。
20. 如何解释当前项目的 health/readiness/CI 自动回归设计。

---

## 二、官方资料

本节参考以下官方资料：

1. Kubernetes：Liveness, Readiness, and Startup Probes
   https://kubernetes.io/docs/concepts/workloads/pods/probes/

   重点：liveness probe 判断容器是否需要重启；readiness probe 判断容器是否准备好接收流量；startup probe 判断应用是否已经启动成功。

2. Kubernetes：Configure Liveness, Readiness and Startup Probes
   https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/

   重点：不同 probe 的目的不同，不应该把所有检查混在一个接口里。

3. Docker Compose startup order
   https://docs.docker.com/compose/how-tos/startup-order/

   重点：Compose 默认只等依赖容器 running；如果要等依赖 healthy，需要使用 `healthcheck` 和 `depends_on.condition: service_healthy`。

4. Docker Compose services reference
   https://docs.docker.com/reference/compose-file/services/

   重点：Compose service 支持 `healthcheck`，并且 `depends_on` 可以使用 `service_healthy`。

5. GitHub Actions workflow syntax
   https://docs.github.com/actions/using-workflows/workflow-syntax-for-github-actions

   重点：workflow 是由 YAML 定义的自动化流程，由事件触发，包含一个或多个 jobs。

6. GitHub Docs：Building and testing Python
   https://docs.github.com/actions/guides/building-and-testing-python

   重点：GitHub Actions 可以用于构建和测试 Python 项目。

7. Astral Docs：Using uv in GitHub Actions
   https://docs.astral.sh/uv/guides/integration/github/

   重点：官方推荐使用 `astral-sh/setup-uv` action 在 GitHub Actions 中安装 uv。

---

## 三、承接上一节 Docker Compose

第 34 节新增了：

```text
compose.yml
compose.env.example
```

并且在 Compose 里配置了 healthcheck。

上一节的重点是：

服务如何一起启动。

这一节的重点是：

服务启动后，如何判断是否真的可用。

比如：

```text
java-mock-service 容器 running
```

不代表：

```text
它的 HTTP API 已经可以接收请求
```

再比如：

```text
ai-service 容器 running
```

不代表：

```text
它在 real_llm 模式下已经有 API Key
```

所以 Compose 里的 healthcheck 最好不要只看容器进程。

它应该访问应用提供的探针接口。

本节把 Compose healthcheck 改为访问：

```text
/ready
```

而不是只访问：

```text
/health
```

因为 health 和 readiness 语义不同。

---

## 四、基础知识铺垫

这一部分是本节核心。

先把概念学明白，再看代码。

### 4.1 什么是 health check

health check 是健康检查。

它用于判断一个服务当前是否健康。

但“健康”这个词很宽泛。

在工程里，我们通常会继续拆成：

```text
liveness
readiness
startup
```

如果不拆，所有东西都叫 health，就容易混乱。

例如：

进程还活着。

配置已经加载。

依赖已经连接。

缓存已经预热。

数据库迁移已经完成。

这些都可以被人叫“健康”。

但它们代表的含义不同。

### 4.2 什么是 liveness

liveness 关注：

服务是不是还活着。

更具体一点：

应用进程是否还在运行。

事件循环是否还能响应。

是否出现死锁、卡死、无法继续处理请求。

Kubernetes 官方文档里说，liveness probe 可以用来判断什么时候重启容器。

如果 liveness 失败，通常表示：

这个容器应该被重启。

所以 liveness 不应该太重。

它不应该依赖太多外部服务。

否则外部服务短暂故障，可能导致你的应用被错误重启。

### 4.3 什么是 readiness

readiness 关注：

服务是否准备好接收流量。

Kubernetes 官方文档说明，readiness probe 用来判断容器是否 ready 接收请求。

如果 readiness 失败，通常表示：

不要把流量发给这个实例。

但不一定要重启它。

例如：

应用刚启动，还在加载配置。

真实模型模式下缺少 API Key。

数据库连接池还没准备好。

依赖正在恢复。

这些情况可能导致 readiness 失败。

但进程本身可能还活着。

所以 readiness 和 liveness 要分开。

### 4.4 什么是 startup probe

startup probe 关注：

应用是否完成启动。

有些应用启动很慢。

比如：

加载大模型。

加载大索引。

执行数据库迁移。

初始化缓存。

如果一开始就用 liveness 检查它，可能应用还没启动完就被误判为不健康。

startup probe 的作用是：

给慢启动应用一个更宽松的启动检查窗口。

当前项目还没有真正需要 startup probe。

但你要知道它存在。

以后如果部署到 Kubernetes，会经常看到这三个概念。

### 4.5 liveness、readiness、startup 对比

可以这样记：

| 类型 | 关心什么 | 失败后通常做什么 |
| --- | --- | --- |
| liveness | 进程是否还活着 | 重启容器 |
| readiness | 是否可以接收流量 | 暂停给它分流 |
| startup | 是否启动完成 | 启动完成前不启用其他 probe |

本节项目里：

`/health` 更接近 liveness。

`/ready` 更接近 readiness。

### 4.6 容器 running 不等于 ready

这是非常重要的概念。

Docker 里容器显示 running，只代表：

容器主进程还在。

它不代表：

HTTP 端口已经监听。

应用配置已经加载。

外部依赖已经连通。

业务服务已经可以接流量。

所以 Compose 里仅仅 `depends_on` 启动顺序还不够。

Docker 官方文档也说明：

Compose 默认只等容器 running，不等服务 ready。

如果要等依赖健康，需要：

```text
healthcheck
depends_on.condition: service_healthy
```

### 4.7 为什么 `/health` 不应该检查太多依赖

如果 `/health` 检查太多外部依赖，可能有问题。

比如：

Qdrant 短暂不可用。

Milvus 正在重启。

模型 API 暂时限流。

如果 `/health` 因此失败，容器平台可能重启你的 AI 服务。

但 AI 服务本身并没有死。

它只是某个下游依赖不可用。

这时候重启 AI 服务并不能解决问题。

所以 `/health` 应该尽量轻。

它主要回答：

```text
这个进程还活着吗？
```

### 4.8 为什么 `/ready` 可以检查更多内容

`/ready` 关注能不能接流量。

它可以比 `/health` 检查更多内容。

比如：

配置是否完整。

当前模式是否满足必需条件。

必要依赖是否可用。

但它也不能无限重。

如果 `/ready` 每次都真实调用 LLM、Qdrant、Milvus，可能导致：

探针本身消耗成本。

探针增加下游压力。

探针导致外部依赖被频繁打。

所以 readiness 要适度。

### 4.9 readiness 是否必须真实探测所有依赖

不一定。

这是生产系统里很重要的设计点。

如果一个依赖是启动必需的：

可以纳入 readiness。

如果一个依赖是可选功能：

不一定要让它阻塞 readiness。

比如当前 `ai-service`：

默认是：

```text
TICKET_AGENT_MODEL_MODE=rule_based
```

这种模式不需要真实 LLM API Key。

所以 `/ready` 不应该因为没有 LLM API Key 而失败。

但如果模式是：

```text
real_llm
```

那 LLM API Key 就变成必需配置。

这时 `/ready` 如果发现没有 key，就应该返回 not_ready。

### 4.10 为什么 readiness 失败要返回 503

HTTP 503 表示：

```text
Service Unavailable
```

也就是服务暂时不可用。

如果 `/ready` 判断服务没有准备好，应该返回非 2xx。

这样 Compose healthcheck、负载均衡器、Kubernetes readiness probe 才能正确识别失败。

如果 `/ready` 返回：

```json
{"ready": false}
```

但 HTTP 状态码仍然是 200。

很多平台会误以为它健康。

所以本节改动中：

`ai-service /ready` 在不 ready 时返回 503。

### 4.11 `/ready` 不等于业务成功

readiness 只说明服务可以接收流量。

它不保证每个业务请求一定成功。

比如：

`/ready` 返回 ready。

但某个订单号不存在。

业务请求仍然会返回订单不存在。

这是正常的。

readiness 判断的是服务准备状态。

不是具体业务结果。

### 4.12 什么是 CI

CI 是 Continuous Integration。

中文叫持续集成。

它的核心思想是：

每次代码变更后，自动执行一组检查。

这些检查可以包括：

依赖同步。

编译检查。

单元测试。

接口测试。

类型检查。

格式检查。

安全扫描。

构建镜像。

本节先做最基础的自动回归。

### 4.13 什么是 regression

regression 是回归。

在软件测试里，回归测试的意思是：

检查新改动有没有破坏旧功能。

比如：

你新增 `/ready`。

不能把 `/health` 弄坏。

你新增 Compose。

不能让现有 RAG 测试失败。

你新增 CI。

不能只跑一小部分测试，结果漏掉旧功能。

### 4.14 为什么本地和 CI 要复用同一套命令

如果本地一套命令，CI 一套命令，就容易出现：

本地通过。

CI 失败。

或者 CI 通过。

本地没跑全。

所以本节新增：

```text
scripts/run_regression.py
```

这个脚本可以本地运行：

```bash
python scripts/run_regression.py
```

也可以在 GitHub Actions 里运行。

这样本地和 CI 复用同一个回归入口。

### 4.15 GitHub Actions 是什么

GitHub Actions 是 GitHub 提供的自动化平台。

GitHub 官方文档说，workflow 是由 YAML 定义的自动化流程。

它可以由事件触发。

比如：

push。

pull request。

手动触发。

本节新增：

```text
.github/workflows/ci.yml
```

它会在 push 到 main、PR 到 main、手动触发时运行回归检查。

### 4.16 CI 为什么不能依赖本地 `.env`

CI 运行在 GitHub 提供的机器上。

它没有你的本地 `.env`。

也不应该默认拥有你的真实 API Key。

所以 CI 里的测试必须默认不真实调用模型。

当前项目默认：

```text
rule_based
```

自动化测试也使用 fake、mock、依赖替换。

这很重要。

CI 不能每次都真实调用模型。

否则会产生费用、速度慢、结果不稳定，也可能泄漏密钥。

---

## 五、本节主题系统讲解

这一节做了三类工程改动：

1. 给两个服务补 `/ready`。
2. 让 Compose healthcheck 使用 `/ready`。
3. 新增本地和 CI 复用的自动回归入口。

### 5.1 本节新增和修改文件

新增：

```text
projects/ai-service/app/schemas/health.py
scripts/run_regression.py
.github/workflows/ci.yml
notes/stage6-35-health-readiness-ci-regression.md
```

修改：

```text
projects/ai-service/app/routers/health.py
projects/ai-service/tests/test_health.py
projects/java-mock-service/app/schemas/health.py
projects/java-mock-service/app/routers/health.py
projects/java-mock-service/tests/test_health_api.py
compose.yml
notes/stage6-34-docker-compose-local-orchestration.md
README.md
docs/learning-progress.md
```

### 5.2 ai-service 的 `/health`

`ai-service /health` 现在使用 Pydantic 响应模型：

```text
HealthResponse
```

它返回：

```json
{
  "status": "ok",
  "service": "ai-service",
  "time": "..."
}
```

它的语义是：

进程能响应 HTTP 请求。

它不检查 LLM。

不检查 Qdrant。

不检查 Milvus。

不检查 Java mock 服务。

这样设计是为了让 `/health` 更接近 liveness。

### 5.3 ai-service 的 `/ready`

`ai-service /ready` 返回：

```text
ReadinessResponse
```

里面有：

```text
status
service
ready
checks
time
```

`checks` 里包含：

```text
java_mock_service_base_url
ticket_agent_model_mode
qdrant_base_url
milvus_uri
llm_api_key
```

其中：

Java mock service base URL 是必需配置。

Ticket Agent model mode 是必需配置。

Qdrant/Milvus 当前是可选工作流配置，不阻塞基础 readiness。

LLM API Key 只在 `real_llm` 模式下必需。

### 5.4 real_llm 模式为什么会影响 readiness

如果：

```text
TICKET_AGENT_MODEL_MODE=real_llm
```

但没有：

```text
LLM_API_KEY
```

那么服务不能可靠接收真实 LLM 流量。

所以 `/ready` 返回：

```text
503
status = not_ready
ready = false
```

如果是：

```text
rule_based
fake_llm
```

则不需要真实 API Key。

`llm_api_key` 检查会标记为：

```text
skipped
```

### 5.5 java-mock-service 的 `/ready`

`java-mock-service` 是当前的 FastAPI mock 业务服务。

它现在也有：

```text
/health
/ready
```

`/ready` 检查：

```text
in_memory_order_store
in_memory_ticket_store
```

因为当前 mock 服务使用内存数据。

只要服务能正常运行，这两个内存 store 就可用。

以后如果它变成真正 Java/Spring Boot 服务，readiness 就可以检查：

数据库连接。

Redis 连接。

消息队列连接。

业务配置。

### 5.6 Compose healthcheck 为什么改成 `/ready`

上一节 Compose 里已经有 healthcheck。

本节把它改成访问：

```text
/ready
```

原因是：

Compose healthcheck 常被 `depends_on.condition: service_healthy` 使用。

这时候我们更关心：

依赖服务是否 ready。

而不只是进程是否还活着。

所以：

`java-mock-service` 的 healthcheck 访问：

```text
http://127.0.0.1:8001/ready
```

`ai-service` 的 healthcheck 访问：

```text
http://127.0.0.1:8000/ready
```

### 5.7 回归脚本做了什么

新增脚本：

```text
scripts/run_regression.py
```

它会依次处理：

```text
projects/java-mock-service
projects/ai-service
```

每个项目执行三步：

```text
uv sync --frozen
uv run python -m compileall -q -x ".venv|__pycache__" .
uv run pytest
```

这三步分别解决：

依赖是否能按锁文件同步。

Python 文件是否能编译。

测试是否通过。

### 5.8 为什么用 Python 写回归脚本

因为 Python 跨平台。

Windows 可以运行。

Linux CI 可以运行。

如果写 PowerShell，只适合 Windows。

如果写 Bash，只适合 Linux/macOS。

当前你主要在 Windows 学习，但 CI 在 Ubuntu。

所以用 Python 做统一入口更合适。

### 5.9 CI workflow 做了什么

新增：

```text
.github/workflows/ci.yml
```

它定义：

```text
name: CI
```

触发条件：

```text
push 到 main
pull_request 到 main
手动 workflow_dispatch
```

核心步骤：

```text
checkout 代码
安装 uv
设置 Python 3.12
运行 python scripts/run_regression.py
```

这就是最小但完整的 CI 自动回归。

### 5.10 为什么 CI 先不跑 Docker Compose

本节 CI 暂时不跑 Compose。

原因是：

当前主要目标是建立自动回归基础。

Python 测试已经覆盖了大量业务逻辑。

Compose 实机验证需要拉镜像，耗时更长。

Milvus 依赖更重。

后续如果要做集成测试，可以再单独加 Compose profile 或服务容器。

不要一开始就把 CI 做得很重。

---

## 六、本节代码讲解

这一部分讲学习相关代码。

### 6.1 ai-service HealthResponse

```python
class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    time: str
```

这个模型约束 `/health` 响应。

`status` 只能是 `ok`。

这样接口结构更稳定。

### 6.2 ai-service ReadinessCheck

```python
class ReadinessCheck(BaseModel):
    name: str
    status: DependencyProbeStatus
    required: bool
    message: str
```

它表示一个就绪检查项。

比如：

```text
llm_api_key
java_mock_service_base_url
```

`required=True` 表示这个检查会影响整体 readiness。

`required=False` 表示它是辅助信息，不阻塞服务接流量。

### 6.3 ai-service readiness_check()

```python
@router.get("/ready", response_model=ReadinessResponse)
def readiness_check(response: Response, settings: Settings = Depends(get_settings)):
```

这个接口通过依赖注入拿到 settings。

然后构造 checks。

如果必需检查失败：

```python
response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
```

同时响应体里返回：

```text
status = not_ready
ready = false
```

### 6.4 build_ai_service_readiness_checks()

这个函数把 readiness 规则集中起来。

它明确说明：

Java mock base URL 是必需的。

模型模式是必需的。

Qdrant/Milvus 当前只做可选配置展示。

LLM API Key 只在 real_llm 模式下必需。

这比把所有逻辑直接塞进路由函数更清楚。

### 6.5 java-mock-service readiness

`java-mock-service /ready` 很简单。

它返回两个检查：

```text
in_memory_order_store
in_memory_ticket_store
```

当前 mock 服务没有数据库。

所以 readiness 不需要做网络探测。

### 6.6 scripts/run_regression.py

脚本的核心数据结构是：

```python
PROJECTS = (
    ("java-mock-service", REPO_ROOT / "projects" / "java-mock-service"),
    ("ai-service", REPO_ROOT / "projects" / "ai-service"),
)
```

它表示要检查两个项目。

每个项目执行：

```python
uv sync --frozen
uv run python -m compileall ...
uv run pytest
```

如果某一步失败，脚本立刻返回失败码。

这对 CI 很重要。

CI 通过退出码判断成功或失败。

### 6.7 .github/workflows/ci.yml

workflow 里：

```yaml
on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main
  workflow_dispatch:
```

表示：

push 到 main 时跑。

PR 到 main 时跑。

也允许手动触发。

```yaml
uses: astral-sh/setup-uv@v5
```

表示使用 uv 官方推荐的 GitHub Action 安装 uv。

最后：

```yaml
run: python scripts/run_regression.py
```

复用本地回归入口。

---

## 七、本节测试讲解

本节新增和更新了 health/readiness 测试。

### 7.1 ai-service health 测试

测试 `/health`：

```text
status = ok
service = ai-service
time 是字符串
HTTP 200
```

它确认 liveness 风格端点稳定。

### 7.2 ai-service rule_based readiness 测试

默认测试环境是 rule_based。

这种模式不需要真实 LLM API Key。

所以 `/ready` 应该：

```text
HTTP 200
status = ready
ready = true
llm_api_key = skipped
```

### 7.3 ai-service real_llm 缺 key 测试

如果设置：

```text
ticket_agent_model_mode = real_llm
llm_api_key = None
```

那么 `/ready` 应该：

```text
HTTP 503
status = not_ready
ready = false
llm_api_key = not_configured
```

这验证了 readiness 的真正价值。

### 7.4 ai-service real_llm 有 key 测试

如果 real_llm 模式下有 key：

```text
llm_api_key = test-key
```

那么 `/ready` 应该通过。

测试里用的是测试字符串。

不会真实调用模型。

### 7.5 java-mock-service readiness 测试

Java mock 服务测试确认：

```text
/health
/ready
```

都返回预期结构。

`/ready` 包含订单内存 store 和工单内存 store。

### 7.6 回归脚本验证

本节实际运行了：

```text
python scripts/run_regression.py
```

它完成：

```text
java-mock-service: 13 passed
ai-service: 880 passed
```

同时也做了 compileall 检查。

这说明本地回归入口可以工作。

---

## 八、把本节讲给别人时可以这样说

如果别人问：

health check 是什么？

你可以回答：

health check 是服务健康探针，但工程里通常要拆成 liveness、readiness、startup。不要把所有检查都塞进一个 `/health`。

如果别人问：

liveness 和 readiness 区别是什么？

你可以回答：

liveness 判断进程是否还活着，失败通常意味着需要重启。readiness 判断服务是否准备好接收流量，失败通常意味着暂时不要给它分流，但不一定要重启。

如果别人问：

为什么 `/ready` 失败要返回 503？

你可以回答：

因为探针系统通常根据 HTTP 状态码判断成功失败。如果 ready=false 但仍返回 200，Compose 或负载均衡器可能误判它健康。

如果别人问：

为什么 `/health` 不检查 Qdrant/Milvus？

你可以回答：

因为 `/health` 更接近 liveness。如果外部依赖短暂不可用就让 `/health` 失败，可能导致 AI 服务被错误重启。外部依赖状态更适合 readiness、诊断接口或单独监控。

如果别人问：

CI 自动回归是什么？

你可以回答：

CI 自动回归是在每次 push 或 PR 时自动运行测试和基础检查，确保新改动没有破坏已有功能。本项目通过 GitHub Actions 运行 `scripts/run_regression.py`。

---

## 九、本节练习

### 练习 1

解释 `/health` 和 `/ready` 的区别。

参考答案：

`/health` 更接近 liveness，表示服务进程还能响应。

`/ready` 更接近 readiness，表示服务是否准备好接收当前模式下的流量。

`/health` 不应该检查太多外部依赖。

`/ready` 可以检查必需配置和必需依赖。

### 练习 2

为什么容器 running 不等于服务 ready？

参考答案：

容器 running 只说明容器主进程还在。

它不保证 HTTP 服务已经监听、配置已经加载、依赖已经可用。

所以需要应用层 `/ready` 和 Compose/Kubernetes 的健康探针。

### 练习 3

为什么 `real_llm` 模式缺少 API Key 时 `/ready` 应该返回 503？

参考答案：

因为 real_llm 模式需要真实模型调用。

没有 API Key 时服务不能可靠处理真实 LLM 请求。

返回 503 可以让 Compose 或负载均衡器知道它暂时不可接流量。

### 练习 4

为什么默认 `rule_based` 模式下没有 LLM API Key 也可以 ready？

参考答案：

因为 rule_based 模式不真实调用模型。

没有 LLM API Key 不影响基础服务处理规则路径请求。

所以这个检查应该 skipped，而不是 not_configured。

### 练习 5

CI 为什么不应该真实调用大模型？

参考答案：

因为 CI 会频繁运行。

真实调用大模型会产生费用、速度慢、结果不稳定，还可能需要暴露密钥。

自动化测试应该默认使用 fake、mock 或依赖替换。

### 练习 6

为什么本地和 CI 要复用同一个 `scripts/run_regression.py`？

参考答案：

这样可以减少“本地一套检查、CI 一套检查”的不一致。

本地跑过的命令和 CI 跑的命令一致，问题更容易复现。

### 练习 7

`uv sync --frozen` 的意义是什么？

参考答案：

它按锁文件同步依赖，不随意更新依赖版本。

这样本地和 CI 使用的依赖更稳定。

### 练习 8

为什么 CI 配置里不能写真实 API Key？

参考答案：

因为 CI 配置会提交到仓库。

真实密钥写进去会泄漏。

如果未来确实需要密钥，应该用 GitHub Secrets，而不是直接写在 YAML 里。

---

## 十、自测题

### 自测 1

liveness 失败通常意味着什么？

答案：

通常意味着容器或进程可能需要重启。

### 自测 2

readiness 失败一定要重启容器吗？

答案：

不一定。

readiness 失败通常表示暂时不要给它分流，但进程本身可能还活着。

### 自测 3

startup probe 主要解决什么问题？

答案：

解决慢启动应用在启动过程中被 liveness/readiness 误判的问题。

### 自测 4

为什么 `/ready` 不能每次都真实调用 LLM？

答案：

因为探针会频繁执行。

真实调用 LLM 会产生费用、增加延迟和下游压力，也可能受限流影响。

### 自测 5

Compose `depends_on` 默认会等服务 ready 吗？

答案：

不会。

默认只等容器 running。

要等 healthy，需要 `healthcheck` 和 `condition: service_healthy`。

### 自测 6

CI workflow 文件一般放在哪里？

答案：

放在：

```text
.github/workflows/
```

本节新增的是：

```text
.github/workflows/ci.yml
```

### 自测 7

本节回归脚本检查了哪两个项目？

答案：

```text
projects/java-mock-service
projects/ai-service
```

### 自测 8

`python scripts/run_regression.py` 会做哪些主要步骤？

答案：

对两个项目分别执行：

```text
uv sync --frozen
uv run python -m compileall ...
uv run pytest
```

### 自测 9

本节是否真实运行了 GitHub Actions？

答案：

没有。

GitHub Actions 需要提交并推送到 GitHub 后，由 GitHub 执行。

本节在本地验证了回归脚本。

### 自测 10

本节是否需要打开 VMware？

答案：

开始阶段不需要。

本节已经在 Windows 完成了代码、测试和回归脚本验证。

如果要真实验证 Compose healthcheck，就需要打开 VMware Ubuntu，因为你的 Docker 在虚拟机里。

---

## 十一、本节小结

本节补齐了服务生产化里非常重要的一块：

服务可用性探针和自动回归。

你现在应该能区分：

```text
/health
/ready
liveness
readiness
startup
CI
regression
```

本节新增 `/ready` 后：

`ai-service` 能根据当前模式判断是否 ready。

`java-mock-service` 能暴露 mock 业务服务 readiness。

Compose healthcheck 也改成了 `/ready`。

本节新增 `scripts/run_regression.py` 后：

本地和 CI 有了统一回归入口。

本节新增 `.github/workflows/ci.yml` 后：

项目具备了最基础的 GitHub Actions 自动回归能力。

---

## 十二、下一节学什么

下一节是阶段 6 第 36 节：

```text
阶段 6 项目整理和面试表达
```

这会是阶段 6 的收尾课。

它会整理：

1. 阶段 6 到底学了什么。
2. Agent 生产化能力有哪些。
3. 如何把评测、观测性、稳定性、编排、CI 讲成一条完整工程链路。
4. 面试时如何表达这个项目。
5. 当前项目还有哪些生产级差距。
6. 下一阶段可以继续学什么。

下一节不需要一开始打开 VMware。
