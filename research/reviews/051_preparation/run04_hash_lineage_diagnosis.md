# Run 04 来源指纹变化诊断

日期：2026-09-26。Run 04 保持 FAILED，新增真实模型派发为 0；诊断没有修改响应或来源 hash。

独立比对显示，首个 session 的原、新四条阶段 2 标注仅 `runId` 不同；其引用、片段、意图和任务候选内容均相同。两份阶段 3 请求逐字段比较时，**仅顶层 `sourceHash` 不同，其余全部语义输入相同**。

因果链如下：

1. `request_cache.configuration` 把整个 `runtime.py` 的 SHA256 放入请求缓存配置。
2. 在 `runtime.py` 中修正 creator JSON 解析器，会改变阶段 2 的请求／运行 ID，即使该阶段提示、模型、输入和输出均不变。
3. 阶段 2 在 annotation 中保存新的 `runId`。
4. `recovery.prepare` 把完整 annotations 放入阶段 3 的 `sourceHash`，因此执行血缘 ID 变化传导为新的来源指纹。
5. 保存响应驱动器严格匹配请求 digest，正确拒绝把旧恢复响应配给不同来源 hash；它没有改写响应绕过校验。

这次失败来自解析器修正的影响范围和缓存／血缘指纹耦合，并非实际会话语义改变、引用丢失或新增模型输出。免费合成控制没有覆盖“全局 runtime 源码改变后，上游 annotation.runId 进入下游来源指纹”的情况，不能用那项控制替代真实保存响应重放。

后续应将 creator 回复兼容解析放在阶段 5 专用模块，恢复抽取链使用的 `runtime.py` 原字节。新运行必须重新冻结代码；在允许阶段 5 `creator.py`／`workflow_bridge.py` 变化的条件下，先用真实八条保存响应免费运行到唯一新 creator 调用之前，验证各阶段请求 digest 仍精确匹配。**不重写任何旧 sourceHash，不修改原 Run 04，也不把其结果改成通过。**

- 原运行：[Run 03 模型记录](../../cases/038_contract_multi_review/private/051-first5-run03/model-runs.json)。
- 拒绝运行：[Run 04 模型记录](../../cases/038_contract_multi_review/private/051-first5-run04/model-runs.json)。
- 实现依据：[request_cache.py](../../../enginering/demo/skilldemo/request_cache.py)、[recovery.py](../../../enginering/demo/skilldemo/recovery.py)。

本诊断为只读结构比较；企业正文未复制到此报告。
