# EvoMind候选轨迹质量评估（2026-10-06）

对冻结的 `enriched_20261006` 做全量客观证据盘点、固定样本语义审阅和图表交付，不修改旧语料、旧标签或Demo。

- [719条逐条质量页](private/index.html)：可搜索任务、学习点、候选或会话编号，按关联准备、主题和本轮语义复核状态筛选。每条链接完整候选正文、原会话阅读页和审计页。
- [整体报告](../../../reports/2026-10-06_evomind_trajectory_quality_assessment.md)／[中文逐条CSV](private/逐条质量清单.csv)／[完整画像JSONL](private/quality_assessments.jsonl)。
- [画像口径](evidence_profile_schema.json)／[独立口径审阅](rubric_audit.md)／[样本语义审阅](semantic_audit.md)。
- `figures/`：三图各PNG／SVG／PDF；`topic_distribution.csv`与`quality_chart_data.csv`为原始数值。

## 质量解释

719份素材来自716条保留会话。每项的原文来源、双边正文、已有对应、工具／文件线索、限制均可回查。任务及学习点沿用已有AI筛选；本轮完整语义复核37个固定样本，不把未复核内容认证为正确。内容对应不是完整时序或同任务关系；工具载荷锚点不是调用归属；文件引用不是字节。0项完整轨迹／结果／收益认证表示认证尚未建立，不表示任务全部失败。

## 本地复算

在项目根目录：

```powershell
python -X utf8 research/datasets/evomind/quality_20261006/build_evidence_profiles.py
python -X utf8 research/datasets/evomind/quality_20261006/build_quality_release.py
python -X utf8 research/datasets/evomind/quality_20261006/verify_quality_release.py
```

不调用外部API或历史工具。固定的语义审阅文件为研究标注，只重读不生成新判断。若来源或评估口径改变，应另建版本。
