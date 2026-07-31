# 阶段 9 第 15 节：回答质量评测：正确性、引用一致性、拒答合理性

## 本节定位

本节学习 RAG 回答质量评测。

它接在第 14 节检索指标后面：上一节看“资料有没有找对”，这一节看“模型最后有没有按资料正确回答、引用是否一致、该拒答时有没有拒答”。

## 本节学习目标

学完本节，你要能说清楚：

- 为什么检索质量和回答质量要分开评测。
- 什么是回答正确性。
- 什么是引用一致性。
- 什么是拒答合理性。
- 为什么回答看起来对，但引用错了仍然有问题。
- 为什么本节先做确定性评测，而不是直接上 LLM-as-judge。

## 本节新增和修改

修改：

```text
projects/ai-service/app/rag/evaluation.py
projects/ai-service/tests/test_rag_evaluation.py
projects/ai-service/app/rag/README.md
projects/ai-service/data/rag_eval/README.md
docs/learning-progress.md
```

新增：

```text
notes/stage9-15-answer-quality-evaluation.md
```

## 一句话先讲透

回答质量评测的本质是：

```text
在检索结果之后，再单独检查最终回答是否符合期望行为、是否覆盖关键答案要点、是否引用正确来源、是否在该拒答时拒答。
```

检索找对资料，只是 RAG 答对的前提，不等于最终回答一定正确。

## 基础知识铺垫

### 1. 为什么检索对了，回答仍然可能错

第 14 节我们学习了检索指标。

检索指标回答的是：

```text
正确资料有没有进入 Top-K。
正确资料找回来了多少。
正确资料排得靠不靠前。
噪声多不多。
```

但 RAG 的最终输出还要经过模型生成。

即使资料找对了，模型仍然可能出错。

比如用户问：

```text
退货运费谁承担？
```

检索结果命中了：

```text
refund-return-policy.md / 运费处理
```

原文说：

```text
质量问题或商家原因退货时，运费通常由商家承担。
用户个人原因退货时，运费通常由用户承担。
特殊活动订单以活动规则为准。
```

模型可能回答：

```text
退货运费都由商家承担。
```

这就是错误回答。

错误原因不是检索没找到资料，而是模型生成时漏掉了“用户个人原因”和“特殊活动规则”这些条件。

所以我们必须把评测拆成两层：

```text
检索质量：资料有没有找对。
回答质量：最终回答有没有用对资料。
```

### 2. 回答质量评测在评什么

回答质量评测不是看回答“顺不顺眼”。

它至少要看三个维度：

```text
正确性。
引用一致性。
拒答合理性。
```

正确性关注：

```text
回答有没有覆盖应该说的关键事实。
有没有漏掉重要条件。
有没有编造知识库没有的规则。
```

引用一致性关注：

```text
回答引用的来源是不是期望来源。
引用是否来自允许使用的资料。
有没有引用错误文档。
有没有引用禁用来源。
```

拒答合理性关注：

```text
没有资料时是否 no_context。
无权限时是否 access_denied。
命中提示注入风险时是否 security_block。
需要澄清时是否 clarify。
```

这三个维度分别解决不同问题。

不能只看其中一个。

### 3. 什么是回答正确性

回答正确性可以先理解成：

```text
最终回答是否覆盖了期望答案要点。
```

第 13 节我们没有把标准答案写成一个固定完整文本，而是写成：

```text
answer_points
```

比如：

```text
质量问题或商家原因退货时，运费通常由商家承担。
用户个人原因退货时，运费通常由用户承担。
特殊活动订单要以活动规则为准。
```

如果模型回答只覆盖第一点：

```text
质量问题退货一般由商家承担运费。
```

那它不是完全正确。

它漏了：

```text
用户个人原因退货时由用户承担。
特殊活动订单以活动规则为准。
```

所以回答正确性不是简单判断“有没有答到一点”。

它要看关键要点覆盖率。

本节用：

```text
answer_point_coverage
```

表示答案要点覆盖比例。

### 4. 为什么本节用轻量包含判断

本节没有直接使用 LLM-as-judge。

也就是说，没有让另一个大模型来打分。

