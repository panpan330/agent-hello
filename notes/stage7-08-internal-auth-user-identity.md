# 阶段 7 第 8 节：AI 场景下的内部鉴权和用户身份传递

## 本节定位

上一节我们把 Java 服务改成了传统 Spring Boot + MyBatis 结构：

```text
controller -> service -> mapper -> MySQL
```

现在结构稳定了，可以继续补一个 AI 调 Java 后端时非常关键的问题：

```text
Java 后端怎么知道这次调用是谁发起的？
Java 后端怎么知道当前用户是谁？
Java 后端怎么知道当前租户是谁？
Java 后端能不能相信模型说“我是某某用户”？
```

这就是本节的主题：

```text
内部鉴权 + 用户身份传递。
```

本节不是做完整登录系统，也不是做 JWT、OAuth2、网关、单点登录。
本节先把当前 internal API 的基础边界补扎实：

```text
Python AI 服务必须带内部调用凭证。
Python AI 服务必须明确传递调用方、真实用户、租户和 trace_id。
Java 服务必须自己校验这些 header。
Java 服务不能把模型输出当成身份事实。
Java 服务进入业务逻辑前必须先构造可信的 InternalRequestContext。
```

## 本节学习目标

学完本节，你应该能讲清楚：

```text
什么是鉴权。
什么是认证。
什么是授权。
为什么 internal API 也需要鉴权。
为什么 AI Agent 场景里不能相信模型直接给出的 user_id。
X-Caller、X-User-Id、X-Tenant-Id、X-Trace-Id、X-Internal-Token 各自代表什么。
服务身份和用户身份有什么区别。
租户 tenant 是什么，为什么不能随便默认。
为什么 Java 后端要在 Service 前先解析 InternalRequestContext。
为什么错误 caller、缺少 tenant、不安全 user_id 都应该被拒绝。
为什么当前方案只是学习项目里的基础 internal token，不是生产级安全方案。
```

## 本节先不做什么

本节不做：

```text
不接入真实登录系统。
不设计 user 表和 role 表。
不做 JWT。
不做 OAuth2。
不做 Spring Security 完整体系。
不做网关鉴权。
不做 mTLS。
不做权限策略引擎。
不修改 Python AI 服务 client。
不修改 java-mock-service。
```

原因是：

```text
我们现在先学 AI 服务调用 Java internal API 的最小可信边界。
完整登录、权限、网关和生产级安全会比本节复杂很多，后面可以单独学习。
```

## 基础知识铺垫

### 1. 认证、鉴权、授权分别是什么

这几个词容易混。

认证，常说 authentication：

```text
确认“你是谁”。
```

例子：

```text
用户登录时输入账号密码。
服务之间调用时携带内部 token。
客户端携带 JWT。
```

鉴权这个中文词在实际项目里经常被混用。
有时它指认证，有时它指授权，有时它泛指安全检查。
本项目里说“内部鉴权”，主要指：

```text
Java 服务确认这次 internal API 调用确实来自允许的内部服务。
```

授权，常说 authorization：

```text
确认“你能不能做这件事”。
```

例子：

```text
U1001 能不能查看 A1001？
U1001 能不能查看 A2001？
当前用户能不能创建工单？
当前租户能不能访问这个订单？
```

在本项目里：

```text
X-Internal-Token + X-Caller 主要解决内部服务调用身份。
Order.visibleTo(...) 主要解决用户是否能看订单。
TicketServiceImpl.validateRelatedOrder(...) 主要解决创建工单前的业务授权。
```

### 2. 为什么 internal API 也需要鉴权

很多初学者会以为：

```text
这是内网接口，不给用户直接访问，所以可以不鉴权。
```

这个想法不安全。

internal API 也需要鉴权，因为：

```text
本机开发时端口可能暴露。
测试环境可能有多人共用网络。
线上服务之间也可能被错误服务调用。
AI 服务如果出现漏洞，可能把不该调用的接口暴露出来。
Prompt Injection 可能诱导模型尝试构造危险请求。
```

