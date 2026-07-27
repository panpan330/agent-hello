# 阶段 7 第 7 节：Redis 幂等、缓存和限流

## 本节定位

第 5 节，我们把订单查询从内存数据推进到了真实 MySQL：

```text
GET /internal/orders/{order_id}
-> Java business service
-> MySQL orders
```

第 6 节，我们把创建工单写操作推进到了真实 MySQL：

```text
POST /internal/tickets
-> Java business service
-> MySQL tickets
-> MySQL ticket_events
```

第 7 节开始接 Redis：

```text
Redis 不负责保存长期业务事实。
Redis 负责让系统更快、更稳、更能抗重复请求和高频调用。
```

这一节真正要学的不是“Spring Boot 怎么连 Redis”这一句配置，而是：

```text
AI Agent 调用真实 Java 后端时，Redis 应该放在哪些位置？
哪些事情可以交给 Redis？
哪些事情绝不能只靠 Redis？
Redis 失败时业务应该怎么降级？
缓存、幂等、限流分别解决什么问题？
```

本节我们实现三件事：

```text
订单查询缓存
工单创建幂等缓存
内部工具接口限流
```

这三件事都和 AI Agent 很相关。

AI Agent 可能会重复查订单、重复尝试创建工单，也可能因为模型循环、重试策略或异常输入导致某个工具接口被高频调用。传统 Java 后端要能保护自己，不能把所有稳定性都押在模型“不会乱调”上。

---

## 一、本节学习目标

学完本节，你应该能讲清楚：

```text
Redis 是什么，它和 MySQL 的职责有什么区别。
为什么 Redis 适合做缓存、幂等加速和限流。
为什么 Redis 不能替代 MySQL 作为工单创建幂等的最终兜底。
什么是 TTL，为什么缓存 key 不能无限期存在。
什么是 read-through cache。
什么是缓存命中和缓存未命中。
什么是缓存穿透、缓存击穿、缓存雪崩。
为什么订单查询可以缓存，但缓存命中后仍然要做权限校验。
为什么幂等缓存只加速判断，最终还要依赖 MySQL unique index。
为什么限流适合用 Redis 计数器。
fixed window rate limit 是什么，有什么优缺点。
Redis 出故障时，缓存和限流分别应该怎么降级。
Spring Data Redis、Lettuce、StringRedisTemplate 分别是什么。
为什么 Redis key 要设计命名空间和业务维度。
为什么测试环境要默认关闭真实 Redis。
```

本节完成后，Java 服务新增这些真实能力：

```text
GET /internal/orders/{order_id} 会优先尝试 Redis 订单缓存。
缓存未命中时查询 MySQL，并把订单结果写回 Redis。
POST /internal/tickets 会优先尝试 Redis 幂等缓存。
幂等缓存命中时仍会回查 MySQL，避免 Redis 单独决定业务事实。
所有 internal 工具接口通过 Redis 计数器做基础限流。
Redis 不可用时，缓存降级为 MySQL 查询，限流降级为放行并记录 warning。
自动化测试不依赖虚拟机 Redis。
真实 smoke 已验证 Windows Java 服务可以连接 VMware Ubuntu Docker Redis。
```

---

## 二、本节先不做什么

本节不提前做：

```text
不做第 7.5 节传统目录结构重构。
不把 JdbcTemplate 切到 MyBatis。
不让 Redis 替代 MySQL 保存订单或工单。
不实现分布式锁。
不实现滑动窗口限流。
不实现令牌桶或漏桶限流。
不接入 Redisson。
不做 Redis Cluster。
不做 Redis Sentinel。
不把 Python AI 服务切换到 java-business-service。
不做完整登录态或用户权限系统。
```

原因是本节的目标非常明确：

```text
先学会 Redis 在 AI 调 Java 业务系统里的三个最常见落点：
缓存、幂等加速、限流。
```

等第 7.5 节完成传统结构 + MyBatis 重构后，再继续做后续 internal 鉴权、用户身份传递、错误码映射、trace 串联和 Python 对接，会更符合你熟悉的 Java 后端项目结构。

---

## 三、基础知识铺垫

### 1. Redis 是什么

Redis 可以先理解成：

```text
一个很快的内存型 key-value 数据库。
```

key-value 的意思是：

```text
key   -> value
名字  -> 内容
```

例如：

```text
java-business:order:default:A1001
-> {"order_id":"A1001","order_status":"shipped",...}
```

它不像 MySQL 那样以表、行、列为主要组织形式。

MySQL 更像：

```text
长期业务事实仓库
```

Redis 更像：

```text
高速临时状态层
```

Redis 的典型特点：

```text
读写快。
适合保存短期数据。
适合做计数。
适合做缓存。
适合保存带过期时间的数据。
数据结构丰富。
可以让多个服务共享同一份临时状态。
```

本节我们主要用 Redis 的最基础能力：

```text
字符串 key-value
TTL 过期时间
INCR 原子自增
```

### 2. Redis 和 MySQL 的职责区别

你可以这样区分：

```text
MySQL 保存事实。
Redis 保存加速状态。
```

订单、工单、工单事件属于业务事实：

```text
订单是否存在。
工单是否创建。
工单是谁创建的。
工单关联哪个订单。
工单事件历史是什么。
```

这些必须放 MySQL。

缓存、短期计数、短期幂等索引属于加速状态：

```text
这个订单最近查过吗？
这个幂等键最近创建过哪个工单？
这个用户一分钟内调用了多少次工具？
```

这些适合放 Redis。

如果 Redis 丢了，业务数据不应该丢。

如果 Redis 挂了，Java 服务应该尽量还能靠 MySQL 完成核心读写。

这是本节最重要的原则之一：

```text
Redis 可以提高性能和稳定性，但不能成为本节业务正确性的唯一来源。
```

### 3. 什么是缓存

缓存就是：

```text
把经常读取、变化不那么频繁的数据，临时放到更快的地方。
```

订单查询是典型读操作。

如果每次 Agent 都问：

```text
帮我查一下订单 A1001
```

Java 服务每次都查 MySQL，当然能工作。

但如果某个用户连续追问：

```text
这个订单发货了吗？
物流到哪了？
可以创建工单吗？
再帮我确认一下订单状态。
```

这些问题可能都会触发同一个订单查询工具。

这时订单数据可以缓存几分钟：

