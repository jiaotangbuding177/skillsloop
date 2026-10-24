# 当前Q评测资料的独立Git分支交接

日期：2026-10-25，Asia/Shanghai。科研模式；本轮仅收集已有结果和证据，无新增效果实证发现，不执行Q评分或业务重跑。

## 用户已确认要求

用户要求将Q所需结果、日志、产物和评测证据统一上传Git新分支，附可交给专门AI评审Agent的指南。已通过问答确认三组范围：当前28道改造题的AutoSkills和Trace2Skills各28；当前49道强匹配题的NoSkills；全部250道WRD。后续用户说明AS/TS关键缺项已跑完并要求继续，本轮据新证据接续，旧缺16结论不再作为当前状态。

## 实际资料与观察

本轮以D:/skillloop实时研究目录为源，独立worktree用于发布。现行结果快照来自output/experiment_results/current.json当时指向的四组1000条索引。355条选择为56 AS/TS、49 NS、250 WRD；request题面355/355与当前prompt精确一致，1090个请求输入绑定实际SHA/大小全一致，355个结果源SHA均核对。最新T0197采用retry2最终completed，旧失败只保留历史。

当前选中4条failed仍有实际产物，不剔除、不把整题Q归零。全部355的749个原始outputs、34,120,615字节与归档逐字节相同；250任务对象和689个portable输入同源。另收录10个明确的替换历史尝试，但不计入355评测分母。本包不冒充全项目所有历史费用/制作尝试全集，原始历史未删除或重写。

交接路径：handoff/20261025_q_evaluation。6个LFS ZIP合计86,239,083字节，归档含11,336个文件绑定、261,892,242原始字节，选中及附带历史分列。来源和文件SHA在COORDINATOR与MANIFEST中，远端评审不依赖D/E盘绝对路径。

4个原failed源缺导出evidence/目录，但原生session_events.jsonl实存且已保留。该缺口为源导出未发生，不是漏复制；指南区分可选导出、原生轨迹、确认内容缺失和评测证据不足。

凭据采用白名单排除profile/config/accounts/runtime_code/host_api_queue/private等；实际文本另做模式扫描。唯一宽模式命中来自T0039题面明确的测试标记密码，原件保留，不能当有效账号；窄扫描与独立宽扫描的计数口径已明确。没有修改源文件，不把模式扫描写成绝对零泄露证明。

## 指南和当前决策

评委从匿名JUDGE队列工作，先产物后必要日志，COORDINATOR中的方法/成本/旧TSR留给协调员。原生日志会暴露技能路径，发生时记录失盲，不声称严格双盲。28改造题四组112条优先，随后完成其余243条；覆盖不对称不直接拿AS/TS28均分与WRD250均分作公平方法比较。

沿用2631项五维rubric，其中新28为338项。权重30/20/20/20/10、条目0/0.5/1、维内等权、Q不乘TSR；单缺陷一个主责、缺产物仅依赖项0、未知保留null/原分母、D5实际像素、每例draft后自review。最新用户文件名政策为type_count_nonzero_format_open，旧具名文件只作角色定位，不能因改名本身扣Q。旧ecnu POST/deadline门禁保留历史身份，不变成本次专门AI的资料读取前置。

AI评分尚未实际执行，人员审核与评分可靠性校准仍未知；未来Q须标探索性，不预设任何方法优越。费用：本轮外部Actor/Judge新增调用0，Codex及协作Agent精确用量/费用不可取得，未知。

## 发布与来源

新分支目标为codex/q-evaluation-handoff-20261025，仓库https://github.com/jiaotangbuding177/skillsloop；独立worktree从71c9e0c548d888bb4daf971ecceaae94ae7fcfd0开始，不将原D盘未提交修改整体带入。只提交本交接目录及本轮研究记忆/索引。最终提交与远端上传成功以本轮git终态核验和最终回复中的SHA/链接为准；尚未评分不因上传而变成效果结果。

主要来源：COORDINATOR/scope.json、alignment_audit.json、selected_runs.jsonl、case_key.jsonl、package_independent_review.json；MANIFEST/build_summary.json、file_sha256.jsonl、verification.json；AGENT_EVALUATION_GUIDE.md、SCORING/result.schema.json。原主线记忆参照D:/skillloop/research/memory/2026-10-25_modified28_rubric_tsr_design.md、four_arm_summary_completed.md及retry9_final_record_replacement.md。
