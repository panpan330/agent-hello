# 阶段 9 第 9 节：引用来源校验：回答必须能对应原文

## 本节定位

本节学习：

```text
RAG 最终回答生成之后，后端如何检查“这个回答有没有可靠地对应到原文资料”。
```

前面几节我们已经学了：

```text
Query Rewrite：把用户问题改写得更适合检索。
Multi Query：一个问题扩展成多个检索角度。
Intent Classification：先判断问题该走 RAG、工具、闲聊还是拒答。
Hybrid Search：把向量检索和关键词检索融合。
Score Interpretation：看懂 score、distance、similarity。
Rerank：召回之后重新排序。
Real Rerank Adapter：为真实 rerank 模型预留工程边界。
```

这些能力都在解决一个问题：

```text
怎么把更可能有用的资料放到模型面前。
```

但是 RAG 链路还有另一个关键问题：

```text
模型拿到资料之后，最终回答是否真的来自这些资料？
```

这就是本节的主题：引用来源校验。

## 本节学习目标

学完本节，你要能做到：

1. 能解释什么是 grounded answer。
2. 能区分 source、chunk、citation、evidence。
3. 能说明为什么 RAG 有了检索结果仍然可能编造。
4. 能说明引用来源校验解决的是哪一层问题。
5. 能解释后端生成 citation 和模型自己生成 citation 的区别。
6. 能说明为什么 `source_index`、`chunk_id`、`source` 必须校验。
7. 能看懂 `CitationVerificationReport`。
8. 能看懂 blocking finding 和 warning finding 的区别。
9. 能说明“结构可追溯”和“语义完全支撑”不是一回事。
10. 能理解为什么本节用了轻量文本重叠评分，但不把它当成绝对事实判断。
11. 能理解为什么 no-context 回答不应该带 citations。
12. 能说明这一层在真实 RAG 系统里的作用和局限。

## 本节新增和修改

本节新增：

```text
projects/ai-service/app/rag/citation_verification.py
projects/ai-service/tests/test_rag_citation_verification.py
notes/stage9-09-citation-source-verification.md
```

本节修改：

```text
projects/ai-service/app/rag/README.md
docs/learning-progress.md
```

本节没有做：

- 不调用真实大模型。
- 不调用真实 embedding。
- 不启动 Qdrant。
- 不启动 Milvus。
- 不打开 VMware 虚拟机。
- 不写手动测试文档。
- 不改 Java 服务。
- 不做敏感信息扫描。

原因是本节是一个工程校验层，核心是把 RAG answer 和 retrieved chunks 做结构化对照。

## 一句话先讲透

引用来源校验做的事情是：

```text
检查最终回答返回的 citations 是否真的能追溯到本次检索出来的 chunks，并给出回答和原文之间的轻量支撑度提示。
```

它不是：

```text
替代大模型判断。
替代人工审核。
替代完整事实核查。
替代法律/医疗/金融级别的高风险审查。
```

它更像一道工程防线：

```text
先把明显的错引、漏引、假引用、状态不一致挡住。
再把“看起来可能没有原文支撑”的回答标出来，供日志、调试、评测或后续更强模型判断使用。
```

## 基础知识铺垫

### 1. 什么是 grounded answer

`grounded answer` 可以理解为：

```text
有依据的回答。
```

在 RAG 里，它的意思是：

```text
最终回答里的核心信息，应该能在检索出来的资料中找到依据。
```

比如知识库原文是：

```text
退款审核通过后，通常会在 1 到 3 个工作日内原路退回。
```

模型回答：

```text
退款审核通过后，一般会在 1 到 3 个工作日内退回到原支付方式。
```

这个回答就是比较 grounded 的，因为它的关键事实来自原文：

```text
退款审核通过后
1 到 3 个工作日
原路退回 / 原支付方式
```

如果模型回答：

```text
退款会在 30 分钟内到账。
```

这个回答就没有被原文支撑。

