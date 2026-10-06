# EvoMind真实数据：KM/OpenClaw技能消费记录统计

日期：2026-10-05。范围为现有1,466条会话。没有连接KM或生产，没有运行技能。

**按已导出工具记录，目前能识别74种位于明确KM/OpenClaw技能运行目录的技能，涉及386条会话。** 统计的是已完成读取技能说明/参考资源或实际发起脚本调用的记录，不是完整库存、版本数、业务成功或方法执行正确率。

扩大到工作区技能包和路径缺失的技能文档后，共81个可识别标识、399条会话：其中74种有明确运行目录，6种只有工作区或相对路径证据，1种只有返回技能文档但缺路径。另有4条会话读取了技能名被脱敏的文件，身份无法可靠恢复，不并入唯一技能数。

## 为什么需要更正上一轮说法

此前根据用户“agent没有skills”的说明，将本批历史会话按无真实技能处理；这不能继续扩成“KM底层没有技能消费”。本轮查看工具载荷和原始工具样本，发现明确读取及脚本调用。用户文字中的“技能已创建”“请使用技能”仍然不作为使用证据；新更正来自工具层记录，而不是这些声明。

这也不证明这些技能由本项目算法生成、组织审核通过或在某任务上起效。`emerged-`前缀只能作为名称，生成来源、版本、真实采纳和权限仍待补证。旧报告与原初判保留，本报告及最新STATE为更正入口。

## 统计口径和数据来源

- 读取：read工具有技能文件/资源路径、完成状态及非空输出；返回可以是部分正文或简化“已读取”回执，不能称完整SKILL.md注入。cat等命令读取文档也单独识别。

- 脚本：实际发起技能目录内的脚本命令；不把列目录、复制、写技能、安装依赖或--help计为消费。执行尝试不自动当脚本成功或业务成功。

- 唯一技能按目录标识去重，同标识不同用户/版本不另加；同一会话读多次只计一个覆盖会话。没有bundle hash和正式库存，不能证明别名与内容级唯一性。

- 来源一：066保留的1,466条会话中rawPayload.toolActivity活动快照。来源二：原始导出raw_payload_sample.jsonl，共1,391条结构抽样记录，1,373条归本批会话；它不是完整工具日志。

- 纳入运行目录：/opt/openclaw-shared-skills/、/opt/evomind-shared-skills/、/opt/evomindskills/、用户.openclaw/.evomind及/home/km-agent/skills。目录证据不代替KM正式注册表。

- 原包约9.3万行工具及返回未导出，因此74是当前可观测的目录标识数量；实际历史总量、完整使用频次和库存数量仍未知。本文不按抽样比例外推。

## 各技能和会话覆盖

此表包含81个可识别标识。运行目录列用于区分主要74种；涉及会话数不是使用次数，也不是成功任务数。

