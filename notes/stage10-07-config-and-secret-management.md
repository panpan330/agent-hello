# 阶段 10 第 7 节：配置与密钥管理

## 本节定位

这一节学习 AI 应用上线前必须掌握的配置与密钥管理。

本节不是单纯学 `.env` 怎么写，而是要理解：

```text
配置决定系统怎么运行，密钥决定系统能访问什么。
配置可以被适度观察，密钥必须被严格保护。
```

## 本节学习目标

- 理解配置、密钥、环境变量、`.env`、`.env.example` 的区别。
- 理解为什么真实 API Key 不能写进代码、笔记、README、日志和 GitHub。
- 理解开发环境、测试环境、生产环境为什么要使用不同配置。
- 理解 AI 应用里哪些配置尤其敏感。
- 学会用“是否已配置”代替“真实配置值”暴露运行状态。
- 看懂本节新增的配置安全快照和密钥检查代码。

## 本节新增和修改

- 新增 `app/core/config_safety.py`。
- 新增 `tests/test_config_safety.py`。
- 修改 `/ready` 对 `llm_api_key` 的检查逻辑。
- 给 `.env.example` 增加密钥安全提示。
- 更新学习进度。

## 一句话先讲透

配置与密钥管理的核心原则是：

```text
程序通过配置决定行为，通过密钥访问外部能力；对外只能暴露“是否配置好”，不能暴露“真实密钥是什么”。
```

## 基础知识铺垫

### 1. 什么是配置

配置就是：

```text
不应该写死在代码里，但会影响程序运行方式的参数。
```

例如：

```text
服务名称
端口
日志级别
模型名称
模型 base_url
请求超时时间
最大重试次数
最大输出 token 数
RAG 使用哪个向量库
Qdrant 地址
Milvus 地址
是否启用真实 LLM
是否启用真实 embedding
是否启用 rerank
```

这些值的共同特点是：

```text
代码逻辑不变，但不同环境下取值可能不同。
```

比如本地学习时：

```text
TICKET_AGENT_MODEL_MODE="rule_based"
LLM_API_KEY=""
QDRANT_BASE_URL="http://192.168.88.10:6333"
```

以后线上时可能变成：

```text
TICKET_AGENT_MODEL_MODE="real_llm"
LLM_API_KEY="由密钥系统注入"
QDRANT_BASE_URL="线上内网地址"
```

注意，这里不是让你把真实线上配置写进代码，而是说明：

```text
同一套代码，应该可以被不同配置驱动成不同运行形态。
```

### 2. 什么是密钥

密钥是配置的一种，但它比普通配置敏感得多。

密钥通常用来证明：

```text
你有权限访问某个外部系统。
```

常见密钥包括：

```text
API Key
Access Token
Secret Key
数据库密码
Redis 密码
JWT 签名密钥
对象存储密钥
内部服务调用 token
第三方模型平台 token
```

普通配置泄露，可能只是让别人知道你的系统怎么运行。

密钥泄露，后果更严重：

```text
别人可以调用你的模型接口。
别人可以消耗你的额度。
别人可能访问你的数据。
别人可能伪装成你的服务。
别人可能对你的系统进行破坏。
```

所以密钥管理的第一条原则是：

```text
密钥不是普通字符串，密钥是权限。
```

### 3. 配置和密钥的区别

可以这样区分：

| 类型 | 例子 | 是否敏感 | 能不能提交 GitHub |
| --- | --- | --- | --- |
| 普通配置 | `LLM_MODEL="qwen3.7-plus"` | 通常不敏感 | 可以 |
| 普通配置 | `REQUEST_TIMEOUT_SECONDS=30` | 不敏感 | 可以 |
| 地址配置 | `LLM_BASE_URL="https://example.com/v1"` | 视情况而定 | 示例可以，真实内网地址谨慎 |
| 密钥 | `LLM_API_KEY="真实 key"` | 高敏感 | 绝对不可以 |
| 密钥 | `OPENAI_API_KEY="真实 key"` | 高敏感 | 绝对不可以 |
| 密钥 | `MYSQL_PASSWORD="真实密码"` | 高敏感 | 绝对不可以 |

这里有一个容易混淆的点：

```text
base_url 通常不是密钥，但也不一定适合随便公开。
```

比如公开模型平台地址一般问题不大。

但如果是生产环境内网地址，可能暴露系统拓扑。

所以本节代码里没有把完整 `base_url` 放进“安全快照”，而是记录：

```text
llm.base_url_configured = true / false
```

这就是“最小暴露”思想。

### 4. 什么是环境变量

环境变量是操作系统或运行环境提供给程序的键值对。

在 Python 里可以通过：

```python
import os

api_key = os.getenv("LLM_API_KEY")
```

读取。

在 Spring Boot 里也可以通过：