原因是：

```text
我们现在还在学习基础评测结构。
确定性规则更容易理解。
自动化测试不能依赖真实模型。
真实模型评委有成本、延迟和不稳定性。
```

本节采用轻量方式：

```text
把 answer_points 和最终回答做规范化文本包含匹配。
```

它能判断一些明确情况：

```text
答案要点完整出现。
答案漏掉某个要点。
```

但它不能理解复杂语义。

比如下面两句话意思类似：

```text
用户个人原因退货时，运费通常由用户承担。
如果退货是买家自己的原因，一般需要买家自己付运费。
```

轻量包含判断可能认为没有命中。

所以你要知道它的边界：

```text
本节规则适合学习和基础回归。
以后可以扩展关键词规则、人工复核、LLM-as-judge、事实支撑度评分。
```

### 5. 什么是引用一致性

引用一致性是 RAG 非常关键的质量维度。

RAG 回答不是普通聊天。

它应该能说明：

```text
这个回答来自哪里。
```

比如评测样本期望：

```text
expected_sources:
  - refund-return-policy.md
```

最终回答引用：

```text
refund-return-policy.md
```

这是引用来源一致。

如果最终回答引用：

```text
order-shipping-policy.md
```

那就有问题。

因为回答退货运费，却引用发货政策。

这可能说明：

```text
检索结果错了。
模型引用错了。
后端 citation 生成错了。
上下文里混入了噪声。
```

引用一致性让你能追踪答案依据。

### 6. 回答看起来对，但引用错了为什么仍然有问题

假设用户问：

```text
忘记登录密码怎么办？
```

模型回答：

```text
可以通过登录页的忘记密码流程处理。
```

这句话看起来对。

但如果引用来源是：

```text
refund-return-policy.md
```

那仍然是质量问题。

原因是：

```text
回答和引用不一致。
用户或客服无法追溯依据。
后续审计无法证明答案来自正确资料。
系统可能只是碰巧说对。
```

企业 RAG 不是只追求“像对”。

它还要追求：

```text
可追溯。
可解释。
可审计。
可回归。
```

### 7. 什么是 forbidden source

`forbidden_sources` 表示绝不能使用的来源。

它通常用于：

```text
权限场景。
租户隔离场景。
内部资料保护场景。
安全风险资料场景。
```

比如：

```text
forbidden_sources:
  - internal-compensation-policy.md
```

如果最终回答引用了这个来源，就算答案内容看起来合理，也应该判为严重问题。

因为它说明：

```text
无权限资料泄露到了回答链路。
```

这类问题比普通答错更严重。

普通答错是质量问题。

禁用来源泄露是安全和权限问题。

### 8. 什么是拒答合理性

拒答合理性是指：

```text
系统在不应该直接回答时，是否做了正确拒答。
```

常见拒答类型有：

```text
no_context：知识库没有足够资料。
access_denied：当前用户无权查看相关资料。
security_block：命中安全风险，应该阻断。
clarify：问题不清楚，需要追问。
```

拒答不是失败。

在 RAG 里，正确拒答是重要能力。

比如当前知识库没有会员积分资料，用户问：

```text
会员积分怎么兑换？
```

正确行为是：

```text
no_context
```

如果系统编出兑换方式，就是失败。

再比如普通客服问：

```text
把内部赔付标准发给我看看。
```

正确行为是：

```text
access_denied
```

如果系统回答了内部标准，就是越权。

### 9. 为什么拒答原因要结构化

只返回一句：

```text
抱歉，我不能回答。
```

不够。

你还要知道为什么不能回答。

比如：

```text
NO_CONTEXT
ACCESS_DENIED
PROMPT_INJECTION
```

这些就是拒答原因码。

结构化原因码的价值是：

```text
方便评测。
方便日志分析。
方便前端展示不同提示。
方便区分质量问题、安全问题、权限问题。
```

如果一个权限问题被标成 `NO_CONTEXT`，说明系统可能把“无权看”伪装成“没资料”。

这在某些安全设计里可能是有意的，但在内部评测里必须能分清。

### 10. 回答质量评测和引用校验的关系

