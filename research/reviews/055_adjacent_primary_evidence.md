# 055 邻近工业论文的一手实验依据

日期：2026-09-28。范围：补充 KDD ADS 工业 agent / workflow 论文；供主报告合并，不修改研究现状。不运行实验、不修改系统代码。本轮无新增本项目实证发现。

## 来源与身份核验

- 两篇均列入 [KDD 2025 官方 ADS 录用目录](https://kdd.org/kdd2025/applied-data-science-ads-track-papers-2/)，不是仅凭 arXiv 标签判定工业轨道。
- **FlowXpert: Expertizing Troubleshooting Workflow Orchestration with Knowledge Base and Multi-Agent Coevolution**：DOI [10.1145/3711896.3737221](https://doi.org/10.1145/3711896.3737221)。细节依据[作者团队公开全文](https://nkcs.iops.ai/wp-content/uploads/2025/05/KDD25-FlowXpert.pdf)，页眉标注 KDD ’25；该文件带行号，不能保证与 ACM 排版终版逐字一致。
- **DiMA: An LLM-Powered Ride-Hailing Assistant at DiDi**：DOI [10.1145/3711896.3737208](https://doi.org/10.1145/3711896.3737208)。先读 v3，再核对 [2025-06-06 作者 v2 全文](https://arxiv.org/html/2503.04768v2)，v2 已有 KDD 2025 正式引用与上述 DOI。以下表号、数字用 v2；不把会后 v3 当唯一出版依据。
- ACM DOI 页面本次返回 403，因此身份依官方目录、实验依作者全文，未声称读取 ACM 终版。

## FlowXpert：核验札记

Evidence source: [author manuscript](https://nkcs.iops.ai/wp-content/uploads/2025/05/KDD25-FlowXpert.pdf), §§5–6, Appendix A/C.

| Item | Verified evidence |
| --- | --- |
| Data | OpsFlowBench: 252 query/workflow pairs, 56 incident types, four scenarios; train/test 148/104 (Table 3). One iteration synthesizes 1,332 preference pairs. |
| Overall comparison | Table 1: zero-shot, VectorRAG, GraphRAG, CoT, SFT, GPT-4o-feedback RL; Qwen2.5-7B, Llama3.1-8B, InternLM2.5-7B. STEPScore precision/recall/F1 matches embedded steps; **not execution success**. |
| Mechanism | Table 2: remove knowledge/graph/vector bases, PPO, or DPO. Table 1/Figure 9: coevolution iterations. Qwen F1 70.4→71.8→71.9; Llama 70.0→69.3→67.3. |
| Production | Figure 5, §6.1: 2024-10-21–12-29, 34,488 tickets, 189 common types; approximately 80% acceptance, defined through OCE assessment and ≥75% core-step recall. Production STEPScore P/R/F1: 63.2/78.4/69.6. |
| Resources | Eight V100-32GB; knowledge construction 2.2h, coevolution 15.1h; workflow generation 22.1s average. Historical manual preparation: seven engineers, seven hours; verification time not quantified equivalently. |
| Execution | Figure 6 and Table 5: human-verified/refined workflows feed Pangu-7B Executor; five incident categories, human/Executor average handling times, e.g. 166.4/111.5s. Category sample counts unspecified. |
| Limits | No randomized production comparison described; acceptance ≠ resolution. Manual physical operations constrain executability; synthetic-data quality affects evolution; no general monotonic-improvement claim supported. |

## DiMA：核验札记

Evidence source: [author v2](https://arxiv.org/html/2503.04768v2), §§7–8, Appendix A.

| Item | Verified evidence |
| --- | --- |
| Five RQs | Online performance; offline baselines; ablations; continual fine-tuning; cost-effectiveness (§8). Cross-city transfer is additional analysis. |
| Data | Table 1: training 2,086 queries; online 3,624 users/10,153 queries; simulated Beijing 272/1,139, Shanghai 168/687. Train May 6–24; online test May 25–July 25, 2024. |
| Metrics | ROA/RRA: correct order/response per round; SOA/SRA: every round correct per session. GPT-4o evaluates all; 25% randomly sampled for human assessment, seven trained annotators plus quality inspection. |
| Production | Table 2: human ROA/RRA/SOA/SRA 93.83/92.17/87.11/85.02%; GPT 86.94/94.66/70.32/86.68%. Deployed since May 2024; not randomized A/B. |
| Baselines | Table 3: CoT/ReAct/Reflexion with Qwen2-72B and GPT-4o, on simulated cities. |
| Mechanism | Table 4: remove time tools, conversation-goal functions, multi-repliers, cost-aware model allocation. Table 5: Beijing↔Shanghai transfer. |
| Evolution | Figure 5: every-three-day updates/evaluation, May 9–24; mixed real/synthetic data (Table 6). No frozen contemporaneous control described; evaluation period overlaps the declared training period. |
| Efficiency | Figure 6: quality versus latency across alternative backbones; DiMA 3.89s, Qwen2.5-72B 6.72s, Mistral-123B 16.21s, Llama3.1-405B 25.17s. Latency ≠ lifecycle monetary cost. |
| Limits | Simulation baseline results ≠ online superiority; human/GPT disagreements substantial; temporal improvement alone does not isolate update causality or demonstrate long-term regression safety. |

## KDD ADS 标准与 WWW 类比边界

[KDD 2025 ADS 官方 CFP](https://www.kdd.org/kdd2025/applied-data-science-ads-track-call-for-papers/) February cycle 的 Scope 明确要求量化上线后表现；一般仅真实数据离线测试、或只公开代码供使用而无充分上线表现，都不满足部署要求。特殊阻碍部署、监管/基础设施限制可有例外，需报告尝试、障碍和可推广教训。Decision 同时考虑技术、原创性、影响、执行/表达、相关工作、复现与伦理。没有指定统一实验数量。

[WWW 2026 Industry 官方 CFP](https://www2026.thewebconf.org/calls/industry.html)评审综合原创性、意义、质量、清晰度及技术、影响、复现等因素。KDD 的“无上线量化通常直接拒稿”措辞不能擅自当作 WWW 的逐字条款。两轨可类比工业证据组织方式，不能互换部署门槛、篇幅或单篇论文的样本规模。

## 对本项目的综合推论（不是论文原话或已验证结论）

1. 按**研究问题族**归类，不能按表数计数：数据统计表、超参数表、案例表并非各自一组独立实验；同一组下按模型、场景、指标拆表，也不增加独立研究问题。DiMA 的五个 RQ 是清楚实例；FlowXpert 的 RQ1 是建立评估体系，不宜当成一个与端到端实验等价的效果实验。
2. FlowXpert 最贴合“workflow 生成后被人/agent复用”，可借鉴步骤保真与真实执行分开验证；它并不研究原始企业会话任务发现，也不能替本项目证明任务聚类准确。
3. DiMA 最贴合“自然会话积累→持续更新→部署”，可借鉴轮级与完整会话级结果、真实/模拟数据隔离和质量—延迟权衡；它更新模型参数，不是个人/组织 skill 库演化。
4. 本项目若以持续演化为贡献，应比单条时间曲线更严格：相同初始库的冻结/演化对照、独立未来任务和旧任务回归，才能区分更新收益、任务变易和退化。此处是研究建议，未授权执行。
5. 两篇是定向样本，不能推出“工业论文普遍只需 N 组”或“达到该数据规模即可录用”。它们共同支持：中间产物质量、机制作用、实际业务使用和资源约束需要各自匹配的证据。

