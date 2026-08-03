# 阶段 10 第 16 节：SSE 流式输出生产化与中断处理

## 本节定位

这一节学习 AI 应用里的流式输出生产化。

前面我们已经有 `/stream-chat`，它能把模型回答一段一段返回给前端。
但“能流式返回”和“适合生产使用”不是一回事。

原来的流式接口主要解决：

```text
模型边生成，后端边返回。
```

本节要解决：

```text
流式响应开始、传输、心跳、中途失败、用户断连、结束事件和排查信息应该怎么设计。
```

本节合并了原来的两节：

```text
SSE 流式输出生产化
流式错误处理和中断
```

不提前学习前端 EventSource 组件、WebSocket、复杂流式 Agent、多路并发流、浏览器端渲染优化和真实模型流式调试。

## 本节学习目标

- 理解 SSE 是什么，和普通 HTTP JSON 响应有什么区别。
- 理解为什么 AI 回答适合流式输出。
- 掌握 `text/event-stream`、`event:`、`data:`、`id:`、`retry:`、注释心跳的含义。
- 理解首 token 延迟、整体耗时、用户感知速度之间的区别。
- 理解流式响应开始后，为什么不能再返回普通 JSON 错误。
- 理解流式中途失败应该用 SSE error 事件表达。
- 理解 heartbeat 心跳和代理缓冲的作用。
- 理解用户取消、浏览器断连时后端为什么要停止继续生成。
- 看懂本项目对 `/stream-chat` 的最小生产化升级。

## 本节新增和修改

- 修改 `projects/ai-service/app/routers/chat.py`
  - SSE 事件增加 `start`、`message`、`error`、`done`。
  - 每个关键事件增加 `id`。
  - `start` 事件增加 `retry`。
  - 增加 heartbeat 注释事件。
  - 增加断连检查。
  - 增加 SSE 响应头：`Cache-Control`、`Connection`、`X-Accel-Buffering`、`X-Trace-Id`。
- 修改 `projects/ai-service/app/core/config.py`
  - 新增 `sse_heartbeat_every_chunks`。
- 修改 `.env.example`
  - 新增 `SSE_HEARTBEAT_EVERY_CHUNKS`。
- 修改 `config_safety.py` 和配置测试
  - 安全暴露 heartbeat 配置值。
- 修改 `tests/test_chat_api.py`
  - 更新 SSE 格式测试。
  - 增加 SSE event 格式、heartbeat、断连边界测试。

## 一句话先讲透

SSE 生产化不是简单地 `yield` 几段文本，而是要把一次长连接设计成可识别、可追踪、可结束、可报错、可断开的事件流。

## 基础知识铺垫

### 1. 普通 HTTP 响应是什么样

普通 HTTP 接口通常是这样：

```text
请求进来
后端处理完全部逻辑
一次性返回完整响应
连接结束
```

例如普通 `/chat`：

```json
{
  "reply": "FastAPI 是一个 Python Web 框架。"
}
```

这种方式适合短任务。

问题是大模型回答可能需要几秒、十几秒甚至更久。
如果一直等完整答案生成完再返回，用户看到的就是页面长时间无反应。

### 2. 什么是流式输出

流式输出的意思是：

```text
后端不是等全部内容生成完再返回，而是生成一点就返回一点。
```

对 AI 回答来说，用户体验会明显不同。

普通响应：

```text
等待 8 秒
一次性看到完整答案
```

流式响应：

```text
等待 1 秒看到第一段
后续内容持续出现
8 秒时完整结束
```

整体耗时可能没有变，但用户感知速度变快了。

### 3. 什么是 SSE

SSE 全称是：

```text
Server-Sent Events
```

意思是：

```text
服务器通过一个 HTTP 长连接，持续向客户端发送事件。
```

SSE 是单向的：

```text
服务器 -> 客户端
```

客户端不能通过同一条 SSE 连接反向发消息。
如果客户端要继续提问，还是发新的 HTTP 请求。

这和 WebSocket 不同。
WebSocket 是双向通信，适合聊天室、实时游戏、协同编辑等场景。

AI 回答流式输出通常用 SSE 就够了，因为主要需求是：

```text
用户发一次问题
服务端持续返回回答片段
```

### 4. SSE 的 Content-Type

SSE 响应必须使用：

```text
Content-Type: text/event-stream
```

这个类型告诉客户端：

```text
这不是普通 JSON，也不是普通文本，而是一段持续到来的事件流。
```

本项目用：

```python
SSE_MEDIA_TYPE = "text/event-stream"
```