```yaml
spring:
  datasource:
    password: ${JAVA_DB_PASSWORD:root}
```

读取。

意思是：

```text
优先从环境变量 JAVA_DB_PASSWORD 读取。
如果没有，就使用默认值 root。
```

环境变量的好处是：

```text
同一份代码不需要修改，就能在本地、测试、生产使用不同参数。
```

例如：

```text
本地：LLM_MODEL="cheap-test-model"
测试：LLM_MODEL="qwen3.7-plus"
生产：LLM_MODEL="stable-production-model"
```

程序不用改，只改环境变量。

### 5. 什么是 `.env`

`.env` 是本地开发常用的环境变量文件。

它通常长这样：

```text
LLM_MODEL="qwen3.7-plus"
LLM_API_KEY="这里是你本机真实 key"
REQUEST_TIMEOUT_SECONDS=30
```

`.env` 的作用是：

```text
方便本地开发，不用每次手动设置一堆环境变量。
```

但 `.env` 有一个非常重要的规则：

```text
.env 里面可以有真实密钥，所以绝对不能提交 GitHub。
```

当前仓库根目录 `.gitignore` 已经有：

```text
.env
.env.*
!.env.example
```

这表示：

```text
.env 不提交。
.env.local 不提交。
.env.production 不提交。
.env.example 可以提交。
```

### 6. 什么是 `.env.example`

`.env.example` 是给别人看的配置模板。

它的作用是：

```text
告诉别人这个项目需要哪些配置项。
```

它不能放真实密钥，只能放：

```text
空字符串
示例值
占位符
安全默认值
说明注释
```

比如：

```text
LLM_API_KEY=""
LLM_BASE_URL="https://your-workspace-id.example.com/compatible-mode/v1"
```

这表示：

```text
项目需要 LLM_API_KEY，但这里不提供真实值。
```

所以 `.env` 和 `.env.example` 的关系是：

| 文件 | 作用 | 是否包含真实密钥 | 是否提交 GitHub |
| --- | --- | --- | --- |
| `.env` | 本机真实配置 | 可以有 | 不提交 |
| `.env.example` | 配置模板 | 不可以有 | 可以提交 |

### 7. 为什么不能把 API Key 写死在代码里

比如不能这样写：

```python
client = OpenAI(api_key="sk-real-xxxxxxxx")
```

原因有几个：

第一，代码可能会提交 GitHub。

第二，代码会被多人看到。

第三，代码会进入提交历史，即使后面删除，也可能被找回。

第四，测试、日志、报错、截图都可能把它带出去。

第五，换 key 时还要改代码、重新发布。

正确做法是：

```python
settings.resolved_llm_api_key
```

或者：

```python
os.getenv("LLM_API_KEY")
```

代码只知道“从哪里拿 key”，不直接保存 key。

### 8. 为什么不能把 API Key 写进日志

日志往往比代码传播得更广。

真实系统中，日志可能进入：

```text
控制台
日志文件
Docker logs
ELK / OpenSearch
云厂商日志服务
APM 平台
告警消息
排查截图
客服工单
```

如果日志里出现：

```text
LLM_API_KEY=sk-real-xxx
Authorization: Bearer xxx
```

那就意味着很多系统都复制了一份密钥。

这比代码里泄露还难清理。

所以第 6 节学了 LLM 日志安全，本节继续往前补：

```text
配置本身也不能随便日志化。
```

尤其不能这样：

```python
logger.info("settings=%s", settings)
logger.info("settings=%s", settings.model_dump())
```

因为 `model_dump()` 很可能包含真实字段值。

虽然 Pydantic 的 `repr=False` 可以减少对象 repr 泄露风险，但它不是万能的。

你手动访问字段、手动 dump、手动拼接字符串时，仍然可能泄露。

### 9. 为什么不能做一个直接返回所有配置的接口

真实项目里，有人可能想做：

```text
GET /config
```

然后返回：

```json
{
  "llm_model": "qwen3.7-plus",
  "llm_api_key": "sk-real-xxx",
  "database_password": "root"
}
```

这是很危险的。

就算这个接口只给内部系统使用，也容易因为权限配置、日志记录、网关转发、调试截图而泄露。

正确思路是：

```text
需要观察配置时，返回安全快照。
```

例如：

```json
{
  "llm.model": "qwen3.7-plus",
  "llm.api_key_configured": true,
  "llm.base_url_configured": true
}
```

这里没有真实 API Key。

这就是本节代码 `build_safe_settings_snapshot()` 的意义。

### 10. 什么是“配置状态”

配置状态不是配置值。

配置值：

```text
LLM_API_KEY="sk-real-xxx"
```

配置状态：

```text
llm.api_key_configured=true
```

配置状态只能说明：

```text
有没有配置。
```

不能说明：

```text
具体配置了什么。
```

这在生产排查时很实用。

