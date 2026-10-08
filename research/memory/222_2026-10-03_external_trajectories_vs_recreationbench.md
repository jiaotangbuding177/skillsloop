# 第222轮：公开GUI轨迹与RecreationBench没有直接对应关系

## 用户问题与约束

用户追问AgentNet/ProCUA公开轨迹与RecreationWorld250题是否相关。本轮澄清数据来源、任务分布和实验含义，不据此改动或取消218独立canary/208学习。

## 证据支持的观察

依据[AgentNet官方卡片](https://huggingface.co/datasets/xlangai/AgentNet)、[ProCUA-SFT官方卡片](https://huggingface.co/datasets/nvidia/ProCUA-SFT)、[RecreationWorld官方仓库](https://github.com/QwenLM/RecreationWorld)与[220报告](../reports/220_recreationworld_pipeline_and_open_trajectories.md)：前两者是独立来源的现有应用GUI操作示范/agent执行轨迹，不是这250题的配套轨迹。RecreationBench评估根据参考应用观察重建应用的混合GUI/编码能力，学习动作/工具类别虽有交集，任务目标与分布不同。

220首条GIMP滤镜示范与corravale Web应用复刻没有直接任务对应，已作为功能验收输入，不能当匹配的主训练数据或证明250题skills适用性。公开下载入口不等于可直接代替本benchmark训练池；未全面逐条核查潜在应用交集，不能额外断言所有实体完全不重叠。RW论文自身训练轨迹是否公开可下载仍未确认。

## 建议与未知

主实验建议在RecreationWorld原生环境采集预先划分学习应用集的真实GLM执行轨迹，官方AutoSkill学习，再对应用/项目家族隔离的评测集做无/有技能配对；不把学习应用自身的重跑分数当泛化收益，私有评分/gold不得输入学习。AgentNet/ProCUA适合单列外部迁移对照，增益未知。不在本轮擅自定义分集、启动批量采集或宣称本建议已执行。

本轮无新增实验实证发现；修正220最终回复可能将公开可用性与任务匹配度混读的表达。原实验失败/0候选/未完成项保留。
