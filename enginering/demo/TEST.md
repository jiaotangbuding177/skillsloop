# 软件验证记录

## 041任务识别修正与038真实案例（2026-09-26）

- 真实模式新增按成员/会话分窗口的LLM任务种子与逐消息处置；宿主校验来源hash、原文引文、ID、覆盖和任务引用，再拼接trace。无效输出不回退词法任务判定。回放模式维持既有规则基线。
- `python -m unittest discover -s tests -q`：39/39通过，包含任务识别验证、无人工replyTo拼接、无效输出拒绝和在线尾窗复用。
- 038受控真实数据：70条原始消息恢复14个用户回合，未人工注入replyTo。最终成功运行见[验收JSON](artifacts/038-detection-1790411117/038-task-detection-result.json)：3个会话得到4个任务实例，三条合同审查分别覆盖4/4/5回合，末轮市价查询单独成任务；14/14有任务归属，结果均保持UNKNOWN。缓存复验核对原始消息ID分组与人工案例标注完全一致，模型请求仍为3次。
- 最终运行3次直连结构化模型请求，报告8626 tokens，现金成本未知；识别阶段没有调用OpenClaw agent循环，也没有技能生成/学习派发。初版OpenClaw识别产生超时与内部重试，v1/v2直连虽覆盖全部消息但误拆T3，保留在[科研报告](../../research/reports/041_task_detection_implementation_and_038_validation.md)；不能据最终一次成功断言通用精度或成本不增。
- 原合同附件和历史交付文件仍缺，不能验收法律审查质量、业务成功、技能生成或跨用户收益。第3阶段精细轨迹恢复、第4阶段workflow聚合仍待单独验证。

## 031多轨迹聚类与Patch归纳（2026-09-24）

- 35项软件测试与前端JS语法检查通过；新增NEW聚类、UPDATE版本池、多来源失效、引用/覆盖/锚点校验、延期和等待测试。
- 真实OpenClaw/qwen3.7-plus：3轨迹→1个NEW、2条实际使用反馈→1个UPDATE，官方封装、个人采纳、组织审核及Bob消费通过；JSON数值170/325及新增字段验证通过。
- 5次成功外层派发、24次内部请求发起、306,250报告tokens；另保留网络拒绝失败1次派发/8次请求尝试，usage未知。不是成本下降对照。
- [当前完整验收](MULTITRACE_ACCEPTANCE.md)；024等以下为历史证据。8767服务已原数据重启，API新字段存在、原技能保留。

## 024真实模型验收（2026-09-24）

- 23/23软件测试通过，含官方封装、下载权限、Python缓存排除、creator维护任务不递归学习；浏览器JS语法通过。
- 7个原生Windows进程/监督器检查通过：参数保真、正常/失败退出、嵌套进程、PowerShell正常/失败和清理竞争。
- 真实OpenClaw/qwen3.7-plus 6次派发完成NEW、v1复用、SUPPORT、纠错UPDATE、v2采纳、组织审核和Bob消费；独立数值90/210/180/275通过。2次学习实际读creator且官方封装成功，全部运行有exec回执。
- HTTP下载与SHA256吻合、权限拒绝、所选技能源码保持不变；UI历史会话/选择/产物链接/NO_REPLY提示实看通过。
- [完整验收报告](ACCEPTANCE.md)及`artifacts/a024c/postcheck.json`为最新证据。构造数据，不是企业效果实验。下方020和019保留历史，未配置模型及只允许文件工具的旧描述不再代表当前版本。

## 020增量复核（2026-09-24）

- 19/19单元测试通过；新增真实配置加载、只传文件清单、原生读取回执、缺失证据和未读技能禁止UPDATE归因验证。
- `node --check web/app.js`通过。
- 原生OpenClaw契约测试通过，7次本地合成模型HTTP请求，包含实际read工具调用，NEW→SUPPORT→UPDATE通过。最终证据：`artifacts/openclaw-contract/run-c5e63db01d/result.json`。
- Windows测试数据库连接清理问题已修正并回归通过。另有一次原生联调在触达合成服务前超时；独立运行目录后两次通过，不能据此声称已查明该超时唯一根因。
- 未配置真实模型，未运行真实LLM或企业收益实验。合成usage不能作为真实成本。下方14项及6请求为019历史结果。


2026-09-23；Windows / Python3.14.3 / 私有Node26.1.0 / OpenClaw2026.9.5。

| 检查 | 结果 | 证明范围 |
| --- | --- | --- |
| `python -m unittest discover -s tests -v` | 14/14通过 | 生命周期、权限、来源与版本冲突、幂等、并发、失败、预算、模式隔离 |
| `node --check web/app.js` | 退出0 | 浏览器脚本语法 |
| `python demo.py replay --data artifacts/initial-replay` | 完整流程通过 | 合成NEW→SUPPORT→UPDATE→组织审核→Bob复用 |
| `python scripts/check_openclaw.py` | 真实OpenClaw发出6次本地模型请求，通过 | CLI/config/返回格式、真实运行器下NEW与UPDATE产出v2 |
| 浏览器验证 | 通过 | 回放、任务轨迹、组织审核、Bob可见及选用组织skill |

原生CLI证据在 `artifacts/openclaw-contract/result.json`。模型输出与usage来自本地固定夹具；没有访问付费模型或企业数据，其中36 tokens等数值不能作为真实成本。选中包已提供给运行器，不证明模型遵循技能或质量提高。

联调发现：固定OpenClaw版本不接受agents.defaults.memorySearch，已移除；Windows锁目录依赖用户目录，子进程使用独立USERPROFILE、OPENCLAW_HOME及STATE目录；本机代理导致localhost连接失败，测试设置NO_PROXY后通过。OpenClaw内部会重试，外层额度不能作为LLM总请求硬上限。

未验证：真实模型与企业工具、无效skills下降、有效能力保留、tokens/成本不增加、通用任务关联精度、真实用户体验和生产认证。本轮未开展论文实验。

工具边界补充：固定版本的coding工具集包含terminal等新工具，旧工具名黑名单不足。适配改用read/write/edit白名单；契约测试检查最终工具列表只含read、write、edit及其派生apply_patch，防止意外开放终端或会话派发。