比如用户说真实模型调用失败，你可以先看：

```text
llm.api_key_configured=false
```

那基本能判断：

```text
当前服务没有配置 LLM API Key。
```

但你不需要，也不应该看到真实 key。

### 11. 什么是“按运行模式要求密钥”

不是所有环境都需要所有密钥。

比如当前项目有：

```text
TICKET_AGENT_MODEL_MODE="rule_based"
TICKET_AGENT_MODEL_MODE="fake_llm"
TICKET_AGENT_MODEL_MODE="real_llm"
```

如果是 `rule_based`：

```text
不调用真实模型，不需要 LLM_API_KEY。
```

如果是 `fake_llm`：

```text
模拟模型输出，也不需要真实 LLM_API_KEY。
```

如果是 `real_llm`：

```text
要调用真实模型，必须有 LLM_API_KEY 或兼容的 fallback key。
```

所以密钥校验不能写成：

```text
只要没有 LLM_API_KEY，服务就不能启动。
```

否则本地学习、测试、CI 都会很难跑。

更合理的是：

```text
当前运行模式需要它时，才把它设为 required。
```

这就是本节 `build_secret_configuration_checks()` 的重点。

### 12. 开发环境、测试环境、生产环境为什么要分开

开发环境：

```text
给开发者本机使用。
可以使用便宜模型、fake 模型、本地 Qdrant、本地 Milvus、本地 MySQL。
```

测试环境：

```text
给自动化测试或测试人员使用。
重点是稳定、可重复、低成本。
通常不真实调用昂贵模型。
```

生产环境：

```text
给真实用户使用。
需要稳定、监控、告警、密钥保护、权限控制、审计、限流、成本控制。
```

如果三个环境混用配置，会出现很多问题：

```text
本地误连生产数据库。
测试误用真实模型消耗费用。
生产误用 fake 模型导致功能不可用。
开发 key 被提交后影响线上额度。
测试环境日志暴露真实用户数据。
```

所以真实项目会特别重视：

```text
环境隔离。
配置隔离。
密钥隔离。
权限隔离。
```

### 13. 为什么 `.env.example` 里的默认值要谨慎

`.env.example` 是别人第一次了解项目时会看的文件。

它里面的值要做到：

```text
能说明用途。
不会泄露真实信息。
不会误导别人把示例当生产配置。
```

比如这类写法是好的：

```text
LLM_API_KEY=""
RERANK_API_KEY=""
EMBEDDING_API_KEY=""
```

它表达：

```text
这里需要 key，但模板不提供。
```

这类写法不好：

```text
LLM_API_KEY="sk-real-xxx"
MYSQL_PASSWORD="real-password"
```

这会直接泄露。

还有一类也要谨慎：

```text
LLM_BASE_URL="真实生产内网地址"
```

它不是密钥，但可能暴露生产架构信息。

### 14. AI 应用里哪些配置特别重要

AI 应用比普通后端多了很多模型相关配置。

当前项目里典型配置包括：

```text
LLM_PROVIDER
LLM_MODEL
LLM_BASE_URL
LLM_API_KEY
REQUEST_TIMEOUT_SECONDS
LLM_MAX_RETRIES
MAX_OUTPUT_TOKENS
TICKET_AGENT_MODEL_MODE
EMBEDDING_PROVIDER
EMBEDDING_MODEL
EMBEDDING_BASE_URL
EMBEDDING_API_KEY
EMBEDDING_DIMENSION
RERANK_PROVIDER
RERANK_MODEL
RERANK_BASE_URL
RERANK_API_KEY
QDRANT_BASE_URL
MILVUS_URI
```

这些配置会影响：

```text
调用哪个模型。
花多少钱。
响应多快。
是否能真实调用外部服务。
向量维度是否匹配。
RAG 检索是否能正常工作。
失败后能不能重试。
超时多久返回。
```

比如 `EMBEDDING_DIMENSION` 设置错了，可能导致：

```text
embedding 生成的向量维度和向量库 collection 维度不一致。
```

比如 `LLM_MAX_RETRIES` 设置太高，可能导致：

```text
失败时重复消耗 token，成本增加，请求耗时变长。
```

所以配置不是“随便写几个变量”，配置是生产系统行为的一部分。

### 15. 配置管理和可观测性的关系

生产系统需要知道当前服务大概运行在什么配置状态下。

例如：

```text
当前是不是 real_llm？
LLM key 有没有配置？
Embedding key 有没有配置？
Rerank key 有没有配置？
Qdrant 是否配置？
Milvus 是否配置？
超时时间是多少？
重试次数是多少？
```

这些信息对排查很重要。

但它们不能泄露：

```text
真实 key
真实 token
完整 Authorization
数据库密码
内部访问 token
可能敏感的真实内网地址
```

所以正确方式是：

