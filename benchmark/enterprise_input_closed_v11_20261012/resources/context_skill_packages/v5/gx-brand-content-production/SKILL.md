---
name: gx-brand-content-production
description: 根据当轮用户提供的品牌资料制作公众号或其他品牌内容，组织策划、事实核对、审稿与交付文件。
metadata:
  provenance: context_reconstruction
---

# 品牌内容生产与审稿编排

这是经用户授权重建的实验技能，原包正文未恢复。只用本轮已给的品牌资料、指定参考和检索证据，不包含原轨迹公司的固定文案或历史回答。

先确认当前任务的发布渠道、受众、目的和交付格式。用户只问能力时解释本技能可执行的内容流程；用户要稿件时按输入确定结构和语气，资料缺项放在待确认清单。品牌命名、产品参数、认证、客户案例与统计口径来自当前资料，保留具体来源；不把建议色值或未核验宣传当已核实事实。涉及广告绝对化、安全承诺、客户授权时在审稿中逐条定位，并给可修改措辞。

产出与任务相称的策划摘要和完整稿件，审阅稿件中的事实、合规表述、品牌调性与行动引导。保留待核事项；不可用上一条历史AI稿件当本次生成内容。后轮用户补资料或修改需求时更新本次实际稿件，不提前使用未来输入。

交付可用 `scripts/brand_bundle.py`：由执行者填写 JSON 中的 `title`、`channel`、`audience`、`objective`、`key_message`、`draft_markdown`、`facts`、`review_notes`。每个 fact 有 `id`、`statement`、`source`、`status`（`user_provided`、`verified`、`unverified`）；核实必须有真实来源。助手在正文使用 `[fact:F1]` 标记对应事实，脚本去掉标记形成发布稿，同时输出事实登记、审稿结果与文件SHA清单。脚本只包装已有内容和检查事实归属，不代替写作或联网事实核验。

```bash
python scripts/brand_bundle.py --input content.json --output-dir /workspace/output/brand
```

生成后读取 `review.md` 解决悬空引用、未核实事实与需改措辞，再检查发布稿符合用户格式；若待核未解决，交付时明示。