```text
第一次查询：
Redis 未命中 -> 查 MySQL -> 写入 Redis -> 返回

第二次查询：
Redis 命中 -> 直接返回缓存 -> 不查 MySQL
```

这叫 read-through cache：

```text
应用先读缓存。
缓存没有时读数据库。
读到数据库后把结果写回缓存。
```

### 4. 什么是缓存命中和缓存未命中

缓存命中：

```text
Redis 里有这个 key。
Java 直接拿到 value。
不需要查 MySQL。
```

缓存未命中：

```text
Redis 里没有这个 key。
Java 继续查 MySQL。
MySQL 查到后再写回 Redis。
```

本节订单查询链路就是：

```text
OrderQueryService
-> OrderCache.get(...)
-> RedisOrderCache
-> 命中则返回 Order
-> 未命中则 OrderRepository.findByTenantIdAndOrderId(...)
-> JdbcOrderRepository
-> MySQL orders
-> OrderCache.put(...)
```

### 5. 什么是 TTL

TTL 是 Time To Live。

可以理解成：

```text
这个 key 在 Redis 里最多活多久。
```

例如本节订单缓存默认：

```text
300 秒
```

意思是：

```text
订单缓存最多保留 5 分钟。
5 分钟后 Redis 自动删除这个 key。
下一次查询重新查 MySQL。
```

为什么要 TTL？

因为缓存里的数据可能过期。

订单状态会变化：

```text
waiting_shipment -> shipped -> delivered
```

如果订单缓存永不过期，用户可能一直看到旧状态。

TTL 是一种简单的缓存一致性折中：

```text
短 TTL：数据更新更及时，但 MySQL 压力更大。
长 TTL：MySQL 压力更小，但用户可能看到旧数据更久。
```

本节默认 300 秒，是学习项目里比较保守的选择。

### 6. 缓存一致性是什么

缓存一致性指的是：

```text
缓存里的数据和数据库里的数据是否一致。
```

严格一致很难。

如果订单状态刚在 MySQL 改了，但 Redis 里还缓存着旧订单，就会出现短暂不一致。

真实项目常见做法：

```text
读多写少数据可以用 TTL 自然过期。
写操作成功后主动删除相关缓存。
高一致性场景不缓存，或使用更严格的失效策略。
```

本节订单查询暂时没有做订单更新接口，所以采用：

```text
read-through + TTL
```

后续如果增加订单状态修改，就应该在修改成功后删除对应订单缓存。

### 7. 缓存穿透、击穿、雪崩

这三个词面试里经常问，先建立基础概念。

缓存穿透：

```text
大量请求查询根本不存在的数据。
Redis 没有。
MySQL 也没有。
每次都打到 MySQL。
```

例子：

```text
不断查询不存在的订单 X999999。
```

常见解决：

```text
参数校验。
缓存空结果短 TTL。
布隆过滤器。
限流。
```

本节已有订单号格式校验：

```text
^[A-Za-z0-9_-]{1,64}$
```

但还没有缓存空结果，这是后续可扩展点。

缓存击穿：

```text
某个热点 key 过期的一瞬间，大量请求同时打到 MySQL。
```

例子：

```text
很多人同时查询订单 A1001。
刚好 Redis key 过期。
所有请求都查 MySQL。
```

常见解决：

```text
互斥锁。
热点 key 永不过期加后台刷新。
请求合并。
```

本节不做复杂击穿保护。

缓存雪崩：

```text
大量 key 同时过期，或 Redis 整体不可用，导致请求集中打到 MySQL。
```

常见解决：

```text
TTL 加随机抖动。
Redis 高可用。
限流。
熔断降级。
缓存预热。
```

本节先掌握基础缓存链路，后续再深入复杂保护策略。

### 8. 什么是幂等

第 6 节已经学过幂等。

这里再用 Redis 角度补充：

```text
幂等不是“不执行”。
幂等是“同一个业务请求重复提交，最终业务结果保持一致”。
```

创建工单的幂等要求：

```text
同一个 tenant_id + idempotency_key + 相同 request_fingerprint
-> 返回同一张工单

同一个 tenant_id + idempotency_key + 不同 request_fingerprint
-> 返回 IDEMPOTENCY_KEY_CONFLICT
```

第 6 节最终兜底在 MySQL：

```sql
UNIQUE KEY uk_tickets_tenant_idempotency (tenant_id, idempotency_key)
```

第 7 节新增 Redis 只是为了更快：

```text
先看 Redis 是否记得这个幂等键对应哪个 ticket_id。
如果记得，回查 MySQL 并返回。
如果不记得，继续走 MySQL 幂等逻辑。
```

这句话非常关键：

```text
Redis 幂等缓存不是最终裁判。
MySQL 唯一索引才是最终裁判。
```

### 9. 为什么幂等缓存命中后还要查 MySQL

假设 Redis 有：

```text
java-business:ticket-idempotency:default:key-001
-> {"request_fingerprint":"abc","ticket_id":"T-001"}
```

能不能直接返回 `T-001`？

不建议。

原因是：

```text
Redis 里的数据可能是旧的。
Redis 里的数据可能是事务提交前写进去的。
Redis 可能发生过恢复或人为写入。
Redis 只保存 ticket_id，不保存完整业务事实。
```

所以本节做法是：

```text
Redis 命中
-> 比对 request_fingerprint
-> fingerprint 一致
-> 用 ticket_id 回查 MySQL
-> MySQL 查到工单才返回
```

如果 Redis 命中了但 MySQL 查不到：

```text
说明 Redis 缓存不可信。
忽略缓存。
继续走 MySQL 幂等查询和创建逻辑。
```

如果 Redis 命中且 fingerprint 不一致，也不能马上只靠 Redis 判冲突。

本节会先确认 Redis 里指向的 ticket_id 在 MySQL 真实存在：

```text
缓存指向的 ticket_id 在 MySQL 存在 -> 说明确实有旧请求 -> 冲突
缓存指向的 ticket_id 在 MySQL 不存在 -> 缓存可能是脏的 -> 忽略缓存，回到 MySQL
```

这样才能避免 Redis 脏数据误伤真实业务请求。

### 10. 什么是限流

限流就是：

```text
限制某个调用方在一段时间内最多能调用多少次接口。
```

本节限制的是 internal 工具接口调用。

维度是：

```text
tenant_id
user_id
HTTP method
URI
时间窗口
```

例如：

```text
同一个 tenant、同一个 user，一分钟内最多调用 GET /internal/orders/A1001 60 次。
```

