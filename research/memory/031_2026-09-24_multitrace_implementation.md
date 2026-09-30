# 031：轨迹聚类、分析器与Patch链路实现

日期：2026-09-24。

## 用户确认与授权

用户要求轨迹聚类必须实现，按Trace2Skill模式快速升级独立demo，补成功/失败处理，并直接替换论文PDF对应正文及图，不追加本轮升级章节。本项明确授权代码、测试与文档更新；不永久切换科研主线，不包含企业生产接入。

## 已实现与证据

- 独立demo此前是单轨迹候选与精确去重，没有真正进入归纳的轨迹聚类；InsightWeaver已有聚类不能混算为demo能力。
- 新增learning.py：NEW规范化目标词频/中文二元组余弦complete-link聚类（阈值0.72）；UPDATE按owner、实际skill及hash分池。最多8条，服务等待120秒吸收，单例正常处理。
- 任务证据包含工具可见结果（截断标记）、产物引用与hash、导入评估依据。生成前按权限/hash复制可用产物，不采集隐藏思维链。
- 在一次OpenClaw学习派发内按success/failure/unknown角色逐轨迹提议，再many-to-one归纳。宿主验证引用、提议归属、基准hash及唯一锚点，实际应用add/append/replace；官方creator校验封装。未验证失败原因不能应用，明确用户规则可保留但不假称因果验证。
- 复用records/events/runs，新增逻辑pool/patchset；全部来源参与过期检查，同池未变化来源在待采纳候选失效后释放；不扩大组织共享授权。管理页面/导出可观察聚类与patch。
- 35项软件测试、前端JS语法通过。真实模型构造验收：3条来源→1个NEW；2次真实使用反馈→1个UPDATE；个人v2、组织审核、Bob实际FILE_READ与JSON交付通过，净额170/325及新增字段检查通过。
- 8767按原启动数据artifacts/a024c和daily-limit 4重启；API含pools/patchsets、pool_wait_seconds=120，原2个可用技能保留，查询时无RUNNING。

## 资源、失败及边界

成功批次5次外层派发（2学习+3消费）、24次内部模型请求发起、306,250报告tokens；现金费用未知，不能与024不同任务的498,204直接算降幅。

初次沙箱网络EACCES产生1次失败外层派发、8次内部请求尝试，usage未返回，不能写零消耗。经正常工具权限流程在独立目录运行成功，原失败记录保留。验收脚本一次因Windows路径分隔符比对中止，实际产物存在；修正后复用已有幂等回执继续，没有重复执行已成功的学习和消费。

默认预算适配不是Trace2Skill独立并行子agent和多层merge的严格复现。导入SUCCESS/FAILURE来自构造检查（IMPORTED_EVALUATION），不是系统独立oracle。未自动化通用失败修复后验证；引用校验不证明语义因果。聚类可能漏合并或误合并；已发布条目局部撤销、内部tokens硬预算、企业效果与算法原创性仍未证明。

本轮新增的是软件/真实模型功能证据，没有企业效果对照实证。用户少无效、保留有效、总成本尽量不增的目标保留，不能升级为已实现效果。

## 文档与产物

- [机制契约](../../enginering/demo/MULTITRACE_SPEC.md)、[真实验收](../../enginering/demo/MULTITRACE_ACCEPTANCE.md)、[资源审计](../../enginering/demo/artifacts/031-multitrace-live-network/resource-audit.json)。
- [概念文档v3](../reports/022_论文概念文档.md)直接改写摘要、全链路、技术第8/9/11节及相关实验/大纲；第10节四篇Industry文献评估保留。没有新增“本轮升级”章节。
- [PDF](../../output/pdf/skillsloop_concept_and_technical_assessment.pdf)：25页，六张矢量图、目录、E1/E2/E3与完整大纲。v2原文单独归档；builder改为读取当前正文，避免每次从v1覆盖新方法。
- 原开发准备文档及README更新。030仍作为实施前决策历史，不静默改成已完成。

## 下一步

以企业授权样本校准聚类与方法标注；用同池强批量摘要对照patch机制；再研究独立失败验证、局部撤销和内部资源预算。当前不扩跑或接入生产。
