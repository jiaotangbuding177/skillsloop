# 第290轮：RW独立演化素材两路真实并行，miniPaint三轮封顶

## 用户已确认要求

用户在“开始生成轨迹”之后明确“太慢了，并发加速”。本项授权同一26应用pilot的题间并发与必要设施准备，不改变每canonical应用最多三轮含首次、成功停、未达就是未达的约束；不能借版本/基础设施恢复重置计数。旧corravale STOP、250题评测未授权、AutoSkill学习未自动启动、其他聊天服务保持。

## 实证观察与当前状态

工作目录 `experiments/288_rw_parallel_evolution_collection`，原285/v1及其全部失败/源码/成绩保留。本轮原生actor版本v2/v2.1/v2.2/v2.3/v2.4均分开冻结；当前Squoosh仍v2.4同一PID，后续端口隔离v2.7只是准备，未启动。并发上限2，v2.4每容器2GiB/2CPU、启动准入要求WSL可用内存4GiB；Squoosh一次真实浏览器MEMCG OOM后以独立v2.6.1外部资源修复记录将其配额升至3GiB，不能称执行资源从始至终未变。官方vendor、模型、当前输入与提示不热改。

两应用已实际运行准入2/26，其余24仍待平台/构建/验证器准入，不能称26全队列运行。独立参考都是新训练应用，不读取250题gold/test。尚无达到既定训练成功门槛的应用；真实失败轨迹不能丢弃，完整canonical公开输入与原创性最终审计仍pending。

### miniPaint：三轮均已执行，不能再跑第四轮

1. 原285首轮 `recreation_eval_1791121638371741570` 正常结束，约34.76分钟，实际nested `recreation/eval_results/scores.json` 功能3/6、SSIM0.1789、总分0.3394。外部观察器最初score路径未找到不等于无交付；原null报告保留，本轮侧证更正。完整原生session11,601,282bytes，来源/复制SHA相同，旧35freeze保持。
2. 288第二轮 `minipaint_recreation_eval_1791126784363902808` 已真实交付：158实际模型调用全部完整、API失败0，原生build/submitted成功。原1.25GiB资源下评分Python被MEMCG OOM，原评分缺失保留为基础设施失败，不填0、不重跑完整agent。完整原生session16,446,007bytes包含首轮历史，SHA/复制一致。
   - 两个此前启动失败是HOME内只读检查点chown、检查点路径分隔符错误，均0模型/0session，失败及旧freeze保留，修复后不是另加能力纠错轮。
   - 对相同固定候选做**仅评分恢复**：首adapter挂载在`/candidate`导致官方向上扫描到`/`，大量设施文件触发路径泄露规则；原低分adapter结果保留。
   - 第二adapter恢复原`/workspace/recreation`路径，功能4/6、SSIM0.179、test_score0.4228，但官方最终0.1带`read_answer_leak`（5条`/data`路径命中）。这可能包含自有模块路径的误报，尚不能越过官方规则改写0.4228为该轮最终分。原标记、候选hash、两个adapter结果全保留。
3. 最后一轮 `minipaint_recreation_eval_1791129685783416430`，恢复自己的完整session与源码、只提供真实概括性功能失败反馈，不给隐藏验证源码；原生自然退出0、无OOM、无编译错误。**功能4/6、SSIM0.179、最终0.4228**，仍未达参考6/6、visual>=0.85的训练接受条件。第三轮完整session19,984,024bytes，copy_manifest逐文件大小/SHA核验通过，不存在64MiB截断。第三轮预算明确3/3已耗尽，不能挑更高分的轮作为三轮成功、不能第四次继续刷分。旧全部成绩与失败保持。

首轮/第二轮/第三轮有会话继承，后续canonical链应明确父轮并去除重复历史，不能把每个raw文件重复送学习并宣称新增独立素材。raw含模型内部内容，仅私有归档，不直接作为公开AutoSkill学习输入。

### Squoosh：首轮持续真实推进

固定GoogleChromeLabs/squoosh源码commit `e8d35e0fb66eb16eff6fe8fc773eabcbb7128de3`，Apache2；独立图像编码训练应用，不是250公开评测实例。原Windows/WSL共享盘构建存在P9等待；不完整tar丢失Linux`.bin`链接导致rollup失败、Linux1.25GiB构建OOM均保留。改用完整固定源码＋本地npm cache在Linux文件系统离线构建、2GiB/2CPU，npm ci与rollup约30.4秒成功，79个site文件；不是agent复刻成功。