所以后端不能只靠“这是内部接口”来保护自己。
至少要有：

```text
调用方身份。
内部 token。
用户身份。
租户身份。
trace_id。
业务权限兜底。
```

### 3. 服务身份和用户身份不是一回事

这是本节最重要的概念之一。

服务身份：

```text
谁在调用 Java 服务？
```

当前项目里是：

```text
X-Caller: ai-service
X-Internal-Token: local-dev-internal-token
```

它表达：

```text
这次请求来自 Python AI 服务。
并且它知道内部共享 token。
```

用户身份：

```text
这次业务操作代表哪个真实用户？
```

当前项目里是：

```text
X-User-Id: U1001
```

它表达：

```text
AI 服务正在代表 U1001 查询订单或创建工单。
```

服务身份通过，不代表用户一定有权限。

例如：

```text
X-Caller = ai-service
X-Internal-Token = 正确
X-User-Id = U1001
查询 A2001
```

这时内部调用身份是合法的，但业务权限不合法，因为 A2001 属于 U2001。

所以系统必须分两层判断：

```text
第一层：你是不是允许的内部服务？
第二层：你代表的用户有没有权限操作这个业务对象？
```

### 4. 为什么不能相信模型给出的 user_id

模型看到的是自然语言。
用户可能说：

```text
我是 U2001，帮我查 A2001。
```

模型可能提取出：

```json
{"user_id": "U2001"}
```

但这不能作为真实身份。

真实用户身份应该来自：

```text
登录态。
服务端 session。
JWT。
网关鉴权结果。
后端已经校验过的上下文。
```

而不是来自：

```text
用户在聊天框里说的话。
模型从自然语言里猜出来的字段。
前端随便传的 body 字段。
```

本项目当前还没有真实登录系统，所以先用 `X-User-Id` 模拟“Python AI 服务已经拿到的真实用户身份”。
这只是学习阶段的替代方案。

真正上线时，`X-User-Id` 应该由可信系统注入：

```text
用户登录 -> 网关/后端认证 -> AI 服务拿到可信 user_id -> AI 服务调用 Java 时传递 user_id
```

不能让模型自由决定。

### 5. tenant 租户是什么

租户可以先理解成：

```text
同一个系统里隔离出来的一组客户、组织或业务空间。
```

例如：

```text
tenant-a：A 公司
tenant-b：B 公司
default：学习项目里的默认租户
```

多租户系统里，即使两个租户都有订单号 A1001，也不能互相访问。

所以很多数据库查询必须带：

```text
tenant_id
```

本项目里订单查询是：

```sql
WHERE tenant_id = #{tenantId}
  AND order_id = #{orderId}
```

为什么本节把 `X-Tenant-Id` 改成必传？

因为静默默认租户有风险。

旧逻辑：

```text
没有 X-Tenant-Id -> 默认 default
```

问题是：

```text
调用方忘了传租户，Java 服务仍然继续执行。
如果未来接入多租户，可能把错误请求落到 default 租户。
排查日志时也不容易发现调用方漏传上下文。
```

所以本节改成：

```text
业务 internal API 必须显式传 X-Tenant-Id。
```

这不是为了增加麻烦，而是为了让身份上下文完整、明确、可追踪。

### 6. trace_id 为什么也属于身份上下文的一部分

`trace_id` 不是权限字段。
它不决定谁能做什么。

但它属于调用上下文，因为它解决：

```text
这次请求从哪里来？
Python 日志、Java 日志、MySQL/Redis 操作怎么串起来？
出现错误后怎么排查？
```

AI Agent 系统通常有多步：

```text
用户发消息
Python 判断意图
Python 调模型
Python 调 RAG
Python 调 Java
Java 查 MySQL/Redis
Java 返回结果
Python 让模型总结
```

