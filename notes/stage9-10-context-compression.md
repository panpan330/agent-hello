# 阶段 9 第 10 节：Context Compression：上下文压缩

## 本节定位

本节学习：

```text
当检索和 rerank 找到很多资料后，后端如何在有限上下文预算里保留最有价值的信息。
```

前面几节我们一直在提升“找资料”的质量：

```text
Query Rewrite 让问题更适合检索。
Multi Query 让检索角度更多。
Intent Classification 决定问题走哪条链路。
Hybrid Search 让关键词和向量互补。
Score Interpretation 让分数可解释。
Rerank 让候选资料重新排序。
Citation Verification 检查最终回答是否能对应原文。
```

现在遇到一个新问题：

```text
资料找得越多，不代表越应该全部塞给模型。
```

大模型上下文是有限的。

即使上下文窗口很大，也不代表你应该把所有内容都塞进去。

上下文越大，通常会带来：

```text
成本更高。
速度更慢。
噪声更多。
重点被稀释。
模型更容易漏看关键证据。
回答更难调试。
```

所以本节要学：

```text
Context Compression，也就是上下文压缩。
```

## 本节学习目标

学完本节，你要能做到：

1. 能解释什么是 context compression。
2. 能说明为什么 RAG 不是“检索越多越好”。
3. 能理解上下文窗口和上下文预算的区别。
4. 能解释 top_k、chunk_size、token budget 的关系。
5. 能区分裁剪、过滤、压缩三件事。
6. 能区分 extractive compression 和 abstractive compression。
7. 能说明为什么学习版先做规则版抽取式压缩。
8. 能看懂 `ContextCompressionPolicy`。
9. 能看懂 `ContextCompressionReport`。
10. 能解释 `keep_full`、`compress`、`drop` 三种动作。
11. 能说明为什么压缩后的 chunk 仍然要保留原始 metadata。
12. 能理解压缩报告在调试 RAG 坏例时的作用。

## 本节新增和修改

本节新增：

```text
projects/ai-service/app/rag/context_compression.py
projects/ai-service/tests/test_rag_context_compression.py
notes/stage9-10-context-compression.md
```

本节修改：

```text
projects/ai-service/app/rag/README.md
docs/learning-progress.md
```

本节没有做：

- 不启动 VMware。
- 不启动 Qdrant。
- 不启动 Milvus。
- 不调用真实大模型。
- 不调用真实 embedding。
- 不调用真实 rerank 模型。
- 不写手动测试文档。
- 不做敏感信息扫描。

原因：

```text
本节是纯工程逻辑和自动化测试，不需要外部服务。
```

## 一句话先讲透

Context Compression 做的事情是：

```text
在模型上下文预算有限的前提下，把检索到的 chunks 变成更短、更聚焦、更适合生成回答的上下文。
```

它不是：

```text
重新检索。
重新排序。
替代 rerank。
替代 citation verification。
随便摘要原文。
把所有资料压成一段模糊总结。
```

它的工程位置一般在：

```text
检索 / hybrid / rerank 之后
生成回答之前
```

也就是：

```text
先找到候选资料
-> 再压缩上下文
-> 再交给模型回答
```

## 基础知识铺垫

### 1. 什么是上下文

在 RAG 里，上下文通常指：

```text
后端放进 prompt 里给大模型看的资料。
```

比如用户问：

```text
退款多久到账？
```

后端检索到几个 chunk：

```text
chunk 1：退款申请条件
chunk 2：退款到账时间
chunk 3：退货运费规则
chunk 4：特殊活动订单规则
```

然后后端把这些 chunk 拼进 prompt：

```text
请根据以下资料回答用户问题：

[资料 1]
...

[资料 2]
...
```

这些资料就是生成回答时的上下文。

上下文不只是文字内容。

它还包括：

```text
source
title
section
chunk_id
score
```

因为模型回答之后，后端还要能做引用、追溯、调试和评测。

### 2. 什么是上下文窗口

上下文窗口通常指：

```text
模型一次请求最多能接收多少 token。
```

例如某个模型可能支持：

```text
8K token
32K token
128K token
```

但注意：

```text
上下文窗口大，不等于可以不控制上下文。
```

原因是：

```text
1. 上下文越长，请求越贵。
2. 上下文越长，响应越慢。
3. 上下文越长，模型越可能被无关内容干扰。
4. 上下文越长，排查问题越困难。
5. 上下文窗口还要留给系统提示词、用户问题、工具结果和模型输出。
```

所以真实项目不会直接说：

```text
模型支持 128K，那我就塞 128K。
```

