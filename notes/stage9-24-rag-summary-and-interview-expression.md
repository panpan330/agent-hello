# 阶段 9 第 24 节：RAG 阶段总复盘和面试表达强化

## 本节定位

这是阶段 9 的最后一节。

阶段 9 的主题是：

```text
RAG 进阶与检索质量优化
```

前面 23 节我们已经从“基础 RAG 能跑通”走到了“RAG 可以被调优、被评测、被排查、被生产化验收”。

本节不新增业务代码。
本节要做的是把阶段 9 的知识整理成三种能力：

```text
能复盘：知道每个模块解决什么问题。
能表达：能把项目讲给别人听。
能应答：面试中能回答 RAG 准确率、评测、安全、生产化等问题。
```

## 本节学习目标

学完本节，你要能做到：

```text
1. 用一条完整链路讲清楚阶段 9 学过什么。
2. 区分 RAG 的查询理解、召回、排序、上下文构造、生成、评测、运营这些层。
3. 面试中能回答“怎么提升 RAG 准确率”。
4. 面试中能回答“RAG 答错了怎么排查”。
5. 面试中能回答“RAG 怎么生产化上线”。
6. 能说清楚当前项目已经做到什么，还没做到什么。
7. 能判断下一阶段应该补哪些技术。
```

## 本节新增和修改

新增：

```text
notes/stage9-24-rag-summary-and-interview-expression.md
```

修改：

```text
docs/learning-progress.md
```

本节是纯总结节，不新增 Python 代码，不新增测试代码，不新增 manual-tasks 文档。

## 一句话先讲透

阶段 9 的核心不是“多学几个 RAG 技巧”，而是建立一套能解释、评测、优化和上线 RAG 系统的工程方法。

## 基础知识铺垫

### 1. 为什么阶段结束必须复盘

如果只是一节一节往前学，很容易出现一个问题：

```text
单节知识都看过，但整体说不出来。
```

真实工作和面试不会按课程目录问你。
别人不会问：

```text
第 5 节你学了什么？
第 8 节你学了什么？
第 17 节你学了什么？
```

别人更可能问：

```text
你做过 RAG 吗？
你怎么提升 RAG 的准确率？
RAG 答错了你怎么排查？
为什么要 rerank？
怎么做权限过滤？
怎么评测 RAG？
怎么防 prompt injection？
怎么上线一个 RAG 系统？
```

所以阶段复盘的目的不是“再重复一遍目录”，而是把学习顺序转换成表达顺序。

学习顺序通常是：

```text
概念 -> 模块 -> 代码 -> 测试 -> 下一节
```

表达顺序应该是：

```text
问题 -> 方案 -> 链路 -> 边界 -> 验证 -> 不足 -> 后续改进
```

这是从学生视角变成工程师视角的关键一步。

### 2. 什么叫真正掌握 RAG

会写一个最小 RAG demo，不等于真正掌握 RAG。

最小 RAG demo 通常是：

```text
加载文档
切 chunk
生成 embedding
写入向量数据库
按用户问题检索 top_k
把检索结果塞给模型
让模型回答
```

这只能证明系统能跑通。

真正掌握 RAG，至少要能解释：

```text
用户问题不清楚怎么办？
一个问题只检索一次够不够？
关键词检索和向量检索为什么要结合？
检索分数到底能不能直接相信？
召回结果为什么还要 rerank？
上下文太多怎么办？
回答引用如何校验？
没有资料时为什么要拒答？
不同用户权限如何隔离？
知识库文档被注入恶意指令怎么办？
RAG 答错了如何定位是哪一层的问题？
调参应该看什么指标？
上线前要验收哪些风险？
上线后如何观察和持续改进？
```

阶段 9 解决的就是这些问题。

### 3. RAG 系统不是一个单点功能，而是一条链路

RAG 不是一个函数。
RAG 是一条从用户问题到最终回答的链路。

可以先把它理解成：

```text
用户问题
-> 查询理解
-> 检索召回
-> 结果排序
-> 上下文构造
-> 模型生成
-> 引用校验
-> 质量评测
-> 线上观测
-> 持续优化
```

每一层都有自己的责任。

如果把所有问题都归因成“模型不够聪明”，就无法真正优化 RAG。

比如：

```text
用户问题写得太口语化，是查询理解问题。
正确文档没有召回，是检索问题。
正确文档召回了但排在后面，是排序问题。
塞给模型的上下文太长太杂，是上下文构造问题。
模型没有引用原文，是生成约束问题。
用户看到无权文档，是权限过滤问题。
文档里有恶意指令，是安全问题。
上线后不知道为什么慢，是可观测性问题。
```

工程化 RAG 的核心能力，就是能把问题放回正确的层。

### 4. RAG 质量优化不是只调 prompt

很多初学者会以为 RAG 答得不好，就去改 prompt。

Prompt 很重要，但它只是其中一层。

RAG 质量通常由这些因素共同决定：