如果没有 trace_id，出错时很难知道哪一步坏了。

所以本节继续要求：

```text
X-Trace-Id 必传。
格式不能太随意。
```

### 7. 为什么 header 也要做格式校验

很多人会觉得：

```text
header 是内部服务传的，拿到就用。
```

但工程上更稳妥的做法是：

```text
进入业务逻辑前，先做格式约束。
```

本节对这些字段做基础格式校验：

```text
trace_id：8 到 128 位，只允许字母、数字、点、下划线、冒号、短横线。
caller：小写字母开头，只允许小写字母、数字和短横线。
user_id / tenant_id：1 到 64 位，只允许字母、数字、点、下划线、冒号、短横线。
```

这不是完整安全方案，但能挡住明显不该进入身份上下文的值，例如：

```text
U1001/../admin
<script>...</script>
tenant id with spaces
```

这些值即使不会直接造成漏洞，也会污染日志、缓存 key、限流 key 和排查上下文。

### 8. 为什么统一返回 INTERNAL_AUTH_FAILED

内部鉴权失败时，我们不细分给调用方太多原因：

```text
token 错了。
caller 错了。
user_id 格式不对。
tenant_id 缺失。
trace_id 格式不对。
```

都返回：

```text
INTERNAL_AUTH_FAILED
```

好处是：

```text
对外不暴露太多安全细节。
Python AI 服务只需要知道 internal 调用上下文不可信。
具体原因看 Java 日志和测试即可。
```

以后如果要做更细粒度监控，可以在内部日志里记录 sanitized reason。
但不应该把 token 错误、caller 错误等细节直接暴露给模型或用户。

## 本节主题系统讲解

### 1. 当前调用链路

本节后，请求进入 Java 业务服务时是这样：

```text
HTTP request
-> Controller
-> InternalRequestResolver.resolve(request)
-> 读取并校验 header
-> 构造 InternalRequestContext
-> ToolRateLimiter.check(...)
-> Service
-> Mapper
-> MySQL
```

关键点：

```text
Controller 不直接相信 header。
Controller 先交给 InternalRequestResolver。
Service 只接收已经解析好的 InternalRequestContext。
后续权限判断基于 InternalRequestContext，而不是重新从 request 里乱取 header。
```

这就是“统一入口解析上下文”。

### 2. `InternalRequestContext` 是什么

它是 Java 服务内部使用的可信上下文对象：

```java
public record InternalRequestContext(
        String traceId,
        String caller,
        String userId,
        String tenantId
) {
}
```

它的意义是：

```text
把 HTTP header 里的调用上下文转成 Java 内部对象。
让 Service 不需要关心 HttpServletRequest。
让业务层只面对已经校验过的 trace/user/tenant。
```

注意：

```text
InternalRequestContext 不是登录态。
它只是当前学习项目里 internal API 的上下文载体。
```

### 3. `InternalApiProperties` 为什么要加 `allowedCaller`

旧代码里 caller 是硬编码：

```java
private static final String EXPECTED_CALLER = "ai-service";
```

本节改成配置：

```java
@ConfigurationProperties(prefix = "app.internal")
public record InternalApiProperties(
        String token,
        String allowedCaller
) {
    public InternalApiProperties {
        if (allowedCaller == null || allowedCaller.isBlank()) {
            allowedCaller = "ai-service";
        }
    }
}
```

这样做的原因：

```text
配置属于部署环境差异。
代码属于业务规则。
不同环境可以允许不同 caller。
以后如果 AI 服务名变化，不需要改 Java 源码。
```

当前 `application.yml` 支持：

```yaml
app:
  internal:
    token: ${JAVA_BUSINESS_INTERNAL_TOKEN:local-dev-internal-token}
    allowed-caller: ${JAVA_BUSINESS_INTERNAL_ALLOWED_CALLER:ai-service}
```

### 4. `InternalRequestResolver` 本节改了什么

