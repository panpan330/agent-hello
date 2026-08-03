# 阶段 10 第 19 节：Bad Case 收集、分析与回归测试

## 本节定位

上一节我们学习了自动化评估平台基础：

```text
评测集
评测集版本
baseline
candidate
run snapshot
regression report
```

上一节重点解决：

```text
怎么发现候选版本相对 baseline 有没有退化。
```

这一节继续往后走，解决另一个更重要的问题：

```text
发现坏例以后，怎么记录、分析、修复，并把它变成以后自动回归检查的一部分。
```

AI 应用里，坏例不能只靠聊天记录随手截图。

真实项目里要形成闭环：

```text
发现坏例
  -> 记录 Bad Case
  -> 分类和定级
  -> 定位失败层
  -> 修复
  -> 加入 regression case
  -> 每次改动自动回归
```

本节不打开 VMware，不启动 Docker，不真实调用大模型。

## 本节学习目标

- 理解 Bad Case 是什么。
- 理解 Bad Case 和普通 bug 的区别。
- 理解 AI 应用坏例常见来源。
- 理解坏例为什么要记录稳定 ID、来源、严重级别、状态和归因层。
- 理解坏例分析不能一上来就改 prompt。
- 理解如何从坏例生成 regression case 草稿。
- 理解 Bad Case registry 和第 18 节 eval platform 的关系。
- 看懂本项目新增的 Bad Case registry 模块。

## 本节新增和修改

- 新增 `projects/ai-service/app/evaluation/bad_case_registry.py`
  - `BadCaseRecord`
  - `BadCaseRegistry`
  - `BadCaseRegistrySummary`
  - `RegressionCaseDraft`
  - 从 `BadCaseAnalysisItem` 生成坏例记录。
  - 从坏例记录生成 regression case 草稿。
  - 标记坏例已加入回归样本。
- 新增 `projects/ai-service/data/evaluation/bad_cases.json`
  - 当前为空，因为当前检入的本地回归报告没有真实失败坏例。
- 修改 `projects/ai-service/data/evaluation/README.md`
  - 补充 Bad Case registry 说明。
- 新增 `projects/ai-service/tests/test_bad_case_registry.py`
  - 覆盖坏例记录生成、汇总、重复 ID 拒绝、回归草稿和状态更新。

## 一句话先讲透

Bad Case 不是“模型答错了就改 prompt”，而是把一次失败沉淀成可追踪记录，并转化为以后必须自动回归通过的固定样本。

## 基础知识铺垫

### 1. 什么是 Bad Case

Bad Case 可以理解为：

```text
系统在某个真实或评测场景下，没有达到预期行为的具体样例。
```

例如：

```text
用户问退款到账时间，系统引用了账号安全文档。
用户要查订单，模型没有调用 query_order，直接编造订单状态。
用户要求创建工单，系统跳过确认直接创建。
用户发起 prompt injection，系统没有拒绝。
RAG 检索到了资料，但最终回答没有引用来源。
```

Bad Case 的重点是“具体样例”。

它不是一句抽象描述：

```text
RAG 效果不好。
```

而应该是：

```text
case_id=rag_refund_shipping_fee_answer_001
query=退货运费谁承担？
expected_source=refund-return-policy.md
actual_source=account-security-faq.md
failure_layer=rag_citation
```

具体到这种程度，后续才有办法复现、分析、修复和回归。

### 2. Bad Case 和普通 bug 的区别

普通 bug 通常更确定。

例如：

```text
接口 500
字段名写错
SQL 语法错误
空指针
参数校验没生效
```

Bad Case 更常见于 AI 应用质量问题。

它可能不是代码崩了，而是效果不对：

```text
分类错了
路由错了
检索错了
引用错了
回答漏关键点
该拒答时没拒答
该调用工具时没调用
调用了不该调用的工具
```

所以 Bad Case 分析不能只看报错堆栈。

它要看：

```text
输入是什么
期望是什么
实际是什么
中间状态是什么
检索结果是什么
模型输出是什么
工具调用是什么
安全规则是否触发
权限是否生效
```

### 3. AI 应用 Bad Case 常见来源

AI 应用坏例通常来自多个层。

常见层包括：

```text
数据层
检索层
排序层
生成层
引用层
意图识别层
字段提取层
路由层
工具调用层
权限层
安全层
模型输出层
评测规则层
```

举例：

数据层：

```text
知识库本来就没有这条规则。
文档过期。
chunk 切分把关键上下文切散了。
metadata 写错。
```

检索层：

```text
正确 chunk 没召回。
top_k 太小。
score_threshold 太高。
query rewrite 改坏了问题。
```

生成层：

```text
context 里有答案，但模型漏了关键点。
模型没有按格式回答。
模型编造了没有依据的内容。
```

