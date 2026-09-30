# 024：真实模型全链路验收

2026-09-24。OpenClaw 2026.9.5 + qwen3.7-plus。**完整功能验收通过**；输入是构造的销售业务案例，未接入真实企业数据库，不是论文效果实验。

## 已跑通的链路

| 阶段 | 实际行为与验收结果 |
| --- | --- |
| 原任务 | Agent执行Python，100销售−10同期退款＝90；跨期退款5单列；生成JSON、CSV、Markdown |
| NEW封装 | 模型实际读取官方skill-creator，生成SKILL.md、计算脚本、脚本测试；官方验证与`.skill`打包通过 |
| 个人注册 | Alice采纳，生成个人技能v1；注册的是demo版本库，选用时安装该版本到独立OpenClaw工作区 |
| 新任务复用 | 实际读取v1，执行脚本，240−30＝210；跨期退款7单列；三个文件内容与哈希通过检查 |
| 无增量使用 | 规则判为SUPPORT，不产生新学习调用 |
| 对话纠错 | 在原会话补充“排除cancelled订单”；completed销售200−退款20＝180，取消订单50被排除 |
| UPDATE | 官方creator再次参与封装；保留旧文件与退款规则；采纳后个人技能升至v2，原v1历史仍在 |
| 组织发布 | 经demo提交和审核动作，发布与个人v2同hash的组织技能；组织库从自身v1开始编号 |
| 跨成员消费 | Bob实际读取组织技能并执行脚本；completed销售300−同期退款25＝275，取消订单40被排除，跨期退款9单列 |
| 权限和下载 | 全部交付文件下载内容符合登记SHA256；Bob可下载组织技能；个人包、跨组织包和他人任务文件越权请求返回403 |

6次agent派发全部正常退出：4次任务执行、2次学习。2次学习都有原生creator读取回执及官方封装产物，全部6次运行均有成功exec回执；所选技能源码在执行后与登记版本一致。

实际观察到35次底层模型请求发起，报告总tokens为498,204，**含缓存读取/写入口径**。它不是新增输出tokens，也不是账单；自定义provider未配置可核实费率，成本保持未知。该统计仅覆盖最终通过的案例，不包括此前诊断和失败尝试；这些失败记录另行保留。不能据此声称资源消耗已下降或“不增加”。

Bob最后一次原生响应为`NO_REPLY`，文件仍实际生成且通过数值验收。页面如实显示“未附文字说明”并提供下载，原始响应保持不变；没有用程序生成一句“模型已正确完成”替换它。此负面观察说明回答文本、CLI状态与交付物应分开核验。

## 直接查看

- [真实Demo](http://127.0.0.1:8767/)：当前展示Bob的`org-task`，可切换Alice查看`source`、`reuse`和个人v2。
- [最终周报](artifacts/a024c/workspaces/chat-cbeba010053ed66f5f1ee735/outputs/report.md)、[CSV](artifacts/a024c/workspaces/chat-cbeba010053ed66f5f1ee735/outputs/report.csv)、[JSON](artifacts/a024c/workspaces/chat-cbeba010053ed66f5f1ee735/outputs/summary.json)。
- [已审核技能包](artifacts/a024c/approved-v2.skill)。
- [完整案例记录](artifacts/a024c/acceptance.json)、[独立回执与HTTP复核](artifacts/a024c/postcheck.json)。
- [Windows阻塞原因与兼容修复](OPENCLAW_COMPATIBILITY.md)。诊断失败保留在`artifacts/diagnosis-024`、`artifacts/a024`、`artifacts/a024b`，不改成成功。

## 使用与重现

```powershell
cd D:\skillsgen-industry_track\enginering\demo
python demo.py serve --mode openclaw --data artifacts/a024c --port 8767 --daily-limit 4
```

当前服务已启动，不要重复启动占用同一目录。自动学习已启用，每成员每日最多4次学习派发；这是外层派发额度，不是内部模型请求硬上限。

新验收：`python scripts/accept_live.py --data artifacts/新的独立目录`，会消耗真实模型资源。已有结果复核：`python scripts/verify_acceptance.py --data artifacts/a024c --port 8767`，不调用模型。

已初始化官方skill-creator、Python、PowerShell工作区规则和输出目录。普通业务任务通过自动发现产生候选；显式`/skill-creator`可交付封装文件，此类技能维护对话标记MAINTENANCE，不再递归挖掘出“创建技能的技能”。入个人库和组织共享仍走采纳、提审、审核。

## 验证边界

23项软件测试通过；7个原生Windows进程/监督器检查通过；页面会话切换、版本、产物链接与HTTP下载已核对。真实案例证明这条受控功能链可以运行，不证明普遍技能质量、效果提升或论文创新。模型自写的辅助测试也不能代替独立企业任务测评。

exec在主机运行，demo身份是可切换测试角色，不是生产认证或操作系统沙箱。浏览器和Web工具已允许，但仍需要各自运行环境；企业API、真实身份、真实数据库未接入。候选资源目前沿用文本文件包契约；长期退化、重要任务排序及内部tokens硬预算仍待后续研究与实现。