独立六项验证含首页、PNG真实像素、JPEG/WebP真实编码与解码尺寸、resize、rotate，静态负对照0/6。初验证Rotate/Resize被官方离线snackbar/控件点击假设与资源影响，v1/v2/v2.3负自验结果全保留；在正式agent前独立新版本修正可见label点击与可见Dismiss及合理动作等待，不改行为assertion。最终**同2GiB/2CPU官方reference self-eval功能6/6、visual1、final1**后启动。

首轮 `squoosh_recreation_eval_1791129536850164583`，controller126497/start_ticks1635703，native actor127286；boot `255b5570-fab4-46e1-a9ff-c307b0bbb76a`。与miniPaint第三轮重叠1248.2555秒（约20.8分钟），这证明题间实际并行，不证明固定2倍加速。采样epoch1791131406：真实trajectory446行、6,325,394bytes，mtime1791131401；不是只凭controller心跳判断推进。

Squoosh exact容器MEMCG OOM杀掉浏览器子进程129212，原agent/runner/controller仍在。失败保留，external_resource_v261_manifest记录旧状态/旧cap/脚本SHA/新cap；仅将同容器增至3GiB，无agent重启/新增完整轮。仍有OOM历史标记，不能说从未异常或用容器running掩盖它。后续须继续核对实际浏览器/工具与API、最终交付和评分。

### 并发代理故障及诚实归属

v2.4两个host-network容器的本机proxy均用8788，第二个proxy EADDRINUSE，但readiness竞态命中了第一个已有proxy。两agent的context、候选、参考端口仍独立、同provider/model；**重叠期间ledger都标Squoosh route，不能把该route所有请求归给Squoosh，也不能凭总请求数认定每路健康**。需保留每agent原生stream/session/端口日志作归属，未完成逐请求对齐不得报精确各路成本。

为防先结束任务关闭后者模型通道，另建8791独立stateless proxy及精确miniPaint cgroup NAT；新连接GET/v1/models与iptables计数实际通过，0模型调用。`ss -K`虽然返回0但没有销毁旧socket，旧“reconnected”报告由新侧证明确纠正。miniPaint在实际模型迁移前自然完成；精确旧连接reset脚本因socket已消失先行assert，**没有应用任何filter规则**。因此不能宣称已观测到独立新代理上的模型完成。已确认miniPaint退出后删除其精确NAT、停止自己8791 proxy，Squoosh原8788与其他实验未动。

未来v2.7单独冻结预留8792/8793，绑定占用前置检查并在HTTP readiness后核实自身proxy仍活；真实占用端口负对照两路均拒绝，0模型调用。跨版本读取canonical预算、第三轮已耗尽就拒绝；已有轮的continuation checkpoint未准入不能冷启动重放。**准备未激活**，不热改当前actor或称其已覆盖26任务。

## 验证、限制与下一步

所有本项既有freeze SHA检查无变化（miniPaint原57/v21 57/v22 57/v24 58，Squoosh v22/v23/v24各23及v27准备文件）；完整miniPaint第三轮19.98MB来源/目标SHA通过。每30秒外部观察器142639/start_ticks见observer_identity持续保存真实身份/API/容器/内存快照；只监控并在两路结束后清自己代理，不自动重跑或增加第四轮。provider请求别名仍`deepseek-v4-flash-vision-exp`，返回`deepseek-v4.1-flash`，物理checkpoint未知，凭据不入记忆。

当前仅可证明并发真实发生及相关设施修复；总体吞吐提升倍数、最终高质量应用数量、skills数量/迁移增益均未知。Squoosh首轮继续；其他24优先完成等价原生reference/verifier准入，再加入独立端口的新冻结管道。平台等待不能伪记失败或假称采集已完成。miniPaint保留三轮失败素材，公开canonical与原创性审计后再作为候选学习输入，本轮没有启动AutoSkill或250评测。

关键证据：288/reports/{current_phase_v261_manifest.json,parallel_health_state.json,runtime_v24.json,external_resource_v261_manifest.json,live_transport_v25_manifest.json,cgroup_route_verification.json,explicit_tcp_reconnect_result.json,transport_cleanup_after_mini_finished.json,concurrency_v27_prepared.json,port_isolation_verification_v27.json,observer_identity.json}；各runs原成绩/score-only/完整copy_manifest。原285、其他聊天289 Airline/268 Telecom/Co-Gym287全部保留。