```text
原始文档质量
chunk 切分策略
embedding 模型
向量数据库检索参数
关键词检索能力
metadata filter
query rewrite
multi query
hybrid search
rerank
context compression
生成 prompt
引用校验
拒答策略
评测集
bad case 分析
```

所以更准确的说法是：

```text
Prompt 能改善生成方式，但不能替代检索质量、权限过滤、评测体系和生产化治理。
```

### 5. RAG 的“准确率”不能只靠主观感觉

如果你只问几个问题，然后觉得回答还可以，这叫人工体验，不叫系统评测。

真正的 RAG 评测要先准备评测集。

评测集里应该包括：

```text
用户问题
期望行为
答案要点
期望证据
权限上下文
拒答原因
业务标签
优先级
```

有了评测集，才能计算：

```text
Hit@K
Recall@K
Precision@K
MRR@K
answer point coverage
citation pass rate
refusal pass rate
```

没有评测集，只能说“我试了几个问题感觉还行”。
有评测集和指标，才能说“这次改动让 Recall@5 从多少提升到多少，citation pass rate 有没有下降”。

### 6. RAG 的安全不只是不让模型乱说

RAG 安全至少包括三类：

```text
权限安全：用户只能检索自己有权看的文档。
内容安全：知识库里的恶意指令不能影响系统行为。
工具安全：RAG 结果不能绕过 Agent 或 Tool 的写操作确认。
```

阶段 9 里我们重点学过：

```text
metadata filter
access scope
permission_group
business_domain
RAG Prompt Injection 防护
RAG 与 Agent 边界
生产化验收 blocker
```

一个真实 RAG 系统，如果权限过滤做错，相关性再高也不能返回。

这句话很重要：

```text
RAG 的相关性不能高于权限边界。
```

### 7. RAG 和 Agent 的边界必须讲清楚

RAG 负责查知识。
Agent 负责流程决策。
Tool 负责真实业务操作。

这三个概念容易混在一起。

正确边界可以这样记：

```text
RAG：根据知识库回答“资料里怎么说”。
Agent：根据任务状态决定“下一步该做什么”。
Tool：调用后端系统执行“真实读写操作”。
```

比如：

```text
用户问退款规则 -> RAG 查政策。
用户问订单 A1001 到哪了 -> Tool 查订单。
用户说帮我创建工单 -> Agent 判断是否需要确认，再调用写 Tool。
用户问政策后继续要求执行动作 -> Agent 接管流程。
```

如果把 RAG 当成 Agent，就会让检索模块承担流程决策。
如果把 RAG 当成 Tool，就可能让知识库回答替代真实业务查询。
如果让模型直接根据 RAG 内容执行写操作，就容易绕过确认和权限。

### 8. RAG 生产化不是“接口能跑”

一个接口能返回答案，只能说明它通过了最小 smoke。

上线前还要看：

```text
质量是否可接受
权限是否正确
prompt injection 是否有防护
性能是否有超时和降级
成本是否可控
日志是否能排查问题
数据更新和删除是否一致
RAG/Agent/Tool 边界是否清楚
```

阶段 9 第 23 节的生产化验收清单，就是把这些风险显式化。

生产化验收的关键不是“有没有写清单”，而是：

```text
每个检查项有没有 evidence。
哪些项是 release blocker。
failed 和 not_checked 如何影响上线判断。
warning 如何跟踪。
上线后如何持续复查。
```

### 9. 面试表达要避免只堆技术名词

面试里说：

```text
我用了 query rewrite、hybrid search、rerank、metadata filter、RAG eval、observability。
```

这只是堆名词。

更好的表达是：

```text
我把 RAG 链路拆成查询理解、召回、排序、上下文构造、生成校验、评测和生产化几个层。
用户问题不规范时用 query rewrite 和 multi query 提高召回覆盖；
召回侧用 hybrid search 结合关键词和向量；
排序侧用 rerank 提升 top results 质量；
安全侧用 metadata filter 和 prompt injection 防护；
质量侧用评测集、检索指标、回答质量指标和 bad case 分析闭环；
线上侧记录 query、召回、rerank、引用、耗时和 warning codes，方便排查。
```

这才像真正做过项目的人。

### 10. 项目表达要同时讲“做到”和“没做到”

真实项目表达不能只讲优点。

你应该能说清楚：

```text
当前已经做到了什么。
当前为了学习和可测试性做了哪些简化。
如果要生产使用，下一步应该补什么。
```

这会让表达更可信。

比如当前项目可以说：

```text
这个项目不是只做了基础 RAG demo，而是在学习项目里补齐了 RAG 工程质量链路。
为了保证自动化测试稳定，很多能力先用了规则版、fake client 或 mock transport。
真实生产还需要接入更完整的线上日志系统、真实评测平台、真实流量回放、权限系统、灰度发布和更严格的安全 review。
```

这种说法比“我已经做成生产级 RAG 了”更稳。

## 本节主题系统讲解

### 1. 阶段 9 的完整能力地图

阶段 9 可以按六大能力来理解：