限流保护的是：

```text
Java 服务本身。
MySQL。
Redis。
被工具接口包住的真实业务能力。
```

在 AI Agent 场景下，限流特别重要。

因为调用方不再只是前端按钮，也可能是：

```text
模型工具循环。
Python retry。
用户异常输入导致的重复推理。
自动化脚本。
```

### 11. fixed window rate limit 是什么

本节用的是固定窗口计数。

逻辑是：

```text
第一次请求：
INCR key -> 1
给 key 设置 TTL 60 秒

第二次请求：
INCR key -> 2

...

超过 limit：
返回 429 TOOL_RATE_LIMITED
```

Redis key 类似：

```text
java-business:rate-limit:default:U1001:GET:%2Finternal%2Forders%2FA1001
```

固定窗口的优点：

```text
简单。
性能好。
容易理解。
Redis INCR 是原子操作。
适合学习和基础保护。
```

固定窗口的缺点：

```text
窗口边界可能有突刺。
比如第 59 秒打满一次，第 61 秒又打满一次，短时间内实际请求会偏多。
```

后续更高级可以学：

```text
滑动窗口。
令牌桶。
漏桶。
分布式限流组件。
网关层限流。
```

### 12. Redis INCR 为什么适合限流

Redis 是单线程执行命令模型为主。

对同一个 key 执行：

```text
INCR key
```

它是原子的。

可以简单理解为：

```text
不会两个请求同时把 1 加成 2 时互相覆盖。
```

所以它适合做计数器：

```text
java-business:rate-limit:default:U1001:GET:%2Finternal%2Forders%2FA1001 -> 3
```

再配合 TTL：

```text
60 秒后自动删除。
下一轮重新计数。
```

### 13. 什么是降级

降级就是：

```text
依赖组件出问题时，系统不一定完全失败，而是退回到能力较弱但还能工作的模式。
```

本节 Redis 失败时：

订单缓存读失败：

```text
记录 warning。
返回 Optional.empty。
继续查 MySQL。
```

订单缓存写失败：

```text
记录 warning。
不影响本次订单查询返回。
```

工单幂等缓存读失败：

```text
记录 warning。
继续查 MySQL 幂等记录。
```

工单幂等缓存写失败：

```text
记录 warning。
不影响 MySQL 创建结果。
```

限流 Redis 失败：

```text
记录 warning。
放行请求。
```

为什么限流失败时放行？

这是本节的教学取舍。

在内部学习项目里，我们优先保证：

```text
Redis 临时不可用时，核心业务读写还能靠 MySQL 跑通。
```

生产环境可能会按业务风险选择：

```text
fail open：限流失败就放行。
fail closed：限流失败就拒绝。
```

读工具一般更偏 fail open。

高风险写工具可能更偏 fail closed 或进入人工审核。

本节的创建工单仍有 MySQL 幂等和业务校验兜底，所以 Redis 限流失败时暂时放行。

### 14. Spring Data Redis 是什么

Spring Data Redis 是 Spring 官方生态里访问 Redis 的封装。

它帮我们处理：

```text
Redis 连接。
RedisTemplate。
StringRedisTemplate。
序列化。
连接池与客户端集成。
Spring Boot 自动配置。
```

