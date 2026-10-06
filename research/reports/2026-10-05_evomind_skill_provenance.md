# EvoMind历史技能：公开来源、用户安装与平台内置标注

日期：2026-10-05。覆盖上一轮81个可识别技能标识，其中74个有明确运行目录。没有连接生产/KM，没有安装或运行技能。

## 先说结论

这批技能不能可靠地强行分成“用户下载开源”和“EvoMind原创”两类。已逐项标注来源、平台配置/部署、用户安装证据、获取方式和未知项。平台内置可以打包公开技能，个人目录也可能由平台分发。

**有4项明确用户请求安装公开项目，但尚无完整安装成功→同用户消费闭环；其中follow-builders有同用户安装请求及另会话消费证据，历史先后和版本仍未证实。** 另外11项合计有可定位的公开参考地址，其中包括这4项，不能把11说成全部已确认开源安装。

## 来源分类
| 类别 | 项数 |
|---|---:|
| 公开源码参考候选（非开源） | 4 |
| 来源未确认 | 60 |
| EvoMind品牌或服务适配候选 | 5 |
| 用户请求安装公开项目 | 4 |
| 涌现命名技能，生成来源待核 | 5 |
| 同名开源来源候选 | 2 |
| 文档直接指向公开上游 | 1 |
## 平台配置与部署（独立于来源分类）
| 观察 | 项数 |
|---|---:|
| 源码列入内置目录 | 20 |
| 共享目录部署可观察，未命中内置目录 | 27 |
| 仅个人/工作区或路径未知，安装者待核 | 34 |
本地API的builtin-skill-catalog.ts按标识精确匹配。这个数字只说明当前源码列入内置目录，不认证历史生产安装或EvoMind原创。Agent Browser与agent-browser、openclaw-karpathy-wiki与karpathy-wiki、huashu-nuwa与nuwa-skill没有擅自合并；可能别名须KM确认。
## 用户明确要求安装的4项
| 技能 | 公开项目与许可 | 用户安装/消费证据 |
|---|---|---|
| guizang-ppt-skill | [https://github.com/op7418/guizang-ppt-skill](https://github.com/op7418/guizang-ppt-skill)；AGPL-3.0，当前公开仓库；历史版本待核对 | 有安装请求，但请求者与消费用户未建立同用户证据；请求会话：conv_576b570b2ec8、conv_987ef318052a |
| follow-builders | [https://github.com/zarazhangrui/follow-builders](https://github.com/zarazhangrui/follow-builders)；MIT，当前公开仓库；历史版本待核对 | 同一用户有安装请求及消费证据；安装成功、先后时序未确认；请求会话：conv_c7115885773a |
| nuwa-skill | [https://github.com/alchaincyf/nuwa-skill](https://github.com/alchaincyf/nuwa-skill)；MIT，当前公开仓库；历史版本待核对 | 有安装请求，但请求者与消费用户未建立同用户证据；请求会话：conv_056a7255a9bc、conv_056a7255a9bc |
| AutoEvoSkillCreate | [https://github.com/OpenEduTech/AutoEvoSkillCreate](https://github.com/OpenEduTech/AutoEvoSkillCreate)；会话给出地址；本轮网页读取失败，许可证未核实 | 有安装请求，但请求者与消费用户未建立同用户证据；请求会话：conv_6f49be523ffa |
## 优先向EvoMind取包的5项品牌/服务适配候选
这5项是平台关联程度较高的补取优先项，不是已经证实EvoMind原创的5项。
| 技能 | 依据 |
|---|---|
| image-generation | 返回文档固定使用ZZZ4AI图片服务；属于平台服务适配证据，不等于原创来源认证 |
| evomind-paper-scan | 返回文档明确EvoMind品牌/29维审查，且在本地内置目录中；包含paperconan归因，不能推定全部原创 |
| pdf_zzz4ai | 平台命名并返回Proprietary条款；疑似PDF适配，需拿实际包做差异比较 |
| evomind-auto | 返回文档为Evomind Auto Research System，运行依赖工作区；外部框架来源待核 |
| zzz4ai-search-engine | 返回文档为ZZZ4AI搜索引擎；路径缺失，平台适配/归属待确认 |
image-ppt-generation、image-ocr、image-editing等虽在共享目录被读取，本轮缺正文/来源证明，仍标来源未确认；不能只看名称认定原生。所有其他来源未确认项也已逐项列出补取方式。
## 公开包怎样使用
guizang当前官方仓库标AGPL-3.0，follow-builders及nuwa当前标MIT；仅核对当前网页，不推定历史安装版本。[guizang](https://github.com/op7418/guizang-ppt-skill)、[follow-builders](https://github.com/zarazhangrui/follow-builders)、[nuwa](https://github.com/alchaincyf/nuwa-skill)。AutoEvoSkillCreate仓库来自用户原请求，本轮读取失败，许可待核。
agent-browser返回文档明确列出[Vercel上游](https://github.com/vercel-labs/agent-browser)，当前仓库Apache-2.0；frontend-design和ui-ux-pro-max只是同名参考候选，没有运行包一致性证明。[frontend-design参考](https://github.com/anthropics/skills/tree/main/skills/frontend-design)、[ui-ux参考与许可证](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/main/LICENSE)。
pdf、docx、pptx、xlsx返回的说明含Proprietary许可，Anthropic官方也明确将文档能力参考包区分为源码可见，而非开源。它们即使平台内置，也不能标“用户自行下载的开源技能”。[官方说明](https://github.com/anthropics/skills)。pdf_zzz4ai同样返回Proprietary条款，需单独取其完整许可及平台差异。
## 发给EvoMind/KM数据方的补取要求
1. 以81项CSV的技能标识及消费会话为固定范围，按用户、企业实例、当时版本导出SKILL.md、references、scripts、assets、LICENSE及依赖说明；当前快照与历史版本明确区分。公开参考包不能替代历史实际包。
2. KM现有GET /api/km/skills取得实际skillId、key、scope、版本及来源字段（若接口实际未提供，注明缺失，不补造）；再通过GET /api/km/skills/{id}/bundle取完整包。按用户x-km-user-id与实例路由查询，避免同名跨用户误合。个人版本可查/api/km/skills/personal/{key}/revisions及/{revision}，是否留有完整历史由服务方核实。
3. 对照平台PostgreSQL insight_weaver_prod中的personal_skill_configs、enterprise_skill_configs、skill_submissions、skill_submission_versions、skill_inventory_snapshots、skill_usage_events；先核对生产schema。它们帮助确定配置、采纳、提交审核和历史库存，不自动证明用户下载或实际执行。安装源仓库、commit、安装者、触发者、成功时间与运行包hash如平台表未存，须KM安装日志、包manifest或部署记录补交；不能虚构一个安装表。
4. 提交每个包的来源结论：平台原创 / 平台改编公开上游 / 原样分发第三方 / 用户安装 / 用户自建 / 系统生成 / 不清楚；附原repo+commit、许可、bundle SHA256、用户/实例、时间、创建/安装回执及消费调用ID。共享原生包优先由EvoMind提供，用户自建或安装包由其用户工作区及KM历史补取。依赖内部服务的包需接口说明与测试配置，不需要明文生产密钥。
5. 11项有参考地址可先拿参考版做预备，70项没有已定位的确切参考地址需要平台/用户补包。为了历史重放，81项都应核对当时实际版本；这不等于81项都是平台原创。身份脱敏的技能另外请数据方恢复ID映射，不并入81唯一计数。
## 全部81项标注
| 技能 | 来源 | 平台配置或部署 | 获取方式 |
|---|---|---|
| pdf | 公开源码参考候选（非开源） | 源码列入内置目录 | 公开地址可取参考版；历史实际包、改动及许可仍向EvoMind补取 |
| image-ppt-generation | 来源未确认 | 共享目录部署可观察，未命中内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| image-generation | EvoMind品牌或服务适配候选 | 共享目录部署可观察，未命中内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| docx | 公开源码参考候选（非开源） | 源码列入内置目录 | 公开地址可取参考版；历史实际包、改动及许可仍向EvoMind补取 |
| evomind-paper-scan | EvoMind品牌或服务适配候选 | 源码列入内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| imap-smtp-email | 来源未确认 | 共享目录部署可观察，未命中内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| pdf_zzz4ai | EvoMind品牌或服务适配候选 | 共享目录部署可观察，未命中内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| contract-review | 来源未确认 | 源码列入内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| karpathy-wiki | 来源未确认 | 共享目录部署可观察，未命中内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| xlsx | 公开源码参考候选（非开源） | 源码列入内置目录 | 公开地址可取参考版；历史实际包、改动及许可仍向EvoMind补取 |
| contract-review-cn | 来源未确认 | 仅个人/工作区或路径未知，安装者待核 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| travel-itinerary-planner | 来源未确认 | 仅个人/工作区或路径未知，安装者待核 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| job-description-writer | 来源未确认 | 源码列入内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| competitive-analysis | 来源未确认 | 源码列入内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| concept-verification-report | 来源未确认 | 共享目录部署可观察，未命中内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| dbs-chatroom | 来源未确认 | 仅个人/工作区或路径未知，安装者待核 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| guizang-ppt-skill | 用户请求安装公开项目 | 共享目录部署可观察，未命中内置目录 | 公开地址可取参考版；历史实际包、改动及许可仍向EvoMind补取 |
| review-resume | 来源未确认 | 共享目录部署可观察，未命中内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| emerged-job_description_learning | 涌现命名技能，生成来源待核 | 仅个人/工作区或路径未知，安装者待核 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| follow-builders | 用户请求安装公开项目 | 仅个人/工作区或路径未知，安装者待核 | 公开地址可取参考版；历史实际包、改动及许可仍向EvoMind补取 |
| getnote-skill | 来源未确认 | 源码列入内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| business-case-builder | 来源未确认 | 源码列入内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| create-prd | 来源未确认 | 共享目录部署可观察，未命中内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| frontend-design | 同名开源来源候选 | 共享目录部署可观察，未命中内置目录 | 公开地址可取参考版；历史实际包、改动及许可仍向EvoMind补取 |
| human-resources-recruitment | 来源未确认 | 源码列入内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| netease-mail-connection | 来源未确认 | 仅个人/工作区或路径未知，安装者待核 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| output-as-word | 来源未确认 | 仅个人/工作区或路径未知，安装者待核 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| pptx | 公开源码参考候选（非开源） | 源码列入内置目录 | 公开地址可取参考版；历史实际包、改动及许可仍向EvoMind补取 |
| research-paper-writer | 来源未确认 | 共享目录部署可观察，未命中内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| agent-browser | 文档直接指向公开上游 | 共享目录部署可观察，未命中内置目录 | 公开地址可取参考版；历史实际包、改动及许可仍向EvoMind补取 |
| dcf-model | 来源未确认 | 源码列入内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| emerged-dfbadf6e297bf6de67a5e5d3 | 涌现命名技能，生成来源待核 | 仅个人/工作区或路径未知，安装者待核 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| grilling | 来源未确认 | 仅个人/工作区或路径未知，安装者待核 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| human-resources-compliance | 来源未确认 | 源码列入内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| human-resources-departures | 来源未确认 | 源码列入内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| image-ocr | 来源未确认 | 共享目录部署可观察，未命中内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| lark-doc | 来源未确认 | 仅个人/工作区或路径未知，安装者待核 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| pptx-generator | 来源未确认 | 共享目录部署可观察，未命中内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| wechat-ai-publisher | 来源未确认 | 仅个人/工作区或路径未知，安装者待核 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| wecom-connection | 来源未确认 | 仅个人/工作区或路径未知，安装者待核 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| ppt-generator | 来源未确认 | 仅个人/工作区或路径未知，安装者待核 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| 3-statements | 来源未确认 | 源码列入内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| ai-news-aggregator | 来源未确认 | 仅个人/工作区或路径未知，安装者待核 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| brainstorm-ideas-new | 来源未确认 | 共享目录部署可观察，未命中内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| competitive-intelligence | 来源未确认 | 源码列入内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| dbs-deconstruct | 来源未确认 | 仅个人/工作区或路径未知，安装者待核 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| deep-research | 来源未确认 | 源码列入内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| emerged-12c473344e84b1c9d850c849 | 涌现命名技能，生成来源待核 | 仅个人/工作区或路径未知，安装者待核 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| emerged-38e6b2915d9c4b7588e54d37 | 涌现命名技能，生成来源待核 | 仅个人/工作区或路径未知，安装者待核 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| emerged-5833d138e66097ffbeb0de98 | 涌现命名技能，生成来源待核 | 仅个人/工作区或路径未知，安装者待核 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| evomind-auto | EvoMind品牌或服务适配候选 | 共享目录部署可观察，未命中内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| feishu-connection | 来源未确认 | 仅个人/工作区或路径未知，安装者待核 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| fund-proposal-assistant | 来源未确认 | 共享目录部署可观察，未命中内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| game-developer | 来源未确认 | 仅个人/工作区或路径未知，安装者待核 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| gx-brand-content-production | 来源未确认 | 仅个人/工作区或路径未知，安装者待核 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| human-resources-performance | 来源未确认 | 源码列入内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| human-resources-training | 来源未确认 | 源码列入内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| image-editing | 来源未确认 | 共享目录部署可观察，未命中内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| lark-shared | 来源未确认 | 仅个人/工作区或路径未知，安装者待核 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| nature-academic-search | 来源未确认 | 仅个人/工作区或路径未知，安装者待核 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| nature-response | 来源未确认 | 仅个人/工作区或路径未知，安装者待核 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| nature-reviewer | 来源未确认 | 仅个人/工作区或路径未知，安装者待核 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| nsfc-research-content-method | 来源未确认 | 共享目录部署可观察，未命中内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| nuwa-skill | 用户请求安装公开项目 | 共享目录部署可观察，未命中内置目录 | 公开地址可取参考版；历史实际包、改动及许可仍向EvoMind补取 |
| patent-scanner | 来源未确认 | 共享目录部署可观察，未命中内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| pricing-strategy | 来源未确认 | 源码列入内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| product-name | 来源未确认 | 共享目录部署可观察，未命中内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| product-strategy | 来源未确认 | 共享目录部署可观察，未命中内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| project-quotation | 来源未确认 | 仅个人/工作区或路径未知，安装者待核 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| qcc-company-connection | 来源未确认 | 仅个人/工作区或路径未知，安装者待核 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| startup-canvas | 来源未确认 | 共享目录部署可观察，未命中内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| swot-analysis | 来源未确认 | 共享目录部署可观察，未命中内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| tencent-meeting-mcp | 来源未确认 | 共享目录部署可观察，未命中内置目录 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| ui-ux-pro-max | 同名开源来源候选 | 共享目录部署可观察，未命中内置目录 | 公开地址可取参考版；历史实际包、改动及许可仍向EvoMind补取 |
| AutoEvoSkillCreate | 用户请求安装公开项目 | 仅个人/工作区或路径未知，安装者待核 | 公开地址可取参考版；历史实际包、改动及许可仍向EvoMind补取 |
| early-tech-investment | 来源未确认 | 仅个人/工作区或路径未知，安装者待核 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| gx-tender-response-workbench | 来源未确认 | 仅个人/工作区或路径未知，安装者待核 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| prd-generator | 来源未确认 | 仅个人/工作区或路径未知，安装者待核 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| remotion-video-generator | 来源未确认 | 仅个人/工作区或路径未知，安装者待核 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| xyq-nest-skill | 来源未确认 | 仅个人/工作区或路径未知，安装者待核 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
| zzz4ai-search-engine | EvoMind品牌或服务适配候选 | 仅个人/工作区或路径未知，安装者待核 | 向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代 |