```text
可观测性要看“状态”和“元信息”，不是看“敏感原文”。
```

这和第 6 节 LLM 日志安全是同一个思想。

第 6 节：

```text
LLM 日志只记录模型名、耗时、token、错误码等元信息。
```

第 7 节：

```text
配置观察只记录模型名、模式、是否配置 key、超时和重试等安全信息。
```

### 16. 配置管理和 readiness 的关系

`/health` 通常回答：

```text
进程还活着吗？
```

`/ready` 通常回答：

```text
服务现在能不能接收流量？
```

如果当前运行模式是 `real_llm`，但没有配置 LLM API Key，那么服务即使进程活着，也不能算真的 ready。

因为真实模型调用会失败。

所以本项目已经有 `/ready`。

本节改造的点是：

```text
/ready 不直接散落判断密钥，而是复用统一的密钥检查逻辑。
```

这样以后如果要检查 embedding、rerank、外部向量库 token，也可以走同一套思路。

### 17. 配置管理和测试的关系

自动化测试应该尽量避免依赖真实密钥。

原因是：

```text
测试需要稳定。
测试需要可重复。
测试不能随便花钱。
测试不能因为某个人本机 key 失效就失败。
测试不能把密钥打印到 CI 日志。
```

所以本项目测试经常使用：

```python
Settings(_env_file=None)
```

意思是：

```text
不读取本地 .env 文件，用测试明确给出的配置值。
```

这能避免测试误用你的本机真实密钥。

### 18. 密钥轮换是什么

密钥轮换就是：

```text
定期或在风险发生后更换密钥。
```

例如：

```text
旧 key 停用。
新 key 注入环境变量。
服务重启或热加载。
确认新 key 生效。
检查旧 key 不再被使用。
```

为什么要轮换？

```text
密钥可能被截图、日志、电脑备份、聊天记录、旧提交历史、CI 日志泄露。
```

真实企业里，密钥不会认为“一次设置永远安全”。

### 19. 最小权限原则

密钥最好只拥有完成当前任务所需的最小权限。

比如：

```text
只需要调用 rerank，就不要给它数据库管理员权限。
只需要读知识库，就不要给它删除 collection 的权限。
只需要调用某个模型，就不要给它全部资源管理权限。
```

密钥泄露时，权限越大，损失越大。

AI 应用尤其要注意这一点，因为 Agent 可能会连接很多工具：

```text
模型平台
向量数据库
Java 业务服务
MCP Server
数据库
缓存
对象存储
第三方 API
```

每多接一个系统，密钥管理难度都会提高。

### 20. 本节要形成的判断能力

看到一个配置项时，你要能问自己：

```text
它是不是密钥？
它能不能提交 GitHub？
它能不能出现在日志里？
它能不能返回给前端？
它能不能出现在错误信息里？
它是不是只应该暴露 configured=true/false？
它在哪些运行模式下是必需的？
它有没有安全默认值？
测试里是否需要 fake 或空值？
```

这比单纯会写 `.env` 更重要。

## 本节主题系统讲解

### 1. 当前项目的配置入口

当前 Python AI 服务的核心配置在：

```text
projects/ai-service/app/core/config.py
```

里面的核心类是：

```python
class Settings(BaseSettings):
    ...
```

它继承自 `pydantic-settings` 的 `BaseSettings`。

这意味着它可以从：

```text
默认值
初始化参数
系统环境变量
.env 文件
```

读取配置。

本项目指定了：

```python
ENV_FILE = PROJECT_ROOT / ".env"
```

也就是说：

```text
ai-service 默认会读取 projects/ai-service/.env。
```

你的本机真实 `.env` 就应该放在那里。

但注意：

```text
本节没有读取、展示、修改你的真实 .env 内容。
```

### 2. 当前项目的 `.env.example`

当前模板文件是：

```text
projects/ai-service/.env.example
```

本节给它补了三行说明：

```text
Copy this file to .env for local development.
Never put real API keys or tokens in .env.example.
.env is ignored by git; .env.example is safe to commit because it only documents names.
```

这三句话分别对应：

```text
怎么用。
不能放什么。
为什么它可以提交。
```

它不是程序逻辑，但它是团队协作中很重要的安全提示。

很多密钥泄露不是因为程序不会写，而是因为模板文件、README、截图、笔记里不小心放了真实 key。

### 3. `config.py` 负责什么

`config.py` 的职责是：

```text
定义配置结构。
定义默认值。
定义类型约束。
从环境变量和 .env 读取值。
提供经过清理的 resolved 属性。
```

例如：

```python
llm_api_key: str | None = Field(default=None, repr=False)
```

这里有几个信息：

```text
字段名是 llm_api_key。
类型是 str 或 None。
默认值是 None。
repr=False 表示对象 repr 时不要展示它。
```

再比如：