工具调用层：

```text
应该调用 query_order 却没有调用。
工具参数 order_id 提取错。
模型请求了未授权工具。
```

安全层：

```text
Prompt Injection 没拦住。
敏感信息没有脱敏。
越权数据被返回。
```

### 4. 为什么不能一看到 Bad Case 就改 prompt

很多初学者看到坏例第一反应是：

```text
那我把 prompt 写得更详细一点。
```

这不一定对。

如果坏例来自检索层，改 prompt 可能没用。

例如正确文档根本没召回，模型看不到资料，再好的 prompt 也没法引用正确来源。

如果坏例来自权限层，改 prompt 更危险。

权限必须由后端和 Java 服务校验，不应该靠模型自觉。

正确流程应该是：

```text
先定位失败层。
再决定修哪里。
最后把坏例加进 regression。
```

### 5. Bad Case 应该记录哪些字段

一个可运营的坏例记录至少要有：

```text
id：稳定坏例 ID
title：简短标题
source：来源，eval / production / manual
task_type：agent / rag / tool_calling / safety
severity：严重级别
status：处理状态
dataset_name：来自哪个评测集
dataset_version：评测集版本
source_case_id：原始样本 ID
failure_layer：失败层
failure_category：失败类别
expected_behavior：期望行为
actual_behavior：实际行为
root_cause：根因说明
recommended_action：建议修复动作
regression_action：回归动作
regression_case_id：加入回归后的样本 ID
evidence_summary：脱敏证据摘要
tags：标签
```

注意这里说的是 `evidence_summary`，不是完整原文。

坏例记录也要遵守隐私边界。

不要把用户真实手机号、地址、API Key、完整聊天隐私直接塞进 registry。

### 6. Bad Case 状态流转

本项目当前使用这些状态：

```text
open
triaged
fixed
regression_added
closed
```

含义：

```text
open：刚发现，还没分析。
triaged：已经分类、定级、初步归因。
fixed：已经修复，但还没加回归样本。
regression_added：已经沉淀为回归样本。
closed：确认修复并完成闭环。
```

一个坏例如果只修了代码，但没加 regression case，下次可能再次出现。

所以更完整的闭环应该至少到：

```text
regression_added
```

### 7. 什么是回归样本

回归样本就是：

```text
从坏例沉淀出来，以后每次评测都必须检查的固定样本。
```

它的作用是防止：

```text
这个问题修好了，过几天又被另一个改动改坏。
```

例如坏例是：

```text
退款运费问题引用错文档。
```

修复后应该把它变成回归样本：

```text
query=退货运费谁承担？
expected_source=refund-return-policy.md
forbidden_source=account-security-faq.md
tags=["regression", "from_bad_case", "rag_citation"]
```

以后每次改 RAG 检索、rerank、citation、prompt，都要跑它。

### 8. Bad Case 和第 18 节的关系

第 18 节关注：

```text
评测集版本 + baseline + candidate + regression report
```

第 19 节关注：

```text
某个 regression 是怎么来的，怎么修，怎么沉淀回评测集。
```

它们连起来是：

```text
eval platform 发现退化
  -> bad case registry 记录坏例
  -> 开发者分析和修复
  -> 生成 regression draft
  -> 加入 eval dataset
  -> 下一轮 eval platform 自动检查
```

## 本节主题系统讲解

### 1. 当前项目已有坏例分析能力

项目中已有：

```text
app/agents/bad_case_analysis.py
```

它能从 Agent eval 报告中提取失败样本，并分类为：

```text
intent_classification
ticket_field_extraction
agent_routing
rag_retrieval_or_citation
agent_decision_after_rag
unknown
```

它更像：

```text
一次 eval 报告的分析器。
```

它会告诉你：

```text
哪个 suite 失败
哪个 case 失败
可能是哪层
建议问哪些排查问题
建议怎么修
建议怎么回归
```

本节新增的是：

```text
app/evaluation/bad_case_registry.py
```

它负责把分析结果变成长期记录。

### 2. 为什么要新增 Bad Case registry

如果只有报告，没有 registry，会有几个问题：

```text
坏例分散在不同 Markdown 报告里。
不知道哪个坏例修了。
不知道哪个坏例已经加入回归。
不知道哪个坏例还 open。
不知道同一个问题有没有重复出现。
不好统计哪些层最常出问题。
```

Bad Case registry 解决的是：

```text
把坏例当成可管理的数据，而不是一次性文本报告。
```

### 3. 为什么当前 `bad_cases.json` 是空的

本节新增：

```text
data/evaluation/bad_cases.json
```

当前内容为空：

```json
{
  "schema_version": "stage10.bad_case_registry.v1",
  "records": []
}
```

原因是当前检入的本地 Agent 回归报告是通过的。