| 技能标识 | 有证据会话数 | 明确运行目录会话数 | 脚本尝试会话数 | 范围 |
|---|---:|---:|---:|---|
| pdf | 65 | 63 | 0 | 运行技能目录 |
| image-ppt-generation | 40 | 40 | 0 | 运行技能目录 |
| image-generation | 37 | 37 | 0 | 运行技能目录 |
| docx | 30 | 30 | 3 | 运行技能目录 |
| evomind-paper-scan | 29 | 29 | 0 | 运行技能目录 |
| imap-smtp-email | 21 | 21 | 0 | 运行技能目录 |
| pdf_zzz4ai | 17 | 17 | 0 | 运行技能目录 |
| contract-review | 13 | 13 | 0 | 运行技能目录 |
| karpathy-wiki | 9 | 9 | 0 | 运行技能目录 |
| xlsx | 9 | 9 | 0 | 运行技能目录 |
| contract-review-cn | 7 | 7 | 0 | 运行技能目录 |
| travel-itinerary-planner | 6 | 6 | 0 | 运行技能目录 |
| job-description-writer | 6 | 5 | 0 | 运行技能目录 |
| competitive-analysis | 4 | 4 | 0 | 运行技能目录 |
| concept-verification-report | 4 | 4 | 0 | 运行技能目录 |
| dbs-chatroom | 4 | 4 | 0 | 运行技能目录 |
| guizang-ppt-skill | 4 | 4 | 1 | 运行技能目录 |
| review-resume | 4 | 4 | 0 | 运行技能目录 |
| emerged-job_description_learning | 4 | 3 | 0 | 运行技能目录 |
| follow-builders | 4 | 3 | 0 | 运行技能目录 |
| getnote-skill | 4 | 3 | 0 | 运行技能目录 |
| business-case-builder | 3 | 3 | 0 | 运行技能目录 |
| create-prd | 3 | 3 | 0 | 运行技能目录 |
| frontend-design | 3 | 3 | 0 | 运行技能目录 |
| human-resources-recruitment | 3 | 3 | 0 | 运行技能目录 |
| netease-mail-connection | 3 | 3 | 0 | 运行技能目录 |
| output-as-word | 3 | 3 | 0 | 运行技能目录 |
| pptx | 3 | 3 | 0 | 运行技能目录 |
| research-paper-writer | 3 | 3 | 0 | 运行技能目录 |
| agent-browser | 2 | 2 | 0 | 运行技能目录 |
| dcf-model | 2 | 2 | 0 | 运行技能目录 |
| emerged-dfbadf6e297bf6de67a5e5d3 | 2 | 2 | 0 | 运行技能目录 |
| grilling | 2 | 2 | 0 | 运行技能目录 |
| human-resources-compliance | 2 | 2 | 0 | 运行技能目录 |
| human-resources-departures | 2 | 2 | 0 | 运行技能目录 |
| image-ocr | 2 | 2 | 0 | 运行技能目录 |
| lark-doc | 2 | 2 | 0 | 运行技能目录 |
| pptx-generator | 2 | 2 | 0 | 运行技能目录 |
| wechat-ai-publisher | 2 | 2 | 0 | 运行技能目录 |
| wecom-connection | 2 | 2 | 0 | 运行技能目录 |
| ppt-generator | 2 | 1 | 0 | 运行技能目录 |
| 3-statements | 1 | 1 | 0 | 运行技能目录 |
| ai-news-aggregator | 1 | 1 | 0 | 运行技能目录 |
| brainstorm-ideas-new | 1 | 1 | 0 | 运行技能目录 |
| competitive-intelligence | 1 | 1 | 0 | 运行技能目录 |
| dbs-deconstruct | 1 | 1 | 0 | 运行技能目录 |
| deep-research | 1 | 1 | 0 | 运行技能目录 |
| emerged-12c473344e84b1c9d850c849 | 1 | 1 | 0 | 运行技能目录 |
| emerged-38e6b2915d9c4b7588e54d37 | 1 | 1 | 0 | 运行技能目录 |
| emerged-5833d138e66097ffbeb0de98 | 1 | 1 | 0 | 运行技能目录 |
| evomind-auto | 1 | 1 | 0 | 运行技能目录 |
| feishu-connection | 1 | 1 | 0 | 运行技能目录 |
| fund-proposal-assistant | 1 | 1 | 0 | 运行技能目录 |
| game-developer | 1 | 1 | 0 | 运行技能目录 |
| gx-brand-content-production | 1 | 1 | 0 | 运行技能目录 |
| human-resources-performance | 1 | 1 | 0 | 运行技能目录 |
| human-resources-training | 1 | 1 | 0 | 运行技能目录 |
| image-editing | 1 | 1 | 0 | 运行技能目录 |
| lark-shared | 1 | 1 | 0 | 运行技能目录 |
| nature-academic-search | 1 | 1 | 0 | 运行技能目录 |
| nature-response | 1 | 1 | 0 | 运行技能目录 |
| nature-reviewer | 1 | 1 | 0 | 运行技能目录 |
| nsfc-research-content-method | 1 | 1 | 0 | 运行技能目录 |
| nuwa-skill | 1 | 1 | 0 | 运行技能目录 |
| patent-scanner | 1 | 1 | 0 | 运行技能目录 |
| pricing-strategy | 1 | 1 | 0 | 运行技能目录 |
| product-name | 1 | 1 | 0 | 运行技能目录 |
| product-strategy | 1 | 1 | 0 | 运行技能目录 |
| project-quotation | 1 | 1 | 0 | 运行技能目录 |
| qcc-company-connection | 1 | 1 | 0 | 运行技能目录 |
| startup-canvas | 1 | 1 | 0 | 运行技能目录 |
| swot-analysis | 1 | 1 | 0 | 运行技能目录 |
| tencent-meeting-mcp | 1 | 1 | 0 | 运行技能目录 |
| ui-ux-pro-max | 1 | 1 | 0 | 运行技能目录 |
| AutoEvoSkillCreate | 1 | 0 | 0 | 工作区/路径未知 |
| early-tech-investment | 1 | 0 | 0 | 工作区/路径未知 |
| gx-tender-response-workbench | 1 | 0 | 0 | 工作区/路径未知 |
| prd-generator | 1 | 0 | 0 | 工作区/路径未知 |
| remotion-video-generator | 1 | 0 | 1 | 工作区/路径未知 |
| xyq-nest-skill | 1 | 0 | 1 | 工作区/路径未知 |
| zzz4ai-search-engine | 1 | 0 | 0 | 工作区/路径未知 |

## 当前能证明和不能证明什么

有目录+读取记录，可以说“已导出日志记录过读取这类技能”。例如PDF、Word、图片生成、论文资料、合同审查等技能可定位到会话和工具调用。只有简化读取回执的案例，仍应向KM补当时技能正文和版本。

不能据此说“74种技能全部有效使用”“有386个成功任务”“本项目生成74种技能”，也不能用技能读取覆盖率代替业务收益。没有读取记录的会话也不能当无技能对照：可能有自动注入，或对应日志没有导出。

## 如何补齐KM侧实际完整数量

数据方按会话—用户—agent实例—KM原生会话键映射，补完整history及当时技能库存/版本。当前GET /api/km/skills只说明当前可见库存；结合GET /api/km/skills/{id}/bundle、个人revisions及历史备份才能核对当时状态。平台skill_inventory_snapshots和skill_usage_events可辅助，但选中不等于消费，原schema需线上核对。

每种技能交技能ID/目录标识、版本/hash、生效区间与全包；每次使用交会话/请求/真实调用编号及注入、读取、脚本调用分别的证据。只有这样才能补成完整历史计数和可靠的有/无技能分组。

## 交付

- [技能清单CSV](../datasets/evomind/km_skill_audit_20261005/skills.csv)；[逐技能来源查看页](../datasets/evomind/km_skill_audit_20261005/private/index.html)。

- [原数据补交说明](2026-10-05_evomind_data_supplement_request.md)及[本轮统计JSON](../datasets/evomind/km_skill_audit_20261005/summary.json)。旧补交说明中的历史无技能假定由本报告更正，其他文件/工具/时间缺口仍成立。

原始输出留在本地受控目录，不复制凭据到报告或记忆。没有改写原数据、071标注、全量主题标签或用户当前人工标注。