本节新增依赖：

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-redis</artifactId>
</dependency>
```

Spring Boot 默认使用 Lettuce 作为 Redis 客户端。

### 15. Lettuce 是什么

Lettuce 是 Java Redis 客户端。

你可以把它理解为：

```text
Java 程序真正和 Redis 服务器通信的底层客户端。
```

我们平时在业务代码里不直接操作 Lettuce。

本节代码使用：

```java
StringRedisTemplate
```

Spring Boot 会在底层帮我们接好 Lettuce。

### 16. StringRedisTemplate 是什么

`StringRedisTemplate` 是 Spring 提供的 Redis 操作工具。

它适合：

```text
key 是字符串。
value 也是字符串。
```

本节订单缓存和幂等缓存都是：

```text
Java 对象 -> JSON 字符串 -> Redis
Redis -> JSON 字符串 -> Java 对象
```

限流是：

```text
Redis 字符串数字 -> INCR
```

所以 `StringRedisTemplate` 足够。

---

## 四、本节主题系统讲解

### 1. 本节完成后的整体链路

本节完成后，Java business service 的读写保护层变成：

```text
Python AI Service / Agent
-> Java internal API
-> InternalRequestResolver
-> RedisToolRateLimiter
-> Application Service
-> Redis cache/idempotency cache
-> MySQL repository
-> ApiResponse
```

注意顺序：

```text
先鉴权。
再限流。
再进业务 Service。
```

原因是：

```text
没有通过 internal token 的请求，不应该占用正常用户限流额度。
已经通过 internal token 的请求，才进入工具调用保护。
```

### 2. 订单缓存链路

订单查询现在是：

```text
OrderQueryService.queryOrder
-> 校验 order_id 格式
-> OrderCache.get(tenant_id, order_id)
-> 如果 Redis 命中，得到 Order
-> 如果 Redis 未命中，查 OrderRepository
-> JdbcOrderRepository 查 MySQL orders
-> OrderCache.put(order)
-> 再做 visibleTo 权限判断
-> 返回 OrderToolView
```

为什么缓存命中后还要做权限判断？

因为缓存里保存的是订单对象，不是“这个用户已经被授权”的结论。

同一个订单缓存可能被不同用户触发读取。

所以正确边界是：

```text
缓存只缓存业务数据。
权限判断每次请求都要重新做。
```

本节没有把权限结果缓存起来。

这是对的。

因为权限结果通常比订单数据更敏感，不能随便复用。

### 3. 订单缓存 key 设计

本节订单缓存 key：

```text
java-business:order:{tenant_id}:{order_id}
```

真实 smoke 里看到：

```text
java-business:order:default:A1001
```

这个 key 里包含：

```text
java-business：项目命名空间
order：业务类别
default：租户
A1001：订单号
```

为什么要有命名空间？

因为同一个 Redis 可能放很多项目的 key。

如果不用前缀，容易冲突：

```text
order:A1001
```

可能另一个系统也这么命名。

所以本节用：

```text
app.redis.key-prefix
```

默认值：

```text
java-business
```

### 4. 为什么 Redis key 要 URL encode

本节 `RedisKeys` 会对 key 片段做 `URLEncoder.encode`。

原因是：

```text
tenant_id、user_id、uri 等字段可能包含斜杠、空格、问号等特殊字符。
```

例如 URI：

```text
/internal/orders/A1001
```

如果直接放进 key：

```text
java-business:rate-limit:default:U1001:GET:/internal/orders/A1001
```

也能用，但可读性和解析边界会变差。

URL encode 后：

```text
%2Finternal%2Forders%2FA1001
```

变成：

```text
java-business:rate-limit:default:U1001:GET:%2Finternal%2Forders%2FA1001
```

这样 key 的每段边界更清楚。

### 5. 工单幂等缓存链路

第 6 节原来的工单幂等链路：

```text
计算 request_fingerprint
-> 查 MySQL tenant_id + idempotency_key
-> 有记录则比对 fingerprint
-> 无记录则插入 tickets 和 ticket_events
-> DuplicateKeyException 时回查 MySQL 兜底
```

第 7 节新增 Redis 后：

```text
计算 request_fingerprint
-> 查 Redis 幂等缓存
-> Redis 命中则回查 MySQL ticket_id
-> MySQL 查到且 fingerprint 一致则返回已有工单
-> Redis 未命中或不可信则继续查 MySQL
-> MySQL 有记录则写回 Redis 并返回
-> MySQL 无记录则插入 tickets 和 ticket_events
-> 插入成功后写 Redis 幂等缓存
-> DuplicateKeyException 时仍然回查 MySQL
```

你要抓住一句话：

```text
Redis 让“重复请求”更快返回。
MySQL 保证“重复请求”不会写出多条数据。
```

### 6. 工单幂等缓存保存什么

本节 Redis 幂等缓存保存：

```json
{
  "request_fingerprint": "8a78a08f8a527d423ea656b3cb69c0393989d0a1514f1523b27732cef9c30ee7",
  "ticket_id": "T-c19da543-6b20-4607-83bd-1421971f4d84"
}
```

key 是：

```text
java-business:ticket-idempotency:{tenant_id}:{idempotency_key}
```

真实 smoke 里看到：

```text
java-business:ticket-idempotency:default:stage7-redis-smoke-20260727-001
```

为什么不把完整工单都存进去？

可以存，但本节没有这么做。

原因是：

```text
幂等缓存的目标不是替代数据库返回完整业务事实。
它只需要帮助我们快速找到“这个幂等键对应哪个 ticket_id 和 fingerprint”。
最终返回前仍然回查 MySQL。
```

这能保持边界清晰。

### 7. Redis 脏幂等缓存怎么处理

本节专门处理了 Redis 脏缓存风险。

如果 Redis 里有记录，但 MySQL 查不到对应 ticket：

```text
忽略 Redis。
继续走 MySQL 幂等查询和创建逻辑。
```

如果 Redis 里 fingerprint 不一致，但它指向的 ticket_id 在 MySQL 不存在：

```text
也忽略 Redis。
不能只靠 Redis 判定冲突。
```

只有当 Redis 指向的 ticket_id 在 MySQL 存在，且 fingerprint 不一致时：

```text
返回 IDEMPOTENCY_KEY_CONFLICT。
```

这体现了：

```text
缓存永远不能比数据库更有话语权。
```

### 8. 限流链路

本节把限流放在 `InternalRequestResolver` 里。

完整步骤：

```text
读取 X-Trace-Id
读取 X-Caller
读取 X-User-Id
读取 X-Tenant-Id
读取 X-Internal-Token
校验 caller 和 token
创建 InternalRequestContext
调用 ToolRateLimiter.check(...)
返回 context 给 Controller
```

限流 key：

```text
java-business:rate-limit:{tenant_id}:{user_id}:{method}:{uri}
```

真实 smoke 里看到：

```text
java-business:rate-limit:default:U1001:GET:%2Finternal%2Forders%2FA1001
java-business:rate-limit:default:U1001:POST:%2Finternal%2Ftickets
```

这说明 GET 订单工具和 POST 工单工具是分开计数的。

### 9. 为什么限流放在 Java 服务里

可能你会问：

```text
Python AI 服务不是也可以限流吗？
为什么 Java 还要限流？
```

答案是：

```text
可以都做。
但 Java 不能完全相信上游一定做了。
```

AI 项目的链路是多层的：

```text
用户
-> Python AI 服务
-> Java 业务服务
-> MySQL/Redis
```

Python 可以做：

```text
用户级限流。
模型调用限流。
会话限流。
Agent 工具调用次数限制。
```

Java 也应该做：

```text
内部 API 保护。
业务资源保护。
租户/用户维度工具调用保护。
```

这叫多层防护。

不要让某一层成为唯一防线。

### 10. 为什么测试环境默认关闭真实 Redis

本节测试配置：

```yaml
app:
  redis:
    enabled: false
```

这样 `mvn test` 不需要 VMware Redis 运行。

原因是：

```text
自动化测试应该稳定。
不能因为虚拟机没开、Docker 没启动、Redis 端口不通，就导致所有单元测试失败。
```

测试环境关闭 Redis 后，Spring 会启用：

```text
NoOpOrderCache
NoOpTicketIdempotencyCache
NoOpToolRateLimiter
```

NoOp 的意思是：

```text
什么都不做。
```

这样测试仍然会走：

```text
H2
JdbcOrderRepository
JdbcTicketRepository
业务校验
MySQL 兼容 schema
```

核心业务逻辑照样验证。

真实 Redis 通过 smoke 单独验证。

### 11. 为什么用 ConditionalOnProperty

本节很多类上有：

```java
@ConditionalOnProperty(name = "app.redis.enabled", havingValue = "true")
```

或者：

```java
@ConditionalOnProperty(name = "app.redis.enabled", havingValue = "false")
```

它的意思是：

```text
根据配置决定创建哪个 Bean。
```

Redis 开启：

```text
RedisOrderCache
RedisTicketIdempotencyCache
RedisToolRateLimiter
```

Redis 关闭：

```text
NoOpOrderCache
NoOpTicketIdempotencyCache
NoOpToolRateLimiter
```

好处是：

```text
业务 Service 不需要到处写 if redisEnabled。
Service 只依赖接口。
具体实现由 Spring 根据配置选择。
```

这就是面向接口编程。

### 12. 本节配置项

主配置里新增：

```yaml
spring:
  data:
    redis:
      host: ${JAVA_BUSINESS_REDIS_HOST:192.168.88.10}
      port: ${JAVA_BUSINESS_REDIS_PORT:6379}
      timeout: 2s