本节核心改动在这里。

旧逻辑大致是：

```text
读取 trace_id / caller / user_id / tenant_id / token。
tenant_id 没有就默认 default。
caller 固定等于 ai-service。
token 正确就通过。
```

新逻辑是：

```text
trace_id 必须存在且格式安全。
caller 必须存在且格式安全。
user_id 必须存在且格式安全。
tenant_id 必须存在且格式安全。
token 必须存在。
caller 必须等于配置里的 allowedCaller。
token 必须等于配置里的 token。
```

这让 internal 请求在进入业务层前更完整。

### 5. 为什么 `X-Tenant-Id` 不再默认 default

这是本节一个重要设计取舍。

旧逻辑方便：

```text
没传 X-Tenant-Id，也能查 default 租户。
```

但真实项目更需要明确：

```text
调用方必须知道自己代表哪个租户。
调用方漏传租户应该尽早失败。
失败比静默落到错误租户更安全。
```

所以本节改成必传。

本项目学习数据仍然是：

```text
X-Tenant-Id: default
```

区别只是：

```text
现在必须显式传。
```

### 6. 为什么 `ToolRateLimiter` 在解析上下文后执行

限流 key 需要这些信息：

```text
tenant_id
user_id
method
uri
```

如果 user_id 或 tenant_id 不可信，就不能拿它们拼 Redis 限流 key。

所以顺序是：

```text
先校验 header。
构造可信 InternalRequestContext。
再调用 ToolRateLimiter。
```

这也是为什么 header 格式校验不只是“好看”，它会影响 Redis key、日志字段和限流维度。

### 7. 本节和后续权限系统的关系

当前阶段没有真实 user 表和 role 表。
本节做的是：

```text
传递可信用户 ID。
传递可信租户 ID。
在订单和工单业务里用这些 ID 做边界判断。
```

后续如果接入真实权限系统，会继续演进成：

```text
用户登录
-> 网关或认证服务验证 token
-> Python AI 服务拿到可信 user_id / tenant_id / roles
-> Python 调 Java internal API
-> Java 再次校验 internal caller
-> Java 根据 user_id / tenant_id / roles 做业务授权
```

也就是说：

```text
本节不是终点。
本节是后续真实权限体系的接口边界基础。
```

## 本节代码讲解

### 1. `InternalApiProperties`

位置：

```text
projects/java-business-service/src/main/java/com/panpan/aibusinessservice/config/InternalApiProperties.java
```

本节把配置从只有 token：

```java
public record InternalApiProperties(String token) {
}
```

扩展成：

```java
public record InternalApiProperties(
        String token,
        String allowedCaller
) {
    public InternalApiProperties {
        if (allowedCaller == null || allowedCaller.isBlank()) {
            allowedCaller = "ai-service";
        }
    }
}
```

这里的学习重点：

```text
token 用来证明调用方知道内部凭证。
allowedCaller 用来限制调用方服务名。
默认 allowedCaller 是 ai-service，方便本地学习。
```

为什么 token 没有在代码里硬编码默认？

因为 token 是凭证。
凭证应该从配置或环境变量来。
当前学习项目的 `application.yml` 给了本地默认值，是为了本地跑通。
真实项目不应该把真实内部 token 写进仓库。

### 2. `InternalRequestResolver`

位置：

```text
projects/java-business-service/src/main/java/com/panpan/aibusinessservice/common/security/InternalRequestResolver.java
```

它现在有三类格式规则：

```java
private static final Pattern TRACE_ID_PATTERN = Pattern.compile("^[A-Za-z0-9._:-]{8,128}$");
private static final Pattern CALLER_PATTERN = Pattern.compile("^[a-z][a-z0-9-]{1,63}$");
private static final Pattern IDENTITY_PATTERN = Pattern.compile("^[A-Za-z0-9._:-]{1,64}$");
```

这三类规则分别对应：