即使这个回答听起来很像客服话术，也不代表它是 grounded answer。

RAG 项目里最危险的情况不是模型不会回答，而是：

```text
模型回答得很自然，但内容没有依据。
```

### 2. RAG 为什么仍然会编造

很多初学者会误以为：

```text
只要用了 RAG，模型就不会胡说。
```

这是错误的。

RAG 只是把外部资料放进上下文，让模型更有机会根据资料回答。

但模型仍然可能出现这些问题：

```text
1. 检索结果本身不相关。
2. 检索结果相关但不完整。
3. rerank 排名不理想。
4. chunk 里只有部分信息。
5. 模型忽略了资料限制。
6. 模型把常识和资料混在一起。
7. 模型把多个 chunk 的信息错误拼接。
8. 模型引用了 A 资料，却回答了 B 资料里的内容。
9. 模型引用了真实 chunk，但回答内容并不在 chunk 里。
10. 模型生成了看起来像引用的假来源。
```

所以 RAG 的质量闭环不只包括：

```text
检索
排序
生成
```

还应该包括：

```text
引用校验
安全检查
评测回归
日志观测
坏例分析
```

本节就是补“引用校验”这一环。

### 3. source、chunk、citation、evidence 是什么

这几个词很容易混在一起。

我们分别讲清楚。

#### source

`source` 是资料来源。

在我们项目里常见形式是：

```text
refund-return-policy.md
order-shipping-policy.md
account-security-faq.md
```

它回答的是：

```text
这段知识来自哪个文件、文档、网页、知识库条目或业务来源？
```

source 的粒度通常比较粗。

一个 source 可能被切成多个 chunk。

#### chunk

`chunk` 是被切分之后的一小段资料。

原始文档可能很长，不能全部塞给 embedding 或模型，所以要切成多个 chunk。

chunk 通常有：

```text
chunk_id
content
metadata
score
```

其中 `chunk_id` 是工程里非常重要的稳定标识。

它回答的是：

```text
这次回答到底依据了哪一个具体资料片段？
```

如果只有 source，没有 chunk_id，追溯会比较粗。

例如：

```text
source = refund-return-policy.md
```

只能说明来自退款文档。

但是：

```text
chunk_id = refund_return_policy_chunk_0003
```

可以说明来自退款文档里的第几个切片。

真实项目里排查坏例时，chunk_id 非常有用。

#### citation

`citation` 是回答返回给调用方的引用信息。

它不是原文，而是一个指向原文的结构化指针。

我们项目里的 `RagCitation` 包含：

```text
source_index
source
title
section
chunk_id
score
```

它回答的是：

```text
这个回答引用了哪份资料、哪个位置、哪个 chunk？
```

注意：

```text
citation 不等于证据本身。
```

citation 更像“证据地址”。

#### evidence

`evidence` 是真正支持回答的原文证据。

比如用户问：

```text
退款多久到账？
```

回答：

```text
退款审核通过后通常 1 到 3 个工作日到账。
```

真正 evidence 是 chunk content 里的：

```text
退款审核通过后，通常会在 1 到 3 个工作日内原路退回。
```

所以四者关系可以这样理解：

```text
source：资料来自哪里
chunk：资料被切出来的具体片段
citation：回答里返回的引用指针
evidence：真正支撑回答的原文内容
```

### 4. 后端生成 citation 比模型生成 citation 更可靠

有两种常见做法：

```text
做法 A：让模型自己在回答里写引用。
做法 B：后端根据检索上下文生成 citation。
```

做法 A 的问题是：

```text
模型可能编造文件名。
模型可能编造页码。
模型可能把 chunk_id 写错。
模型可能引用并不存在的资料。
模型可能引用了真实资料但内容不对应。
```

做法 B 更稳：

```text
检索到了哪些 chunks，后端是知道的。
chunk_id 是后端拿到的。
source/title/section 是后端从 metadata 里取的。
score 是检索或 rerank 链路产生的。
```