```text
查询理解层
检索召回层
排序和上下文层
生成校验层
评测调优层
生产运营层
```

对应关系是：

| 能力层 | 学过的内容 | 解决的问题 |
| --- | --- | --- |
| 查询理解层 | Query Rewrite、Multi Query、查询意图识别 | 用户问题不规范、太短、太口语化、意图不清 |
| 检索召回层 | Hybrid Search、Metadata Filter、多知识库路由、score/distance 理解 | 找不找得到资料、检索范围对不对、分数怎么看 |
| 排序和上下文层 | Rerank、真实 Rerank 模型、Context Compression | 找到的资料怎么排序、哪些内容塞给模型 |
| 生成校验层 | 引用来源校验、拒答合理性、Prompt Injection 防护 | 回答是否有根据、该拒答时是否拒答、是否被恶意内容影响 |
| 评测调优层 | 评测集、检索指标、回答质量评测、Bad Case 分析、参数调优 | 如何量化质量、如何定位问题、如何验证改动有效 |
| 生产运营层 | 缓存/超时/降级、可观测性、数据更新、RAG/Agent 边界、生产化验收 | 如何上线、如何排查、如何控制风险和成本 |

这个表比单纯背 24 节目录更有用。

因为它回答的是：

```text
一个真实 RAG 系统需要哪些工程能力。
```

### 2. 从用户问题到最终回答的完整链路

可以把阶段 9 的完整 RAG 链路讲成这样：

```text
用户问题
-> 查询意图识别
-> Query Rewrite
-> Multi Query
-> 多知识库路由
-> Metadata Filter
-> Hybrid Search
-> 分数解释和阈值判断
-> Rerank
-> Context Compression
-> LLM 生成回答
-> 引用来源校验
-> 回答质量评测
-> Bad Case 分析
-> 参数调优
-> 性能保护和可观测性
-> 数据更新和生产化验收
```

这不是说每次请求都必须走满所有步骤。

真实项目里要根据业务做取舍。

比如：

```text
简单 FAQ 可能不需要 Multi Query。
内部政策库可能必须做 Metadata Filter。
高价值问答更适合接真实 rerank。
低延迟场景可能要减少 rerank 或压缩上下文。
生产系统必须有日志、超时、降级和验收清单。
```

工程能力不是把所有模块都打开，而是知道什么时候该用、什么时候不该用。

### 3. 查询理解层：先让系统知道用户到底想问什么

阶段 9 前几节解决的是查询理解问题。

查询理解层包括：

```text
Query Rewrite
Multi Query
Query Intent Classification
```

它们的分工是：

```text
Query Intent：判断用户问题属于哪类任务。
Query Rewrite：把一个不适合检索的问题改写成更适合检索的问题。
Multi Query：从多个角度生成多个检索问题，扩大召回覆盖。
```

例子：

```text
用户问：这个能退吗？
```

直接检索很难，因为“这个”指代不清。

系统可能需要先识别：

```text
这是退款政策问题。
需要补齐关键词：退款、退货、售后规则。
可能生成多个检索 query：退款条件、退货流程、运费承担、质量问题退款。
```

查询理解层的目标不是让模型回答，而是让后面的检索更容易成功。

### 4. 检索召回层：先保证正确资料有机会被找到

召回层的核心问题是：

```text
正确资料有没有被找出来。
```

阶段 9 里召回相关内容包括：

```text
Hybrid Search
score / distance / similarity
Metadata Filter
多知识库路由
```

Hybrid Search 的价值是：

```text
关键词检索擅长精确词、编号、专有名词。
向量检索擅长语义相近、表达不同的问题。
两者融合可以提高召回稳定性。
```

Metadata Filter 的价值是：

```text
先限制检索范围，再谈相关性。
```

多知识库路由的价值是：

```text
不同问题进入不同知识库，减少无关资料干扰。
```

分数理解的价值是：

```text
知道不同向量库、不同 metric、不同模型的分数不能乱比。
```

召回层最重要的一句话：

```text
如果正确资料没有进入候选集，后面的 rerank 和 prompt 再强也很难补救。
```

### 5. 排序和上下文层：把找到的资料变成模型可用的上下文

召回出来的 top_k 不一定就是最终应该给模型的上下文。

排序和上下文层解决：

```text
哪些资料更应该排前面。
哪些 chunk 应该保留。
哪些 chunk 应该压缩。
哪些 chunk 应该丢弃。
```

阶段 9 里对应内容是：

```text
Rerank
真实 Rerank 模型 adapter
Context Compression
```

Rerank 的作用是：

```text
在粗召回结果中重新判断 query 和 document 的相关性。
```

Context Compression 的作用是：

```text
在上下文预算有限时，保留最有证据价值的内容。
```

这里要注意：

```text
Rerank 不能凭空找回没有召回的文档。
Context Compression 不能把错误资料压缩成正确资料。
```

它们是在召回结果基础上提升上下文质量。

### 6. 生成校验层：不能只相信模型最终回答

RAG 最终还是要经过大模型生成回答。