```text
trace_id：链路追踪 ID。
caller：服务名。
user_id / tenant_id：业务身份维度。
```

为什么 caller 只允许小写开头？

因为服务名通常是稳定机器字段，例如：

```text
ai-service
ticket-agent
gateway
```

不应该出现空格、斜杠、中文、HTML、SQL 片段等。

为什么 user_id / tenant_id 允许大写？

因为当前学习数据是：

```text
U1001
default
```

真实项目可能也有大小写混合的用户 ID。

### 3. `resolve()` 的顺序

本节后的核心代码逻辑是：

```java
String traceId = requiredHeader(request, TraceHeaders.TRACE_ID, TRACE_ID_PATTERN);
String caller = requiredHeader(request, TraceHeaders.CALLER, CALLER_PATTERN);
String userId = requiredHeader(request, TraceHeaders.USER_ID, IDENTITY_PATTERN);
String tenantId = requiredHeader(request, TraceHeaders.TENANT_ID, IDENTITY_PATTERN);
String token = requiredHeader(request, TraceHeaders.INTERNAL_TOKEN);
```

先读并校验 header。

然后：

```java
if (!properties.allowedCaller().equals(caller)
        || properties.token() == null
        || !properties.token().equals(token)) {
    throw new BusinessException(BusinessErrorCode.INTERNAL_AUTH_FAILED);
}
```

这段表达：

```text
caller 不在允许范围：拒绝。
服务端没有配置 token：拒绝。
请求 token 不匹配：拒绝。
```

最后：

```java
InternalRequestContext context = new InternalRequestContext(traceId, caller, userId, tenantId);
toolRateLimiter.check(context, request.getMethod(), request.getRequestURI());
return context;
```

这说明：

```text
只有通过鉴权和格式校验的请求，才能进入限流和业务层。
```

### 4. 测试补了什么

本节补了三个关键测试：

```text
缺少 X-Tenant-Id 会被拒绝。
X-Caller 不是 ai-service 会被拒绝。
X-User-Id 带不安全字符会被拒绝。
```

它们验证的不是“业务查订单”，而是：

```text
请求有没有资格进入业务层。
```

测试不需要把所有非法字符都列一遍。
只要覆盖典型风险，就能保护本节规则不被后续改坏。

## 常见误区

### 1. “有 internal token 就够了”

不够。

internal token 只能说明：

```text
调用方知道一个内部凭证。
```

它不能说明：

```text
代表哪个用户。
属于哪个租户。
用户是否能操作这个订单。
```

### 2. “模型很聪明，可以判断用户是谁”

不行。

模型只能处理文本。
模型不能成为身份来源。

真实身份必须来自可信系统。

### 3. “tenant 默认 default 更方便”

学习早期方便。
但接近真实项目时，显式传更安全。

本节开始，internal 业务接口应该明确带：

```text
X-Tenant-Id: default
```

### 4. “权限校验只在 Python 做就行”

不行。

Python AI 服务可以做第一层工具调用控制。
但 Java 业务服务必须兜底。

因为 Java 服务才真正接触：

```text
MySQL
Redis
订单
工单
业务状态
写操作
```

## 本节练习

### 练习 1：区分服务身份和用户身份

问题：

```text
X-Caller 和 X-User-Id 分别代表什么？
```

参考答案：

```text
X-Caller 代表调用 Java 服务的内部服务，例如 ai-service。
X-User-Id 代表这次业务操作所代表的真实用户，例如 U1001。
服务身份合法不代表用户一定有业务权限。
```

### 练习 2：判断请求是否应该通过

请求：

```text
X-Caller: ai-service
X-Internal-Token: local-dev-internal-token
X-User-Id: U1001
X-Tenant-Id: default
查询 A2001
```

问题：

```text
这次请求应该是鉴权失败，还是业务权限失败？
```

参考答案：

