# EvoMind主题学习材料池

1,224条会话素材（716保留+508暂存），719条已有局部学习片段；242条排除材料不进入本版。完整轨迹尚未认证。

[检索入口](private/index.html) · [完整报告](../../../reports/2026-10-06_evomind_task_topic_release.md) · [统计CSV](topic_statistics.csv)

带标注正文在 `private/conversations.jsonl`；无研究答案模型输入在 `private/model_inputs.jsonl`；片段正文在 `private/learning_candidates.jsonl`；按会话主主题和片段具体任务分别分区到 `private/topics/`。分类不是完整任务聚类或独立金标准。任务、方法和来源摘录全量复查，7条会话扩展读全部用户正文；4条会话主主题和129条片段主题修订，记录修改前后标签。原归档不变。

复现：项目根运行 `python -X utf8 research/datasets/evomind/task_topics_20261006/prepare_topic_review.py`，然后运行 `build_release.py`、`write_documentation.py`。分类修订是脚本中的显式人工式语义审阅决定，不是关键词匹配算法。