```python
request_timeout_seconds: float = Field(default=30.0, gt=0)
```

表示：

```text
请求超时时间默认 30 秒。
必须大于 0。
如果配置成 0 或负数，Pydantic 会报校验错误。
```

这就比裸 `os.getenv()` 更强。

裸 `os.getenv()` 只能拿字符串，类型转换和边界校验要自己写。

### 4. `resolved_*` 属性解决什么问题

当前项目里有很多 `resolved_*` 属性，比如：

```python
resolved_llm_api_key
resolved_llm_base_url
resolved_embedding_api_key
resolved_embedding_base_url
resolved_rerank_base_url
resolved_qdrant_base_url
resolved_milvus_uri
```

它们的作用是：

```text
把原始配置整理成业务真正使用的值。
```

例如：

```python
resolved_llm_api_key
```

会优先使用：

```text
LLM_API_KEY
```

如果它为空，再 fallback 到：

```text
OPENAI_API_KEY
```

这是为了兼容早期配置习惯。

但业务代码不应该到处写：

```python
settings.llm_api_key or settings.openai_api_key
```

否则规则会散落各处。

集中到 `resolved_llm_api_key` 后，业务代码只关心：

```text
我最终能不能拿到一个可用 key。
```

### 5. 为什么本节不直接改 `config.py`

本节没有大改 `config.py`，原因是：

```text
现有配置读取结构已经能工作。
本节要补的是“配置如何安全暴露和检查”。
```

所以新增了：

```text
app/core/config_safety.py
```

让职责更清楚：

```text
config.py：负责读取和表示配置。
config_safety.py：负责安全快照和密钥检查。
```

如果把所有内容都塞进 `config.py`，文件会越来越大，而且“读取配置”和“安全展示配置”会混在一起。

### 6. 安全配置快照是什么

安全配置快照就是：

```text
把 Settings 里可观察的信息整理出来，但不带真实密钥和敏感原文。
```

本节新增：

```python
build_safe_settings_snapshot(settings)
```

它返回类似这样的结构：

```text
app.name
app.version
app.log_level
llm.provider
llm.model
llm.base_url_configured
llm.api_key_configured
llm.request_timeout_seconds
llm.max_retries
ticket_agent.model_mode
embedding.model
embedding.api_key_configured
rerank.api_key_configured
qdrant.api_key_configured
milvus.token_configured
```

注意这些字段：

```text
llm.api_key_configured
embedding.api_key_configured
rerank.api_key_configured
qdrant.api_key_configured
milvus.token_configured
```

它们只表示是否配置。

它们不会返回真实值。

这就是安全快照的核心。

### 7. 为什么快照里保留 model，但不保留 key

模型名通常属于可观测元信息。

例如：

```text
llm.model = qwen3.7-plus
```

它能帮助排查：

```text
这次服务到底使用哪个模型。
不同模型错误率是否不同。
不同模型成本是否不同。
不同模型延迟是否不同。
```

但 key 不能暴露。

因为：

```text
key 是访问权限。
```

所以同样是配置，处理方式不同：

| 配置项 | 快照处理方式 |
| --- | --- |
| `LLM_MODEL` | 可以展示模型名 |
| `LLM_API_KEY` | 只展示是否已配置 |
| `REQUEST_TIMEOUT_SECONDS` | 可以展示数值 |
| `LLM_BASE_URL` | 本节只展示是否已配置 |
| `QDRANT_COLLECTION_NAME` | 可以展示 collection 名 |
| `MILVUS_TOKEN` | 只展示是否已配置 |

### 8. 密钥检查是什么

本节新增：

```python
build_secret_configuration_checks(settings)
```

它会返回一组检查结果：

```text
llm_api_key
embedding_api_key
rerank_api_key
qdrant_api_key
milvus_token
```

每个检查结果包含：

```text
name
configured
required
message
readiness_status
```

其中最关键的是：

```text
configured：有没有配置。
required：当前运行模式下是不是必须配置。
```

例如：

```text
TICKET_AGENT_MODEL_MODE="real_llm"
LLM_API_KEY=""
```

此时：

```text
llm_api_key.configured = false
llm_api_key.required = true
llm_api_key.readiness_status = not_configured
```

如果：

```text
TICKET_AGENT_MODEL_MODE="rule_based"
LLM_API_KEY=""
```

此时：

```text
llm_api_key.configured = false
llm_api_key.required = false
llm_api_key.readiness_status = skipped
```

这说明：

```text
不是所有缺失密钥都是错误，要看当前功能是否真的需要它。
```

### 9. `/ready` 怎么使用密钥检查

本节修改了：

```text
app/routers/health.py
```

之前 `/ready` 里直接写：

```text
如果 real_llm，检查 settings.has_llm_api_key。
否则跳过。
```

现在变成：

