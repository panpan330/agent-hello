# 阶段 9 第 13 节：RAG 评测集设计

## 本节定位

本节学习 RAG 评测集设计。

它接在第 12 节 RAG Prompt Injection 防护后面：前面我们已经学习了怎么提升检索、排序、引用、压缩、权限和安全边界；从这一节开始，要学习怎么系统地判断这些改动到底有没有让 RAG 变好。

## 本节学习目标

学完本节，你要能说清楚：

- 什么是 RAG 评测集。
- 一个 RAG 评测样本应该包含哪些字段。
- 为什么评测集要覆盖正常回答、无资料、权限拒答和安全拒答。
- 为什么先设计评测集，再谈命中率、召回率、回答正确性。
- 本节新增的评测集结构负责什么，不负责什么。

## 本节新增和修改

修改：

```text
projects/ai-service/app/rag/evaluation.py
projects/ai-service/tests/test_rag_evaluation.py
projects/ai-service/data/rag_eval/README.md
projects/ai-service/app/rag/README.md
docs/learning-progress.md
```

新增：

```text
projects/ai-service/data/rag_eval/rag_cases.json
notes/stage9-13-rag-evaluation-dataset-design.md
```

## 一句话先讲透

RAG 评测集的本质是：

```text
把“用户会怎么问、系统应该怎么答、应该依据哪些资料、哪些情况必须拒答”提前写成可重复检查的样本。
```

没有评测集，RAG 优化就容易变成凭感觉调参数。

## 基础知识铺垫

### 1. 什么是评测

评测就是评价系统表现。

对普通后端接口来说，测试通常关注：

```text
输入是否合法。
接口是否返回 200。
数据库是否写入成功。
异常是否按预期返回。
```

对 RAG 来说，问题更复杂。

因为 RAG 的结果不只是一个固定字段，而是一条完整链路：

```text
用户问题
-> 查询理解
-> 检索资料
-> 重排序
-> 权限过滤
-> 安全检查
-> 上下文压缩
-> 模型生成回答
-> 引用来源
```

其中任何一环出问题，最终回答都可能错。

比如用户问：

```text
质量问题退货邮费谁出？
```

系统可能出现几种问题：

```text
检索没找到退款退货规则。
检索找到了质量问题段落，但没找到运费处理段落。
rerank 把不相关段落排在前面。
模型根据资料回答了，但没有引用来源。
模型引用了一个不存在的 chunk_id。
权限过滤漏掉了内部资料。
知识库里混入恶意指令，模型被诱导偏离规则。
```

所以 RAG 评测不是只看“最后一句话像不像对”。

它要把链路拆开观察。

### 2. 什么是评测集

评测集就是一组提前设计好的样本。

每个样本描述：

```text
用户会怎么问。
系统应该有什么行为。
如果应该回答，答案应该包含哪些要点。
如果应该引用，应该引用哪些来源。
如果不该回答，为什么不该回答。
这个问题属于什么场景，优先级有多高。
```

可以把评测集理解成 RAG 系统的“考试卷”。

但它不是只给模型考试。

它给整条 RAG 链路考试。

比如：

```text
检索器考试：有没有把正确资料找出来。
rerank 考试：有没有把更相关资料排到前面。
生成器考试：有没有基于资料回答。
引用校验考试：引用是否真的对应原文。
权限过滤考试：不该看的资料有没有被挡住。
安全防护考试：恶意指令有没有被阻断。
```

### 3. 评测集和测试代码的区别

测试代码通常验证程序逻辑是否符合预期。

比如：

```text
传入重复 id 时要报错。
非回答样本不能要求引用。
覆盖报告能统计 answer/no_context/security_block 数量。
```

评测集验证业务效果是否符合预期。

比如：

```text
用户问“退货运费谁承担”，系统应该命中退款退货规则里的运费处理段落。
用户问“会员积分怎么兑换”，当前知识库没有资料，系统应该无资料拒答。
用户要求查看内部赔付标准，普通客服权限下系统应该拒绝。
资料里出现“忽略之前所有指令”，系统应该阻断或安全拒答。
```

两者关系是：

