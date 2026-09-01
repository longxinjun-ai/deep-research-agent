# AI 时代的检索：Agent 与人类的检索版图

> 调研整理于 2026-08-30，供学习参考。覆盖三大产品（Undermind / Tavily / Perplexity）、
> 语义检索代表 Exa，以及 GitHub 上主流的 wide/deep research 开源项目。
> 所有第三方数字（stars 等）为检索时点的约值。

## 0. 一张图看清分化

AI 时代的检索不是一条路线，而是沿三个维度分化：

| 维度 | 分化 |
|---|---|
| **给谁检索** | for human（Perplexity 答案引擎、Undermind 共同研究者）vs **for agent**（Tavily / Exa——返回 LLM-ready 文本而非蓝色链接） |
| **检索范式** | 关键词倒排（Google）→ 神经语义（Exa 的 embedding + next-link 预测）→ **检索编排层**（Tavily：搜+抓+洗+排一体）→ 迭代智能体循环（deep research 类）→ **并行扇出**（wide research 类） |
| **深度 vs 宽度** | 深度（Undermind：迭代挖长尾文献，分钟级慢搜索换精度）vs 宽度（Manus / WideSeek：分而治之并行覆盖） |

与 [yage.ai 方法论](yage-methodology.md)的对齐：deep research 解决"问得更深"，
wide research 解决"铺得更开"；两者共同服务的信息目标仍是鸭哥说的——
先关闭信息不对称，个人上下文再关闭认知不对称。

## 1. 产品层

### 1.1 Undermind — 学术文献的"共同研究者"