不能为了演示而伪造“真实坏例”放进主数据。

测试里会用 synthetic bad case 验证逻辑。

真实项目中，如果以后 eval 或线上发现问题，再把脱敏后的真实坏例记录进这个文件。

### 4. 从分析项到坏例记录

本节提供：

```text
build_bad_case_record_from_analysis_item()
```

它把：

```text
BadCaseAnalysisItem
```

转换成：

```text
BadCaseRecord
```

转换时会补充：

```text
dataset_name
dataset_version
discovered_run_id
severity
failure_layer
tags
stable bad case id
```

这样报告中的一条失败，就能进入长期 registry。

### 5. 失败层映射

旧分析类别会映射到更稳定的 failure layer：

```text
intent_classification -> intent
ticket_field_extraction -> field_extraction
agent_routing -> routing
rag_retrieval_or_citation -> rag_citation
agent_decision_after_rag -> agent_decision
```

为什么要映射？

因为分析类别可能偏报告文本，而 failure layer 更适合统计和运营。

例如以后你可以统计：

```text
最近 30 个坏例里，rag_citation 占 12 个，routing 占 8 个。
```

这会指导你优先优化哪层。

### 6. 严重级别怎么来

当前最小规则：

```text
p0 -> critical
p1 -> high
p2 -> medium
未知 -> medium
```

为什么 p0 是 critical？

因为 p0 通常代表核心回归场景。

如果 p0 坏了，通常说明核心能力被破坏，应该优先处理。

以后可以继续扩展更细规则：

```text
安全样本失败 -> critical
权限样本失败 -> critical
高频业务样本失败 -> high
普通边缘样本失败 -> medium
体验类小问题 -> low
```

### 7. 从坏例生成 regression draft

本节提供：

```text
build_regression_case_draft()
```

它不会直接修改 `agent_cases.json` 或 `rag_cases.json`。

它生成的是“草稿”。

原因是不同评测集格式不一样：

```text
Agent case 有 inputs / expected / metadata
RAG answer case 有 query / expectation / access_context
Retrieval case 有 expected_sources / expected_sections / filters
```

所以自动生成完整合法样本容易误写。

当前更稳妥的做法是：

```text
先生成 regression draft
开发者确认后，再按目标评测集格式补完整样本。
```

这符合“省 token 模式”和工程安全边界。

### 8. 标记 regression_added

坏例修复后，如果已经加入回归样本，就可以调用：

```text
mark_bad_case_regression_added()
```

它会更新：

```text
status=regression_added
regression_case_id=...
regression_dataset_name=...
```

这表示：

```text
这个坏例已经不只是修了，还被加入以后自动评测的保护网。
```

## 本节代码讲解

### 1. `BadCaseRecord`

它是坏例记录的核心模型。

关键字段：

```text
id
title
source
task_type
severity
status
dataset_name
dataset_version
source_case_id
failure_layer
expected_behavior
actual_behavior
recommended_action
regression_action
evidence_summary
tags
```

你可以把它理解成：

```text
一个坏例的工单。
```

区别是这个工单不是用户业务工单，而是 AI 质量工单。

### 2. `BadCaseRegistry`

它是一组坏例记录。

它要求：

```text
record id 不能重复。
```

如果 ID 重复，就无法知道某次状态更新更新的是哪条坏例。

### 3. `BadCaseRegistrySummary`

它用于快速统计：

```text
总坏例数
open 数量
已加入回归数量
严重级别分布
状态分布
失败层分布
```

这些统计对项目复盘很有用。

例如如果发现大部分坏例都在 `rag_citation`，就说明引用链路需要优先加强。

### 4. `build_bad_case_record_from_analysis_item()`

它把旧的分析项转换成 registry record。

这个函数是本节和旧代码的连接点。

也就是说：

```text
旧 eval report -> BadCaseAnalysisItem -> BadCaseRecord -> registry
```

这样旧能力可以继续复用，不需要重写 eval suite。

### 5. `build_regression_case_draft()`

它从坏例生成回归样本草稿。

草稿包含：

```text
source_bad_case_id
target_dataset_name
suggested_case_id
title
input_summary
expected_behavior
assertions
tags
```

注意它叫 draft。

它提醒你应该把这个坏例加到哪个评测集、建议 ID 是什么、要断言哪些行为。

### 6. `mark_bad_case_regression_added()`

它返回一个更新后的 record。

原 record 不会被原地修改。

这样做更安全，也更容易测试。

## 常见误区

### 误区 1：Bad Case 就是模型答错了

不完整。

模型答错只是结果。

坏例可能来自数据、检索、路由、工具、权限、安全、评测规则等多个层。

### 误区 2：坏例越多越说明项目差

不一定。

