# Deep Research Agent（中文）

一个以文档为记忆、提供商无关的**深度 & 宽度研究智能体系统**——综合了
[grapeot/deep_research_agent](https://github.com/grapeot/deep_research_agent)、
[grapeot/codex_wide_research](https://github.com/grapeot/codex_wide_research)、
[grapeot/context-infrastructure](https://github.com/grapeot/context-infrastructure)
三个开源项目的方法论，并吸收了 [Anthropic 多智能体研究系统](https://www.anthropic.com/engineering/built-multi-agent-research-system)
与 [Manus Wide Research](https://manus.im/blog/introducing-wide-research) 的工程经验。

[English docs](README.md)

## 为什么再造一个研究智能体

大多数"Deep Research"产品其实是 **Wide Research**：解决的是信息不对称，
不是认知不对称。而且所有 LLM 都有一个规律：输出一旦接近上下文窗口上限，
就会开始偷懒——丢条目、缩略、跳过。本仓库用架构而非 prompt 技巧同时解决
这两个问题：

1. **文档即记忆。** 结构化 scratchpad 是智能体之间唯一的沟通渠道，重要
   信息绝不依赖上下文窗口存活。
2. **用代码合并，而不是 LLM。** 宽模式的并行 worker 各自拥有隔离上下文，
   报告由脚本逐字拼接——无损合并，天然免疫长输出偷懒。
3. **激励感知验证。** Claim Ledger 为每个关键主张记录信源层级与验证通道；
   厂商叙事不能自证。
4. **用户主权。** 命令执行前需要确认；引用全部内联；每次运行都是可审计
   的目录。

## 两种研究模式

**深度模式**（deep）—— Planner ⇄ Executor 循环：

```bash
python -m deep_research_agent "分析 NVDA 股价近期走势：价格变化、原因、市场情绪"
```

Planner 分解问题，把可验证的成功标准与下一步写入 `runs/<id>/scratchpad.md`
后交棒。Executor 搜索（≥3 组关键词、≥10 个信源）、抓取全文、产出带引用的
报告文件、经你 `[y/N]` 确认后运行分析脚本，并回写状态。Planner 审阅、再
规划、循环，直到满足标准——最后由反馈门交还控制权。

**宽度模式**（wide）—— 分而治之的并行扇出：

```bash
python -m deep_research_agent "调研 25 个开源 RSS 阅读器：维护状态、功能、社区健康度" --mode wide --workers 6
```

侦察阶段生成子任务清单 → 并行 worker（隔离上下文）各写一份带引用报告 →
**脚本**逐字合并 → 编辑阶段分章节润色（绝不一次性重写）。这就是覆盖 50+
条目而不被模型悄悄丢掉一半的方法。

## 快速开始

```bash
git clone https://github.com/<you>/deep-research-agent && cd deep-research-agent
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export OPENAI_API_KEY=sk-...        # 或下方任意提供商
python -m deep_research_agent "你的研究问题"
```

### 每个角色独立路由到任意提供商

```bash
# 例：OpenAI 推理型 planner + DeepSeek 便宜 worker
export DRA_PLANNER_MODEL=o3                              # + OPENAI_API_KEY
export DRA_RESEARCHER_PROVIDER=openai_compatible
export DRA_RESEARCHER_MODEL=deepseek-chat                # + DEEPSEEK_API_KEY
export DRA_RESEARCHER_BASE_URL=https://api.deepseek.com/v1

# Anthropic 执行者
export DRA_EXECUTOR_PROVIDER=anthropic
export DRA_EXECUTOR_MODEL=claude-sonnet-4-20250514       # + ANTHROPIC_API_KEY
```

兼容 OpenAI、Anthropic、DeepSeek、GLM、OpenRouter、Ollama、vLLM 等一切
OpenAI 协议端点。

## 目录结构

```
deep_research_agent/        Python 包
  orchestrator.py           深度模式 planner<->executor 主循环
  wide.py                   宽度模式：侦察 → 扇出 → 程序化合并 → 分章综合
  scratchpad.py             结构化共享记忆（含 Claim Ledger）
  llm.py                    提供商无关的对话 + 工具调用
  agents/                   planner / executor（行为契约在 rules/）
  tools/                    网络搜索/抓取（带缓存）、沙箱化文件与命令
rules/                      行为契约与方法论（真正的核心资产）
  planner.md · executor.md · wide_research_playbook.md · source_tiers.md
docs/                       设计文档 · 调研 SOP · 个人上下文指南
scripts/run_wide_children.sh  外部 CLI（codex 等）批量运行器
examples/                   示例运行（deep + wide）
```

## 即使不跑代码也值得读的方法论

- [docs/yage-methodology-map.html](docs/yage-methodology-map.html) — **可视化
  方法论图谱**（共识天花板、宽研究、三层记忆、信源分级 → 本仓库实现映射）
- [docs/yage-methodology.md](docs/yage-methodology.md) — 图谱的文字版沉淀笔记
- [docs/DESIGN.md](docs/DESIGN.md) — 架构与上游传承关系
- [deep_research_agent/rules/source_tiers.md](deep_research_agent/rules/source_tiers.md) — 激励感知的信源分级、
  claim 台账、读者模式
- [docs/survey_workflow.md](docs/survey_workflow.md) — 五阶段调研 SOP
- [docs/memory.md](docs/memory.md) — 用个人上下文突破共识天花板（三层记忆）

## 致谢

本项目建立在鸭哥（[@grapeot](https://github.com/grapeot)）的开源工作之上——
[deep_research_agent](https://github.com/grapeot/deep_research_agent)、
[codex_wide_research](https://github.com/grapeot/codex_wide_research)、
[context-infrastructure](https://github.com/grapeot/context-infrastructure)，
以及他在 [yage.ai](https://yage.ai/) 的写作；同时感谢 Anthropic 多智能体
研究系统、Manus Wide Research 与斯坦福 STORM 的公开成果。上游均为 MIT
协议，本综合项目同样采用 MIT。

## 许可

MIT — 见 [LICENSE](LICENSE)。