所以我们项目在基础 RAG 阶段就已经做过一个重要选择：

```text
最终 citation 由后端根据 retrieved chunks 生成，不让模型自由编造。
```

这不是说后端生成 citation 就绝对正确。

它只是减少了一类错误：

```text
假来源。
```

但还剩另一个问题：

```text
回答内容是否真的被这些来源支撑？
```

这就是本节继续补的校验层。

### 5. 引用校验分两类

引用校验可以分成两类。

第一类是确定性校验：

```text
这个 source_index 是否存在？
这个 chunk_id 是否在本次 retrieved chunks 中？
source_index 指向的 chunk 和 citation.chunk_id 是否一致？
citation.source 是否等于 chunk.metadata["source"]？
no_context 状态是否错误携带了 citations？
answered 状态是否没有 citations？
```

这些可以靠代码精确判断。

第二类是支撑性估计：

```text
回答里的核心信息是否能在 cited chunk content 里找到？
```

这个难很多。

因为模型可能会改写表达。

比如：

```text
原文：原路退回。
回答：退回到原支付方式。
```

这两个说法语义接近，但字面不完全一样。

再比如：

```text
原文：1 到 3 个工作日。
回答：一般需要几个工作日。
```

字面重叠减少，但语义仍可能是有依据的。

所以本节代码只做轻量文本重叠评分。

它的定位是：

```text
用于发现明显可疑的回答。
用于 debug。
用于坏例分析。
用于自动化测试里的基本防线。
```

它不负责最终判断复杂语义是否完全一致。

### 6. blocking 和 warning 的区别

本节校验结果分两种严重程度：

```text
blocking
warning
```

`blocking` 表示结构上已经不可信。

例如：

```text
answered 回答没有 citation。
citation.chunk_id 不在本次 retrieved chunks 里。
source_index 超出范围。
source_index 指向 A chunk，但 citation 写的是 B chunk。
citation.source 和 chunk.metadata["source"] 不一致。
```

这些问题不是模型表达方式不同，而是工程结构错了。

所以可以直接认为：

```text
这个回答的引用不合格。
```

`warning` 表示需要注意，但不一定马上判死刑。

例如：

```text
回答和 cited chunk 的字面重叠较低。
同一个 chunk 被重复引用。
title 或 section 不一致。
no_context 状态下仍传入了 retrieved chunks。
```

这些可能是问题，也可能是边界情况。

比如低重叠可能是因为模型做了合理改写。

所以 warning 更适合进入：

```text
日志
debug 面板
评测报告
坏例分析
人工复核
```

### 7. 为什么不能只看 score 或 rerank_score

一个常见误区是：

```text
只要检索 score 高，回答就一定可靠。
```

这不成立。

score 只说明：

```text
query 和 chunk 在检索或 rerank 阶段看起来相关。
```

它不说明：

```text
最终回答的每一句话都来自这个 chunk。
```

比如用户问：

```text
退款多久到账？
```

系统检索到了退款政策，score 很高。

但模型回答：

```text
退款会在 30 分钟到账，并且赠送优惠券。
```

这个回答依然可能没有依据。

所以链路要分清楚：

```text
retrieval score：资料是否值得召回。
rerank score：候选资料是否更应该排前面。
citation verification：最终回答是否能追溯到资料。
```

它们不是同一个问题。

## 本节主题系统讲解

### 1. 引用来源校验在完整 RAG 链路里的位置

一个更完整的 RAG 链路可以这样看：

```text
用户问题
-> 意图识别
-> Query Rewrite / Multi Query
-> 向量检索 / 关键词检索
-> Hybrid Fusion
-> Rerank
-> 安全过滤
-> 构造上下文
-> 模型生成回答
-> 后端生成 citations
-> 引用来源校验
-> 返回结果 / 记录日志 / 进入评测
```

本节新增的位置在最后几步：