app:
  redis:
    enabled: ${JAVA_BUSINESS_REDIS_ENABLED:true}
    key-prefix: ${JAVA_BUSINESS_REDIS_KEY_PREFIX:java-business}
    order-cache-ttl-seconds: ${JAVA_BUSINESS_ORDER_CACHE_TTL_SECONDS:300}
    ticket-idempotency-ttl-seconds: ${JAVA_BUSINESS_TICKET_IDEMPOTENCY_TTL_SECONDS:86400}
    rate-limit:
      enabled: ${JAVA_BUSINESS_RATE_LIMIT_ENABLED:true}
      limit: ${JAVA_BUSINESS_RATE_LIMIT_LIMIT:60}
      window-seconds: ${JAVA_BUSINESS_RATE_LIMIT_WINDOW_SECONDS:60}
```

这里有两个层次：

```text
spring.data.redis：告诉 Spring Boot 怎么连接 Redis。
app.redis：告诉我们自己的业务功能怎么使用 Redis。
```

不要混在一起。

连接配置归 Spring。

业务策略归 app。

### 13. 为什么 Redis 默认 host 是 192.168.88.10

你的 Redis 跑在 VMware Ubuntu Docker 里。

你之前验证过：

```text
Windows -> 192.168.88.10:6379 -> TcpTestSucceeded = True
```

所以本节 Java 服务默认连：

```text
192.168.88.10:6379
```

如果后面 IP 变了，可以临时覆盖：

```powershell
$env:JAVA_BUSINESS_REDIS_HOST = "新的虚拟机 IP"
```

或者启动时指定：

```powershell
$env:JAVA_BUSINESS_REDIS_ENABLED = "true"
```

如果没开虚拟机，想先跑 Java 服务基础功能，可以关闭 Redis：

```powershell
$env:JAVA_BUSINESS_REDIS_ENABLED = "false"
```

---

## 五、本节代码变更讲解

### 1. 新增 Redis 依赖

文件：

```text
projects/java-business-service/pom.xml
```

新增：

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-redis</artifactId>
</dependency>
```

这让项目具备：

```text
Redis 自动配置。
StringRedisTemplate。
Lettuce Redis 客户端。
```

你不用手动 new Redis 连接。

Spring Boot 会根据 `spring.data.redis.*` 创建连接相关 Bean。

### 2. `RedisFeatureProperties`

文件：

```text
projects/java-business-service/src/main/java/com/panpan/aibusinessservice/common/redis/RedisFeatureProperties.java
```

它负责读取：

```text
app.redis.enabled
app.redis.key-prefix
app.redis.order-cache-ttl-seconds
app.redis.ticket-idempotency-ttl-seconds
app.redis.rate-limit.enabled
app.redis.rate-limit.limit
app.redis.rate-limit.window-seconds
```

这类配置不要散落在业务代码里。

集中配置类的好处是：

```text
字段名清楚。
默认值集中。
业务代码不直接读环境变量。
测试可以方便构造配置对象。
```

### 3. `RedisKeys`

文件：

```text
projects/java-business-service/src/main/java/com/panpan/aibusinessservice/common/redis/RedisKeys.java
```

它统一生成 Redis key：

```text
orderCacheKey
ticketIdempotencyKey
rateLimitKey
```

为什么要专门写一个类？

因为 Redis key 是一种隐形契约。

如果每个地方手写：

```text
"java-business:order:" + tenantId + ":" + orderId
```

很容易出现：

```text
前缀不一致。
顺序不一致。
漏掉 tenant_id。
特殊字符没有处理。
```

统一 key 生成能减少这类问题。

### 4. `OrderCache`

文件：

```text
projects/java-business-service/src/main/java/com/panpan/aibusinessservice/infrastructure/cache/OrderCache.java
```

接口很小：

```java
Optional<Order> get(String tenantId, String orderId);

void put(Order order);
```

为什么只做这两个方法？

因为本节订单场景只需要：

```text
读缓存。
写缓存。
```

不提前做删除、批量、刷新、预热。

这是合理的最小实现。

后续如果有订单更新，再补：

```text
evict(tenantId, orderId)
```

### 5. `RedisOrderCache`

文件：

```text
projects/java-business-service/src/main/java/com/panpan/aibusinessservice/infrastructure/cache/RedisOrderCache.java
```

它做三件事：

```text
根据 tenant_id + order_id 生成 key。
把 Order 转成 JSON 写入 Redis。
从 Redis 读取 JSON 并还原成 Order。
```

写入时带 TTL：

```text
Duration.ofSeconds(properties.orderCacheTtlSeconds())
```

异常处理：

```text
读失败 -> 返回 Optional.empty
写失败 -> 记录 warning，不影响主流程
```

为什么不抛异常？

因为订单缓存只是加速层。

Redis 挂了，订单查询还能查 MySQL。

### 6. `NoOpOrderCache`

文件：

```text
projects/java-business-service/src/main/java/com/panpan/aibusinessservice/infrastructure/cache/NoOpOrderCache.java
```

它在 Redis 关闭时生效。

行为是：

```text
get 永远返回 empty。
put 什么都不做。
```

这让业务代码不用关心 Redis 是否开启。

`OrderQueryService` 只依赖：

```text
OrderCache
```

具体是 Redis 还是 NoOp，由 Spring 配置决定。

### 7. `OrderQueryService` 接入缓存

文件：

```text
projects/java-business-service/src/main/java/com/panpan/aibusinessservice/application/service/OrderQueryService.java
```

核心逻辑变成：

```text
先查 OrderCache。
缓存没有再查 OrderRepository。
查到 MySQL 后写入 OrderCache。
再做权限判断。
```

你要重点理解的是：

```text
缓存没有改变业务规则。
缓存只改变数据读取路径。
```

无论缓存命中还是 MySQL 命中，最后都要：

```text
order.visibleTo(context.userId(), context.tenantId())
```

### 8. `TicketIdempotencyCache`

文件：

```text
projects/java-business-service/src/main/java/com/panpan/aibusinessservice/infrastructure/cache/TicketIdempotencyCache.java
```

接口：

```java
Optional<TicketIdempotencyCacheEntry> get(String tenantId, String idempotencyKey);

void put(String tenantId, String idempotencyKey, TicketIdempotencyCacheEntry entry);
```

它只服务于创建工单幂等判断。