更常见的做法是：

```text
给 RAG context 单独设置预算。
```

### 3. 什么是上下文预算

上下文预算是工程配置，不一定等于模型最大窗口。

比如模型最大窗口是：

```text
32K token
```

但我们可能规定：

```text
RAG context 最多占 6K token。
系统提示词和规则占 1K token。
用户历史消息占 2K token。
模型输出预留 2K token。
其它工具结果预留 1K token。
```

这样做是为了稳定。

因为一个 AI 服务不是只有 RAG context。

它可能还有：

```text
system prompt
developer prompt
chat history
tool results
retrieved chunks
guardrail instructions
output schema
```

如果 RAG context 把预算占满，别的内容就会被挤掉。

### 4. token 和字符不是一回事

本节代码用的是：

```text
字符预算 chars
```

不是严格 token 预算。

这是学习版选择。

原因是：

```text
1. 字符数容易理解。
2. 不需要引入 tokenizer 依赖。
3. 自动化测试稳定。
4. 足够表达上下文压缩的工程思想。
```

真实项目更建议使用：

```text
模型对应 tokenizer 的 token 计数。
```

但你要先理解一个核心关系：

```text
chunk 内容越长，占用 token 越多。
top_k 越大，占用 token 越多。
metadata 越多，占用 token 越多。
历史消息越长，留给 RAG 的预算越少。
```

所以 RAG 不是只调一个 `top_k=20` 就完事。

你还要考虑：

```text
这 20 个 chunk 加起来能不能放得下？
放进去之后模型还能不能稳定回答？
```

### 5. RAG 为什么不是检索越多越好

检索更多资料有好处：

```text
召回率可能更高。
遗漏关键资料的概率可能更低。
rerank 有更多候选可选。
```

但也有坏处：

```text
噪声更多。
上下文更长。
模型注意力被分散。
不同 chunk 之间可能互相冲突。
生成速度变慢。
成本上升。
引用更难追踪。
```

所以真实 RAG 常见策略是：

```text
先多召回。
再重排序。
再压缩。
最后只把高价值上下文给模型。
```

这可以理解成漏斗：

```text
召回阶段：宁可多找一些。
排序阶段：把更可能有用的放前面。
压缩阶段：在预算内保留最关键的信息。
生成阶段：让模型基于更干净的上下文回答。
```

### 6. 裁剪、过滤、压缩有什么区别

这三个词容易混。

#### 裁剪

裁剪是：

```text
超过长度就截掉。
```

比如：

```text
chunk[:500]
```

优点：

```text
简单。
快。
稳定。
```

缺点：

```text
关键答案可能在后半段，被截掉。
```

#### 过滤

过滤是：

```text
决定某个 chunk 要不要进入上下文。
```

比如：

```text
score 太低的不要。
权限不匹配的不要。
rerank 排名太靠后的不要。
```

过滤作用在 chunk 粒度。

#### 压缩

压缩是：

```text
chunk 仍然保留，但内容变短。
```

比如一个 chunk 原本 1000 字。

压缩后只保留和用户问题最相关的 300 字。

压缩作用在 chunk 内部。

所以三者关系是：

```text
过滤：决定 chunk 留不留。
压缩：决定留下的 chunk 变多短。
裁剪：最简单但最粗糙的一种压缩方式。
```

### 7. Extractive Compression 和 Abstractive Compression

上下文压缩常见有两类。

#### Extractive Compression

抽取式压缩。

意思是：

```text
只从原文里抽取片段，不改写原文含义。
```

例如原文：

```text
退款申请通过后，系统会原路退回款项。通常 1 到 3 个工作日到账。特殊活动订单以活动规则为准。
```

用户问：

```text
退款多久到账？
```

抽取式压缩可能保留：

```text
通常 1 到 3 个工作日到账。
```

优点：

```text
不容易引入新事实。
可追溯。
适合做 citation。
测试稳定。
```

缺点：

```text
可能不够自然。
可能漏掉需要综合的信息。
```

#### Abstractive Compression

生成式压缩。

意思是：

```text
让模型把原文重新总结、改写、合并。
```

例如：

```text
退款通常在审核通过后 1 到 3 个工作日退回原支付方式。
```

优点：

```text
更短。
更自然。
能合并多段信息。
```

缺点：

```text
可能改写错。
可能遗漏限制条件。
可能引入原文没有的信息。
需要真实模型调用。
成本更高。
测试更不稳定。
```

所以本节学习版选择：

```text
规则版抽取式压缩。
```

先建立可解释、可测试的工程边界。

## 本节主题系统讲解