```text
模型生成回答
-> 后端生成 citations
-> 引用来源校验
```

它不是为了替换 retrieval。

它是为了回答一个新问题：

```text
前面的资料链路看起来工作了，但最终答案有没有引用混乱？
```

### 2. 本节新增的核心对象

本节新增文件：

```text
projects/ai-service/app/rag/citation_verification.py
```

它包含几类对象。

#### CitationVerificationPolicy

这个对象表示校验策略。

核心字段：

```text
require_citations_for_answered
min_answer_support_score
min_citation_support_score
warn_on_duplicate_citations
```

意思分别是：

```text
answered 状态是否必须有 citation。
整段 answer 与 cited chunks 的最低重叠评分。
单条 citation 对应 chunk 的最低重叠评分。
是否提示重复引用同一个 chunk。
```

为什么要有 policy？

因为真实项目里不同业务的严格程度不同。

内部客服知识库可以比较严格。

普通搜索摘要可以稍微宽一点。

高风险业务可能还要接入更强的事实核查模型或人工审核。

#### CitationVerificationFinding

这个对象表示一个校验问题。

核心字段：

```text
code
category
severity
message
citation_index
source_index
chunk_id
source
evidence
```

它的作用是：

```text
不要只返回 true/false，而要告诉开发者为什么不合格。
```

如果只返回 false，排查很痛苦。

如果返回结构化 finding，就可以知道：

```text
是 citation 缺失？
是 chunk_id 不存在？
是 source_index 错了？
是 source 不匹配？
是回答和原文重叠太低？
```

#### CitationVerificationReport

这个对象表示完整校验报告。

核心字段：

```text
answer_status
is_valid
retrieved_chunk_count
checked_citation_count
cited_chunk_count
missing_citation_count
answer_support_score
findings
debug_lines
```

它适合用于：

```text
接口调试
日志记录
评测脚本
坏例分析
测试断言
后续监控
```

### 3. `verify_rag_answer_sources()` 做了什么

核心函数是：

```python
verify_rag_answer_sources(rag_answer, retrieved_chunks, policy=None)
```

它接收两个东西：

```text
rag_answer：最终 RAG 回答，里面包含 answer、status、citations。
retrieved_chunks：本次用于生成回答的资料 chunks。
```

它做的事情可以拆成五步。

第一步：检查回答状态。

如果是：

```text
no_context
```

那么正常情况应该是：

```text
没有 citations。
```

因为系统都说没有可用上下文了，就不应该还说“我引用了某某资料”。

如果是：

```text
answered
```

那么正常情况应该是：

```text
有 retrieved chunks。
有 citations。
```

第二步：检查 citation 是否真的指向本次 retrieved chunks。

会检查：

```text
source_index 是否越界。
chunk_id 是否存在。
source_index 指向的 chunk_id 是否等于 citation.chunk_id。
```

第三步：检查 citation metadata。

会检查：

```text
citation.source 是否等于 chunk.metadata["source"]。
citation.title 是否等于 chunk.metadata["title"]。
citation.section 是否等于 chunk.metadata["section"]。
```

其中 source 不一致是 blocking。

title / section 不一致是 warning。

原因是 source 是最基础的来源标识，错了会严重影响追溯。

title / section 有时可能缺失或被规范化，所以先作为 warning。

第四步：计算回答与引用 chunk 的轻量支撑度。

它会提取文本里的关键词和中文字符组合，然后算重叠比例。

这不是语义判断。

它只是一个轻量信号：

```text
如果回答和原文几乎没有任何字面重叠，就应该被标出来。
```

第五步：生成 report 和 debug lines。

最后返回：

```text
CitationVerificationReport
```

### 4. 为什么 `source_index` 和 `chunk_id` 都要校验

你可能会问：

```text
有 chunk_id 不就够了吗？为什么还要 source_index？
```

因为它们解决的问题不同。

`source_index` 表示：

```text
这个引用对应第几个上下文资料块。
```