但工程上不能只相信最终自然语言。

阶段 9 里我们补了：

```text
引用来源校验
回答质量评测
拒答合理性
Prompt Injection 防护
```

引用校验的意义是：

```text
回答里的依据应该能对应到召回原文。
```

拒答合理性的意义是：

```text
没有资料、无权限、遇到高风险问题时，不应该强行回答。
```

Prompt Injection 防护的意义是：

```text
知识库文档是外部输入，不应该被当成系统指令执行。
```

生成校验层的核心原则是：

```text
模型可以组织语言，但事实依据、权限边界和安全策略要由系统约束。
```

### 7. 评测调优层：把“感觉变好”变成“指标变好”

RAG 优化不能凭感觉。

阶段 9 里我们建立了：

```text
RAG 评测集
检索指标
回答质量指标
Bad Case 分析
参数调优建议
```

一个成熟的优化过程应该是：

```text
收集 bad case
-> 判断是哪一层问题
-> 修改对应模块或参数
-> 跑评测集
-> 比较指标变化
-> 保留有效改动，回滚无效改动
```

这比“我改了 prompt，感觉好一点”更可靠。

参数调优也不是乱调：

```text
Recall 太低，可能增加 top_k、降低 threshold、优化 query rewrite。
Precision 太低，可能提高 threshold、加强 rerank、改 chunk 策略。
MRR 太低，说明正确文档可能有召回但排序靠后。
no_context 太高，说明检索覆盖不足或过滤太严。
citation pass rate 低，说明回答和证据不一致。
```

### 8. 生产运营层：让 RAG 从学习项目走向真实项目

生产运营层关注的不是“能不能回答”，而是：

```text
能不能稳定回答。
能不能安全回答。
能不能排查问题。
能不能控制成本。
能不能持续更新。
能不能上线验收。
```

阶段 9 对应内容是：

```text
缓存
超时
降级
性能保护
可观测性
数据更新
RAG/Agent 边界
生产化验收清单
```

一个真实 RAG 服务上线后，常见问题不是只有“答错”。
还有：

```text
响应太慢。
rerank 或 LLM 超时。
成本突然升高。
知识库旧数据还在。
用户看到了无权内容。
日志里没有足够信息排查。
某次改动让原来能回答的问题答错了。
```

所以生产运营层是 RAG 工程化不可缺少的一部分。

### 9. 当前项目里阶段 9 的价值怎么概括

当前项目可以这样概括：

```text
这是一个围绕 Java 后端、Python AI 服务、RAG、Agent 和 MCP 逐步搭建的 AI 客服学习项目。
阶段 9 重点不是重新做基础 RAG，而是在已有企业知识库 RAG 的基础上，补齐 RAG 检索质量优化、评测、排查、安全和生产化验收能力。
```

更具体可以说：

```text
我把 RAG 链路拆成查询理解、召回、排序、上下文、生成校验、评测调优和生产运营几层。
在查询理解侧实现了 query rewrite、multi query 和 intent classification。
在召回侧补了 hybrid search、metadata filter 和多知识库路由。
在排序侧补了 rerank 和真实 rerank adapter。
在上下文侧补了 context compression。
在质量侧补了 citation verification、评测集、检索指标、回答质量评测和 bad case 分析。
在工程侧补了缓存、超时、降级、可观测性、数据更新、RAG/Agent 边界和生产化验收清单。
```

注意表达时不要夸大。

更稳的说法是：

```text
这个项目是学习型工程项目，很多模块先用规则版或 fake client 保证可测试性。
但它覆盖了真实 RAG 项目会遇到的核心工程问题，并且每个模块都有结构化输入输出和自动化测试思路。
```

### 10. 当前项目已经掌握的 RAG 能力

阶段 9 完成后，可以认为你已经系统学习过这些能力：

```text
基础 RAG 链路
查询改写
多查询扩展
查询意图识别
混合检索
检索分数理解
召回后重排序
真实 rerank 接入方式
引用来源校验
上下文压缩
metadata 权限过滤
RAG Prompt Injection 防护
RAG 评测集设计
检索指标
回答质量评测
Bad Case 分析
参数调优
缓存、超时、降级
RAG 可观测性
数据增量更新和删除
多知识库路由
RAG 与 Agent 边界
生产化验收
```

这些内容已经超过“只会调一个向量库接口”的层次。

### 11. 当前项目还不能夸大的地方

当前项目不能夸大成：

```text
已经是完整商业生产系统。
已经经过大量真实用户流量验证。
已经有完善线上监控平台。
已经接入企业真实权限系统。
已经做了大规模 RAG 评测平台。
已经实现复杂多模态 RAG。
已经完成 Elasticsearch 深度优化。
```

更准确的表达是：

```text
当前项目已经覆盖 RAG 工程化核心链路和学习级实现。
下一步如果做真实生产系统，需要补充真实数据规模、真实线上监控、真实权限集成、灰度发布、持续评测平台和更完整的成本治理。
```

这样表达更专业，也更可信。

## 面试表达强化

