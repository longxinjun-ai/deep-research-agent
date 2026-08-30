# yage.ai 方法论沉淀笔记

> 本文档是 [yage-methodology-map.html](yage-methodology-map.html)（可视化图谱）的文字版，
> 沉淀自鸭哥（Yan Wang / [@grapeot](https://github.com/grapeot)）在 [yage.ai](https://yage.ai/)
> 的写作与三个开源项目。每节标注了在
> [deep-research-agent](https://github.com/longxinjun-ai/deep-research-agent) 中的对应实现。
> 整理日期：2026-08-30。

## 1. 共识天花板：正确的废话从哪来

**诊断**：LLM 的默认输出是"共识"——多数人会同意的话。两个机制叠加：
下一词预测天然选择最高概率词（≈ 平均意见）；RLHF 进一步惩罚争议观点、奖励不表态。
结果是对均值回归：正确、安全、平庸。这对新手是提升，对专家是无增益——
深度天生是非共识的，恰是模型被训练远离的东西。

**关键区分**：
- 信息不对称（知道更多事实）→ 宽研究可以解决；
- 认知不对称（知道如何解读）→ 只有注入个人判断上下文才能解决。

**为什么直觉修法全部失败**：换更强模型、写更精巧 prompt、叠加多智能体 harness，
都在优化同一个维度——模型智能。对照实验（同等模型、同样工具、同一任务，唯一变量是
有无一年积累的判断框架）产出截然不同：无上下文的一台产出通用清单，有上下文的一台
做出跨源综合并点出底层权衡——"一个是快递员，一个是分析师"。

**资产视角**：模型智能会贬值（每次升级都让它廉价而普及）；个人上下文不贬值且复利
（只属于你）。所以系统性的投资方向是后者。

**出处**：[Why AI Only Gives You Correct Nonsense](https://yage.ai/context-infrastructure-en.html)；
实现映射：`rules/planner.md` 的成功标准与停止条件、`docs/memory.md`。

## 2. 宽研究（Wide Research）：让 53 篇博客一篇不少

**现象**：所有 LLM 在输出占到上下文窗口一定比例（50%，有时甚至 20%）后开始偷懒——
跳句、缩略、丢条目，然后声称完成。归因于 Transformer 全局注意力机制，是架构性质，
不是 prompt 能修的。各模型开始偷懒的长度不同（GPT-4o-mini 几百词；GPT-5/GLM-4.6
约 2-3 千词），但无一幸免。

**基准案例**：53 篇学生博客总结。Cursor/ChatGPT 完成 ~9 篇；Deep Research ~17 篇；
Codex 串行硬做 ~21 篇；DeepSeek 的总结"基本全是幻觉"。只有分而治之的宽研究做到
53/53 且姓名-URL 对应无误、零幻觉。

**解法**（Manus 洞察 + Codex 实现）：
1. 问题拆成独立子问题 → 每个子问题一个轻量 agent（上下文隔离）；
2. 每个 agent 输出都很短 → 结构上消灭偷懒；
3. **用代码（不是 LLM）聚合**子结果 → 无损合并；
4. 主 LLM 只做最后的分章润色。

**反"角色扮演"多智能体**：不写"你是资深工程师"——LLM 本来持有全部职业技能，角色
设定只会限制它。正确做法是纯上下文隔离：不同进程拿不同子问题，只通过文件通信。

**管理层方法**：像 senior manager 一样管理 AI——不微观管理，设计流程；建 5-10 个
典型用例做 prompt 回归；把迭代本身也宽研究化（让子 agent 自反思并给"过去的自己"提建议）。

**出处**：[wide-research（中文）](https://yage.ai/wide-research.html) /
[英文版](https://yage.ai/wide-research-en.html)、
[grapeot/codex_wide_research](https://github.com/grapeot/codex_wide_research)、
[Manus Wide Research](https://manus.im/blog/introducing-wide-research)；
实现映射：`wide.py`（侦察→清单→扇出→代码合并→分章综合）、
`rules/wide_research_playbook.md`。合并不变量：`wide.aggregate()` 是纯代码。

## 3. 三层记忆：把判断力沉淀成资产

**起点**：高手说不清自己为什么厉害（大部分是肌肉记忆），所以收集**行为数据**而非
自我报告：语音转写、会议记录、聊天导出、每一次你对 AI 的纠正，本地文件集中一处。

**分层蒸馏**（过滤标准是**稳定性**：跨情境、跨时间反复出现的判断才是真实认知结构）：
- **L1 观察者**（每日 cron）：扫描文件变更，提取观察，写运行日志；
- **L2 反思者**（每周 cron）：合并重复、剪枝过期、找跨项目模式；
- **L3 公理**（不定期）：把稳定模式蒸馏成可引用的决策原则。

**与 Mem0 类系统的本质区别**：事实记忆止步于"你偏好 TypeScript"；本系统到达判断
原则——如何权衡取舍。*事实告诉 AI 你是谁；判断公理告诉 AI 你怎么想。*

**按需加载**（CPU 存储层级类比）：不能把一切塞进上下文（无关数据稀释信号）。
L1 cache = 路由文件（AGENTS.md）；L2 = 技能索引；L3 = 具体技能/公理文件，按任务加载。

**反馈闭环**：知识产品（AI 日报、调研报告）既消费上下文又再生新数据，循环自增强。
刻意注入自己的偏见是重点——培养出来的偏见是深度的来源。

**出处**：[grapeot/context-infrastructure](https://github.com/grapeot/context-infrastructure)
（一年期参考实现：44 条公理、25+ 技能、observer.py / reflector.py）；
实现映射：`docs/memory.md`、AGENTS.md 路由表、runs/ 产物回流。

## 4. 激励感知验证：信源不是平等的

**原则**：信息价值取决于信源的激励结构。厂商叙事有用但不能自证；每个关键主张都要
追溯到不因该主张获益的独立证据。

| 层级 | 类型 | 用法 |
|---|---|---|
| Tier 1 | 厂商文档/官方 blog | 只提取主张，不作验证依据 |
| Tier 2 | 媒体报道/软文评测 | 理解市场叙事 |
| Tier 3 | 独立博客/HN/Reddit | 验证信号（注意采样偏差） |
| Tier 4 | GitHub issues/迁移故事/post-mortem/commit | **行为证据**，最高可信度 |

可信度递增链：态度表达 < 使用场景 < 对比决策 < 迁移故事 < post-mortem < 代码证据。

**Claim Ledger**：每个关键主张一行（主张 · 层级 · 验证通道 · 状态）。只有 Tier 3-4
证据能改状态；**contested 是合法结果**，写进报告而非悄悄选边。

**读者模式**：内部备忘（共享上下文，跳过常识只写增量）vs 外部论证（零预设读者，
显式回答 why this matters）。三问选模式：共享上下文吗？要快判断还是要信服？
拿掉私有背景还成立吗？

**出处**：context-infrastructure `workflow_deep_research_survey` 技能；
实现映射：`rules/source_tiers.md`、scratchpad 的 Claim Ledger 区、
`docs/survey_workflow.md`（五阶段 SOP）。

## 5. 实现与验证状态

本仓库 [deep-research-agent](https://github.com/longxinjun-ai/deep-research-agent)
把上述理念落成可运行系统：deep 模式（planner⇄executor + scratchpad）与 wide 模式
（扇出 + 代码合并），提供商无关（实测 GLM-5.3-Flash 全角色端到端跑通：19 分钟完成
DuckDB 调研，版本结论 3 信源交叉验证，DuckLabs 新闻被正确标注"厂商叙事未独立验证"，
独立抽查无幻觉）。

**遗留待办**：`usage.py` 的 PRICES 表补充 glm-5.3-flash 实际价格；wide 模式实测；
为会话增加断点续跑命令（见 CONTRIBUTING.md 的 suggested first issues）。
