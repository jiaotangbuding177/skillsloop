# 真实模型与技能消费

024功能更新：已初始化 OpenClaw 自带 skill-creator，自动提炼/更新必须读取它；候选通过官方验证和 `.skill` 封装后再入库。页面提供技能包和任务产物下载。对话可输入 `/skill-creator` 加具体需求，直接封装交付；共享仍走原审核流程。Windows 兼容修复见 [兼容说明](OPENCLAW_COMPATIBILITY.md)。下方021运行故障和020工具限制是历史状态。

本轮补齐真实模型配置文件、技能文件读取证据、产物清单和独立通路验证。沿用OpenClaw2026.9.5，不用固定回答冒充真实模型。

## 启动

```powershell
cd D:\skillsgen-industry_track\enginering\demo
Copy-Item .env.example .env
# 编辑.env，在本机填写真实模型ID、兼容API地址和密钥。
python demo.py doctor
python demo.py live-check
python demo.py serve --mode openclaw --port 8766
```

若已有.env，不要重新覆盖，直接编辑。默认读取demo/.env，可用`--env-file`指定其他文件；进程环境优先。配置文件只读取DEMO_*键，不执行脚本，不打印密钥。OpenAI-compatible Chat Completions为默认协议；其他API类型需模型提供方明确支持后再设置DEMO_MODEL_API。

021历史记录（运行阻塞已由024修复）：已配置用户提供的阿里云Anthropic兼容端点，暂选qwen3.7-plus。真实模型已读取控制技能并输出文件内随机校验码，2条模型响应、报告总tokens10724（含缓存口径）。但CLI在模型完成后收尾超时，外层仍报UNKNOWN；完整页面返回链路尚未稳定，先处理该问题再批量运行。真实证据在`artifacts/live/live-7294d214f89f-recovered-evidence.json`，失败记录同时保留；它不代表企业任务效果。此配置为Coding Plan，正式批量/多人研究须按服务范围另定模型资源，见021执行计划。

## 如何真实使用技能

1. 在真实模式产生任务会话，等后台提炼候选；查看并采纳个人技能，或提审后进入组织库。
2. 在技能库点击“选用并开始任务”，提出一个独立的新任务。
3. 后端将选定版本完整文件包复制到该次OpenClaw工作区。给模型的是ID、版本、哈希和文件路径清单，**不再同时在提示中重复注入全部正文**。
4. OpenClaw通过实际read工具读取SKILL.md及所需资源，用真实模型执行；可把交付文件写到outputs目录。
5. 运行记录中`skillEvidence`从该次OpenClaw本地transcript_events读取调用与工具结果，`FILE_READ`表示观察到成功读取精确入口路径。`artifacts`记录outputs文件相对路径、大小和SHA256。
6. 使用后在正常对话纠错；轨迹保留使用版本，形成UPDATE候选，采纳后下一次使用新版本。组织更新仍须审核。

没有read回执显示READ_NOT_OBSERVED；读不到原生事件表显示UNKNOWN。二者不能改写成“已使用”。当前证据分层为：SELECTED / CONTEXT_INJECTED（版本已传给运行器）→FILE_READ（文件读取）→行为遵循（需独立验收）→业务成功（需任务验收）。读取不等于遵循，更不等于收益。

## live-check测什么

该命令只做一次真实agent派发。随机控制字符串只存在于技能文件中，任务提示不携带它。成功要求：原生read回执存在，最终回答包含文件规定的字符串。输出证据保存到`artifacts/live`的独立运行文件。

它证明模型获得并使用了控制技能中的信息，不是企业任务benchmark，不证明复杂技能泛化。此控制skill人工构造，不能算自动涌现结果。学习与演化质量仍须使用论文协议中的独立任务测试。

024工具配置开放工作区文件读写、exec/process、browser、web_fetch/web_search、skill_workshop。已为本地脚本任务配置 Python 与 PowerShell 规则。exec 在本机执行，工作区规则不等于操作系统沙箱。浏览器、搜索仍取决于浏览器或搜索服务配置；企业 API 和登录尚未接入。消息发送、定时任务、其他设备和多agent派发不属于当前 skills 闭环，不启用。

完整真实案例命令：`python scripts/accept_live.py --data artifacts/新目录`。它调用真实模型、消耗模型资源；相同目录成功步骤可续接，失败不会自动重复。构造销售数据只验证功能与数值验收，不是企业效果实验。

## 可复核验证

- 19项本地测试通过，包含配置、清单不泄露正文、按会话/路径匹配读取、缺失证据保持UNKNOWN，以及未读取技能不能归因为UPDATE。
- 真实OpenClaw+本地合成服务测试通过：7次HTTP请求，新增一次真实read工具调用，完整NEW→SUPPORT→UPDATE链路通过。
- 最终复核证据：`artifacts/openclaw-contract/run-c5e63db01d/result.json`；前次通过记录为`run-345aac2b69/result.json`。输出与usage是夹具生成，不是实际LLM计费。
- OpenClaw事件表解析针对固定版本；升级时必须重跑契约验证。先前一次复用测试目录运行超时、没有触达测试服务；改用独立运行目录后通过，尚未证明该次超时的唯一原因，不删除这条失败记录。
