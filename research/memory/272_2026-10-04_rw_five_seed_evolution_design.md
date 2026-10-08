# 第272轮：用户改为五题多轮演化、245题单次测试

## 用户已确认方向

用户问35,000训练轨迹是否来自重复公开题，并提出五个平台各1题多轮轨迹沉淀多个skills、其余各49题单次评测，已有示例复用。此新分集覆盖270两折建议及corravale只开发不入学习的旧建议；同题最多三轮／不达标如实保留仍生效。不把方案讨论当恢复已停止267，当前未执行新任务或AutoSkill。

## 证据支持的观察

已先读README/CHARTER/STATE/270，重开论文§3.1：训练任务另从GitHub开源GUI应用采集，与评测去重，Qwen3.8-Max采轨迹后每平台筛选7,000共35,000；不是公开250题反复跑，独立训练应用数尚未知。引用https://arxiv.org/html/2609.22000v1#S3.SS1。

264公开manifest实际638动作观察/41图、继承257模型source、追加指导、物理checkpoint未知；265完整结果0.7006/threshold_met=false，40/40视图/API40完整/build success/source102hash/产物hash通过。可复用失败素材而非成功或基线；历史17版本/18片段不能因选一份就写成三轮内所得。218原学习脚本实际官方trajectory入口success_only=False并逐题processed/API/真实ECNU及导出验收；当前Web消费为派生索引Read，不能声称原生Skill工具已开启或效果已验收。

## 已准备产物与建议

[272方案](../protocols/272_rw_five_seed_skill_evolution_plan.md)和[5演化／245测试候选JSON](../protocols/272_rw_five_seed_245_eval_draft.json)已保存：Web corravale复用264；其他四个平台固定SHA256/medium且不查分选择Ubuntu ksnip-ksnip、macOS objective-see-netiquette、Windows beryx-fxgl-sliding-puzzle、Android v1tzor-timeplanner。各剩49，合计245，无重复身份跨组；known相同ID跨平台2组不作种子。候选仍draft，完整来源/fork与平台就绪审核pending，不声称全5环境已齐备。

Web不再重跑，四题最多3轮含首次，上限12次新增演化执行。每轮完整公开轨迹含失败送官方AutoSkill候选抽取／维护／语义库；不人为凑技能数，可能合并或空候选。统一库先冻结，再245单次有技能测试，官方agent索引发现／按需读取实证必须验收；测试无更新／逐题人工提示／挑分重跑。245有技能单次无匹配baseline，只能测绝对迁移表现，不能归因提升；不擅自另跑245无技能。

## 研究假设与未知

少数长轨迹能否产生多个可迁移技能待验证，尤其每平台单应用无法代表平台全部需求；历史Web指导与四题预算不同需披露。多个skills不是程序承诺。论文SFT收益不等于AutoSkill有效。当前无新增实验效果、模型／judge调用0；267 STOP及原失败/freeze保留，其他聊天不变。
