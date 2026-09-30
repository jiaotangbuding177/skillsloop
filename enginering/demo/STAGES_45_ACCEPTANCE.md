# 阶段4/5与个人工作台验收

日期：2026-09-26。当前实现说明以[049研究报告](../../research/reports/049_stage45_implementation_and_harness_acceptance.md)为准；[048实施计划](STAGES_45_PLAN.md)保留实施前设计状态。

050后续审查已确认：下列属于分阶段开发验收，当前仍有妨碍冻结新实验的运行/恢复断点。进行新一轮原始会话→skill实验前，先读[050审查与开跑标准](../../research/reports/050_first5_preflight_review.md)，不能直接串联两个旧验收脚本视作完整新跑。

## 已运行

1. 使用047隔离数据库快照，`scripts/check_038_stages45.py`读取A/B生成轨迹并检查C等留出用途不进入阶段4/5；阶段4产生方法台账、一个初始聚类和两个NEW workflow。
2. `workflow_creator`首次超时后保留FAILED；一次显式重试实际读取官方creator并写出草稿。宿主修正Windows字节写入后对已完成草稿重验，官方打包、解包hash均通过。一个候选成为READY。
3. 测试人员明确调用个人采纳；`scripts/check_049_skill_consumption.py`在构造新任务中选用该skill v1，实际读取回执为 `FILE_READ`，补充立场后得到回答和Markdown产物。
4. 59项单元测试通过；HTTP和浏览器检查个人库、对话选择器及下载通路。

受控证据在 `research/cases/038_contract_multi_review/private/049-stages45-acceptance/`；[无正文摘要](../../research/cases/038_contract_multi_review/private/049-stages45-acceptance/acceptance-summary.json)、[消费摘要](../../research/cases/038_contract_multi_review/private/049-stages45-acceptance/consumption-followup-summary.json)。原始对话、候选私有侧记和模型输出仅留在受控目录。

## 使用

当前进程：[个人技能库](http://127.0.0.1:8769/skills)、[对话](http://127.0.0.1:8769/chat)、[研究后台](http://127.0.0.1:8769/)。演示成员选Alice，个人库有“合同整体风险审阅与批注生成”v1；对话选中它并发送新任务。使用后在回复下查看真实读取回执和产物。技能下载由服务按成员权限提供。[本次技能包](http://127.0.0.1:8769/api/skill-package?actor=alice&id=skill-079da6a6da354645)。

如需自行启动相同隔离目录，在 `enginering/demo` 下先加载本地模型配置，再运行：

```powershell
python demo.py serve --mode openclaw --data D:\skillsgen-industry_track\research\cases\038_contract_multi_review\private\049-stages45-acceptance --port 8769 --no-auto-learn --daily-limit 30
```

`--no-auto-learn`保留手动受控调用；新对话仍会真实消耗模型。运行示例脚本会再次调用模型，勿把脚本重跑当零成本验证。角色选择不是生产认证。

## 尚未通过的研究主张

当前只验证阶段4/5工程链路及个人选版消费。没有独立专业质量判定、客观任务成功率、企业真实采纳、无效技能比例对照、长期成本对照、使用后UPDATE或跨成员组织复用实证。creator超时run用量缺失；这不能记为零。阶段4/5两次结构化请求和creator内部循环的已报告用量见049报告。