`chunk_id` 表示：

```text
这个引用对应哪个稳定资料片段。
```

如果只校验 source_index，可能出现：

```text
source_index=1
但 citation.chunk_id 写成了另一个 chunk。
```

如果只校验 chunk_id，可能出现：

```text
chunk_id 存在
但 source_index 指向的上下文位置不对。
```

真实调试时，这两种错都会让人混乱。

所以本节同时校验：

```text
source_index 存在。
chunk_id 存在。
source_index 指到的 chunk_id 必须等于 citation.chunk_id。
```

这就是引用结构的闭环。

### 5. 为什么 low overlap 只是 warning

本节有一个分数：

```text
answer_support_score
```

它表示：

```text
回答文本与被引用 chunk 文本的轻量词面重叠程度。
```

如果分数很低，说明回答可能没有被原文支撑。

但它不能直接判定“回答一定错”。

原因有三个。

第一，模型可能做了同义改写。

```text
原文：原路退回。
回答：退回到原支付方式。
```

第二，中文分词和表达变化会影响字面匹配。

```text
原文：修改登录密码。
回答：更新账号密码。
```

第三，有些回答会做归纳总结。

```text
原文分散在多个 chunk 里。
回答把它们合成一句话。
```

所以本节把低重叠设为 warning。

工程含义是：

```text
这条回答值得进一步检查。
```

而不是：

```text
这条回答一定错误。
```

### 6. 为什么要过滤英文停用词

本节实现里有一个小细节：

```text
ENGLISH_STOPWORDS
```

它过滤了：

```text
the
are
from
to
of
and
```

这类词。

原因是这些词太常见。

如果不过滤，就会出现假支撑。

比如回答：

```text
Customers can update account security settings from the profile page.
```

原文：

```text
Refunds are returned to the original payment method within 1 to 3 business days.
```

这两段业务含义完全不同。

但它们可能都包含：

```text
are
to
the
from
```

如果这些词参与评分，系统可能误以为有重叠。

所以要过滤一部分无业务含义的常见词。

这也是一个重要的工程思想：

```text
简单规则也要知道自己的误判来源。
```

### 7. 为什么本节不直接调用大模型做事实核查

可以用大模型做事实核查吗？

可以。

例如：

```text
把 answer 和 cited chunks 再交给一个 judge model。
让它判断 answer 是否被 evidence 支撑。
```

但本节没有这么做。

原因是：

```text
1. 本节目标是先建立确定性工程边界。
2. 自动化测试不应该依赖真实模型。
3. judge model 自身也可能误判。
4. 先有轻量规则，后续才能更好接入模型评测。
```

真实项目里更完整的做法可能是：

```text
确定性引用校验
-> 轻量重叠评分
-> 大模型 judge
-> 人工抽检
-> 回归评测集
```

本节完成的是前两层。

## 本节代码讲解

### 1. 新增文件：`citation_verification.py`

路径：

```text
projects/ai-service/app/rag/citation_verification.py
```

这个文件的职责是：

```text
验证 RagAnswer 的 citations 是否能追溯到 retrieved chunks。
```

它不负责：

```text
生成回答。
调用模型。
做检索。
做 rerank。
做权限过滤。
```

这符合我们之前一直在强调的模块边界。

### 2. `CitationVerificationPolicy`

它控制校验严格度：

```python
class CitationVerificationPolicy(BaseModel):
    require_citations_for_answered: bool = True
    min_answer_support_score: float = Field(default=0.12, ge=0, le=1)
    min_citation_support_score: float = Field(default=0.05, ge=0, le=1)
    warn_on_duplicate_citations: bool = True
```

这段代码值得掌握的点：

```text
1. 策略是配置对象，不写死在函数里。
2. 分数阈值限制在 0 到 1。
3. answered 默认必须有 citation。
4. 重复引用默认给 warning。
```

为什么阈值看起来比较低？