```text
应该是业务权限失败。
内部调用身份是合法的，但 A2001 属于 U2001，不属于 U1001。
所以应该返回 ORDER_ACCESS_DENIED，而不是 INTERNAL_AUTH_FAILED。
```

### 练习 3：解释为什么 tenant 必传

问题：

```text
为什么本节不再让缺少 X-Tenant-Id 时自动使用 default？
```

参考答案：

```text
因为缺少 tenant 说明调用上下文不完整。
如果静默默认 default，未来多租户场景可能把请求落到错误租户，也会隐藏调用方漏传上下文的问题。
显式失败更利于安全和排查。
```

### 练习 4：解释模型不能传 user_id

问题：

```text
为什么不能让模型从用户聊天内容里提取 user_id 后直接传给 Java？
```

参考答案：

```text
因为用户聊天内容不是可信身份来源。
用户可以冒充别人，模型也可能提取错误。
真实 user_id 应该来自登录态、JWT、网关、session 或其他已认证上下文。
```

### 练习 5：解释格式校验的意义

问题：

```text
为什么 X-User-Id 带 U1001/../admin 这种值时要拒绝？
```

参考答案：

```text
因为 user_id 会进入日志、权限判断、Redis 限流 key 和业务上下文。
明显不安全的格式会污染系统上下文。
即使当前不会直接造成漏洞，也应该在边界入口拒绝。
```

## 自测题

### 自测 1：`INTERNAL_AUTH_FAILED` 和 `ORDER_ACCESS_DENIED` 有什么区别？

参考答案：

```text
INTERNAL_AUTH_FAILED 表示 internal 调用身份或上下文不可信，例如 token 错、caller 错、缺少 tenant。
ORDER_ACCESS_DENIED 表示 internal 调用身份可信，但当前用户没有权限访问某个业务对象。
```

### 自测 2：为什么 Java 后端还要做权限兜底？

参考答案：

```text
因为 Java 后端是真正执行业务读写的系统。
Python AI 服务、模型、前端都可能出错或被诱导。
Java 后端必须根据自己的数据库和业务规则再判断一遍。
```

### 自测 3：本节的 internal token 是生产级方案吗？

参考答案：

```text
不是。
它只是学习项目里的最小内部调用凭证。
生产系统通常还会结合网关、JWT、mTLS、服务注册、密钥轮换、审计日志、权限系统等。
```

### 自测 4：为什么 allowedCaller 要配置化？

参考答案：

```text
因为调用方服务名属于部署环境和系统拓扑的一部分。
配置化后，如果 ai-service 改名或不同环境服务名不同，不需要改 Java 源码。
```

### 自测 5：本节之后 Python AI 服务调用 Java 时必须带哪些 header？

参考答案：

```text
X-Trace-Id
X-Caller
X-User-Id
X-Tenant-Id
X-Internal-Token

如果是写接口，还必须带 Idempotency-Key。
```

## 本节总结

本节把 internal API 的身份边界从“能跑”推进到“更像真实项目”：

```text
X-Caller 从硬编码改为配置 allowedCaller。
X-Tenant-Id 改为必传。
trace_id / caller / user_id / tenant_id 加入基础格式校验。
错误 caller、缺租户、不安全 user_id 会在进入业务层前被拒绝。
```

现在 Java 服务的调用边界更清楚：

```text
Python AI 服务负责传递可信上下文。
模型不能决定真实身份。
Java 服务负责 internal 鉴权、上下文校验和业务权限兜底。
```

下一节进入：

```text
阶段 7 第 9 节：Java 错误码到 AI 用户回答
```

那一节会重点讲：

```text
Java 返回 ORDER_NOT_FOUND / ORDER_ACCESS_DENIED / INTERNAL_AUTH_FAILED / IDEMPOTENCY_KEY_CONFLICT 后，
Python AI 服务应该怎样把这些机器错误码变成用户能理解、又不泄露内部细节的回答。
```