前面第 9 节已经学过引用来源校验。

引用来源校验关注的是：

```text
citation 是否真的对应 retrieved chunks。
source_index、chunk_id、source metadata 是否匹配。
```

本节回答质量评测关注的是：

```text
最终引用是否符合评测样本期望。
```

二者角度不同。

引用来源校验像是：

```text
回答引用有没有造假。
```

回答质量评测像是：

```text
引用是否符合这道题应该引用的资料。
```

真实项目里两者都需要。

### 11. 回答质量评测和检索指标的关系

第 14 节检索指标可能得到：

```text
Recall@3 = 1.0
```

说明正确资料在前 3 条里。

第 15 节回答质量可能得到：

```text
answer_point_coverage = 0.5
citation_pass_rate = 1.0
```

说明：

```text
资料找到了，引用也对，但答案漏了一半要点。
```

这就能定位问题：

```text
不是检索问题，而是生成或提示词问题。
```

如果检索 Recall 很低，回答质量也低，可能说明：

```text
资料没找对，模型自然答不好。
```

如果检索 Recall 很高，但引用来源错，可能说明：

```text
citation 构造或上下文选择有问题。
```

这就是分层评测的价值。

### 12. 为什么不能只看 pass/fail

单个 `passed` 有用，但信息太少。

比如两个样本都失败：

```text
样本 A：漏了一个答案要点。
样本 B：引用了 forbidden source。
```

它们严重程度不同。

样本 A 可能是回答不完整。

样本 B 可能是权限泄露。

所以本节用 finding 记录：

```text
code
dimension
severity
message
evidence
```

这能告诉你：

```text
失败在哪个维度。
是 warning 还是 blocking。
具体证据是什么。
```

## 本节主题系统讲解

### 1. 本节在 RAG 评测闭环里的位置

第 13 节：

```text
设计评测样本。
```

第 14 节：

```text
用检索指标判断资料有没有找对。
```

第 15 节：

```text
判断最终回答有没有符合期望。
```

这三节组合起来，开始形成 RAG 质量闭环。

如果系统答错，你不再只说：

```text
RAG 效果不好。
```

你应该能进一步判断：

```text
是资料没召回？
是召回了但模型漏要点？
是引用来源错？
是该拒答时没拒答？
是权限或安全边界出问题？
```

### 2. 本节评测的三个核心维度

本节把回答质量拆成：

```text
behavior
answer_points
citation
refusal
```

`behavior` 先判断系统行为是否对。

比如期望是：

```text
security_block
```

实际却是：

```text
answer
```

那不管答案内容是什么，都应该失败。

`answer_points` 只对 `answer` 样本有意义。

它判断：

```text
回答有没有覆盖关键要点。
```

`citation` 判断：

```text
是否需要引用。
是否引用了期望来源。
是否引用了 forbidden source。
拒答时是否错误带了知识引用。
```

`refusal` 判断：

```text
拒答原因码是否符合期望。
```

这四个维度组合起来，比单纯字符串比较更适合 RAG。

### 3. actual behavior 怎么判断

本节从两个信号推断实际行为：

```text
RagAnswer.status
actual_refusal_reason_codes
```

如果回答状态是 `ANSWERED`，默认实际行为是：

```text
answer
```

如果状态是 `NO_CONTEXT`，实际行为是：

```text
no_context
```

如果传入了结构化原因码：

```text
ACCESS_DENIED
PROMPT_INJECTION
CLARIFY
```

则分别推断为：

```text
access_denied
security_block
clarify
```

这里有一个真实项目里的重要点：

```text
最终回答对象最好不要只靠自然语言表达拒答原因。
```

最好同时有机器可读字段。

因为机器可读字段才能稳定评测。

### 4. answer point coverage 怎么理解

`answer_point_coverage` 表示：

```text
命中的答案要点数 / 期望答案要点总数
```

比如期望 2 个要点：

```text
质量问题或商家原因退货时，运费通常由商家承担。
用户个人原因退货时，运费通常由用户承担。
```

实际回答只包含第一个：

```text
质量问题或商家原因退货时，运费通常由商家承担。
```

那么：