能系统收集坏例，说明项目进入了可改进状态。

真正危险的是：

```text
用户已经遇到问题，但项目没有记录、没有复现、没有回归。
```

### 误区 3：修复坏例就是改 prompt

不对。

应该先归因。

检索坏例修检索，权限坏例修权限，工具坏例修工具边界，prompt 坏例才改 prompt。

### 误区 4：坏例修完就可以关闭

还不够。

修完后最好加入 regression case。

否则下次改动可能再次引入同样问题。

### 误区 5：Bad Case registry 可以保存完整用户原文

不推荐。

registry 应该保存脱敏摘要和可复现信息。

真实隐私内容不要长期沉淀在学习仓库或日志里。

## 当前项目边界

本节已经具备：

```text
Bad Case registry 模型
坏例状态
严重级别
失败层
坏例汇总统计
从 Agent bad case analysis 转 registry record
从坏例生成 regression draft
标记 regression_added
空 bad_cases.json
关键测试
```

尚未深入：

```text
自动写回 agent_cases.json
自动写回 rag_cases.json
线上坏例采集 API
坏例数据库
人工审核工作台
前端可视化
和 CI 的强制阻断联动
```

这些后续可以在完整项目作品化和上线阶段继续补。

## 练习题

### 练习 1：判断下面哪个是合格 Bad Case 描述

题目：

```text
A. RAG 不太准。
B. case_id=rag_refund_shipping_fee_answer_001，问题“退货运费谁承担？”，期望引用 refund-return-policy.md，实际引用 account-security-faq.md，failure_layer=rag_citation。
```

参考答案：

```text
B 更合格。

A 太抽象，无法复现和回归。
B 有具体样本、期望、实际和失败层，可以进入 Bad Case registry。
```

### 练习 2：为什么坏例修复后还要加入 regression case？

参考答案：

```text
因为修复只解决当前问题，regression case 可以防止未来改动再次破坏这个能力。
AI 应用经常改 prompt、RAG 参数、工具 schema 和路由逻辑，如果没有回归样本，旧问题很容易重新出现。
```

### 练习 3：为什么不能一看到坏例就改 prompt？

参考答案：

```text
因为坏例可能不是 prompt 问题。
如果正确文档没召回，应该先修检索；如果权限没拦住，应该修后端权限；如果工具参数错，应该修参数提取或 schema。
不归因就改 prompt，可能修不好当前问题，还引入新退化。
```

### 练习 4：Bad Case registry 为什么要有 status？

参考答案：

```text
因为坏例需要长期跟踪。
status 可以区分 open、triaged、fixed、regression_added、closed，帮助判断哪些还没分析、哪些已修复、哪些已经进入回归保护。
```

## 自测问题

### 自测 1：Bad Case 的核心价值是什么？

参考答案：

```text
把一次具体失败沉淀成可复现、可分析、可修复、可回归的质量资产。
```

### 自测 2：Bad Case 和 regression case 的关系是什么？

参考答案：

```text
Bad Case 是已经发生过的失败样例。
Regression case 是从坏例沉淀出来、以后每次评测都要检查的固定样本。
```

### 自测 3：failure_layer 为什么重要？

参考答案：

```text
因为它帮助定位应该修哪一层。
如果 failure_layer 是 rag_citation，就优先查引用和检索；如果是 routing，就查 Agent 路由；如果是 security，就查安全边界。
```

### 自测 4：为什么当前 `bad_cases.json` 是空的？

参考答案：

```text
因为当前检入的本地回归报告没有真实失败坏例。
项目不应该为了演示而伪造真实坏例数据，测试里使用 synthetic bad case 验证逻辑即可。
```

### 自测 5：坏例记录里为什么只放 evidence_summary？

参考答案：

```text
因为坏例可能来自真实用户输入或包含敏感信息。
registry 要保存可排查的脱敏摘要，不应该长期保存完整隐私原文、密钥或敏感业务内容。
```

## 本节手动验证命令

本节不需要打开 VMware Ubuntu。

本节不需要真实调用大模型。

按当前约定，测试由你手动执行：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run pytest tests/test_bad_case_registry.py -q
```

如果想顺便验证旧坏例分析：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run pytest tests/test_bad_case_analysis.py tests/test_bad_case_registry.py -q
```

## 本节小结

本节把 Bad Case 从“报告里的一段失败文本”推进到“可管理的坏例记录和回归草稿”。

你现在应该能讲清：

```text
Bad Case 是什么。
Bad Case 和普通 bug 有什么区别。
为什么要先归因再修复。
为什么坏例要有状态、严重级别和失败层。
为什么修复后要加入 regression case。
为什么坏例记录也要注意隐私脱敏。
```

下一节进入：

```text
阶段 10 第 20 节：生产监控指标与告警基础
```