因为它只是轻量字面重叠，不是语义相似度。

阈值太高会误伤合理改写。

### 3. `CitationVerificationFinding`

它表示一个问题：

```python
class CitationVerificationFinding(BaseModel):
    code: str
    category: CitationFindingCategory
    severity: CitationFindingSeverity
    message: str
    citation_index: int | None
    source_index: int | None
    chunk_id: str | None
    source: str | None
    evidence: str | None
```

这里的关键不是字段多，而是：

```text
每一个问题都能定位。
```

比如：

```text
第几个 citation 出问题？
它声称 source_index 是多少？
它声称 chunk_id 是什么？
它声称 source 是什么？
实际期望值是什么？
```

这对排查 RAG 坏例很重要。

### 4. `CitationVerificationReport`

报告对象包含：

```text
answer_status
is_valid
retrieved_chunk_count
checked_citation_count
cited_chunk_count
missing_citation_count
answer_support_score
findings
debug_lines
```

`is_valid` 的含义是：

```text
没有 blocking finding。
```

它不是说：

```text
回答在语义上 100% 正确。
```

这一点要记住。

在工程里，不同字段表达不同层次：

```text
is_valid：引用结构是否合格。
answer_support_score：回答和证据的轻量重叠程度。
findings：具体问题列表。
```

### 5. `verify_rag_answer_sources()`

这是入口函数。

伪流程如下：

```text
如果 answer.status 是 no_context：
    检查是否错误携带 citations。
    检查是否仍传入 retrieved chunks。

如果 answer.status 是 answered：
    检查有没有 retrieved chunks。
    检查有没有 citations。
    检查每个 citation 是否能追溯到 chunk。
    检查 source/title/section metadata。
    计算 answer_support_score。
    低支撑度给 warning。

最后：
    如果没有 blocking finding，is_valid=True。
    生成 debug_lines。
```

这就是本节的核心。

### 6. `_inspect_citations()`

这个内部函数负责逐条检查 citation。

关键检查包括：

```text
source_index 是否存在。
chunk_id 是否在 retrieved chunks 中。
source_index 指向的 chunk_id 是否等于 citation.chunk_id。
source metadata 是否一致。
title/section metadata 是否一致。
是否重复引用同一个 chunk。
回答与该 chunk 的文本重叠是否太低。
```

这里最重要的代码思想是：

```text
引用校验不是只看一个字段，而是多个字段互相印证。
```

这和真实后端系统很像。

例如订单系统不会只看 order_id，也会看 user_id、tenant_id、permission、status。

RAG 引用也是一样：

```text
chunk_id
source_index
source
title
section
```

这些字段共同组成可信追溯链。

### 7. `_extract_evidence_terms()`

这个函数做轻量文本特征提取。

它提取两类东西：

```text
英文/数字词。
中文字符组合。
```

同时过滤英文停用词。

它不是完整 NLP 分词器。

本节不用复杂分词库，原因是：

```text
1. 保持学习版本轻量。
2. 自动化测试稳定。
3. 先理解校验思想，不引入额外依赖。
```

以后如果要做得更强，可以换成：

```text
中文分词。
embedding 相似度。
NLI 模型。
LLM judge。
人工标注评测集。
```

## 本节测试讲解

本节新增测试：

```text
projects/ai-service/tests/test_rag_citation_verification.py
```

测试覆盖：

```text
1. 后端生成的正常 citation 可以通过。
2. no_context 且没有 citations 可以通过。
3. answered 但没有 citations 会被 blocking。
4. source_index 越界会被 blocking。
5. chunk_id 不在 retrieved chunks 中会被 blocking。
6. source_index 指向的 chunk 和 citation.chunk_id 不一致会被 blocking。
7. source metadata 不一致会被 blocking。
8. 回答和原文重叠过低会给 warning。
9. 重复引用同一 chunk 会给 warning。
10. debug lines 包含关键排查信息。
```