- **定位**：YC 系的 AI 深度文献检索（[undermind.ai](https://www.undermind.ai/)），复杂技术问题的精确检索
- **架构特点**：自适应多步迭代搜索；**读全文和图表**而非只看标题摘要；跟随引用链直到找全；
  跨多个学术库主动挖"长尾"论文（精确相关但难以检索的）
- **取舍**：一次深度搜索要几分钟——用时间换精度，与"秒回"的答案引擎相反
- **学习点**：迭代预算可以公开承诺（"慢而深"是卖点而非缺陷）；引用链遍历是学术场景独有的
  高价值通道（对应信源分级里 Tier 4 的 commit/引用级证据思想）
- 来源：[官网](https://www.undermind.ai/) · [Aaron Tay 的学术 deep research 分析](https://aarontay.substack.com/p/why-i-think-academic-deep-research) · [HN 发布讨论](https://news.ycombinator.com/item?id=39906683)

### 1.2 Tavily — for agent 的检索编排层

- **定位**：专为 LLM agent 设计的 Search API（[docs.tavily.com](https://docs.tavily.com/documentation/about)）：
  一次调用完成搜索+抓取+清洗+排序，输出"塞进上下文窗口就能用"的干净文本
- **产品面**：Search / Extract（整页抽取）/ Crawl 三件套；LangChain 等框架集成 + 官方 MCP
- **与 Google SERP 的本质区别**：Google 返回给人看的 SERP 数据（自己再建抓取管道）；
  Tavily 返回给机器用的已处理内容——**它是 RAG 管道的编排层**，不是排名引擎
- **社区口碑分裂**：有第三方测评认为它"比任何检索 API 都接近 Google"[cloro.dev](https://cloro.dev/blog/tavily-vs-google-search/)；
  也有 r/Rag 用户觉得不如直接用 Google GCP 自建（[Reddit](https://www.reddit.com/r/Rag/comments/1gr8jnr/which_search_api_should_i_use_between_tavilycom/)）——检索 API 选型没有银弹，按查询类型测
- **实用**：免费层 1,000 credits/月；本项目已集成（`DRA_SEARCH_BACKEND=tavily`）
- 来源：[Hybrid RAG 博客](https://www.tavily.com/blog/hybrid-rag-with-tavily-combining-static-knowledge-and-dynamic-web-data) · [IBM corrective RAG 教程](https://www.ibm.com/think/tutorials/build-corrective-rag-agent-granite-tavily) · [竞品横评](https://www.firecrawl.dev/blog/tavily-alternatives)

### 1.3 Perplexity — 答案引擎到研究 API

- **定位**：面向人的 AI 答案引擎；对开发者开放 [Sonar API](https://docs.perplexity.ai/docs/sonar/quickstart)
  （OpenAI 兼容的 web-grounded chat completions）
- **Sonar Deep Research**：穷尽式检索数百源、多步"搜索→阅读→评估"、综合成专家级报告；
  2–4 分钟完成人类专家数小时的工作（[官方模型文档](https://docs.perplexity.ai/docs/sonar/models/sonar-deep-research)）
- **工程细节**：限频显著低于普通 Sonar 档（Tier 0 仅 5 RPM，漏桶算法管理）——深度检索的
  计算成本是真实约束；有企业通过策略优化省约 40% 成本
- **学习点**：把 deep research 做成**模型档位**而非工作流（API 调用即研究）——与我们的
  显式编排路线互为镜像；其 2-4 分钟/数百源的规模是单上下文 deep research 的上限参照
- 来源：[Deep Research 发布博客](https://www.perplexity.ai/hub/blog/introducing-perplexity-deep-research)

### 1.4 Exa — 神经检索（第三条路线）

- **定位**：为 agent 建的语义检索 API（[exa.ai](https://exa.ai/)）
- **核心创新**：不把文档预处理成关键词，而是预处理成 **embedding**；训练网络做
  **next-link prediction**——给定文本预测"下一个该去的网页"（LLM 的 next-token 在链接域的类比），
  CEO 称之为 neural PageRank（[Latent Space 访谈](https://www.latent.space/p/exa)）
- **与关键词系的本质差异**：查询与结果无需共享字词，按语义排序；自建 web 规模向量库
  （[工程博客](https://exa.ai/blog/building-web-scale-vector-db)）
- **学习点**：关键词搜索（Tavily/ddgs）+ 语义搜索（Exa）互补——前者强在精确匹配与新闻时效，
  后者强在"找同类"与概念探索；本项目可将 Exa 加为第二 search backend 做混合检索

## 2. 开源项目层（GitHub）

### deep research 系列（迭代循环：search → read → reason）

| 项目 | 一句话 | 架构核心 | 学习点 |
|---|---|---|---|
| [assafelovic/gpt-researcher](https://github.com/assafelovic/gpt-researcher)（~29k★） | 最早的 open deep research | 规划-检索-写作分离，报告生成积木，web+本地文档 | 生产化最成熟；多源报告模板值得借鉴 |
| [stanford-oval/storm](https://github.com/stanford-oval/storm) | Wikipedia 式长文 + 引用 | **视角驱动提问**（perspective-guided）；Co-STORM 交互式知识共构 | 部分评测胜过 Perplexity/Google DR；"多视角提问"是我们的 manifest 尚未显式做的 |
| [langchain-ai/open_deep_research](https://github.com/langchain-ai/open_deep_research) | 可配置参考实现 | 多模型/多搜索工具/MCP 全可换 | 配置化设计：我们的 env 路由思路的更完整版 |
| [huggingface/open-deep-research](https://huggingface.co/blog/open-deep-research) | 24h hackathon 复刻 | **CodeAgent**：写 Python 代码作为行动（而非 JSON 工具调用），GAIA 55%（OpenAI DR 约 67%） | 代码即行动（code-as-action）的表达力上限；纯文本浏览器足够 |
| [jina-ai/node-DeepResearch](https://github.com/jina-ai/node-deepresearch) | 12 小时复刻 OpenAI DR | 严格 **token 预算**内的迭代 search-read-reason；只求找到答案不写长文 | 预算显式化；"答案型 vs 报告型"的定位切割 |
| [dzhng/deep-research](https://github.com/dzhng/deep-research) | ~500 行极简版 | 递归：搜索→提炼 learnings→生成新查询方向 | 极简可读，最佳入门材料；[Langfuse 架构深潜](https://langfuse.com/blog/2025-02-20-the-agent-deep-dive-open-deep-research) |

### wide research 系列（并行扇出：fan-out → merge）

| 项目 | 一句话 | 架构核心 | 学习点 |
|---|---|---|---|
| [grapeot/codex_wide_research](https://github.com/grapeot/codex_wide_research) | 宽研究 playbook（本项目上游） | 子进程上下文隔离 + 代码合并 | 已吸收 |
| [hzy312/WideSeek](https://github.com/hzy312/WideSeek)（[论文](https://www.alphaxiv.org/abs/2602.02636)） | 学术化 wide research | **动态分层**：按任务要求自主 fork 数量不等的并行子代理 | 动态 fork vs 我们的静态 manifest——可做自适应扇出 |
| [WideSeek-R1](https://arxiv.org/abs/2602.04634)（[项目页](https://wideseek-r1.github.io/)） | 宽度扩展 + RL | lead/subagent 系统经**多智能体 RL（MARL）**训练做广度信息seek | 扇出编排可学习而非手写规则——长期方向 |
| [bastani-inc/atomic](https://github.com/bastani-inc/atomic) | 可验证编码 agent 运行时 | `/workflow fan-out-and-synthesize`：按子系统切分仓库并行 | fan-out 模式从检索迁移到代码域的证据 |
| [Google Research: scaling agent systems](https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/) | 扇出的定量科学 | 180 种配置的系统性评测，给出**何时该/不该**用多智能体的定量原则 | 直接支撑我们 rules 里的 effort-scaling 规则，值得精读 |
| [DavidZWZ/Awesome-Deep-Research](https://github.com/DavidZWZ/Awesome-Deep-Research) | awesome list | — | 持续跟踪用 |
| [yibie/awesome-autoresearch](https://github.com/yibie/awesome-autoresearch) | 自动研究 awesome | 含 AutoResearchBench：deep+wide 互补任务基准 | 评测基准视角 |

## 3. 演化主线与启示

**范式链条**（按时序与抽象层级递进）：

```
关键词检索(Google SERP, 给人)
  → 神经语义检索(Exa, 给agent, 按意义排序)
  → 检索编排层(Tavily, 搜抓洗排一体, agent-ready)
  → 迭代智能体(deep research: 预算内 search-read-reason 循环)
  → 并行扇出(wide research: 分而治之+代码合并)
  → 编排可学习(WideSeek-R1: MARL 训练扇出策略)
```

**对本项目（deep-research-agent）的行动启示**，按 ROI 排序：

1. **精读 Google 的 scaling agent systems 博客**——把 effort-scaling 规则从启发式升级为定量依据（免费）
2. **Exa 作为第二 search backend**——`tools/web.py` 的 backend 抽象已就位，加一条分支即可；关键词+语义混合检索
3. **STORM 的视角驱动提问**——manifest 生成时按"支持者/批评者/历史学家"等多视角出查询，提升覆盖多样性
4. **HF CodeAgent 的代码即行动**——executor 的 execute_command 已是雏形；数据采集类子任务可鼓励直接写代码而非多轮工具调用
5. **WideSeek 的动态 fork**——按 recon 阶段估计的规模自适应决定子任务数/并发，替代固定 --workers
6. **Undermind 的定位启示**——学术场景的 claim 台账可加"引用链遍历"通道（顺藤摸瓜式验证）

## 4. 全部来源

- Undermind：[官网](https://www.undermind.ai/) · [CASRAI 指南](https://casrai.org/guides/undermind-ai) · [Aaron Tay 分析](https://aarontay.substack.com/p/why-i-think-academic-deep-research) · [HN 讨论](https://news.ycombinator.com/item?id=39906683)
- Tavily：[About 文档](https://docs.tavily.com/documentation/about) · [Hybrid RAG](https://www.tavily.com/blog/hybrid-rag-with-tavily-combining-static-knowledge-and-dynamic-web-data) · [IBM 教程](https://www.ibm.com/think/tutorials/build-corrective-rag-agent-granite-tavily) · [cloro 测评](https://cloro.dev/blog/tavily-vs-google-search/) · [竞品横评](https://www.firecrawl.dev/blog/tavily-alternatives) · [Reddit r/Rag](https://www.reddit.com/r/Rag/comments/1gr8jnr/which_search_api_should_i_use_between_tavilycom/)
- Perplexity：[Sonar Deep Research 文档](https://docs.perplexity.ai/docs/sonar/models/sonar-deep-research) · [Quickstart](https://docs.perplexity.ai/docs/sonar/quickstart) · [发布博客](https://www.perplexity.ai/hub/blog/introducing-perplexity-deep-research)
- Exa：[官网](https://exa.ai/) · [nextgen search 博客](https://exa.ai/blog/how-to-build-nextgen-search) · [post-ChatGPT 检索](https://exa.ai/blog/building-search-for-the-post-chatgpt-world) · [web 规模向量库](https://exa.ai/blog/building-web-scale-vector-db) · [Latent Space 访谈](https://www.latent.space/p/exa)
- 开源：[gpt-researcher](https://github.com/assafelovic/gpt-researcher) · [storm](https://github.com/stanford-oval/storm) · [langchain open_deep_research](https://github.com/langchain-ai/open_deep_research) · [HF open-deep-research 博客](https://huggingface.co/blog/open-deep-research) · [jina node-DeepResearch](https://github.com/jina-ai/node-deepresearch) · [dzhng deep-research](https://github.com/dzhng/deep-research) · [Langfuse 深潜](https://langfuse.com/blog/2025-02-20-the-agent-deep-dive-open-deep-research) · [GAIA 榜](https://huggingface.co/spaces/gaia-benchmark/leaderboard)
- wide research 学术线：[WideSeek](https://github.com/hzy312/WideSeek) · [WideSeek-R1](https://arxiv.org/abs/2602.04634) · [Google scaling science](https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/) · [SearchSwarm](https://arxiv.org/html/2606.09730v2) · [Awesome-Deep-Research](https://github.com/DavidZWZ/Awesome-Deep-Research) · [awesome-autoresearch](https://github.com/yibie/awesome-autoresearch)