### 1. 30 秒版本：你做过 RAG 吗

可以这样回答：

```text
做过。我的项目里有一个企业知识库 RAG 模块，不只是基础的文档切分、embedding 和向量检索，还补了查询改写、多查询扩展、混合检索、rerank、metadata 权限过滤、引用校验、评测集、检索指标、bad case 分析、缓存超时降级和可观测性。我的重点是把 RAG 从能跑通推进到能评测、能排查、能优化和能生产化验收。
```

### 2. 1 分钟版本：你的 RAG 系统怎么设计

可以这样回答：

```text
我的 RAG 链路按层设计。用户问题进来后，先做查询意图识别，判断是政策查询、流程查询、订单查询还是其他任务；对于适合知识库的问题，再做 query rewrite 和 multi query，提高召回覆盖。检索侧结合向量检索和关键词检索做 hybrid search，同时用 metadata filter 限制用户、租户、权限组和业务域。召回后用 rerank 提升候选资料排序质量，再做 context compression，避免把太多无关 chunk 塞给模型。生成后做引用来源校验和回答质量评测。如果出现 bad case，会按 retrieval、ranking、generation、citation、access control、security 等层归因，再根据指标调 top_k、score_threshold、chunk_size、rerank 和 prompt。上线侧还考虑缓存、超时、降级、可观测性、数据更新和生产化验收清单。
```

### 3. 3 分钟版本：完整项目表达

可以这样回答：

```text
我在项目里把 RAG 当成一条工程链路来做，而不是只做一个向量检索 demo。

第一层是查询理解。因为真实用户的问题经常比较口语化、缺少关键词或者意图不明确，所以我做了 intent classification、query rewrite 和 multi query。意图识别负责判断问题适不适合走 RAG，query rewrite 负责把问题改写成更适合检索的形式，multi query 负责从多个角度扩展召回。

第二层是检索召回。基础向量检索对语义相近问题有帮助，但对订单号、专有名词、精确关键词不一定稳定，所以我补了 hybrid search，把关键词检索和向量检索融合。同时用 metadata filter 限定租户、权限组、业务域、文档类型等范围，避免用户检索到无权内容。多知识库场景下，我还做了知识库路由，减少所有资料混在一起检索带来的干扰。

第三层是排序和上下文构造。召回出来的 top_k 不一定是最适合给模型的上下文，所以我补了 rerank，并了解真实 rerank 模型的 adapter 接入方式。之后通过 context compression 控制上下文预算，把有证据价值的内容保留下来。

第四层是生成校验和安全。RAG 回答必须尽量能对应原文，所以我做了 citation verification。对于无资料、无权限或高风险场景，需要结构化拒答。同时我把知识库文档当成不可信输入，做了 RAG Prompt Injection 风险识别，避免文档里的恶意指令影响系统行为。

第五层是评测和调优。我设计了 RAG 评测集，把用户问题、期望答案要点、期望证据、权限上下文和拒答原因结构化。检索侧用 Hit@K、Recall@K、Precision@K、MRR@K 看正确资料有没有找出来、排序是否靠前；回答侧看答案要点覆盖、引用一致性和拒答合理性。出现 bad case 后，不直接归因成模型不行，而是按 retrieval、ranking、generation、citation、access control、security 等层定位，再调整 top_k、threshold、chunk 参数、rerank、prompt 或过滤策略。

第六层是生产化。RAG 服务可能慢、贵、不稳定，所以我补了缓存、超时、降级、可观测性和数据更新计划。最后用生产化验收清单把质量、安全、性能、成本、可观测性、数据和 RAG/Agent 边界都纳入上线前检查。

这个项目目前是学习型工程项目，很多模块用规则版或 fake client 保证可测试性，但它覆盖了真实 RAG 系统从检索质量到生产化治理的核心问题。
```

### 4. 面试题：怎么提升 RAG 准确率

回答思路：

```text
不能只说调 prompt。
要按链路分层回答。
```

可以这样答：

```text
我会先区分问题发生在哪一层。如果是用户问题表达不清，可以做 query rewrite 或 multi query；如果正确文档没有召回，要看 chunk 策略、embedding、top_k、score_threshold、hybrid search 和 metadata filter；如果正确文档召回了但排得靠后，可以加 rerank；如果上下文太长太杂，可以做 context compression；如果模型回答和资料不一致，要加强 prompt 约束、引用校验和拒答策略。最后要用评测集和指标验证，比如 Recall@K、MRR@K、答案要点覆盖率和引用通过率，而不是只凭感觉判断。
```

### 5. 面试题：RAG 答错了怎么排查

可以这样答：

```text
我会按链路排查。第一步看 query 是否理解错，比如意图识别或 query rewrite 是否有问题。第二步看 retrieval，正确 chunk 有没有进入 top_k，如果没有进入就是召回问题。第三步看 ranking，如果正确 chunk 进来了但排得靠后，就是排序或 rerank 问题。第四步看 context，是否因为上下文太长、太杂、被压缩掉导致模型没看到关键证据。第五步看 generation，模型是否忽略证据、编造、没有拒答。第六步看 citation 和权限，确认引用是否对应原文，是否检索到了无权资料。最后把 bad case 归类到 retrieval、ranking、generation、citation、access control、security 等层，再针对性改参数或模块。
```