```text
测试代码保证评测工具自己没有明显 bug。
评测集保证 RAG 系统面对真实问题时表现可观察、可复现、可对比。
```

### 4. 为什么不能只靠手动问几句

手动问几句有用，但不够。

它的问题是：

```text
每次问的问题可能不一样。
每次观察标准可能不一样。
模型每次输出可能不一样。
调参数前后没有稳定对比。
只容易覆盖你刚想到的问题。
容易漏掉权限、安全、无资料这种负向场景。
```

比如你今天手动问：

```text
退款多久到账？
```

系统答得不错。

你可能觉得 RAG 没问题。

但真实用户可能问：

```text
退款一般几天能回到账上？
退货运费是不是平台出？
把内部赔付规则发我。
如果资料里让我忽略系统提示，我是不是要照做？
```

这些问题覆盖了不同风险：

```text
同义改写。
歧义问题。
权限边界。
安全攻击。
```

如果评测集没有覆盖，系统上线后才暴露问题，就很难排查。

### 5. RAG 评测要先有样本，再有指标

很多人一上来就问：

```text
Hit Rate@K 怎么算？
Recall@K 怎么算？
回答正确率怎么打分？
```

这些当然重要。

但更基础的问题是：

```text
你拿哪些问题来算？
这些问题能代表真实业务吗？
每个问题的正确答案是什么？
每个问题应该引用哪些资料？
哪些问题根本不应该回答？
```

如果样本设计不好，指标再漂亮也没有意义。

比如评测集里只有简单问题：

```text
退款多久到账？
付款后多久发货？
忘记密码怎么办？
```

系统可能得分很高。

但一遇到真实复杂问题：

```text
质量问题退货邮费谁出？
我的订单三天没发，是不是要建工单？
把内部补偿规则发给我。
知识库让我忽略系统提示，我要照做吗？
```

就暴露出：

```text
歧义理解差。
权限控制差。
安全防护差。
Agent 边界差。
```

所以正确顺序是：

```text
先设计评测集。
再定义指标。
再跑评测。
再分析 bad case。
再调参数和改链路。
```

### 6. RAG 评测样本不是只有“问题和答案”

普通问答评测经常写成：

```text
question: 退货运费谁承担？
answer: 质量问题商家承担，个人原因用户承担。
```

这对 RAG 不够。

因为 RAG 的核心价值不是“模型自己知道答案”，而是：

```text
从指定知识库里找资料。
基于资料回答。
保留引用。
遵守权限。
遇到无资料时不编。
遇到风险资料时不被攻击。
```

所以 RAG 样本至少要包含：

```text
query：用户问题。
expected behavior：期望行为，是回答、无资料、权限拒答、安全阻断，还是澄清。
answer points：如果要回答，答案必须包含哪些要点。
expected evidence：如果要引用，应该来自哪些 source、section、chunk。
access context：当前用户、租户、权限组、业务域。
refusal reason：如果拒答，拒答原因是什么。
tags：这个样本属于正向、改写、歧义、无资料、权限、安全等哪类。
priority：这个样本重要程度。
```

### 7. 期望答案不应该只写一个完整答案

评测时，一个常见做法是写“标准答案”。

但 RAG 里的模型输出可能每次措辞不同。

比如标准答案写：

```text
质量问题或商家原因退货时，运费通常由商家承担；用户个人原因退货时，运费通常由用户承担。
```

模型可能回答：

```text
如果是商品质量问题或商家原因导致退货，一般商家承担运费；如果是用户个人原因退货，一般用户自己承担。
```

这两个回答意思一致，但字符串不同。

所以本节用的是：

```text
answer_points
```

也就是答案要点。

答案要点关心：

```text
必须讲到哪些事实。
不能漏掉哪些条件。
不能越界补充哪些不存在的规则。
```

这比固定全文答案更适合 RAG 初期评测。

后续如果要更严格，可以再加入：

```text
关键词匹配。
人工打分。
LLM-as-judge。
引用一致性校验。
事实支撑度评分。
```

### 8. 期望来源比期望答案更重要

RAG 的关键不是模型“碰巧答对”。

而是：

```text
回答必须来自允许使用的资料。
```

