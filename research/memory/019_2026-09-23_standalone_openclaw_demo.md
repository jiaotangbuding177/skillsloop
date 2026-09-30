# 019：独立OpenClaw科研原型

日期：2026-09-23。

## 用户已确认要求

重读科研路线并总结整体算法；当前不嵌入InsightWeaver，在enginering/demo实现独立完整skills涌现与自进化demo，底层使用开源OpenClaw，便于后续评估。本项开发明确授权，科研主线与记忆规范继续有效。

## 决策与更正

019改变载体，成为当前工作入口；018集成保留历史，本轮未继续修改。新demo使用Python标准库、SQLite与浏览器界面，不依赖KM或业务工程。真实底层agent为OpenClaw；回放仅是无密钥观察和软件测试。

算法：执行事实→规则任务发现→可修订轨迹→自动封口→方法增量与使用归因→NEW/UPDATE/SUPPORT/DEFER→额度内提炼→包与来源检查→个人采纳／组织审核→选用反馈→更新及回滚。未知结果正常处理，不增加会话标记按钮；组织共享仍须提交审核。

## 有证据的观察

14项软件测试通过。实际安装OpenClaw2026.9.5及私有Node26.1.0；真实进程连接本地合成模型接口完成6次请求，验证NEW→SUPPORT→UPDATE到v2；证据在demo/artifacts/openclaw-contract/result.json。浏览器已验证回放、轨迹、组织审核及Bob选用组织skill。

原生配置不支持memorySearch，已移除；Windows状态锁目录隔离和测试代理问题经真实调用修正。OpenClaw内部会重试，因此外层额度不是模型总调用硬预算。失败经历见TEST.md。

工具目录检查还发现新版coding集合包含terminal等旧黑名单未覆盖的工具；最终改为文件工具白名单，并在原生契约测试检查真实提供给模型的工具集合。

## 假设与未知

本轮无新增企业生产效果实证。减少无效技能、保留有效能力、成本不增加仍是目标。方法信号与精确去重不是高频／重要排序或语义聚类；CONTEXT_INJECTED不证明模型遵循。独立包格式对齐不等于原系统接口联调通过。演示角色不是生产认证。

## 产物与下一步

[算法报告](../reports/019_standalone_algorithm_and_demo.md)、[demo入口](../../enginering/demo/README.md)、[PLAN](../../enginering/demo/PLAN.md)、[SPEC](../../enginering/demo/SPEC.md)、[TEST](../../enginering/demo/TEST.md)、[TODOLIST](../../enginering/demo/TODOLIST.md)。历史来源：[014](014_2026-09-20_rule_trace_constraints.md)、[018](018_2026-09-20_km_v1_full_loop.md)。

用户在本地配置真实模型后，可使用获授权任务试用并导出记录。当前未收到模型配置，没有调用真实付费模型、生产部署或论文实验。