### 6. 面试题：为什么要 Hybrid Search

可以这样答：

```text
向量检索擅长语义相似，但对精确关键词、编号、专有名词、短语匹配不一定稳定。关键词检索擅长精确匹配，但对同义表达和口语化问题不够灵活。Hybrid Search 把两者结合，可以提高召回稳定性。比如用户问订单编号、政策条款名、错误码时，关键词检索可能更可靠；用户换一种说法问同一件事时，向量检索更有优势。
```

### 7. 面试题：为什么召回后还要 Rerank

可以这样答：

```text
召回阶段通常追求覆盖，先尽量把可能相关的候选找出来；rerank 阶段追求排序质量，对 query 和候选文档做更精细的相关性判断。向量检索的 top_k 不一定最适合直接给模型，rerank 可以把更相关、更能回答问题的 chunk 提到前面。但 rerank 不能解决正确文档完全没召回的问题，所以它是召回后的精排，不是召回替代品。
```

### 8. 面试题：RAG 怎么做权限控制

可以这样答：

```text
RAG 权限控制不能只在回答后做遮挡，最好在检索侧就限制范围。我的做法是把 tenant_id、permission_group、business_domain、doc_type、status 等字段作为 metadata 入库，请求时根据用户身份构造 access scope，再转成向量库 payload filter。这样用户只能在自己有权访问的文档范围内检索。即使某个无权文档语义相关，也不应该进入候选集。
```

### 9. 面试题：RAG Prompt Injection 是什么

可以这样答：

```text
RAG Prompt Injection 是指知识库文档里包含恶意或误导性指令，比如“忽略系统提示”“调用某个工具”“泄露用户信息”。这些内容本质上是外部数据，不应该被模型当成系统指令执行。防护上要做角色隔离、文档风险扫描、工具调用边界、敏感动作确认和系统侧校验。不能只靠 prompt 告诉模型不要听文档指令。
```

### 10. 面试题：怎么评测 RAG

可以这样答：

```text
我会先设计评测集，而不是先谈指标。评测集里要包含用户问题、期望行为、答案要点、期望证据、权限上下文、拒答原因和标签。检索侧可以看 Hit@K、Recall@K、Precision@K、MRR@K；生成侧可以看答案要点覆盖率、引用一致性、拒答合理性和 forbidden source 检查。评测结果还要和 bad case 分析结合，定位问题发生在召回、排序、生成、引用、权限还是安全层。
```

### 11. 面试题：RAG 怎么上线生产

可以这样答：

```text
上线前我会做生产化验收，不只看接口能不能返回答案。质量上要有评测集和核心指标；安全上要检查权限过滤、prompt injection 和敏感信息；性能上要有超时、缓存、降级；成本上要估算 embedding、rerank、LLM token 和重试成本；可观测性上要记录 query、召回、rerank、引用、耗时和 warning codes；数据上要支持增量更新、删除和重建索引；和 Agent 组合时要明确 RAG、Agent、Tool 的边界。阻断项 failed 或 not_checked 时不应该上线。
```

### 12. 面试题：你的项目还有哪些不足

可以这样答：

```text
当前项目是学习型工程项目，覆盖了 RAG 的核心工程链路，但还不是完整商业生产系统。比如真实线上流量规模还不大，评测集规模有限，部分 query rewrite、multi query 和 rerank 逻辑使用规则版或 mock 方式保证测试稳定，线上 tracing、灰度发布、权限系统集成、成本看板和大规模自动化评测平台还需要继续完善。这些也是后续可以继续深入的方向。
```

## 当前项目表达素材

### 1. 简历 bullet 示例

可以整理成：

```text
设计并实现企业知识库 RAG 进阶链路，覆盖 Query Rewrite、Multi Query、Hybrid Search、Rerank、Metadata Filter、Context Compression、Citation Verification、RAG Eval、Bad Case Analysis、Observability 和 Production Readiness。
```

更工程化一点：

```text
将基础 RAG 链路拆分为查询理解、召回、排序、上下文构造、生成校验、评测调优和生产运营模块，建立基于检索指标、回答质量指标和 bad case 分层归因的 RAG 优化闭环。
```

如果想强调安全：

```text
在 RAG 检索侧引入 tenant、permission_group、business_domain 等 metadata filter，并补充 RAG Prompt Injection 风险识别、引用来源校验和生产化验收清单，降低无权访问、错误引用和恶意文档指令风险。
```

### 2. 项目介绍开头

可以这样说：

```text
这个项目是一个 Java 后端 + Python AI 服务的企业客服学习项目。Java 侧提供订单、工单等真实业务服务，Python 侧负责 LLM API、Tool Calling、Agent 编排、RAG 检索和 MCP 工具体系。阶段 9 重点对 RAG 做了进阶优化，不只是能检索知识库，而是围绕准确率、安全性、可评测性、可观测性和生产化验收补齐工程能力。
```