测试不调用真实大模型。

测试不调用 Qdrant / Milvus。

测试只验证：

```text
引用校验规则本身是否稳定。
```

这符合我们之前的原则：

```text
自动化测试不要依赖外部模型和外部服务。
```

## 本节和前面几节的关系

### 和 Rerank 的关系

Rerank 解决：

```text
哪些候选资料应该排在前面。
```

引用校验解决：

```text
最终回答引用的资料是否真实、是否对应。
```

Rerank 发生在生成前。

引用校验发生在生成后。

### 和 RAG Security 的关系

RAG Security 解决：

```text
资料能不能进入模型上下文。
```

比如：

```text
权限组不允许。
资料里有提示注入。
资料里有敏感数据。
```

引用校验解决：

```text
回答出来后，引用是否可信。
```

一个在输入侧。

一个在输出侧。

### 和 Evaluation 的关系

Evaluation 解决：

```text
整体检索效果和回答质量怎么评测。
```

引用校验可以成为 evaluation 的一个指标。

比如：

```text
多少回答没有 citation？
多少 citation 指向不存在的 chunk？
多少回答出现低支撑度 warning？
哪些问题最容易错引？
```

后续做评测平台时，这些 finding 都可以被统计。

## 真实项目里的使用方式

真实接口里可能会这样用：

```text
retrieved_chunks = retrieve(...)
reranked_chunks = rerank(...)
answer = rag_answer_service.generate_answer_with_citations(...)
verification_report = verify_rag_answer_sources(answer, reranked_chunks)

if not verification_report.is_valid:
    记录日志
    返回兜底
    或进入人工审核
```

注意这里传入的 chunks 应该是：

```text
真正用于生成回答的 chunks。
```

不要拿“原始召回的 100 个 chunks”去校验最终回答。

因为模型可能只看到了 rerank 后的 top 5。

引用校验必须对照：

```text
模型实际看到的上下文。
```

否则会误判。

## 本节局限

本节是学习版本，不是最终生产版本。

它的局限包括：

```text
1. 文本重叠不是语义蕴含判断。
2. 不知道回答里的每一个事实分别对应哪一段原文。
3. 不会做句子级 claim 拆分。
4. 不会判断数值是否被错误改写。
5. 不会判断多个 chunk 拼接后是否形成错误结论。
6. 不会调用 judge model。
7. 不会做人审流程。
```

但它已经补上了非常重要的一层：

```text
引用结构必须真实可追溯。
```

这是做真实 RAG 系统的底线能力。

## 以后可以怎么增强

后续可以增强成四层：

第一层：

```text
结构校验。
```

也就是本节做的：

```text
source_index / chunk_id / source / status / citation 数量。
```

第二层：

```text
文本重叠和关键词支撑。
```

本节已经做了轻量版本。

第三层：

```text
句子级 claim -> evidence 对齐。
```

例如把回答拆成：

```text
退款审核通过后会原路退回。
退款通常 1 到 3 个工作日到账。
特殊活动订单以活动规则为准。
```

然后分别找 evidence。

第四层：

```text
LLM judge / NLI / 人工抽检。
```

这层更强，但成本更高。

## 本节练习

### 练习 1：解释概念

问题：

```text
source、chunk、citation、evidence 分别是什么？
```

参考答案：

```text
source 是资料来源，比如某个 Markdown 文件、网页、知识库条目。
chunk 是原始资料切分后的具体片段，有 chunk_id、content、metadata、score。
citation 是回答返回的引用指针，告诉调用方引用了哪个 source 和 chunk。
evidence 是真正支撑回答内容的原文。
```

### 练习 2：判断是否合格

问题：

```text
RAG 回答状态是 answered，但 citations 是空列表，这算不算合格？
```

参考答案：

```text
通常不合格。
因为 answered 表示系统根据资料回答了用户问题。
既然是根据资料回答，就应该至少返回一个 citation。
否则用户和开发者都无法追溯答案来源。
在本节代码里，这会产生 RAG_ANSWERED_WITHOUT_CITATIONS，属于 blocking finding。
```

