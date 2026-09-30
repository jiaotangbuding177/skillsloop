# 行为规格

024当前补充：每次运行初始化 OpenClaw 官方 skill-creator 文档、验证器、打包器及工作区规则。提炼/更新先读 creator，在 draft 写完整候选，官方验证打包通过后才能 READY。支持对话显式 `/skill-creator` 封装交付；不会绕过个人采纳和组织审核。开放本地脚本执行，交付物及技能包可下载；exec 是主机执行，不是 OS 沙箱。Windows 适配及检查见 OPENCLAW_COMPATIBILITY.md。

020补充：真实消费只传技能版本和文件清单，由agent实际read；按当前session及精确入口路径的成功工具回执产生FILE_READ。缺失回执保持UNKNOWN／READ_NOT_OBSERVED，不得仅凭选中产生UPDATE归因。FILE_READ不表示行为遵循或业务成功。读取解析绑定OpenClaw2026.9.5事件表，升级需契约验证。交付物只登记outputs内普通文件的路径、大小和hash。


- 本地研究demo，身份由服务端固定demo成员表产生。浏览器可切换研究角色，非生产登录系统；只监听127.0.0.1。
- scope=(org,user)。原始会话和任务不跨成员共享；审核通过的技能包可共享。同一session属于唯一scope。
- 技术完成不等于业务成功。无用户验收也可封口学习；规则无法判断时保留pending／defer。无新增方法的skill使用为SUPPORT。
- 选择技能时绑定已发布版本和完整包hash；修改原任务无需再选skill即可保留归因。独立目标重新路由；多skill归因不明不广播UPDATE。
- SQLite事务内幂等收录、输入冻结、版本CAS、预算预留；模型调用不占数据库事务。未知执行不自动重发。重启时标记未完成运行，保留预算记录。
- NEW／UPDATE共享每人每天学习派发限额，离线与真实运行分开统计；使用调用另记。缺失tokens／cost为null，不填0。
- skill包保持SKILL.md+可选scripts/references/assets；路径必须相对安全，禁止symlink、绝对路径、重复路径。市场五项沿用前版。候选发布只接受校验后的文本文件包；agent可在获准本地工作任务中运行辅助脚本。Python缓存不打入技能包。
- 个人UPDATE需原目标版本不变且输入未过期。组织UPDATE进入审核，审核时CAS，普通成员不能直接发布组织版本。回滚也是新版本，不销毁历史。
- 超大输入明确拒绝／延期，不静默截断。学习决策可被模型返回DEFER／SUPPORT，不为凑数量强制生成。
- OpenClaw运行目录只装入本次获准skill，记录CONTEXT_INJECTED，不称之为已证明执行或业务成功。工具摘要与原运行JSON分开保存。
- replay是合成夹具模式，openclaw是真实执行模式；无OpenClaw／无模型配置时报错，不自动切换replay。