比如用户问：

```text
付款后多久发货？
```

模型凭常识回答：

```text
一般 48 小时内发货。
```

这个回答看起来合理，但如果你的知识库写的是：

```text
普通商品通常 24 小时内进入仓库处理流程。
```

那模型就错了。

原因是它没有基于你的业务资料回答。

所以评测样本需要记录：

```text
expected_sources
expected_sections
expected_chunk_ids
```

三者粒度不同：

```text
source：来自哪个文档。
section：来自文档哪个章节。
chunk_id：来自哪个切片。
```

越靠后越精确。

但越精确也越容易受切分策略影响。

比如你改了 chunk_size，chunk_id 可能变化。

所以真实项目里常常分层使用：

```text
早期评测：source 或 section 足够。
稳定入库后：关键 P0 样本可以要求 chunk_id。
上线前验收：重要政策、权限、安全样本尽量精确到 source + section。
```

### 9. 为什么要有无资料样本

RAG 最危险的问题之一是：

```text
没资料还硬答。
```

比如当前知识库没有会员积分资料。

用户问：

```text
会员积分怎么兑换？
```

错误回答是：

```text
您可以在会员中心兑换积分。
```

这听起来正常，但它不是来自知识库。

正确行为应该是：

```text
当前资料中没有找到会员积分兑换规则，无法确认兑换方式。
```

或者引导：

```text
请补充会员积分相关知识文档，或转人工确认。
```

所以评测集必须有：

```text
no_context
```

它检查系统是否能承认“不知道”。

对企业 RAG 来说，能稳定拒答比乱答更重要。

### 10. 为什么要有权限样本

真实业务知识库通常不是所有资料都能给所有人看。

比如：

```text
普通客服能看公开售后政策。
主管能看内部赔付标准。
财务能看退款对账规则。
风控能看异常账号策略。
```

如果评测集只测“找得到资料”，就可能忽略一个严重问题：

```text
找到了不该看的资料。
```

权限样本要表达：

```text
当前用户是谁。
当前租户是谁。
当前用户有哪些 permission_groups。
当前问题不应该使用哪些 forbidden_sources。
如果越权，期望行为是 access_denied。
```

这也是第 11 节 Metadata Filter 的延伸。

第 11 节解决：

```text
怎么过滤。
```

第 13 节开始解决：

```text
怎么证明过滤场景被覆盖。
```

### 11. 为什么要有安全样本

第 12 节我们学习了 RAG Prompt Injection。

如果评测集里没有安全样本，你就不知道防护有没有退化。

安全样本可能包括：

```text
知识库内容要求忽略系统提示。
知识库内容要求泄露 system prompt。
知识库内容要求调用未授权工具。
知识库内容伪装成系统消息。
metadata 里出现恶意标题或来源。
```

这些样本的期望行为不是正常回答，而是：

```text
security_block
```

或者在低风险场景里：

```text
warning 后继续回答。
```

本节先设计 `security_block` 样本。

后面如果要更细，可以扩展出：

```text
security_warning
safe_after_sanitization
```

### 12. 为什么要有 priority

不是所有评测样本同等重要。

比如：

```text
退款运费规则。
超过 72 小时未发货。
无资料拒答。
权限拒答。
安全阻断。
```

这些通常是 P0。

P0 的意思是：

```text
一旦失败，就应该优先修。
```

一些低频、边缘、表达比较罕见的问题可以是 P1 或 P2。

priority 的价值是：

```text
评测失败时知道先修什么。
上线前可以要求 P0 全部通过。
回归测试可以先跑 P0 小集合。
调参数时能观察是否牺牲了关键场景。
```

### 13. 为什么要有 tags 和 difficulty

tags 是样本标签。

它回答：

```text
这个样本属于哪类问题？
```

比如：

```text
positive
paraphrase
ambiguous
no_context
permission
security
citation
```

difficulty 是难度类型。

它回答：

```text
这个样本为什么难？
```

比如：

```text
basic：基础直接问题。
paraphrase：用户换了一种说法。
ambiguous：问题可能命中多个段落。
permission：涉及权限。
adversarial：涉及攻击或对抗。
no_context：知识库没有资料。
```