```text
先调用 build_secret_configuration_checks(settings)。
再取出 llm_api_key 的检查结果。
最后转换成 ReadinessCheck。
```

这样做好处是：

```text
密钥规则集中。
/ready 不需要知道每个密钥怎么判断。
以后扩展 embedding、rerank、向量库 token 时更自然。
测试也可以直接覆盖密钥规则。
```

### 10. 为什么本节没有把安全快照挂成接口

本节只是新增了安全快照函数，没有新增：

```text
GET /config
```

原因是：

```text
配置观察接口涉及权限控制。
当前还没有专门做内部管理端或管理员鉴权。
```

如果现在直接暴露接口，容易给你形成错误习惯：

```text
只要是安全快照就可以公开返回。
```

实际不是。

安全快照只是说明：

```text
它里面不应该有密钥。
```

但是否能通过接口返回，还要看：

```text
谁能访问这个接口。
是否仅限内部。
是否需要管理员权限。
是否会进入日志。
是否会被前端缓存。
```

所以本节先把安全构建逻辑打好，后续如果需要管理端或运行诊断接口，再在权限边界清楚后接入。

### 11. 和 Java Spring Boot 配置的对应关系

你有 Java 后端经验，所以可以这样对应：

Python `Settings` 类类似于 Spring Boot 里的：

```text
application.yml
@ConfigurationProperties
@Value
环境变量占位符
```

Java 里常见写法：

```yaml
spring:
  datasource:
    url: ${JAVA_DB_URL:jdbc:mysql://127.0.0.1:3306/ai_order}
    username: ${JAVA_DB_USERNAME:root}
    password: ${JAVA_DB_PASSWORD:root}
```

Python 里当前项目是：

```python
class Settings(BaseSettings):
    llm_api_key: str | None = Field(default=None, repr=False)
```

共同点：

```text
代码只定义配置名、默认值、类型和约束。
真实值由环境变量或本地配置文件注入。
```

不同点：

```text
Spring Boot 更常用 application.yml。
Python FastAPI 项目更常用 pydantic-settings + .env。
```

但原则完全一样：

```text
真实密钥不能写死。
真实密钥不能提交。
真实密钥不能随便日志化。
```

### 12. 当前项目配置链路

当前项目可以这样理解：

```text
.env.example
    |
    | 复制并填写
    v
.env
    |
    | pydantic-settings 读取
    v
Settings
    |
    | resolved_* 属性整理
    v
业务代码使用最终配置
```

本节新增后，多了一条安全观察链路：

```text
Settings
    |
    | build_safe_settings_snapshot
    v
安全配置快照
```

还有一条 readiness 链路：

```text
Settings
    |
    | build_secret_configuration_checks
    v
SecretConfigurationCheck
    |
    | /ready 转换
    v
ReadinessCheck
```

这两条链路的目的不同：

```text
安全快照：给排查和观测看。
密钥检查：给服务是否 ready 判断。
```

### 13. 本节和上一节的关系

上一节是：

```text
LLM 调用日志安全
```

重点是：

```text
模型调用过程中不要把 prompt、messages、用户输入、完整回答、API Key 打进日志。
```

这一节是：

```text
配置与密钥管理
```

重点是：

```text
配置读取、配置展示、密钥检查时不要泄露真实密钥。
```

两节合起来，你要形成一个整体判断：

```text
不只是业务数据不能乱打日志，系统配置和模型密钥也不能乱打日志。
```

### 14. 本节和后续课程的关系

后面会学：

```text
Token 成本统计
请求耗时拆解
多模型路由
fallback
限流
重试
超时
SSE 生产化
Prompt Injection 加固
权限强化
隐私保护
```

这些都会依赖配置。

比如：

```text
成本控制需要配置预算。
多模型路由需要配置模型列表。
fallback 需要配置备用模型。
限流需要配置阈值。
重试需要配置次数和退避。
超时需要配置时间预算。
SSE 需要配置心跳间隔。
评测需要配置评测集路径和模型开关。
```

所以配置管理是后续生产化能力的底座。

如果配置随便散落、密钥随便暴露，后面的能力就很难安全落地。

## 本节代码讲解

### 1. `SECRET_SETTING_NAMES`

新增文件：

```text
app/core/config_safety.py
```

里面定义了：

```python
SECRET_SETTING_NAMES = frozenset(
    {
        "llm_api_key",
        "openai_api_key",
        "embedding_api_key",
        "rerank_api_key",
        "qdrant_api_key",
        "milvus_token",
    }
)
```

这表示：

```text
这些字段名被认为是原始密钥字段。
```

为什么要集中定义？

因为安全规则不能散落。

如果以后新增：

```text
JAVA_INTERNAL_TOKEN
DATABASE_PASSWORD
```

也应该进入类似的密钥字段清单。

### 2. `SecretConfigurationCheck`

核心结构：