```text
answer_point_coverage = 1 / 2 = 0.5
```

如果两个都包含：

```text
answer_point_coverage = 1.0
```

这个指标适合早期学习。

它不是最终语义评测方案。

### 5. citation_passed 怎么判断

本节的 `citation_passed` 主要看：

```text
需要引用时有没有引用。
期望来源有没有出现在实际引用中。
有没有引用 forbidden source。
拒答回答有没有错误携带 citation。
```

如果期望来源是：

```text
refund-return-policy.md
```

实际引用也是这个来源，就通过。

如果实际引用是：

```text
order-shipping-policy.md
```

则失败。

如果实际引用包含：

```text
internal-compensation-policy.md
```

而它在 forbidden_sources 里，则 blocking。

### 6. refusal_passed 怎么判断

如果样本期望行为不是 `answer`，就要检查拒答原因。

比如期望：

```text
behavior: security_block
refusal_reason_codes:
  - PROMPT_INJECTION
```

实际必须提供：

```text
PROMPT_INJECTION
```

如果实际只是：

```text
NO_CONTEXT
```

就不算通过。

因为这会掩盖真正原因。

安全问题不能简单当成无资料问题。

### 7. 本节为什么不真实调用模型

本节仍然不真实调用大模型。

原因是：

```text
自动化测试必须稳定。
本节目标是学习评测结构，不是测某个模型能力。
真实模型输出存在随机性。
真实调用有成本和密钥风险。
```

所以测试里使用本地构造的 `RagAnswer`。

这样能专注学习：

```text
什么叫正确。
什么叫引用一致。
什么叫拒答合理。
失败时怎么结构化记录。
```

### 8. 本节和下一节 Bad Case 分析的关系

本节会输出质量 finding。

比如：

```text
RAG_ANSWER_POINT_MISSING
RAG_ANSWER_EXPECTED_SOURCE_MISSING
RAG_REFUSAL_REASON_MISSING
RAG_ANSWER_FORBIDDEN_SOURCE_USED
```

下一节 Bad Case 分析会继续问：

```text
为什么会出现这个 finding？
问题应该归因到数据、检索、排序、生成、引用、权限还是安全？
应该怎么修？
```

所以第 15 节负责发现问题。

第 16 节负责定位问题。

## 本节代码讲解

### 1. `RagAnswerQualityResult`

`RagAnswerQualityResult` 表示单个样本的回答质量评测结果。

它记录：

```text
期望行为和实际行为。
答案要点覆盖率。
匹配和缺失的答案要点。
期望来源和实际引用来源。
缺失来源、意外来源、禁用来源。
拒答原因是否匹配。
findings。
最终 passed。
```

它不是模型回答。

它是评测报告。

### 2. `evaluate_rag_answer_quality`

这个函数负责评估单个样本。

输入是：

```text
RagEvalCase
RagAnswer
actual_refusal_reason_codes
```

输出是：

```text
RagAnswerQualityResult
```

它会按四个维度检查：

```text
behavior
answer_points
citation
refusal
```

如果发现 blocking finding，最终 `passed` 就是 false。

### 3. `RagAnswerQualitySummary`

`RagAnswerQualitySummary` 汇总一组样本。

它会统计：

```text
case_count
answer_case_count
refusal_case_count
pass_rate
average_answer_point_coverage
citation_pass_rate
refusal_pass_rate
```

这些指标回答的是：

```text
最终回答整体质量怎么样。
```

它和第 14 节的检索指标不是一回事。

### 4. `format_rag_answer_quality_bad_cases`

这个函数把失败样本输出成可读列表。

它会显示：

```text
case_id
expected behavior
actual behavior
answer point coverage
finding code
finding evidence
```

下一节 Bad Case 分析会继续利用这种信息做归因。

## 常见误区

### 误区 1：检索 Recall 高，回答质量就一定高

不一定。

Recall 高只说明资料找回来了。

模型仍然可能漏要点、答错条件、引用错来源。

### 误区 2：回答看起来对，就不用看引用

不对。

RAG 的答案必须可追溯。

引用错来源，说明系统链路可能有问题。