注意它保存的不是完整工单。

它保存的是：

```text
request_fingerprint
ticket_id
```

### 9. `TicketIdempotencyCacheEntry`

文件：

```text
projects/java-business-service/src/main/java/com/panpan/aibusinessservice/infrastructure/cache/TicketIdempotencyCacheEntry.java
```

它是一个 record：

```java
public record TicketIdempotencyCacheEntry(
        String requestFingerprint,
        String ticketId
) {
}
```

这两个字段的含义：

```text
requestFingerprint：证明这个幂等键对应的是哪个请求内容。
ticketId：指向 MySQL 里真正的工单。
```

### 10. `RedisTicketIdempotencyCache`

文件：

```text
projects/java-business-service/src/main/java/com/panpan/aibusinessservice/infrastructure/cache/RedisTicketIdempotencyCache.java
```

它的读写方式和订单缓存类似：

```text
entry -> JSON -> Redis
Redis -> JSON -> entry
```

TTL 默认：

```text
86400 秒
```

也就是 1 天。

为什么幂等缓存 TTL 比订单缓存长？

因为：

```text
订单状态变化可能较快，所以订单缓存短。
幂等键用于防重复创建，通常希望能覆盖更长的重试窗口。
```

但最终历史仍然在 MySQL。

Redis 幂等 key 过期后，如果同一个幂等键再次提交，MySQL 仍然能通过 unique index 和 request_fingerprint 兜底。

### 11. `JdbcTicketRepository` 接入幂等缓存

文件：

```text
projects/java-business-service/src/main/java/com/panpan/aibusinessservice/infrastructure/persistence/JdbcTicketRepository.java
```

新增逻辑主要是：

```text
计算 fingerprint 后先查 TicketIdempotencyCache。
缓存可信时快速返回。
缓存没有或不可信时回到 MySQL。
MySQL 查到已有记录时把幂等结果写回 Redis。
新工单创建成功后把幂等结果写入 Redis。
```

这段代码的学习重点不是“多写了几行 Redis get/put”。

真正重点是：

```text
Redis 命中不等于业务事实成立。
业务事实必须回到 MySQL 确认。
```

### 12. `ToolRateLimiter`

文件：

```text
projects/java-business-service/src/main/java/com/panpan/aibusinessservice/common/rate/ToolRateLimiter.java
```

接口：

```java
void check(InternalRequestContext context, String method, String uri);
```

它表达的是：

```text
给定当前调用上下文和接口路径，判断这次工具调用能不能继续。
```

为什么传 `method` 和 `uri`？

因为：

```text
GET /internal/orders/A1001
POST /internal/tickets
```

这两个工具风险不同，应该分开计数。

### 13. `RedisToolRateLimiter`

文件：

```text
projects/java-business-service/src/main/java/com/panpan/aibusinessservice/common/rate/RedisToolRateLimiter.java
```

核心动作：

```text
生成 rate-limit key。
INCR key。
如果 count == 1，设置 TTL。
如果 count > limit，抛出 TOOL_RATE_LIMITED。
Redis 异常时记录 warning 并放行。
```

为什么 `count == 1` 时设置 TTL？

因为第一次请求代表这个窗口刚开始。

如果每次请求都重置 TTL，就会变成：

```text
只要用户持续请求，窗口一直向后延长。
```

那就不是固定窗口了。

### 14. `NoOpToolRateLimiter`

文件：

```text
projects/java-business-service/src/main/java/com/panpan/aibusinessservice/common/rate/NoOpToolRateLimiter.java
```

Redis 关闭时使用。

这样测试环境不需要真实 Redis，也不会在 `InternalRequestResolver` 注入时报错。

### 15. `BusinessErrorCode.TOOL_RATE_LIMITED`

文件：

```text
projects/java-business-service/src/main/java/com/panpan/aibusinessservice/common/error/BusinessErrorCode.java
```

新增：

```text
TOOL_RATE_LIMITED -> HTTP 429
```

429 的含义是：

```text
Too Many Requests
```

它比 500 更准确。

因为这不是服务器代码崩了，而是调用频率超过了规则。

AI Agent 后续收到这个错误码时，可以把它翻译成用户能理解的话：

```text
当前请求过于频繁，请稍后再试。
```

### 16. `InternalRequestResolver` 接入限流

文件：

```text
projects/java-business-service/src/main/java/com/panpan/aibusinessservice/common/security/InternalRequestResolver.java
```

本节让它多依赖：

```text
ToolRateLimiter
```

并在 internal token 校验通过后执行：

```text
toolRateLimiter.check(context, request.getMethod(), request.getRequestURI());
```

为什么不放 Controller？

因为所有 internal Controller 都会先调用 `InternalRequestResolver`。

把限流放这里，可以统一保护：

```text
GET /internal/orders/{order_id}
POST /internal/tickets
未来更多 internal 工具接口
```

---

## 六、本地真实 Redis/MySQL 验证

本节真实环境：

```text
Java service：Windows 本机
MySQL：Windows 本机 127.0.0.1:3306
Redis：VMware Ubuntu Docker 192.168.88.10:6379
Qdrant/Milvus：本节不需要
```

你之前验证过 Redis 容器：

```text
Test-NetConnection 192.168.88.10 -Port 6379
TcpTestSucceeded : True
```

本节临时启动 Java 服务：

```text
http://localhost:18003
```

健康检查通过：

```text
GET /health
{"service":"java-business-service","status":"ok"}
```

真实请求验证：

```text
GET /internal/orders/A1001
GET /internal/orders/A1001
POST /internal/tickets
POST /internal/tickets
```

结果：

```text
order_id = A1001
order_status = shipped
ticket_id_first = T-c19da543-6b20-4607-83bd-1421971f4d84
ticket_id_second = T-c19da543-6b20-4607-83bd-1421971f4d84
same_ticket_id = True
```

说明：

```text
重复创建工单没有产生新工单。
相同 Idempotency-Key + 相同请求体返回了同一个 ticket_id。
```

Redis key 验证看到：

```text
java-business:order:default:A1001
java-business:ticket-idempotency:default:stage7-redis-smoke-20260727-001
java-business:rate-limit:default:U1001:GET:%2Finternal%2Forders%2FA1001
java-business:rate-limit:default:U1001:POST:%2Finternal%2Ftickets
```

TTL 验证看到：