### 1. 上下文压缩在 RAG 链路的位置

完整链路可以这样看：

```text
用户问题
-> 意图识别
-> Query Rewrite / Multi Query
-> 向量检索 / 关键词检索
-> Hybrid Search
-> Rerank
-> Context Compression
-> 构造 prompt
-> 模型生成回答
-> Citation Verification
```

Context Compression 位于：

```text
rerank 之后，prompt 构造之前。
```

为什么不是检索之前？

因为检索之前还没有 chunks。

为什么不是生成之后？

因为它要控制进入模型的上下文。

为什么通常放在 rerank 之后？

因为 rerank 已经告诉我们：

```text
哪些 chunk 更重要。
```

压缩时就可以优先保留排名靠前的资料。

### 2. 本节为什么先用字符预算

真实项目最好用 token 预算。

但本节用：

```text
max_total_chars
max_chunk_chars
min_chunk_chars
```

原因是：

```text
字符数更适合入门。
不需要 tokenizer。
测试更稳定。
能清楚表达预算思想。
```

你要先学会这个思路：

```text
总预算：所有上下文加起来不能超过多少。
单 chunk 预算：一个 chunk 最多占多少。
最小 chunk 预算：如果剩余预算太少，宁可丢弃，不塞碎片。
```

以后把 chars 换成 tokens，本质不变。

### 3. 本节新增核心对象

新增文件：

```text
projects/ai-service/app/rag/context_compression.py
```

核心对象有三个。

#### ContextCompressionPolicy

它表示压缩策略：

```text
max_total_chars：最终上下文总字符预算。
max_chunk_chars：单个 chunk 最多保留多少字符。
min_chunk_chars：非强保留 chunk 至少要有多少字符才值得进入上下文。
always_keep_top_n：优先保留前几个 chunk。
```

这些字段解决的是：

```text
压缩到底多严格。
```

#### ContextCompressionItem

它表示单个 chunk 的处理结果：

```text
chunk_id
original_rank
action
original_chars
final_chars
saved_chars
score
source
section
query_term_hits
reason
```

这里最重要的是 `action`。

它有三种：

```text
keep_full：完整保留。
compress：压缩后保留。
drop：不进入最终上下文。
```

#### ContextCompressionReport

它表示完整压缩报告：

```text
query
budget_chars
original_total_chars
final_total_chars
saved_chars
input_chunk_count
kept_chunk_count
compressed_chunk_count
dropped_chunk_count
compressed_chunks
items
debug_lines
```

它适合用于：

```text
调试。
测试。
日志。
评测。
坏例分析。
```

### 4. `compress_retrieved_context()` 做了什么

核心入口是：

```python
compress_retrieved_context(query, chunks, policy=None)
```

它接收：

```text
用户问题 query。
检索或 rerank 后的 chunks。
压缩策略 policy。
```

输出：

```text
ContextCompressionReport。
```

流程是：

```text
1. 检查 query 不能为空。
2. 读取压缩策略。
3. 按输入顺序遍历 chunks。
4. 计算剩余预算。
5. 如果 chunk 能放下，完整保留。
6. 如果 chunk 太长，抽取和 query 更相关的片段。
7. 如果剩余预算太少，丢弃后续 chunk。
8. 给保留下来的 chunk 写入压缩 metadata。
9. 生成 items 和 debug_lines。
```

### 5. 为什么压缩后仍然返回 RetrievedChunk

本节压缩后的结果仍然是：

```text
list[RetrievedChunk]
```

原因是现有生成模块已经接受：

```text
Sequence[RetrievedChunk]
```

如果压缩后改成一个全新类型，后面还要改 `generator.py`。

而本节只是在生成前插入一个处理步骤。

所以更稳的做法是：

```text
保留 RetrievedChunk 结构。
只把 content 换成压缩后的内容。
metadata 里记录压缩信息。
```

这样现有：

```python
build_rag_context(report.compressed_chunks)
```

仍然可以工作。

### 6. 为什么 metadata 里要记录压缩信息

压缩后的 chunk metadata 会增加：

```text
context_compression_action
context_original_rank
context_original_chars
context_final_chars
```

这些信息很重要。

因为以后排查问题时，你需要知道：

```text
这个 chunk 原来排第几？
它是不是被压缩过？
原文多长？
压缩后多长？
是不是因为压缩把关键限制条件截掉了？
```

没有这些信息，debug 会很痛苦。

这也是工程里常见的做法：

```text
不要只返回结果，还要返回结果是怎么来的。
```

### 7. 本节抽取式压缩怎么选内容

