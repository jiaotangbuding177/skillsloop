# 本地tools盘点与公开skills资料获取

日期：2026-10-06。科研评测资料准备，不是Demo开发或效果实验。

## 用户已确认要求

核对当前tools是否具备；列需向EvoMind取得的技能；公开可以获取的skills直接获取，不全部转成平台补交负担。沿用筛选后的材料池，保持原数据和旧结论可追溯。

## 证据支持的观察

- 1224真实会话（716保留/508暂存）内，74可识别技能、449读取/脚本尝试记录/376会话；另3脱敏记录去重后452记录/378会话，不算第75个已识别技能。原81标识全量清单继续保留，7项未在当前范围再出现。
- 默认Windows Node26.1.0/OpenClaw2026.9.5版本通过；允许工具不认证依赖。LibreOffice在PATH/常见位置/注册项未检出；通用FFmpeg/ffprobe缺，PDF提取PATH混版；Python3.14与Codex3.12、Demo与Codex Node库分散。浏览器二进制存在但未启动/Agent验收；WSL仅停止docker-desktop，无Ubuntu；企业/图片/搜索接口及权限未认证。因此tools没有全部齐备，不能沿用旧Linux环境结论。
- 原11公开线索及剩余42非品牌/非emerged标识定向主源检索后，保存42 GitHub固定commit独立包、2 ClawHub固定版本独立包及1视频组合参考（6嵌套SKILL.md），对应45历史标识。image-editing额外保存外层仓库上下文。公开同名或目录同名不证明历史原包一致。
- 29标识仍需实际包/获取落实：5平台品牌/服务适配候选，另24项来源/获取待核。其中腾讯会议已有官方包说明、须登录获取，不称EvoMind原生。原创认证仍为0，不把未找到公开包当原创证明。
- 5优先候选：image-generation35会话、evomind-paper-scan27、pdf_zzz4ai17、evomind-auto1、zzz4ai-search-engine1。需要完整包、版本/hash/许可、依赖和服务契约，不只SKILL.md；默认无需全部KM源码，也不要求所有74项成为试跑前置。
- AutoEvoSkillCreate本轮实际可取且MIT，更正10-05当时页面失败/许可未知，旧记录保留。frontend-design实际Apache-2.0，与4个Anthropic限制许可文档包不同。源码可见不认证给DashScope/OpenClaw直接使用的权利；dbs为CC BY-NC4.0，ClawHub许可仅metadata、IMAP来源许可差异保留。
- xyq目录同名但frontmatter改名、patent名称大小写/空格、fund发布版本与正文自报不同均保存。image-ocr来自SkillsBench任务随附技能，未来重叠盲测须隔离或明确共同基础能力，不当无泄露的新学技能库。

## 工作、核验和限制

官方skill-installer助手指定项目研究目录，固定提交；公开请求不携带GitHub令牌，不上传企业正文。静态ZIP校验路径/大小/符号链接，未执行内容。GitHub API限流改从公开仓库网页固定元数据；FastCtx连接关闭后用限定只读shell和研究资料脚本。

环境审计拒绝整份runtime.json输出，未执行，改限定非秘密元数据完成。一次报告编辑自动审批超时，先只读确认未落盘后小范围重试完成，无遗留阻塞；不把超时当不安全结论。

最终1389资料文件hash、3份冻结来源hash及74唯一/45参考+29待落实分区通过。未注册到全局/Demo、安装依赖、执行历史命令、转换产物、调用新模型/业务服务、生成或消费技能、改Demo或上传Git。下载成功不等于Agent消费通过。并行新增[官方Trace2Skill单主题计划](2026-10-06_trace2skill_single_topic_pilot_plan.md)已回读；本轮建议按其表格主题优先冻结依赖，不强制旧合同主题。

## 产物与来源

收尾再回读并行新增[生成依赖边界](2026-10-06_skill_generation_dependency_boundary.md)：本轮工具/原包清单用于后续消费；先从正文生成候选不等历史附件/KM环境/全库，仅需生成器自身依赖、模型、共同弱草稿和格式检查。已将这点明确写入交付报告，不凭公开同名包补造缺失内部方法。

- [完整报告](../environment/20261006/README.md)、[转发平台请求](../environment/20261006/向EvoMind索取skills清单.md)
- [74项获取CSV](../environment/20261006/skills_全部获取清单.csv)、[29项待落实CSV](../environment/20261006/skills_需平台确认与补交.csv)、[45项公开参考CSV](../environment/20261006/skills_已下载公开参考.csv)
- [核验](../environment/20261006/verification.json)、[环境探针](../reviews/2026-10-06_tool_readiness_probe/local_inventory.json)
- public_skill_downloads.json、additional_archives.json、remotion_archive.json和各包provenance；private/retained_skill_coverage.json保留受控关联，不复制私有正文/凭据到记忆。
- 关联旧[来源审计](2026-10-05_evomind_skill_provenance_annotation.md)、[环境讨论](2026-10-05_skill_tool_environment_adaptation.md)、[工具记录更正](2026-10-05_existing_tool_records_correction.md)。

本轮新增环境/公开文件获取实证，不新增算法收益或业务成功结论。下一步按拟执行主题冻结一个环境/基础库、取得专属原包和测试接口，做真实Agent消费。方法比较固定同一能力，环境失败与算法失败分开。