```text
订单缓存 TTL 接近 300 秒。
幂等缓存 TTL 接近 86400 秒。
限流 key TTL 接近 60 秒。
```

本次 smoke 产生的 MySQL 工单记录和 Redis key 已清理。

临时 Java 服务也已停止。

---

## 七、测试说明

本节自动化测试：

```text
mvn test
```

结果：

```text
Tests run: 11, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

其中 Redis 相关新增测试：

```text
RedisToolRateLimiterTest
```

它验证：

```text
第一次请求会设置窗口 TTL。
超过 limit 会抛出 TOOL_RATE_LIMITED。
Redis 异常时不会打断业务请求。
```

为什么没有在 `mvn test` 里真实连接 Redis？

因为自动化测试应该稳定，不应该依赖你是否打开 VMware 虚拟机。

真实 Redis 连接用 smoke 验证。

这两类验证分工是：

```text
自动化测试：验证业务逻辑和代码契约。
真实 smoke：验证本机环境和外部依赖连接。
```

---

## 八、常见误区

### 误区 1：接了 Redis，幂等就可以不靠 MySQL

不对。

Redis 可以丢 key，可以过期，也可能临时不可用。

创建工单这种写操作必须有 MySQL 唯一约束兜底。

正确说法：

```text
Redis 加速幂等判断。
MySQL 保证幂等正确性。
```

### 误区 2：缓存命中后就不用做权限校验

不对。

缓存保存的是订单数据，不是权限结论。

每次请求都要基于当前 `user_id` 和 `tenant_id` 做权限判断。

### 误区 3：Redis 失败就应该直接让接口失败

不一定。

要看 Redis 在当前链路里的角色。

本节 Redis 是加速层和保护层，不是核心事实层。

所以本节选择：

```text
缓存失败 -> 查 MySQL
幂等缓存失败 -> 查 MySQL
限流失败 -> warning 后放行
```

如果以后 Redis 存的是登录态或关键分布式锁，那失败策略就要重新评估。

### 误区 4：TTL 越长越好

不对。

TTL 太长会让用户看到旧数据。

TTL 太短会让缓存效果变弱。

正确做法是结合业务变化频率设计。

订单状态会变化，所以本节订单缓存是 300 秒。

幂等键是为了覆盖重试窗口，所以本节是 86400 秒。

### 误区 5：限流只需要在 Python AI 服务做

不对。

Java 业务服务也应该保护自己。

上游可能有 bug、重试风暴、模型循环或绕过路径。

Java 内部接口自己限流，是后端服务的自我保护。

### 误区 6：固定窗口限流就是最好的限流

不对。

固定窗口只是简单、好学、低成本。

它有边界突刺问题。

以后真实生产可以考虑：

```text
滑动窗口。
令牌桶。
漏桶。
网关限流。
Redisson RRateLimiter。
```

---

## 九、面试表达

如果面试官问：

```text
你们项目里 Redis 用在哪里？
```

可以这样回答：

```text
在 Java business service 里，我把 Redis 用在三个位置：订单查询缓存、创建工单幂等加速、internal 工具接口限流。订单查询走 read-through cache，Redis 未命中时查 MySQL 并写回缓存；创建工单的幂等结果会缓存 request_fingerprint 和 ticket_id，但最终仍然以 MySQL 的唯一索引和 request_fingerprint 作为兜底；限流使用 Redis INCR + TTL 做固定窗口计数，按 tenant、user、method、uri 维度限制 internal 工具调用频率。
```

如果面试官问：

```text
为什么幂等不能只靠 Redis？
```

可以这样回答：

```text
因为 Redis 是缓存层，key 会过期，也可能丢失或短暂不可用。创建工单是写操作，不能因为 Redis 丢 key 就重复落库。所以我把 Redis 作为幂等加速层，把 MySQL unique(tenant_id, idempotency_key) 作为最终兜底。即使 Redis 失效，MySQL 仍然能保证同一幂等键不会创建多张工单。
```

如果面试官问：

```text
Redis 挂了怎么办？
```

可以这样回答：

```text
要看 Redis 承担的职责。在我这个阶段的实现里，Redis 不保存长期业务事实，只做缓存、幂等加速和限流。订单缓存读失败会降级查 MySQL；幂等缓存失败会走 MySQL 幂等逻辑；限流失败会记录 warning 并放行。这样 Redis 不可用不会导致核心业务读写直接失败。但如果 Redis 存登录态、分布式锁或强依赖状态，策略就要重新设计，不能简单放行。
```

如果面试官问：

```text
你怎么设计 Redis key？
```

可以这样回答：

```text
我会加项目级前缀，然后加业务类别和关键维度。比如订单缓存 key 是 java-business:order:{tenant_id}:{order_id}；幂等 key 是 java-business:ticket-idempotency:{tenant_id}:{idempotency_key}；限流 key 是 java-business:rate-limit:{tenant_id}:{user_id}:{method}:{uri}。这样能避免不同业务 key 冲突，也能保留租户、用户和接口维度。
```

---

## 十、本节练习

### 练习 1：Redis 和 MySQL 在本节里的职责有什么区别？

参考答案：

```text
MySQL 保存长期业务事实，比如 orders、tickets、ticket_events。Redis 保存短期加速状态，比如订单缓存、幂等键到 ticket_id 的映射、限流计数。Redis 可以提高速度和稳定性，但不能替代 MySQL 做写操作正确性的最终兜底。
```

### 练习 2：为什么订单查询适合做缓存？

参考答案：

```text
订单查询是读操作，同一个用户在一段对话里可能多次查询同一订单。把订单结果短时间缓存到 Redis，可以减少重复 MySQL 查询，提高响应速度。由于订单状态可能变化，所以缓存需要 TTL，本节默认 300 秒。
```

### 练习 3：为什么缓存命中后仍然要做权限校验？

参考答案：

```text
因为缓存里保存的是订单业务数据，不是某个用户的授权结果。不同用户可能访问同一个订单 key，但是否可见要由当前请求的 user_id 和 tenant_id 决定。所以无论缓存命中还是 MySQL 查询命中，都必须重新执行 visibleTo 权限判断。
```

### 练习 4：为什么创建工单的幂等最终要靠 MySQL unique index？

参考答案：

```text
因为 Redis key 可能过期、丢失或不可用，不能保证长期业务正确性。MySQL unique(tenant_id, idempotency_key) 能在数据库层保证同一租户下同一个幂等键只能对应一张工单，即使并发请求同时到达，也能通过唯一约束兜底。
```

### 练习 5：Redis 幂等缓存里为什么保存 `request_fingerprint` 和 `ticket_id`？

参考答案：

```text
request_fingerprint 用来判断同一个 idempotency_key 是否对应相同请求内容，ticket_id 用来回查 MySQL 中真实存在的工单。这样 Redis 可以加速重复请求判断，但最终返回前仍然能通过 MySQL 确认业务事实。
```

### 练习 6：为什么限流 key 要包含 tenant_id、user_id、method 和 uri？

参考答案：

```text
tenant_id 用来区分租户，user_id 用来区分用户，method 和 uri 用来区分具体工具接口。这样 GET 订单和 POST 工单不会混在一起计数，不同用户也不会互相挤占限流额度。
```

### 练习 7：本节 fixed window 限流的流程是什么？

参考答案：

```text
请求进来后根据 tenant、user、method、uri 生成 Redis key。执行 INCR key 得到当前窗口计数。如果 count 等于 1，就给 key 设置窗口 TTL。如果 count 超过 limit，就抛出 TOOL_RATE_LIMITED，对应 HTTP 429。TTL 到期后 key 自动删除，下一轮重新计数。
```

### 练习 8：为什么测试环境默认关闭 Redis？

参考答案：

```text
因为自动化测试应该稳定，不应该依赖 VMware 虚拟机和 Docker Redis 是否启动。测试环境关闭 Redis 后启用 NoOp 实现，核心业务仍然走 H2、JdbcRepository 和业务校验。真实 Redis 连通性通过单独 smoke 验证。
```

### 练习 9：Redis 失败时，本节的缓存和限流分别怎么处理？

参考答案：

```text
订单缓存读失败返回 empty 并继续查 MySQL，写失败只记录 warning；幂等缓存读失败继续查 MySQL，写失败不影响 MySQL 创建结果；限流 Redis 失败时记录 warning 并放行请求。这是因为本节 Redis 是加速和保护层，不是长期业务事实层。
```

### 练习 10：如果以后新增订单状态更新接口，缓存应该怎么处理？

参考答案：

```text
订单状态更新成功后应该删除或刷新对应订单缓存，比如删除 java-business:order:{tenant_id}:{order_id}。否则用户可能在 TTL 过期前看到旧订单状态。读多写少场景可以用 TTL 自然过期，写入场景更建议更新成功后主动失效缓存。
```

---

## 十一、自测问题

### 自测 1：本节 Redis 保存的是长期业务事实吗？

答案：

```text
不是。长期业务事实仍然保存在 MySQL。Redis 在本节只保存订单缓存、幂等加速映射和限流计数。
```

### 自测 2：本节订单缓存的默认 TTL 是多久？

答案：

```text
300 秒，也就是 5 分钟。
```

### 自测 3：本节工单幂等缓存的默认 TTL 是多久？

答案：

```text
86400 秒，也就是 1 天。
```

### 自测 4：本节限流超过阈值返回什么 HTTP 状态？

答案：

```text
HTTP 429 Too Many Requests，对应业务错误码 TOOL_RATE_LIMITED。
```

### 自测 5：`StringRedisTemplate` 适合操作什么类型的 Redis 数据？

答案：

```text
适合 key 和 value 都是字符串的 Redis 数据。本节对象缓存通过 JSON 字符串保存，限流计数通过字符串数字配合 INCR 实现。
```

### 自测 6：为什么 Redis 幂等缓存命中后还要回查 MySQL？

答案：

```text
因为 Redis 只是缓存层，可能存在脏数据、过期问题或事务边界问题。回查 MySQL 可以确认 ticket_id 对应的工单真实存在，避免 Redis 单独决定业务事实。
```

### 自测 7：本节自动化测试是否依赖真实 Redis？

答案：

```text
不依赖。测试配置里 app.redis.enabled=false，会启用 NoOp 缓存和 NoOp 限流。真实 Redis 通过单独 smoke 验证。
```

### 自测 8：如果 Redis 订单缓存读取失败，本节代码会怎么做？

答案：

```text
记录 warning，返回 Optional.empty，让业务继续查 MySQL。
```

### 自测 9：本节为什么不使用分布式锁？

答案：

```text
因为本节创建工单幂等已经由 MySQL unique index 和 DuplicateKeyException 兜底，Redis 只是加速层。为了先学清楚缓存、幂等加速和限流，不提前引入分布式锁复杂度。
```

### 自测 10：下一节学什么？

答案：

```text
下一节是阶段 7 第 7.5 节：Java 服务结构传统化重构 + MyBatis。会把当前 java-business-service 逐步对齐到 controller / service / service.impl / mapper / entity / dto / config / exception / common 这类你更熟悉的传统 Spring Boot 结构，并把 JdbcTemplate 切换到 MyBatis，同时保留 AI Agent 调用边界。
```

---

## 十二、本节总结

本节把 Redis 正式接入了真实 Java business service。

核心成果：

```text
新增 spring-boot-starter-data-redis。
新增 app.redis 配置。
新增 RedisFeatureProperties。
新增 RedisKeys。
新增订单 Redis 缓存。
OrderQueryService 接入 read-through cache。
新增工单幂等 Redis 缓存。
JdbcTicketRepository 接入 Redis 幂等加速，并坚持 MySQL 兜底。
新增 Redis fixed window 工具限流。
InternalRequestResolver 统一接入限流。
测试环境默认关闭真实 Redis。
新增 RedisToolRateLimiterTest。
mvn test 通过。
真实 Windows Java + Windows MySQL + VMware Ubuntu Docker Redis smoke 通过。
```

你现在应该能讲清楚：

```text
Redis 在 AI Agent 调 Java 业务系统里不是“替代数据库”，而是“加速和保护业务系统”。
订单缓存减少重复查询。
幂等缓存加速重复写请求判断。
限流保护 internal 工具接口。
MySQL 仍然保存长期业务事实，并用唯一索引兜底写操作正确性。
Redis 失败时要根据它承担的职责决定 fail open 还是 fail closed。
```

下一节进入已经约定好的插入课：

```text
阶段 7 第 7.5 节：Java 服务结构传统化重构 + MyBatis
```

这节会把当前代码结构变成你更熟悉的传统 Spring Boot 项目结构，然后再继续阶段 7 后面的 AI internal 鉴权、用户身份传递、错误码回传和 Python 对接。