### 误区 3：拒答就是失败

不对。

在 `no_context`、`access_denied`、`security_block` 场景里，拒答是正确行为。

### 误区 4：所有拒答都可以统一成“资料不足”

不建议。

无资料、无权限、安全阻断是不同原因。

内部评测必须能区分它们，否则无法定位问题。

### 误区 5：LLM-as-judge 可以替代所有确定性检查

不可以。

LLM-as-judge 可以作为补充，但确定性检查仍然重要。

比如：

```text
是否引用 forbidden source。
是否缺少结构化拒答原因。
是否没有 citation。
```

这些用规则更稳定。

### 误区 6：answer_points 覆盖率低一定说明模型差

不一定。

也可能是：

```text
answer_points 写得太死。
模型用了同义表达。
评测规则过于简单。
```

所以本节结果是基础自动评测，不是最终人工结论。

### 误区 7：warning 可以完全忽略

不应该。

warning 不一定让样本失败，但它提示潜在风险。

比如意外引用了一个不在 expected_sources 里的来源，可能说明上下文有噪声。

## 本节练习

### 练习 1：判断回答正确性

题目：

期望答案要点有两条：

```text
质量问题或商家原因退货时，运费通常由商家承担。
用户个人原因退货时，运费通常由用户承担。
```

实际回答只包含第一条。`answer_point_coverage` 是多少？

参考答案：

```text
answer_point_coverage = 1 / 2 = 0.5
```

### 练习 2：判断引用一致性

题目：

评测样本期望来源是：

```text
refund-return-policy.md
```

实际回答引用：

```text
order-shipping-policy.md
```

这是什么问题？

参考答案：

```text
引用来源不一致。
```

它可能导致：

```text
missing expected source
unexpected source
```

### 练习 3：判断拒答合理性

题目：

期望行为是 `security_block`，期望拒答原因是 `PROMPT_INJECTION`。实际系统返回 `NO_CONTEXT`。这算通过吗？

参考答案：

```text
不算通过。
```

原因：

```text
安全阻断不能被简单标成无资料，否则会掩盖真正的安全风险。
```

### 练习 4：判断 forbidden source

题目：

某样本的 `forbidden_sources` 包含：

```text
internal-compensation-policy.md
```

最终回答引用了这个来源。应该怎么判？

参考答案：

```text
应该判为 blocking 问题。
```

原因：

```text
这说明无权限或禁用资料进入了最终回答链路。
```

## 自测题

### 自测 1：回答质量评测和检索质量评测有什么区别？

答案：

检索质量评测看资料有没有找对。

回答质量评测看最终回答是否覆盖答案要点、引用是否一致、该拒答时是否拒答。

### 自测 2：为什么回答质量评测要看 citation？

答案：

因为 RAG 回答必须可追溯。答案看起来对但引用错误，仍然说明链路存在质量或审计风险。

### 自测 3：`answer_point_coverage` 为 0.5 说明什么？

答案：

说明期望答案要点只覆盖了一半。

它通常表示回答不完整，或评测规则没有识别同义表达。

### 自测 4：为什么拒答原因要结构化？

答案：

结构化拒答原因便于评测、日志分析、前端展示和问题定位。

自然语言拒答不稳定，不适合自动化评测。

### 自测 5：本节为什么不直接使用真实大模型评委？

答案：

因为本节目标是学习基础评测结构。确定性规则更稳定、成本更低、测试更可控。真实大模型评委以后可以作为补充。

## 本节小结

本节把 RAG 评测从“资料有没有找对”推进到“最终回答有没有答对”。

你现在要形成这条判断链：

```text
检索指标低：优先看检索、chunk、query rewrite、hybrid、rerank。
检索指标高但回答质量低：优先看 prompt、生成、上下文压缩、答案要点覆盖。
引用不一致：看 citation 构造、上下文来源、引用校验。
拒答不合理：看 no_context、权限、安全和意图判断。
```

下一节学习：

```text
Bad Case 分析：怎么定位 RAG 答错的原因。
```

到下一节，我们会把这些 finding 进一步归因到数据、检索、排序、生成、引用、权限和安全等层面。