然后通过 `StreamingResponse` 返回。

### 5. SSE 事件格式

SSE 是纯文本协议。

一个事件通常长这样：

```text
event: message
data: {"content":"你好"}

```

注意最后有一个空行。

空行表示：

```text
一个事件结束了。
```

常见字段包括：

```text
event: 事件类型
data: 事件数据
id: 事件编号
retry: 客户端断线后建议多久重连
```

### 6. `event:` 是什么

`event:` 表示事件类型。

本节使用 4 种事件：

```text
start：流开始
message：内容片段
error：流中途失败
done：流正常结束
```

前端可以根据事件类型做不同处理：

```text
start -> 初始化状态
message -> 追加文本
error -> 显示错误提示
done -> 标记回答完成
```

如果没有事件类型，前端只能把所有内容当成普通消息，后续扩展会很难。

### 7. `data:` 是什么

`data:` 是事件携带的数据。

本项目把 data 写成 JSON 字符串。

例如：

```text
event: message
data: {"content":"FastAPI"}
```

这样前端拿到后可以解析出：

```json
{
  "content": "FastAPI"
}
```

注意：SSE 本身不是 JSON 协议。
只是我们把每个事件的 data 内容设计成 JSON。

### 8. `id:` 是什么

`id:` 是事件编号。

例如：

```text
id: trace-001:2
event: message
data: {"content":"第二段"}
```

它的作用有两个。

第一，排查问题时能知道输出到第几个事件。

第二，一些客户端会记录 last event id，断线重连时可能带上它。

本项目暂时不做“从断点继续生成”，但先把事件 id 设计出来，这样日志和前端排查会更清楚。

### 9. `retry:` 是什么

`retry:` 是 SSE 协议支持的重连建议。

例如：

```text
retry: 3000
```

含义是：

```text
如果连接断开，客户端可以 3000 毫秒后尝试重连。
```

注意：这不是后端重试模型调用。

它只是告诉 SSE 客户端：

```text
连接断了以后，多久再连。
```

### 10. heartbeat 心跳是什么

heartbeat 是心跳事件。

SSE 里常用注释行表示心跳：

```text
: heartbeat

```

以冒号开头的行是 SSE 注释。
客户端通常不会把它当业务消息。

心跳的作用是：

```text
让连接保持活跃
让代理、网关、浏览器知道这条连接还没死
减少长时间无数据导致的断开
```

真实生产里 heartbeat 通常按时间发送，比如每 15 秒一次。
本项目为了本地测试稳定，用“每 N 个 chunk 插一次 heartbeat”的确定性方式演示。

### 11. 首 token 延迟

首 token 延迟指：

```text
用户发出请求后，到看到第一段模型输出之间的时间。
```

它和总耗时不同。

例如：

```text
首 token 延迟：1 秒
总生成时间：8 秒
```

用户通常更在意首 token 延迟。

因为只要第一段出现，用户就知道系统正在工作。

### 12. 流式响应开始后，为什么不能再返回普通 JSON 错误

这是本节最关键的概念之一。

普通 HTTP 错误是这样：

```json
{
  "code": "LLM_TIMEOUT",
  "message": "模型调用超时"
}
```

但 SSE 一旦开始返回，响应头已经发出去了：

```text
HTTP 200
Content-Type: text/event-stream
```

这时不能再把状态码改成 500，也不能突然返回普通 JSON。

所以流式中途失败时，只能在事件流里发：

```text
event: error
data: {"code":"LLM_CALL_FAILED","message":"模型调用失败","trace_id":"..."}
```

这也是为什么流式接口的错误处理和普通接口不一样。

### 13. 流开始前错误和流开始后错误

流开始前错误：

```text
还没创建 StreamingResponse
还没发响应头
可以返回普通 JSON 错误
```

例如 API Key 没配置，`stream_reply()` 在创建迭代器前就失败。

流开始后错误：

```text
响应头已经发出
前端已经开始按 SSE 解析
只能返回 SSE error 事件
```

本项目保留了这个边界：

```text
stream_reply 创建失败 -> 统一异常处理返回 JSON
迭代 chunks 中途失败 -> SSE error 事件
```

### 14. 用户取消和浏览器断连

用户可能关闭页面、刷新页面、切换路由，或者前端主动取消请求。

如果后端不知道客户端已经断开，还继续调用模型生成，就会浪费：

```text
模型费用
CPU/内存
连接资源
日志和 trace
下游服务压力
```

所以生产化流式接口要检查：

```text
客户端是否已经断开
```

FastAPI 的 `Request` 提供：