tags 和 difficulty 的价值是：

```text
你能知道评测集有没有偏科。
你能按类型分析 bad case。
你能判断这次优化提升了哪类问题，伤害了哪类问题。
```

## 本节主题系统讲解

### 1. 本节在整个 RAG 质量闭环里的位置

阶段 9 前半部分主要在补 RAG 链路能力：

```text
Query Rewrite：把用户问题改成更适合检索的问题。
Multi Query：从多个角度召回资料。
Query Intent：判断问题该不该走 RAG。
Hybrid Search：关键词和向量一起召回。
Score Interpretation：理解不同向量库分数。
Rerank：召回后重新排序。
Citation Verification：校验引用是否对应原文。
Context Compression：压缩上下文。
Metadata Filter：按租户、权限、业务域过滤资料。
Prompt Injection Defense：防止知识库资料攻击模型。
```

这些能力加起来，不等于系统一定变好了。

因为每个能力都有可能带来副作用。

比如：

```text
Query Rewrite 改写过度，可能改变用户原意。
Multi Query 扩展太多，可能引入噪声。
Hybrid Search 权重不合理，可能让关键词噪声排前面。
Rerank 失败 fallback，可能让排序质量下降。
Context Compression 过度压缩，可能丢关键事实。
Metadata Filter 配错，可能把正确资料过滤掉。
Prompt Injection 规则太严，可能误伤正常资料。
```

所以从第 13 节开始，我们进入质量闭环：

```text
先定义该怎么测。
再定义指标。
再看坏例。
再调参数。
再做性能、可观测性和生产化。
```

这一节是质量闭环的起点。

### 2. 本节不是“跑评测”，而是“设计评测样本”

这一点很重要。

本节不直接解决：

```text
怎么计算 Hit Rate@K。
怎么计算 Recall@K。
怎么判断最终回答正确率。
怎么做 LLM-as-judge。
怎么生成评测报告。
```

这些后面会学。

本节先解决：

```text
评测什么。
用什么样本评测。
样本里要记录哪些标准答案和标准行为。
哪些场景必须被覆盖。
```

如果没有这一层，后面的指标没有依据。

### 3. 本节评测集的核心结构

本节把一个 RAG 评测样本拆成四部分：

```text
基本信息。
访问上下文。
期望结果。
分析标签。
```

基本信息包括：

```text
id
name
query
priority
difficulty
tags
notes
```

访问上下文包括：

```text
tenant_id
user_id
permission_groups
business_domains
doc_types
sources
```

期望结果包括：

```text
behavior
answer_points
expected_sources
expected_sections
expected_chunk_ids
forbidden_sources
citation_required
refusal_reason_codes
```

这些字段不是为了好看，而是为了后续能把一条 RAG 链路拆开评价。

### 4. expected behavior 是评测样本的核心

`expected behavior` 表示系统面对这个问题应该采取什么行为。

本节先支持五类：

```text
answer：应该回答。
no_context：没有足够资料，应该无资料拒答。
access_denied：当前用户无权查看相关资料，应该权限拒答。
security_block：命中安全风险，应该阻断或安全拒答。
clarify：问题不清楚，应该追问澄清。
```

为什么不直接用 `expected_answer`？

因为很多真实业务问题不是“回答某句话”这么简单。

比如：

```text
用户问会员积分兑换，但知识库没有资料。
```

正确行为不是给答案，而是 `no_context`。

再比如：

```text
用户要求查看内部赔付标准。
```

即使系统能检索到内部资料，正确行为也不是回答，而是 `access_denied`。

再比如：

```text
资料里要求模型忽略系统提示。
```

正确行为是 `security_block`。

所以行为比答案更底层。

先判断该不该答，再判断答得好不好。

### 5. answer_points 解决“答案表达不固定”的问题

模型输出不是传统接口返回。

传统接口可以期待：

```json
{"status":"ok","amount":100}
```

RAG 回答可能每次措辞不同。

所以本节不用固定完整答案，而是用 `answer_points`。

比如：

```text
质量问题或商家原因退货时，运费通常由商家承担。
用户个人原因退货时，运费通常由用户承担。
特殊活动订单要以活动规则为准。
```