本节规则比较简单：

```text
先从 query 中提取关键词。
把 chunk 拆成若干文本单元。
给包含 query 关键词的文本单元打分。
优先保留分数高的单元。
如果没有匹配，就退回 head-tail 截取。
```

head-tail 截取意思是：

```text
保留开头一部分。
保留结尾一部分。
中间用 ... 省略。
```

为什么不只保留开头？

因为很多文档前面是背景说明。

答案可能在中间或后面。

head-tail 至少比单纯 `content[:max_chars]` 稍微稳一点。

### 8. 为什么要保留输入顺序

压缩函数不会重新排序 chunks。

原因是：

```text
排序应该由 retrieval / hybrid / rerank 负责。
compression 只负责缩短上下文。
```

如果压缩模块又重新排序，就会造成职责混乱。

所以本节保持：

```text
输入是什么顺序，输出保留的 chunks 就是什么顺序。
```

这也方便 citation 的 `source_index` 对应最终上下文顺序。

### 9. 压缩可能带来的风险

压缩不是只有好处。

它可能带来新风险：

```text
1. 把关键限制条件压掉。
2. 保留了答案句，丢掉了例外条件。
3. 多个 chunk 被压缩后上下文断裂。
4. metadata 保留了，但 content 证据变少。
5. 低质量压缩会误导模型。
```

比如原文：

```text
退款通常 1 到 3 个工作日到账。但特殊活动订单以活动规则为准。
```

如果压缩后只剩：

```text
退款通常 1 到 3 个工作日到账。
```

模型可能忽略特殊活动限制。

所以压缩报告非常重要。

后续做坏例分析时，要看：

```text
是检索没找到？
是 rerank 排错？
是 compression 把关键信息丢了？
是模型生成错了？
是 citation 校验没挡住？
```

## 本节代码讲解

### 1. 新增 `ContextCompressionAction`

代码：

```python
class ContextCompressionAction(str, Enum):
    KEEP_FULL = "keep_full"
    COMPRESS = "compress"
    DROP = "drop"
```

这三个动作就是上下文压缩最核心的结果。

如果你能看懂这三个动作，就能看懂大部分压缩报告。

### 2. 新增 `ContextCompressionPolicy`

代码核心：

```python
class ContextCompressionPolicy(BaseModel):
    max_total_chars: int
    max_chunk_chars: int
    min_chunk_chars: int
    always_keep_top_n: int
```

这段代码的学习重点不是 Pydantic 写法，而是预算思想：

```text
总预算控制整体长度。
单 chunk 预算防止一个 chunk 独占上下文。
最小 chunk 预算防止塞入没有意义的碎片。
top_n 优先保留高排名资料。
```

### 3. 新增 `ContextCompressionReport`

它让压缩结果可解释。

如果只返回：

```text
compressed_chunks
```

你不知道哪些 chunk 被丢了。

也不知道压缩节省了多少字符。

所以 report 里要有：

```text
items
debug_lines
saved_chars
dropped_chunk_count
compressed_chunk_count
```

真实项目里，这类 report 可以进入日志和评测系统。

### 4. `_compress_chunk_text()`

这个函数负责把一个长 chunk 变短。

它的策略是：

```text
如果原文能放下，直接返回。
如果太长，优先抽取包含 query 关键词的文本单元。
如果没有关键词匹配，使用 head-tail excerpt。
```

这属于：

```text
extractive compression。
```

它不会让模型总结，也不会制造新句子。

### 5. `_copy_chunk_with_compressed_content()`

这个函数把压缩后的 content 写回一个新的 `RetrievedChunk`。

重点是：

```text
不修改原 chunk。
复制出新的 chunk。
metadata 中增加压缩信息。
```

这样做更安全。

因为原始 retrieved chunks 可能还要用于：

```text
日志。
评测。
引用校验。
debug。
对比压缩前后效果。
```

## 本节测试讲解

新增测试：

```text
projects/ai-service/tests/test_rag_context_compression.py
```

测试覆盖：

```text
1. 预算足够时完整保留 chunks。
2. 长 chunk 会围绕 query 关键词抽取。
3. 预算耗尽时后续 chunks 会 drop。
4. 第二个 chunk 在预算允许时可以压缩保留。
5. 保留 chunks 的顺序不变。
6. 压缩后的 chunks 仍能交给 build_rag_context()。
7. debug lines 包含 keep/compress/drop 信息。
8. 空 query 和非法 policy 会报错。
```

本节测试没有讲太细，因为你之前要求：

```text
测试部分讲重要点即可，重点放在基础知识和主题系统讲解。
```