```python
await request.is_disconnected()
```

本节把它接入到流式事件生成过程里。

## 本节主题系统讲解

### 1. 本节前 `/stream-chat` 的链路

原来的链路大致是：

```text
POST /stream-chat
-> ChatRequest 校验
-> llm_chat_service.stream_reply()
-> StreamingResponse
-> build_stream_events()
-> message / error / done
```

它已经具备基础流式能力。

但它缺少生产化信息：

```text
没有 start 事件
没有事件 id
没有 retry 建议
没有 heartbeat
没有断连检查
没有防代理缓冲响应头
done 事件里没有 chunk 数量
```

这些不影响 demo 跑通，但会影响真实系统的体验、排查和资源保护。

### 2. 本节后的 `/stream-chat` 链路

现在链路变成：

```text
POST /stream-chat
-> ChatRequest 校验
-> stream_reply 创建流式 chunk 迭代器
-> StreamingResponse 设置 SSE 响应头
-> start 事件
-> message 事件
-> heartbeat 注释
-> 中途断连检查
-> error 事件或 done 事件
```

这个链路更接近真实生产接口。

### 3. 为什么先发 start 事件

start 事件的作用是：

```text
告诉前端：流已经真正开始。
```

它可以携带：

```text
trace_id
retry 建议
事件 id
```

前端收到 start 后，可以进入“正在生成”的状态。

### 4. 为什么 message 事件只放 content

message 事件只放：

```json
{"content":"..."}
```

原因是内容片段会很多。

如果每个片段都重复塞大量元信息，会浪费带宽，也会让前端处理复杂。

trace_id 已经在：

```text
start 事件
done 事件
error 事件
X-Trace-Id 响应头
```

所以 message 保持轻量。

### 5. 为什么 done 事件要带 chunks

done 事件现在包含：

```json
{
  "trace_id": "trace-stream",
  "chunks": 3
}
```

`chunks` 表示本次一共输出了多少个内容片段。

这对排查很有用。

例如：

```text
用户说页面只显示了一半
日志里显示 done chunks=3
前端只收到 1 个 message
```

就说明可能是前端消费、网络或浏览器端出了问题。

### 6. 为什么要设置 `X-Accel-Buffering: no`

有些反向代理会缓冲响应。

如果代理把后端一段一段返回的内容先攒起来，等攒够再发给浏览器，流式体验就没了。

`X-Accel-Buffering: no` 常用于告诉 Nginx：

```text
不要缓冲这条响应。
```

本地开发可能看不出差异，但生产部署时很重要。

### 7. 为什么要设置 `Cache-Control: no-cache`

SSE 是实时输出，不应该被缓存。

所以要告诉客户端和中间代理：

```text
不要缓存这条流式响应。
```

### 8. 为什么 build_stream_events 改成 async

断连检查是异步的：

```python
await request.is_disconnected()
```

所以事件生成器需要支持 async。

但模型 chunk 迭代器是同步的。

本节使用：

```python
iterate_in_threadpool(chunks)
```

它的作用是把同步迭代器放到线程池里消费，避免直接在 async generator 里阻塞事件循环。

这点很关键。

如果你在 async 函数里直接跑阻塞的同步迭代器，可能会影响整个服务的并发能力。

## 本节代码讲解

### 1. `format_sse_event`

这个函数负责把结构化事件变成 SSE 文本。

它支持：

```text
id
retry
event
data
```

这样所有 SSE 格式集中在一个函数里，不要在路由里到处手写字符串。

### 2. `format_sse_comment`

这个函数生成 heartbeat：

```text
: heartbeat
```

这不是业务消息，而是 SSE 注释。

它的学习价值是让你理解：

```text
流式连接不一定每次发送的都是业务内容，也可能发送连接保活信号。
```

### 3. `build_sse_headers`

这个函数集中构造 SSE 响应头。

包含：

```text
Cache-Control: no-cache
Connection: keep-alive
X-Accel-Buffering: no
X-Trace-Id: trace_id
```

这样前端、代理和排查系统都能更清楚地理解这条响应。

### 4. `build_stream_events`

这是本节核心函数。

它的流程是：

```text
先发 start
循环读取模型 chunk
每次读取前检查客户端是否断开
正常 chunk 变成 message 事件
按配置插入 heartbeat
AppException 变成 error 事件
未知异常变成 INTERNAL_SERVER_ERROR 事件
正常结束发 done 事件
```

它同时处理了：

```text
正常输出
业务错误
未知错误
客户端断连
正常结束
```