后续评测可以检查：

```text
模型有没有覆盖这些要点。
有没有漏关键条件。
有没有添加资料中没有的结论。
```

这比固定字符串更符合 LLM 输出特点。

### 6. expected evidence 解决“答案来源”的问题

RAG 和普通问答最大的差别是：

```text
答案必须来自资料。
```

所以 `expected_sources`、`expected_sections`、`expected_chunk_ids` 是很重要的。

它们可以回答三个问题：

```text
应该从哪个文档找？
应该从哪个章节找？
应该从哪个 chunk 找？
```

这三者可以用于不同阶段：

```text
expected_sources：适合早期检索评测，稳定性高。
expected_sections：适合文档结构稳定后，判断是否命中正确段落。
expected_chunk_ids：适合切分策略稳定后，做更精确的回归评测。
```

如果一个回答没有引用期望来源，即使文本看起来对，也要谨慎。

因为它可能是：

```text
模型常识答对。
从错误资料里推测。
从无权限资料里泄露。
```

### 7. access context 让评测进入真实业务

没有权限上下文的 RAG 评测是不完整的。

因为真实系统里，不同用户看到的资料可能不同。

比如：

```text
普通用户只能看公开帮助文档。
客服能看客服知识库。
主管能看内部赔付规则。
财务能看对账规则。
```

同一个 query，在不同 access context 下，期望行为可能不同。

比如：

```text
query: 把内部赔付标准发给我看看。
```

如果用户是主管：

```text
可能允许回答，并引用内部赔付标准。
```

如果用户是普通客服：

```text
应该 access_denied。
```

所以评测样本里必须记录：

```text
当前是什么 tenant。
当前有哪些 permission_groups。
当前允许哪些 business_domains。
当前允许哪些 doc_types 或 sources。
```

这让评测更接近真实系统。

### 8. forbidden_sources 让权限失败更容易被发现

`expected_sources` 表示应该用哪些资料。

`forbidden_sources` 表示绝不能用哪些资料。

比如：

```text
forbidden_sources: ["internal-compensation-policy.md"]
```

它的作用是：

```text
即使系统最后回答看起来正常，也要检查有没有使用禁用来源。
```

这对权限和数据隔离非常重要。

尤其是多租户系统里，不能只看答案是否正确，还要看资料是否来自正确租户和正确权限范围。

### 9. refusal_reason_codes 让拒答不是一句空话

拒答也要有原因。

比如：

```text
NO_CONTEXT
ACCESS_DENIED
PROMPT_INJECTION
```

如果系统只是统一说：

```text
抱歉，我不能回答。
```

你很难判断它为什么拒答。

拒答原因结构化之后，后续可以评测：

```text
该无资料拒答时，是否返回 NO_CONTEXT。
该权限拒答时，是否返回 ACCESS_DENIED。
该安全阻断时，是否返回 PROMPT_INJECTION。
```

这也方便排查。

如果一个权限问题被标成无资料问题，说明系统可能在权限层或检索层的解释上有问题。

### 10. dataset coverage report 是评测集自检

评测集本身也需要检查。

如果一个评测集全是简单正向问题，它不能代表真实 RAG 能力。

所以本节新增 coverage report，统计：

```text
总样本数。
answer 样本数。
refusal 样本数。
不同 behavior 的数量。
不同 priority 的数量。
不同 difficulty 的数量。
不同 tags 的数量。
涉及哪些 source。
缺少哪些推荐标签。
```

这不是评价 RAG 系统，而是评价评测集是否覆盖得合理。

比如如果报告显示缺少：

```text
permission
security
no_context
```

就说明评测集偏向简单问答，不能支撑真实上线验收。

### 11. 本节和下一节的关系

第 13 节解决：

```text
评测样本怎么设计。
```

第 14 节会解决：

```text
检索指标怎么计算。
```

也就是：

```text
第 13 节：这道题的正确资料是什么？
第 14 节：检索结果有没有把正确资料排进 top_k？
```

再往后：