这里最重要的是：

```text
压缩结果必须可解释、可测试、可接入现有生成链路。
```

## 本节练习

### 练习 1：解释概念

问题：

```text
什么是 context compression？
```

参考答案：

```text
Context compression 是在模型上下文预算有限的情况下，对检索到的资料进行过滤、缩短或抽取，使最终传给模型的上下文更短、更聚焦、更少噪声。
它通常发生在检索/rerank 之后，生成回答之前。
```

### 练习 2：判断对错

问题：

```text
RAG 检索到的 chunk 越多，最终回答一定越好。这个说法对吗？
```

参考答案：

```text
不对。
更多 chunk 可能提高召回率，但也会增加噪声、成本和延迟。
如果无关资料太多，模型注意力会被分散，回答质量反而可能下降。
真实项目通常会先多召回，再 rerank，再压缩上下文。
```

### 练习 3：区分三件事

问题：

```text
过滤、裁剪、压缩有什么区别？
```

参考答案：

```text
过滤是决定某个 chunk 要不要进入上下文。
裁剪是超过长度就直接截断，通常比较粗糙。
压缩是保留 chunk 的高价值内容，让 chunk 变短。
裁剪可以看作最简单的一种压缩方式，但不一定保留最相关信息。
```

### 练习 4：解释策略

问题：

```text
为什么要有 max_total_chars、max_chunk_chars、min_chunk_chars？
```

参考答案：

```text
max_total_chars 控制最终上下文总长度。
max_chunk_chars 防止单个 chunk 占用过多预算。
min_chunk_chars 防止剩余预算太少时塞入没有意义的碎片。
这三个参数一起控制上下文长度和质量。
```

### 练习 5：说明风险

问题：

```text
上下文压缩有什么风险？
```

参考答案：

```text
压缩可能丢掉限制条件、例外说明、上下文前后关系或关键证据。
如果压缩策略不好，模型可能基于不完整资料回答。
所以压缩结果必须有 report 和 debug 信息，后续还要配合 citation verification 和评测。
```

## 自测题

### 自测 1

问题：

```text
Context Compression 通常放在 RAG 链路的哪个位置？
```

答案：

```text
通常放在检索、hybrid、rerank 之后，prompt 构造和模型生成之前。
```

### 自测 2

问题：

```text
Extractive Compression 和 Abstractive Compression 的区别是什么？
```

答案：

```text
Extractive Compression 只从原文中抽取片段，不改写事实。
Abstractive Compression 会用模型或算法重新总结、改写、合并内容。
前者更可追溯、更稳定；后者更短更自然，但更容易引入新错误。
```

### 自测 3

问题：

```text
为什么本节压缩后的结果仍然返回 RetrievedChunk？
```

答案：

```text
因为现有 RAG 生成模块接收 RetrievedChunk。
压缩后继续返回 RetrievedChunk，可以直接接入 build_rag_context() 和后续生成链路。
同时通过 metadata 记录压缩动作、原始排名、原始长度和最终长度。
```

### 自测 4

问题：

```text
为什么压缩模块不应该负责重新排序？
```

答案：

```text
重新排序是 retrieval、hybrid search 或 rerank 的职责。
compression 的职责是控制上下文长度和保留高价值内容。
如果压缩模块也排序，模块边界会混乱，也会影响 source_index 和调试。
```

### 自测 5

问题：

```text
上下文窗口很大的模型还需要 context compression 吗？
```

答案：

```text
仍然需要。
上下文窗口大不代表应该塞满。
长上下文会增加成本和延迟，也会引入噪声，使模型更难聚焦关键证据。
真实项目通常会给 RAG context 单独设置预算。
```

## 本节小结

本节完成了 RAG 生成前的一道重要工程控制：

```text
Context Compression。
```

你现在应该理解：

```text
RAG 不是资料越多越好。
上下文窗口和上下文预算不是一回事。
top_k、chunk 长度、metadata 和历史消息都会占预算。
压缩要发生在生成之前。
抽取式压缩更适合学习版和可追溯场景。
压缩结果必须有 report，不能只悄悄截断。
```

到这里，阶段 9 的链路继续完善：

```text
找更多候选
-> 排得更准
-> 压得更聚焦
-> 回答更可控
-> 引用更可校验
```

下一节适合学习：

```text
阶段 9 第 11 节：Metadata Filter：用户、租户、权限、业务域过滤。
```

因为上下文压缩解决的是“放多少、怎么缩短”。

下一节要解决：

```text
哪些资料从一开始就不应该被当前用户看到。
```