### 3. 技术亮点表达

可以分层讲：

```text
查询理解：intent classification、query rewrite、multi query。
检索召回：hybrid search、metadata filter、多知识库路由、分数语义解释。
排序上下文：rerank、真实 rerank adapter、context compression。
生成校验：citation verification、拒答合理性、RAG prompt injection 防护。
评测调优：RAG eval dataset、Hit@K、Recall@K、MRR@K、answer quality、bad case analysis、parameter tuning。
生产运营：cache、timeout、degradation、observability、data update、RAG/Agent boundary、production readiness checklist。
```

### 4. 和传统后端经验的连接

你有 Java 后端基础，所以可以这样连接：

```text
传统后端更关注接口契约、数据一致性、权限、事务、缓存、限流、日志和可观测性。
RAG 工程不是替代这些，而是把这些工程能力扩展到 AI 检索和生成链路里。
比如 metadata filter 对应权限边界，评测集和指标对应测试体系，cache/timeout/degradation 对应服务稳定性，trace 和 warning codes 对应线上排查，production readiness 对应上线 checklist。
```

这个连接很重要。
它能说明你不是只会调 AI API，而是能把 AI 能力放进真实后端工程里。

## 常见误区

### 误区 1：RAG 优化就是调 prompt

不对。

Prompt 只是生成层的一部分。
RAG 优化还包括查询理解、召回、排序、上下文、权限、安全、评测、调参和生产化。

### 误区 2：Rerank 可以解决所有检索问题

不对。

Rerank 只能重排已经召回的候选。
如果正确文档没有召回，rerank 没有机会把它排上来。

### 误区 3：检索分数高就一定能回答

不一定。

分数受向量库、metric、embedding 模型、归一化方式和 query 表达影响。
高分 chunk 也可能只是语义相似，不一定包含答案证据。

### 误区 4：只要回答看起来对，就不用引用校验

不对。

RAG 的价值之一是 grounded answer。
没有引用校验，模型可能说得像真的，但实际没有证据支撑。

### 误区 5：权限过滤可以放到最后再处理

不建议。

权限最好在检索侧就过滤。
否则无权内容可能进入上下文，被模型吸收后再泄露出来。

### 误区 6：评测集等上线后再做

不建议。

没有评测集，就无法证明改动是否真的提升质量，也无法防止回归。

### 误区 7：Bad Case 就是模型不行

不对。

Bad Case 可能来自数据、chunk、召回、排序、上下文、权限、prompt、生成、引用或安全策略。
必须分层归因。

### 误区 8：生产化只需要服务能启动

不对。

生产化还要关注质量、安全、性能、成本、可观测性、数据更新、灰度、回滚和验收证据。

### 误区 9：RAG 和 Agent 可以随便混用

不对。

RAG 查资料，Agent 做流程决策，Tool 执行业务读写。
边界混乱会带来安全和业务风险。

### 误区 10：学习项目就不能写进简历

不对。

学习项目可以写，但要表达真实边界。
不要说成大规模商业生产项目，可以说“学习型工程项目，覆盖真实 RAG 工程链路和核心问题”。

## 本节练习

### 练习 1：用 5 层结构总结阶段 9 的 RAG 能力

答案：

可以总结为：

```text
查询理解层：intent classification、query rewrite、multi query。
检索召回层：hybrid search、metadata filter、多知识库路由、分数理解。
排序上下文层：rerank、真实 rerank adapter、context compression。
生成校验层：citation verification、拒答合理性、prompt injection 防护。
评测运营层：评测集、检索指标、回答质量、bad case、参数调优、缓存超时降级、可观测性、数据更新、生产化验收。
```

### 练习 2：回答“怎么提升 RAG 准确率”

答案：

可以按链路回答：

```text
先分析问题发生在哪一层。查询表达不清就做 query rewrite / multi query；正确资料没召回就优化 chunk、embedding、top_k、threshold、hybrid search 和 filter；正确资料召回但排序靠后就加 rerank；上下文太多太杂就做 compression；回答没有依据就加强 prompt、引用校验和拒答策略。最后用评测集和指标验证，而不是只靠主观感觉。
```

### 练习 3：回答“RAG 答错了怎么排查”

答案：

可以这样答：

```text
先看 query intent 和 rewrite 是否正确，再看正确 chunk 是否进入 top_k；如果没进，是召回问题；如果进了但排序靠后，是 ranking/rerank 问题；如果正确 chunk 被压缩或上下文太杂，是 context 问题；如果模型看到证据还答错，是 generation/prompt 问题；如果引用不对应原文，是 citation 问题；如果出现无权资料，是 access control 问题；如果文档指令影响模型，是 security 问题。
```

### 练习 4：给当前项目写一句简历描述

答案：

可以写：