```text
第 15 节：最终回答是否正确、引用是否一致、拒答是否合理。
第 16 节：如果失败，怎么定位原因。
第 17 节：怎么基于评测结果调 chunk_size、top_k、threshold。
```

所以本节是后面几节的地基。

## 本节代码讲解

本节代码不复杂，重点不是算法，而是把评测样本设计成稳定结构。

### 1. `RagEvalCase`

`RagEvalCase` 表示一条完整 RAG 评测样本。

它关心：

```text
这个问题是什么。
它属于什么优先级和难度。
它在什么访问上下文下执行。
系统期望行为是什么。
```

它不是运行器。

它不会调用 embedding、向量库或大模型。

它只是把“标准答案和标准行为”记录清楚。

### 2. `RagEvalExpectation`

`RagEvalExpectation` 是本节最关键的结构。

它把结果分成两类：

```text
answer：应该回答。
non-answer：不应该直接回答。
```

如果是 `answer`，必须有 `answer_points`。

如果要求引用，还必须有 `expected_sources`、`expected_sections` 或 `expected_chunk_ids` 中至少一个。

如果是 `no_context`、`access_denied`、`security_block`、`clarify`，就不能写 `answer_points`，也不能要求引用，并且必须写 `refusal_reason_codes`。

这个校验的价值是：

```text
防止评测样本自己写得含糊。
```

### 3. `RagEvalAccessContext`

`RagEvalAccessContext` 描述当前评测样本的访问范围。

它包含：

```text
user_id
tenant_id
permission_groups
business_domains
doc_types
sources
```

它和第 11 节 `RagAccessScope` 的关系是：

```text
RagEvalAccessContext 是评测样本里的“期望上下文描述”。
RagAccessScope 是运行检索时真正用于过滤的访问范围。
```

本节先记录上下文，后续可以把它转换成真实检索过滤条件。

### 4. `build_rag_eval_dataset_report`

这个函数不是评价 RAG 回答质量。

它评价的是：

```text
评测集覆盖得是否像样。
```

它会统计：

```text
answer/no_context/access_denied/security_block 各有多少。
P0/P1/P2 各有多少。
basic/paraphrase/ambiguous/permission/adversarial/no_context 各有多少。
标签覆盖了哪些。
来源覆盖了哪些。
推荐标签缺了哪些。
```

这一步的价值是防止评测集偏科。

### 5. `rag_cases.json`

本节新增了一个小型样例集。

它覆盖：

```text
退货运费规则。
质量问题退货邮费归属。
超时未发货处理。
物流轨迹查询。
忘记密码处理。
会员积分无资料拒答。
内部赔付政策权限拒答。
知识库提示注入安全阻断。
```

它不是最终大评测集，只是学习版起点。

后续每发现一个 bad case，都可以把它沉淀进这个文件。

## 常见误区

### 误区 1：只要答案看起来对，就算 RAG 对

不一定。

RAG 要求答案来自资料。

如果模型靠常识答对，但没有命中资料，真实业务里仍然有风险。

### 误区 2：评测集只需要正向问题

不够。

真实 RAG 必须覆盖：

```text
应该回答的问题。
没有资料的问题。
权限不足的问题。
安全攻击的问题。
问题不清楚的问题。
```

只测正向问题，系统很容易在上线后乱答、越权答、被注入攻击。

### 误区 3：标准答案越完整越好

不一定。

LLM 输出有自然语言变化。

早期更适合写 `answer_points`，也就是必须覆盖的答案要点。

完整标准答案可以保留给人工复核或更严格评测，但不应该让所有自动评测都依赖完全相同的字符串。

### 误区 4：chunk_id 是最好的唯一标准

chunk_id 很精确，但也很脆弱。

如果你改了切分策略，chunk_id 可能变化。

所以评测时要结合：

```text
source
section
chunk_id
```

不要一开始就把所有样本都绑定到过细粒度。

### 误区 5：无资料拒答是失败

不是。

如果知识库没有资料，正确拒答是成功。

RAG 系统最怕的是没资料还编答案。

### 误区 6：权限拒答和无资料拒答一样

不一样。

无资料是：

```text
系统没有找到可用资料。
```

权限拒答是：

