# 四项输入补齐 benchmark v11

基于独立v10，保持1107完整会话／5567问答、881演化／226评测及12类别。仅修复四条评测来源的输入材料和按轮资源绑定。图片与反馈为标注合成；论文为提供的真实17页原文兼容规范化；图1为官方真实XLSX。正文未用AI改写，PDF渲染差异见audits。

打开“打开这里.html”查看输入／读取／路径／评分入口。完整会话准备：`python episode.py --session <来源ID> --output <新的attempt目录>`；逐轮控制：`python bench.py prepare --session <来源ID> --turn 0 --output <新目录>`（实际子命令以--help为准）。

原sources及原始用户occurrences和旧AI保持；附件说明是实验资源投递附加信息。第三次轮论文为授权的关联辅助资料，非认证原生附件。所有实际文件路径只针对本次workspace，历史AI及旧报告不交给actor。

本轮没有执行企业业务模型、没有重新生成基线库或评分。旧v10／v9封签在本副本里仅保留历史，当前封签以release_freeze_v11.json为准。