### 练习 3：解释 source_index 和 chunk_id

问题：

```text
为什么 citation 里有了 chunk_id，还要检查 source_index？
```

参考答案：

```text
chunk_id 表示稳定资料片段。
source_index 表示它对应模型上下文里的第几个资料块。
如果 source_index 指向 A chunk，但 citation.chunk_id 写成 B chunk，说明引用位置和引用标识不一致。
这会导致调试和用户追溯混乱，所以两者都要检查。
```

### 练习 4：判断 warning

问题：

```text
回答和 cited chunk 的字面重叠很低，为什么本节只给 warning，而不是直接判 invalid？
```

参考答案：

```text
因为字面重叠不是语义判断。
模型可能用同义表达、概括表达或跨 chunk 总结。
低重叠说明回答可疑，应该记录和复核，但不能直接证明回答一定错误。
所以本节把它设为 warning。
```

### 练习 5：设计生产增强

问题：

```text
如果真实项目要求更严格的引用校验，可以在本节基础上加什么？
```

参考答案：

```text
可以加句子级 claim 拆分、claim 到 evidence 的对齐、NLI 模型、LLM judge、人工抽检、评测集回归、错误样本统计和监控告警。
但这些应该建立在本节的结构化引用校验之上。
```

## 自测题

### 自测 1

问题：

```text
RAG 使用了检索资料，是否代表模型一定不会编造？
```

答案：

```text
不是。
RAG 只是把资料提供给模型，模型仍然可能忽略资料、误解资料、拼错资料、引用错误资料或补充没有依据的内容。
```

### 自测 2

问题：

```text
后端生成 citation 的优势是什么？
```

答案：

```text
后端知道本次检索和生成实际使用了哪些 chunks。
因此后端可以从 retrieved chunks 的 metadata 中生成 source、title、section、chunk_id、score。
这比让模型自由编造引用更稳定。
```

### 自测 3

问题：

```text
什么情况下 citation 校验应该 blocking？
```

答案：

```text
source_index 越界、chunk_id 不在本次 retrieved chunks 中、source_index 指向的 chunk 和 citation.chunk_id 不一致、citation.source 和 chunk metadata 不一致、answered 状态没有 citation。
这些都属于结构不可追溯的问题。
```

### 自测 4

问题：

```text
answer_support_score 低说明什么？
```

答案：

```text
说明回答文本和被引用 chunks 的字面重叠较低，回答可能缺少原文支撑。
但它不是绝对语义判断，只能作为 warning、debug 和坏例分析信号。
```

### 自测 5

问题：

```text
引用来源校验应该对照原始召回结果，还是对照模型实际看到的上下文？
```

答案：

```text
应该对照模型实际看到的上下文。
如果模型只看到了 rerank 后的 top 5，就应该拿这 top 5 校验。
否则会把模型根本没看到的 chunk 也算作可用依据，导致错误判断。
```

## 本节小结

本节完成了 RAG 生成后的一个关键工程防线：

```text
引用来源校验。
```

你现在应该能理解：

```text
检索相关不等于回答有依据。
rerank 排名前不等于最终回答正确。
citation 不等于 evidence。
后端生成 citation 可以减少假来源。
引用校验可以挡住明显的错引、漏引、假引用。
轻量支撑度评分只能作为 warning，不能当成绝对事实判断。
```

到这里，阶段 9 的 RAG 质量链路又补上了一环：

```text
召回更好
-> 排序更准
-> 引用可追溯
-> 回答更容易调试和评测
```

下一节适合继续学习：

```text
阶段 9 第 10 节：Context Compression：上下文压缩。
```

因为当检索和 rerank 能找到更多候选资料之后，我们马上会遇到新问题：

```text
不能把所有 chunk 都塞进模型上下文。
```
