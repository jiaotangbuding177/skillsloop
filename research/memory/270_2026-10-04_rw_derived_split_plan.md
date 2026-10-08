# 第270轮：RecreationBench派生分集可行性与候选名单

## 用户要求与约束

用户问已有示例后能否基于当前全部任务／数据量划分演化和测试。按“目前的RecreationBench”理解“默契的bench”。只调研和准备方案，不把问可行性当恢复267；立即停止和同题最多三轮持续生效。

## 证据支持的观察

已先读README/CHARTER/STATE及224/229/234/235相关记录，重开官方GitHub/HF/论文。官方250应用任务、五平台50，HF公开test；35,000为论文独立训练轨迹包，尚未取得，不是benchmark题数。本地5个固定tasks jsonl只读聚合各50，总250；Web排corravale后49（easy15 medium17 hard17），同ID跨平台2组mifi-lossless-cut、sqlitebrowser-sqlitebrowser（macOS/Ubuntu）。只排相同ID不证明完整来源去重。93,739公开文件名未全下载；多轮corravale仍单题，Web单题链路已验收，不代表250平台就绪。

论文§4.1明确Web可以查看served HTML/styles/scripts/assets，保护GT/tests且交付运行不得加载参考；先前更严观察门禁是变体，后续协议应统一冻结并披露，不热改旧run。源码/真实负分保持。

## 研究建议（不是效果实证或执行授权）

保持250登记，corravale仅开发排除正式演化／测试/技能，249候选；首期建议Web49两折24/25、互补两库，每题使用另一折轨迹学出的库。49无技能采集如事前相同协议，可兼baseline；冻结两库后49有技能，共98正式执行，judge/学习另计。全249同法498执行包含Web98，平台设施尚需验收；目标近半不能绕过来源分组。失败不挑分，无逐题人工提示，主指标首有效配对总/功能/视觉分，最多三轮纠正另单列。

已保存[完整方案](../protocols/270_rw_derived_evolution_evaluation_plan.md)与[可复现候选Web名单](../protocols/270_rw_web49_split_draft.json)：固定SHA顺序按难度分层A24（8/8/8）、B25（7/9/9），明确draft_not_frozen、来源组审计pending、无执行。不能称官方train/test、250完整held-out或技能提升已证。

独立只读分集审计复核数据范围与方案：两折98执行覆盖49配对，同库相关需分折披露；省成本的单向30演化／19测试为68执行、一个冻结库但测试量较小。建议作为可选方案保留，不自动替换草案或启动执行。

## 下一步与未知

用户确认范围并明确恢复后才做新独立协议／逐题来源与设施验收。本轮无新增实验效果证据，未调用模型／judge、未停止其他聊天。RW STOP保持；旧全部分数/轨迹/失败与三轮限制保留。
