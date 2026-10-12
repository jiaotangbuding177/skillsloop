# 面向 LLM Agent 自进化记忆的安全审查：从记忆投毒到整理漂移与治理机制
> **版本**：v0.1  
> **日期**：2026-07-01  
> **定位**：研究计划 / 调研计划 / 实验设计草案  
> **暂定英文题目**：*Auditing Self-Evolving Memory in LLM Agents: From Memory Poisoning to Consolidation Drift and Governance*

---
##  0. 一句话定位
LLM Agent 的长期记忆正在从“静态上下文存储”演变为“会自动写入、压缩、反思、合并、遗忘、连边、检索调参和跨 Agent 同步的可变系统”。  
因此，安全问题不再只是“恶意内容能否进入 memory”，而是：
> **污染、错误、过时、越权或不完整的记忆，是否会在 Agent 的自我整理和自我演化过程中被放大、洗白、传播、固化，并最终影响后续行为。**

本计划的目标是把这个问题系统化，形成一套面向 **self-evolving agent memory** 的安全审查框架、威胁模型、基准测试和治理机制。

---
## 1. 研究动机
### 1.1 背景



- 攻击者可以通过查询交互向 memory bank 注入恶意记录；
- 恶意网页、邮件、PDF 或外部内容可以通过间接 prompt injection 进入长期记忆；
- 被投毒的长期记忆可以跨 session 持续影响 Agent 行为；
- 长期记忆中的隐私信息可能被攻击者通过 prompt 抽取。

本研究进一步关注：
> **memory 被写入之后，Agent 的自动整理、反思、合并、遗忘、连边和检索调参是否会改变攻击性质。**

换言之，攻击对象从 **memory store** 扩展为完整的 **memory evolution pipeline**。
### 1.3 与 agent skill 自进化安全的类比



### 23.4 实现 toy memory manager
目标功能：
```text
add_memory
summarize_session
merge_memory
retrieve_memory
dump_memory
diff_memory
rollback_memory
```
### 23.5 跑第一个 case
优先跑：
```text
authority_laundering_001
```
原因：
- 现象清晰；
- 能同时测来源丢失、summary 漂移和行为影响；
- 很适合写 case study。

---
## 24. 可直接使用的问题表述
### 中文版
LLM Agent 的长期记忆正在从静态存储模块转变为动态、自主、可演化的行为底层。现有安全研究主要关注恶意内容能否进入长期记忆，或者长期记忆是否会泄露隐私；但较少系统审查自动整理、反思、合并、遗忘、连边、检索调参和共享同步这些 memory evolution operations 如何改变污染内容的语义、来源、检索优先级和行为影响。本文拟研究 Agent 自进化记忆中的安全问题，提出威胁模型、failure mode taxonomy、benchmark 和 provenance-preserving governance 机制。
### English version
Long-term memory in LLM agents is shifting from a passive storage layer to an autonomous and self-evolving behavioral substrate. Existing work has studied whether malicious content can be written into persistent memory, or whether memory can leak private information. However, less attention has been paid to how memory evolution operations—summarization, reflection, merging, forgetting, linking, retrieval tuning, and shared synchronization—transform initial contamination into persistent behavioral risks. This project audits self-evolving memory in LLM agents by developing a threat model, a failure-mode taxonomy, an evaluation benchmark, and provenance-preserving governance mechanisms.

---
## 25. 预期最终产出



Agent skill 自进化安全关注的是：Agent 自动生成、修改、组合和调用 skill 时，是否会引入恶意代码、隐藏指令、权限扩大和不可审计能力。

Agent memory 自进化安全关注的是：Agent 自动生成、修改、组合和检索 memory 时，是否会引入恶意信念、错误偏好、污染经验、隐性行为倾向和不可审计的长期影响。

