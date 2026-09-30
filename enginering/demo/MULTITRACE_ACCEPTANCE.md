# 多轨迹技能归纳验收

2026-09-24。范围：构造销售任务、真实OpenClaw/qwen3.7-plus、官方skill-creator。本记录不是企业效果或基线优越性实验。

## 结果

- 3个独立任务经过词法聚类形成1个NEW池：成功、失败和UNKNOWN各一条。成功/失败标签来自显式提供的构造评估，标为IMPORTED_EVALUATION。
- 模型输出逐轨迹提议及合并组，宿主检查引用与覆盖，应用patch并用官方creator封装。候选READY后纳入个人库。
- 在新的输入上实际读取v1，输出`net=170`、`cross_period_refund=30`，原生FILE_READ与JSON产物检查均通过。
- 2次真实使用的反馈组成同基准UPDATE池，分别提出gross/current_refund和currency要求；合并为1个更新候选，宿主应用后采纳为v2。
- 原组织提审/审核后，Bob实际读取组织版本，JSON输出gross=350、current_refund=25、net=325、cross_period_refund=15、currency=CNY，独立数值及字段检查通过。
- 35项软件测试通过，包括原闭环、聚类隔离、多个来源失效、UPDATE聚池、冲突锚点、假引用、失败假设、提议遗漏及预算等待。前端JS语法检查通过；8767新API包含pools/patchsets、120秒等待，原2个可用技能保留，无运行中任务。

## 资源和失败记录

成功验收批次有5次Agent派发：2次学习、3次消费；本地传输日志共24次模型请求发起，报告306,250 tokens（含供应商缓存口径，非账单），现金成本未知。

此前沙箱网络拒绝产生1次失败学习派发、8次内部请求发起，未返回usage，不能记成零token或零费用。重跑在独立目录保留成功证据，不删除旧失败。另一次验收脚本因Windows路径分隔符比较失败中止：实际JSON已经生成且数值正确；修正路径标准化后复用原请求回执继续，没有重新付费生成该技能或重复消费该任务。

这些数值不能与024的498,204 tokens直接计算节省比例：任务、输入量、交付内容和验证负载不同。此次没有旧算法/强批量摘要对照，不宣称无效比例下降、有效方法保留率提高或成本不增已被证明。

## 证据

- [验收汇总](artifacts/031-multitrace-live-network/acceptance.json)
- [完整资源审计](artifacts/031-multitrace-live-network/resource-audit.json)
- [NEW候选及patch](artifacts/031-multitrace-live-network/01-new.json)
- [UPDATE候选及patch](artifacts/031-multitrace-live-network/04-update.json)
- [组织消费回执](artifacts/031-multitrace-live-network/05-shared.json)
- [可重现验收脚本](scripts/check_multitrace_live.py)，需要真实模型配置；不要以不同数据目录反复执行来美化结果。

## 算法边界

此实现是Trace2Skill启发的预算适配：单次Agent派发内分角色分析、单层小池归纳，不是独立并行分析器和层次merge的严格复现。UNKNOWN保留，未验证失败原因延期；引用有效不等于因果证明。词法聚类、整候选失效、内部tokens软约束和缺少通用业务oracle均为当前局限。