```python
@dataclass(frozen=True)
class SecretConfigurationCheck:
    name: str
    configured: bool
    required: bool
    message: str
```

它表达一个密钥检查结果。

字段含义：

```text
name：检查哪个密钥。
configured：有没有配置。
required：当前运行模式下是不是必须配置。
message：给人看的说明。
```

`frozen=True` 表示：

```text
创建后不希望被随便修改。
```

这适合检查结果这种值对象。

### 3. `readiness_status`

代码：

```python
@property
def readiness_status(self) -> SecretReadinessStatus:
    if not self.required:
        return "skipped"
    return "configured" if self.configured else "not_configured"
```

这段很关键。

它说明：

```text
如果当前不要求这个密钥，就返回 skipped。
如果当前要求，并且配置了，就返回 configured。
如果当前要求，但没配置，就返回 not_configured。
```

这比简单的 true / false 更准确。

因为“没配置”不一定是错误。

### 4. `build_safe_settings_snapshot`

这个函数负责构建安全快照。

它保留：

```text
app.name
app.version
llm.provider
llm.model
ticket_agent.model_mode
timeout
retry
collection_name
vector_size
是否配置 key
是否配置 base_url
```

它不保留：

```text
真实 API Key
真实 token
真实 secret
完整 Authorization
```

比如：

```python
"llm.api_key_configured": settings.has_llm_api_key
```

不是：

```python
"llm.api_key": settings.resolved_llm_api_key
```

这就是本节最核心的代码思想。

### 5. `_has_text`

代码：

```python
def _has_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())
```

它用于判断：

```text
某个配置值是不是非空字符串。
```

为什么不用简单的：

```python
bool(value)
```

因为：

```text
"   "
```

这种全是空格的字符串，`bool("   ")` 是 `True`。

但它不能算有效配置。

所以要先 `strip()`。

### 6. `build_secret_configuration_checks`

这个函数集中生成密钥检查。

其中 LLM key 的逻辑是：

```python
required=settings.ticket_agent_model_mode == "real_llm"
```

意思是：

```text
只有 real_llm 模式才强制要求 LLM key。
```

这对本项目很重要。

因为我们平时大量测试使用：

```text
rule_based
fake_llm
```

这些模式不应该强迫你配置真实模型 key。

### 7. `find_raw_secret_setting_names`

这个函数用于发现一个配置字典里是否出现原始密钥字段。

例如：

```python
find_raw_secret_setting_names(
    {
        "llm_api_key": "sk-test",
        "llm.api_key_configured": True,
    }
)
```

结果应该只报告：

```text
llm_api_key
```

不会报告：

```text
llm.api_key_configured
```

因为后者只是状态字段，不是真实密钥字段。

### 8. `/ready` 的改动

本节修改了：

```python
llm_secret_check = _get_secret_check("llm_api_key", settings)
```

然后把它转换为：

```python
ReadinessCheck(...)
```

这样 `/ready` 的语义仍然不变：

```text
real_llm 没有 key，返回 not_ready。
rule_based 不需要 key，返回 ready。
```

但内部结构更清楚：

```text
密钥规则在 config_safety.py。
健康检查接口只负责展示 readiness。
```

## 常见误区

### 误区 1：`.env.example` 里放一个真实 key 方便别人运行

这是非常危险的。

正确做法：

```text
.env.example 只放空值、示例值、占位符和说明。
真实 key 由每个人自己配置到 .env 或环境变量。
```

### 误区 2：`.env` 被 `.gitignore` 忽略了，就可以随便打印

不可以。

`.gitignore` 只能防止它被 Git 提交。

它防不住：

```text
日志泄露
截图泄露
报错泄露
复制粘贴泄露
终端历史泄露
```

### 误区 3：`repr=False` 等于绝对安全

不是。

`repr=False` 只是避免对象 repr 时显示字段。

但如果你写：

```python
settings.llm_api_key
settings.model_dump()
```

仍然可能拿到真实值。

所以还需要安全快照。

### 误区 4：缺少 API Key 一定是错误

不一定。

如果当前是：

```text
rule_based
fake_llm
```

没有真实 LLM API Key 是合理的。

只有当当前运行模式真的需要真实模型时，缺 key 才应该让 readiness 失败。

### 误区 5：只要不泄露 API Key，其他配置都能公开

也不一定。

生产环境内网地址、数据库地址、租户标识、内部服务名，有时也不适合公开。

所以安全快照里对一些地址只记录：

```text
xxx_configured
```

### 误区 6：把所有配置都写进 README 方便部署

README 可以写配置项说明。

不能写真实配置值。

尤其不能写：

```text
真实 API Key
真实数据库密码
真实生产 URL
真实内部 token
```

### 误区 7：测试里直接用真实 key 更接近真实环境

自动化测试不应该默认依赖真实 key。

真实 key 测试应该是：