### 5. `sse_heartbeat_every_chunks`

配置含义：

```text
每输出多少个内容 chunk 后插入一次 heartbeat。
0 表示关闭这种确定性 heartbeat。
```

真实生产更常见的是按时间发心跳。
本项目先用 chunk 数量做演示，是为了测试稳定、容易观察。

## 常见误区

### 误区 1：SSE 就是普通 JSON 分多次返回

不是。

SSE 有自己的文本格式：

```text
event:
data:
id:
retry:
空行结束事件
```

前端必须按 SSE 方式解析。

### 误区 2：流式接口中途失败还能返回 HTTP 500

通常不能。

只要响应头已经发出，状态码就基本定了。

中途失败应该用：

```text
event: error
```

### 误区 3：只要后端 yield，浏览器就一定能马上看到

不一定。

中间可能有：

```text
代理缓冲
网关缓冲
浏览器缓冲
前端消费逻辑问题
```

所以生产部署要关注响应头、代理配置和前端解析。

### 误区 4：用户断开后后端继续生成也没事

有成本。

模型调用还在继续、token 还在消耗、资源还在占用。

断连检查是生产系统保护资源的重要手段。

### 误区 5：heartbeat 是业务消息

不是。

heartbeat 通常是保活信号。
前端不应该把它显示给用户。

## 本节关键测试说明

本节测试不真实调用模型。

关键测试包括：

```text
/stream-chat 返回 text/event-stream
响应头包含 no-cache、X-Accel-Buffering、X-Trace-Id
流事件包含 start、message、heartbeat、done
中途 AppException 变成 SSE error 事件
流开始前错误仍然返回普通 JSON 错误
断连检查命中后停止继续输出
```

这些测试主要防止：

```text
事件格式被改坏
trace_id 丢失
中途错误被错误地抛成普通异常
断连后继续输出
```

## 手动测试命令

本节按省 token 模式，我没有自动跑 pytest。你可以手动运行：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run pytest tests/test_chat_api.py tests/test_config.py tests/test_config_safety.py -q
```

如果要跑全量测试：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run pytest -q
```

## 本节练习

### 练习 1：普通 HTTP JSON 和 SSE 最大区别是什么？

参考答案：

普通 HTTP JSON 通常是后端处理完一次性返回完整结果。

SSE 是服务器通过一个长连接持续发送多个事件，客户端可以边接收边处理。

### 练习 2：为什么流式中途失败不能直接返回普通 JSON 错误？

参考答案：

因为流式响应开始后，HTTP 状态码和响应头已经发出，客户端已经按 `text/event-stream` 解析内容。

这时不能突然改成普通 JSON，只能在 SSE 流里发送 `event: error`。

### 练习 3：heartbeat 有什么作用？

参考答案：

heartbeat 用来保持连接活跃，让浏览器、代理、网关知道这条长连接还在工作，减少因为长时间无数据导致连接被断开的概率。

### 练习 4：`id:` 有什么用？

参考答案：

`id:` 用来标识事件顺序，便于排查输出到第几个事件，也为未来断线重连和 last event id 留下扩展空间。

### 练习 5：用户关闭页面后，后端为什么要停止继续生成？

参考答案：

因为用户已经不再接收结果，如果后端继续生成，会浪费模型费用、连接资源、服务端资源，并增加无意义的下游压力。

## 自测问题

### 自测 1：SSE 的 `Content-Type` 应该是什么？

参考答案：

```text
text/event-stream
```

### 自测 2：本节使用了哪 4 种业务事件？

参考答案：

```text
start
message
error
done
```

### 自测 3：SSE 注释心跳长什么样？

参考答案：

```text
: heartbeat

```

### 自测 4：`X-Accel-Buffering: no` 主要解决什么问题？

参考答案：

主要用于告诉 Nginx 等代理不要缓冲响应，避免后端已经流式输出，但代理攒起来再一次性发给前端。

### 自测 5：为什么 `build_stream_events` 要检查 `request.is_disconnected()`？

参考答案：

为了在客户端断开后及时停止继续输出，避免无意义地消耗模型成本和服务端资源。

## 本节小结

本节把 `/stream-chat` 从基础流式接口升级成更接近生产的 SSE 事件流。

现在它具备：

```text
start 事件
message 事件
heartbeat
error 事件
done 事件
事件 id
retry 建议
SSE 响应头
断连检查
trace_id 贯穿
```

你需要真正理解的不是某个字符串格式，而是这个生产化思想：

```text
流式输出是一条长连接协议，不是普通接口的分段打印。
```