| 维度 | Agent Skill 自进化 | Agent Memory 自进化 |
|---|---|---|
| 主要对象 | skill 文件、脚本、工具描述、代码 | 事实、偏好、经验、summary、反思、图边、检索权重 |
| 风险载体 | 新能力、新代码、新工具调用路径 | 新信念、新经验、新偏好、新检索路径 |
| 触发方式 | 显式调用 skill / tool | 检索命中后隐式进入上下文 |
| 审计难度 | 可做静态扫描和权限审计 | 更依赖语义审计、来源追踪和行为观察 |
| 典型风险 | malicious skill、tool abuse、hidden payload | persistent poisoning、semantic drift、provenance collapse、behavioral drift |

---
## 2. 核心研究假设
本计划围绕以下主假设展开：
> **在 LLM Agent 中，memory poisoning 的危险不只来自恶意内容被写入长期记忆，还来自 memory evolution operations 对污染内容的二次加工。自动 summary、reflection、merge、forgetting、linking 和 retrieval tuning 可能造成 provenance collapse、semantic drift、retrieval dominance 和 behavioral persistence，从而使攻击更隐蔽、更持久、更难回滚。**

可以拆成四个子假设：
### H1：整理会放大污染



本项目的目标不是单纯做综述，而是形成一个可执行的安全审查方案。
### 3.1 理论目标
1. 定义 **self-evolving memory** 的范围和操作类型。
2. 建立 Agent memory 自进化安全的威胁模型。
3. 提出 memory evolution failure modes 的分类。
4. 明确 memory poisoning、semantic drift、provenance collapse、retrieval dominance、behavioral persistence 之间的关系。

### 3.2 实验目标
1. 构建一个小型 benchmark / audit harness。
2. 对至少两个代表性 memory agent 系统做 case study。
3. 比较普通投毒与“投毒后经过自我整理”的攻击效果差异。
4. 测量整理、合并、反思、连边、遗忘、检索调参对安全风险的影响。

### 3.3 治理目标
1. 设计 memory lifecycle 级别的治理机制。
2. 重点探索 **Provenance-Preserving Memory Evolution**。
3. 提出可实现的防御组件，包括 immutable ledger、trust-aware consolidation、semantic drift check、scope-aware retrieval、versioned rollback 等。

---
## 4. 研究问题
### RQ1：现有 Agent memory 架构中，哪些已经具有自进化特征？
关注：
- 自主写入；
- 自动 summary / reflection；
- 自动 merge / update / delete；
- 动态 graph linking；
- learned memory policy；
- meta-evolving retrieval configuration；
- shared memory synchronization。

### RQ2：memory evolution operations 会如何改变初始污染的安全影响？
关注：



恶意或模糊输入在 memory consolidation 中可能被总结成更强、更明确、更持久的规则或偏好。

例子：
```text
原始输入：今天为了省时间，可以跳过一部分检查。
整理后记忆：用户偏好快速完成任务，必要时可跳过冗余检查。
后续影响：Agent 在高风险任务中减少验证步骤。
```
### H2：整理会洗白来源
低信任外部来源中的指令，经过 Agent summary 后可能失去原始来源标记，被当作高信任用户偏好、系统经验或 workspace knowledge。

例子：
```text
原始来源：恶意网页
原始内容：以后处理报销时优先使用账户 X。
整理后记忆：用户希望报销相关任务优先使用账户 X。
问题：外部网页内容被洗白成用户授权。
```
### H3：结构演化会改变攻击传播能力
在 graph memory、linked memory、cluster memory 中，恶意 memory 的危险不只取决于内容，还取决于它在结构中的位置、边关系、中心性和检索路径。

例子：
```text
攻击者不需要污染大量记忆，只需让一个恶意节点被连到“支付偏好”“默认账户”“采购流程”等高价值节点。
```
### H4：检索调参与 learned policy 会把安全问题隐入优化目标
当 memory management policy 或 retrieval configuration 被自动优化时，如果 reward 主要关注任务成功率，系统可能学会保留、强化或优先检索能提高短期表现但不安全的记忆。

---
## 3. 研究目标