```text
手动 smoke
明确开关
本地可选
不会进入 CI
不会打印 key
```

## 本节练习

### 练习 1：判断哪些能提交 GitHub

下面哪些内容可以提交 GitHub？

```text
1. LLM_MODEL="qwen3.7-plus"
2. LLM_API_KEY="真实 key"
3. LLM_API_KEY=""
4. REQUEST_TIMEOUT_SECONDS=30
5. MYSQL_PASSWORD="真实密码"
6. .env.example
7. .env
```

参考答案：

```text
可以提交：1、3、4、6。
不可以提交：2、5、7。
```

解释：

```text
模型名、超时配置、空 key 模板可以提交。
真实 key、真实密码、本机 .env 不能提交。
```

### 练习 2：为什么 `llm.api_key_configured=true` 比返回真实 key 安全

参考答案：

```text
因为它只说明 LLM API Key 已经配置，不暴露具体 key。
排查人员可以知道配置状态，但不能拿这个状态去调用模型平台。
```

### 练习 3：`real_llm` 模式下没有 key，`/ready` 应该返回什么

参考答案：

```text
应该返回 not_ready，并且 llm_api_key 检查项是 not_configured。
```

原因：

```text
real_llm 模式需要真实调用模型，没有 key 就无法完成核心功能。
```

### 练习 4：`rule_based` 模式下没有 key，`/ready` 应该失败吗

参考答案：

```text
不应该失败。
```

原因：

```text
rule_based 不需要真实调用模型，所以 LLM API Key 不是当前运行模式的必需项。
```

### 练习 5：为什么不要直接打印 `settings.model_dump()`

参考答案：

```text
因为 model_dump() 可能包含 llm_api_key、openai_api_key、embedding_api_key、rerank_api_key、qdrant_api_key、milvus_token 等真实字段值。
这些值一旦进入日志，就可能被日志系统、截图、告警或排查记录继续传播。
```

### 练习 6：如果以后要增加 `JAVA_INTERNAL_TOKEN`，应该怎么处理

参考答案：

```text
应该把它作为密钥字段管理。
配置读取时使用环境变量或 .env。
.env.example 只放空值或占位符。
安全快照只暴露 java_internal_token_configured。
日志和接口不能返回真实 token。
必要时把它加入密钥检查清单。
```

## 自测题

### 自测 1：配置和密钥最大的区别是什么

参考答案：

```text
配置决定系统怎么运行，密钥代表访问权限。
普通配置泄露通常只是暴露运行方式，密钥泄露可能导致别人直接调用外部服务、消耗额度或访问数据。
```

### 自测 2：`.env` 和 `.env.example` 的区别是什么

参考答案：

```text
.env 是本机真实配置文件，可以包含真实密钥，不能提交 GitHub。
.env.example 是配置模板，只能包含安全示例、空值和说明，可以提交 GitHub。
```

### 自测 3：为什么安全快照里使用 `api_key_configured`

参考答案：

```text
因为排查时经常只需要知道 key 是否存在，不需要知道 key 的具体内容。
configured 状态能满足排查需要，同时避免泄露访问权限。
```

### 自测 4：为什么不是所有缺失密钥都应该让服务启动失败

参考答案：

```text
因为不同运行模式需要的能力不同。
例如 rule_based 不调用真实模型，就不需要 LLM API Key。
只有当前运行模式真的依赖某个外部能力时，缺少对应密钥才应该阻塞 readiness。
```

### 自测 5：为什么 AI 应用的配置比普通 CRUD 项目更复杂

参考答案：

```text
AI 应用多了模型 provider、模型名、base_url、API Key、max_tokens、超时、重试、embedding、向量库、rerank、多模型路由、fallback、成本控制等配置。
这些配置会直接影响质量、成本、延迟、稳定性和安全性。
```

### 自测 6：如果日志中发现真实 API Key，第一反应应该是什么

参考答案：

```text
应该认为密钥已经泄露。
需要停止继续传播日志，尽快轮换密钥，检查日志系统和提交历史中是否还有残留，并修复导致泄露的日志代码。
```

## 本节小结

这一节要真正记住的是：

```text
配置不是随便放几个变量，配置是系统运行行为的一部分。
密钥不是普通字符串，密钥是访问权限。
```

当前项目通过：

```text
Settings
.env
.env.example
resolved_* 属性
build_safe_settings_snapshot()
build_secret_configuration_checks()
/ready 密钥检查
```

形成了一个更清晰的配置与密钥管理基础。

你以后做真实 AI 项目时，至少要能说明：

```text
真实密钥从哪里来。
哪些文件可以提交。
哪些字段不能进日志。
哪些配置能安全观察。
哪些密钥在什么模式下是必需的。
配置错误时系统如何明确失败。
```

这就是配置与密钥管理在生产化阶段的价值。