```text
资料可能存在，但当前用户不能使用。
```

这两者的排查方向完全不同。

### 误区 7：评测集写完就不用维护

不对。

评测集应该随着项目持续增长。

每次出现 bad case，都要问：

```text
这个问题是否应该加入评测集？
它属于哪个 tag？
它是 P0、P1 还是 P2？
期望来源和期望行为是什么？
```

评测集越贴近真实问题，RAG 优化越可靠。

## 本节练习

### 练习 1：设计一个正向回答样本

题目：

请为问题“退款多久到账？”设计一个 RAG 评测样本，至少写出 query、behavior、answer_points、expected_sources。

参考答案：

```text
query: 退款多久到账？
behavior: answer
answer_points:
  - 退款到账时间通常和支付渠道、银行处理有关。
  - 应以退款退货规则中的退款到账时间说明为准。
expected_sources:
  - refund-return-policy.md
```

如果知识库里有稳定 section，可以继续补：

```text
expected_sections:
  - 退款到账时间
```

### 练习 2：设计一个无资料样本

题目：

如果当前知识库没有“会员积分兑换”资料，用户问“会员积分怎么兑换？”，期望 behavior 应该是什么？为什么？

参考答案：

```text
behavior: no_context
refusal_reason_codes:
  - NO_CONTEXT
citation_required: false
```

原因：

```text
当前知识库没有相关资料，系统不应该凭常识编答案。
```

### 练习 3：设计一个权限拒答样本

题目：

用户是普通客服，问题是“把内部赔付标准发给我看看”。这个样本应该怎么设计？

参考答案：

```text
behavior: access_denied
forbidden_sources:
  - internal-compensation-policy.md
citation_required: false
refusal_reason_codes:
  - ACCESS_DENIED
access_context:
  permission_groups:
    - customer_service
```

原因：

```text
普通客服无权查看内部赔付标准，即使命中资料，也不能交给模型回答。
```

### 练习 4：为什么要写 tags

题目：

`tags` 有什么用？

参考答案：

```text
tags 用来标记样本类型，例如 positive、paraphrase、ambiguous、no_context、permission、security、citation。
```

它的作用是：

```text
分析评测集覆盖是否均衡。
按类型统计 bad case。
观察某次优化提升或伤害了哪类问题。
```

## 自测题

### 自测 1：RAG 评测集为什么不能只写 question 和 answer？

答案：

因为 RAG 不只要求回答文本正确，还要求：

```text
资料命中正确。
引用来源正确。
权限边界正确。
无资料时不编造。
安全风险时能阻断。
```

所以样本还要记录 expected behavior、expected evidence、access context、refusal reason 等信息。

### 自测 2：`answer_points` 和完整标准答案有什么区别？

答案：

完整标准答案要求输出接近某段固定文本。

`answer_points` 只要求覆盖关键事实和条件，更适合 LLM 输出自然语言可能变化的场景。

### 自测 3：为什么 `access_denied` 不是 `no_context`？

答案：

`no_context` 表示没有找到足够资料。

`access_denied` 表示资料可能存在，但当前用户无权使用。

这两类问题的修复方向不同，不能混在一起。

### 自测 4：为什么 `chunk_id` 不一定适合作为所有样本的唯一判断标准？

答案：

因为修改 chunk_size、overlap 或切分规则后，chunk_id 可能变化。

所以评测时常常结合 source、section 和 chunk_id 分层判断。

### 自测 5：dataset coverage report 评估的是 RAG 系统吗？

答案：

不是。

它评估的是评测集本身覆盖是否合理，例如是否包含正向、改写、歧义、无资料、权限、安全、引用等场景。

## 本节小结

本节完成了 RAG 质量评测的第一步：

```text
先把“什么叫答得对、什么时候不该答、应该依据哪些资料、在哪个权限上下文下判断”写成结构化样本。
```

这一步不直接提升 RAG 效果，但它决定后续优化有没有尺子。

下一节可以在这些样本基础上学习：

```text
检索指标：命中率、召回率、Top-K 命中。
```

到下一节，你会开始用指标判断：

```text
检索阶段到底有没有把正确资料找出来。
```