```text
在 Java + Python AI 客服学习项目中，设计 RAG 进阶链路，覆盖查询改写、多查询扩展、混合检索、Rerank、权限过滤、引用校验、评测集、Bad Case 分析、可观测性和生产化验收，建立可评测、可排查、可优化的知识库问答能力。
```

### 练习 5：说明当前项目还有哪些不足

答案：

可以说：

```text
当前项目覆盖了 RAG 工程化核心链路，但仍是学习型工程项目。真实生产还需要更大规模真实数据、线上流量验证、完整权限系统集成、持续评测平台、真实 tracing/metrics 看板、灰度发布、成本治理和更完整的安全 review。
```

## 自测题

### 自测 1：为什么不能只靠 prompt 提升 RAG 质量？

答案：

因为 RAG 质量受查询理解、召回、排序、上下文构造、权限过滤、安全防护、评测和生成共同影响。
Prompt 只能约束生成方式，不能替代正确资料召回、权限过滤、引用校验和评测闭环。

### 自测 2：Hybrid Search 和 Rerank 的区别是什么？

答案：

Hybrid Search 发生在召回阶段，目的是结合关键词和向量检索，把可能相关的候选找出来。
Rerank 发生在召回之后，目的是对候选重新排序，把更相关、更有证据价值的内容排到前面。

### 自测 3：为什么 metadata filter 应该尽量发生在检索侧？

答案：

因为权限边界应该先于相关性判断。
如果无权文档进入候选上下文，即使最后再过滤，也可能已经影响模型生成，带来泄露风险。

### 自测 4：RAG 评测为什么要先有评测集？

答案：

没有评测集，就无法稳定比较不同版本的质量，也无法判断改动是否真的提升。
评测集把问题、期望答案、证据、权限和拒答场景结构化，是指标计算和 bad case 分析的基础。

### 自测 5：RAG 与 Agent 的边界是什么？

答案：

RAG 负责根据知识库查资料并提供证据。
Agent 负责根据任务目标和状态做流程决策。
Tool 负责调用后端系统执行真实读写。
RAG 不能替代 Agent 决策，也不能绕过 Tool 的权限、幂等和确认机制。

### 自测 6：上线一个 RAG 系统至少要检查哪些方面？

答案：

至少检查：

```text
质量
安全
性能
成本
可观测性
数据更新
RAG/Agent/Tool 边界
```

质量看评测指标和 bad case。
安全看权限、prompt injection、敏感信息和写操作确认。
性能看超时、缓存、降级。
可观测性看 query、召回、rerank、引用、耗时和 warning codes。

## 阶段 9 总结

阶段 9 完成后，你不应该只记住一堆名词。

你应该形成一套完整思路：

```text
RAG 不是单次向量检索。
RAG 是从用户问题理解、知识召回、候选排序、上下文构造、模型生成、引用校验、质量评测、线上观测到持续优化的一条工程链路。
```

这阶段最重要的能力是：

```text
能分层。
能定位。
能评测。
能调优。
能讲清楚边界。
能知道生产化还差什么。
```

以后别人问你“你会 RAG 吗”，不要只回答：

```text
会，我用过向量数据库。
```

你应该能回答：

```text
我理解 RAG 从能跑通到能上线之间需要补齐哪些工程能力，包括查询理解、召回、排序、上下文压缩、权限过滤、引用校验、安全防护、评测集、指标、bad case 分析、性能保护、可观测性、数据更新和生产化验收。我也知道这些模块分别解决什么问题、有什么边界，以及怎么在项目里逐步落地。
```

这才是阶段 9 要达到的学习效果。

## 后续学习方向

阶段 9 结束后，RAG 主线已经比较扎实。

后续可以进入更偏真实岗位加分项的新技术方向，例如：

```text
Tracing 和可观测性平台
自动化评估平台
多模型路由和成本控制
LangGraph 进阶
Human-in-the-loop
Agent 状态持久化
MCP 真实生态接入
混合检索与 Rerank 深入
Redis/MySQL 在 AI 应用中的工程治理
SSE 流式输出体验优化
Prompt Injection 与权限控制强化
```

下一阶段具体学什么，可以根据目标来选：

```text
想更像真实生产系统：优先 Tracing、评测平台、成本控制、限流和降级。
想更像 Agent 工程师：优先 LangGraph 进阶、Human-in-the-loop、状态持久化。
想更像 AI 后端工程师：优先多模型路由、SSE、Redis/MySQL 工程治理、权限和安全。
想更像 RAG 专项工程师：优先 Elasticsearch/BM25、混合检索、Rerank、评测平台和数据治理。
```

当前更建议下一阶段先补：

```text
AI 应用生产化能力：Tracing、自动化评估、成本控制、多模型路由、限流降级、SSE 流式体验、权限和 Prompt Injection 加固。
```

原因是：

```text
你已经有 Java 后端基础，也已经完成 RAG、Agent、MCP 和真实 Java 服务接入。
接下来最有价值的不是继续重复基础功能，而是把 AI 应用做得更稳定、更可观测、更可评估、更像真实工作项目。
```
