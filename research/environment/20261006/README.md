# 当前本地环境与 skills 获取结果

日期：2026-10-06。**本地tools尚未齐全。已下载44个独立公开参考包（GitHub 42＋ClawHub 2），另下载1个视频组合参考包（内含6个SKILL.md）；这不是已注册、可执行的历史技能库。**

## 核查范围和口径

以task_topics_20261006的1224条会话（716保留学习、508暂存）为本轮准备范围。历史全1466会话清单有81个技能标识，本范围仍出现74个可识别标识，449条读取/脚本尝试记录、376条会话；另3条脱敏记录合计去重覆盖378条会话。读取、脚本尝试不是有效应用或任务成功认证；本轮也没有新增模型调用、技能生成或效果实验。

旧81项中本次未再出现的7项为dcf-model、3-statements、competitive-intelligence、dbs-deconstruct、deep-research、human-resources-training、swot-analysis。原档保留，不作为本轮必须收齐的前置包。

## tools到底哪些已有，哪些还缺

| 能力 | 本轮确认 | 距离执行验收的差距 |
|---|---|---|
| OpenClaw基本工具 | Windows默认launcher：Node26.1.0/OpenClaw2026.9.5版本通过；read/write/edit/exec/process等已允许 | 允许列表不等于工具链执行成功；本轮没有启动新Agent消费 |
| Office转换 | LibreOffice在PATH、常见位置、注册安装项均未检出；Pandoc2.12可达 | Word/PPT/Excel到PDF及公式重算不能因此判为可用 |
| PDF渲染/提取 | pdftoppm/pdfinfo26.07.0可达，PATH的pdftotext是MiKTeX23.13.0 | 需固定同一套工具路径，并检查真实文件/中文排版 |
| Python文档与数据库 | 默认3.14.3部分库导入通过，缺python-pptx/reportlab/cairosvg；Codex3.12.14另有文档库 | Codex的库不会自动成为Demo默认库；pandas导入探针超时，未验收 |
| Node文档工具 | Codex依赖中找到docx/pptxgenjs/sharp/pdfjs-dist；Demo核到playwright-core | 需在Agent执行的Node模块搜索路径解析，不能借宿主目录存在就说已接通 |
| 浏览器 | Edge与Playwright Chromium二进制存在 | 没有启动探针或Agent浏览器测试；agent-browser技能包不等于CLI已安装 |
| 视频/音频 | 通用ffmpeg/ffprobe不在PATH，仅有Playwright极简FFmpeg缓存 | 不证明MP4/音频功能具备；Remotion相关依赖尚未安装验收 |
| Linux历史路径 | WSL仅docker-desktop且停止，未发现Ubuntu；Docker CLI有但daemon未检查 | /workspace、/opt及bash脚本不自动在Windows等价运行 |
| 平台/企业服务 | 有历史调用线索，未认证当前Tavily/ZZZ4AI/企业搜索等接口和权限 | 通用exec/web_search不能替代专属工具；需要测试接口、配置契约和授权 |

默认launcher确实指向Windows原生环境，不能沿用历史WSL Ubuntu/OpenClaw2026.9.7实验结论。DEMO_OPENCLAW_COMMAND可覆盖，本轮没有读取.env或进程秘密环境，后续真正运行时须冻结最终解析配置。本轮扫描未发现引用已知Demo启动脚本的活动进程；不等于排除了别处运行的服务。完整非秘密版本/路径/导入记录见../../reviews/2026-10-06_tool_readiness_probe/local_inventory.json。

## 优先向EvoMind要的5项

| 技能标识 | 用途线索 | 涉及会话 |
|---|---|---|
| image-generation | 平台图片生成服务调用 | 35 |
| evomind-paper-scan | 论文检索与研读的 EvoMind 适配 | 27 |
| pdf_zzz4ai | 平台 PDF 处理服务适配 | 17 |
| evomind-auto | EvoMind 自动研究流程 | 1 |
| zzz4ai-search-engine | 平台搜索服务适配 | 1 |

这5项有平台品牌或专属服务适配证据，优先要实际包及接口。**目前“平台原创已确认”数量为0，不能把来源未知的技能一概称为原生。** 本轮另外24项尚未取得可对应的公开参考包，需先确认来源和获取方式，再决定由平台、原作者或个人库拥有者交包；其中腾讯会议已有官方说明，须登录取得，不属于“网上不存在”的判断。详见[可直接转发的索取清单](向EvoMind索取skills清单.md)和[逐项CSV](skills_需平台确认与补交.csv)。

## 已替你下载的公开参考

| 技能标识 | 下载结果 | 许可 | 来源 |
|---|---|---|---|
| pdf | 完整下载 | Anthropic 源码可见限制许可；不能当开源使用 | https://github.com/anthropics/skills |
| docx | 完整下载 | Anthropic 源码可见限制许可；不能当开源使用 | https://github.com/anthropics/skills |
| xlsx | 完整下载 | Anthropic 源码可见限制许可；不能当开源使用 | https://github.com/anthropics/skills |
| pptx | 完整下载 | Anthropic 源码可见限制许可；不能当开源使用 | https://github.com/anthropics/skills |
| frontend-design | 完整下载 | Apache-2.0（保存了全文） | https://github.com/anthropics/skills |
| agent-browser | 完整下载 | Apache-2.0（保存了全文） | https://github.com/vercel-labs/agent-browser |
| guizang-ppt-skill | 完整下载 | AGPL-3.0（保存了全文） | https://github.com/op7418/guizang-ppt-skill |
| follow-builders | 完整下载 | 包内许可或发布者说明需逐项核对；不视为无条件开源 | https://github.com/zarazhangrui/follow-builders |
| nuwa-skill | 完整下载 | MIT（保存了全文） | https://github.com/alchaincyf/nuwa-skill |
| AutoEvoSkillCreate | 完整下载 | MIT（保存了全文） | https://github.com/OpenEduTech/AutoEvoSkillCreate |
| ui-ux-pro-max | 完整下载 | MIT（保存了全文） | https://github.com/nextlevelbuilder/ui-ux-pro-max-skill |
| getnote-skill | 完整下载 | Apache-2.0（保存了全文） | https://github.com/AaronWan/getnote-skill |
| lark-doc | 完整下载 | MIT（保存了全文） | https://github.com/larksuite/cli |
| lark-shared | 完整下载 | MIT（保存了全文） | https://github.com/larksuite/cli |
| brainstorm-ideas-new | 完整下载 | MIT（保存了全文） | https://github.com/phuryn/pm-skills |
| pptx-generator | 完整下载 | MIT（保存了全文） | https://github.com/MiniMax-AI/skills |
| grilling | 完整下载 | MIT（保存了全文） | https://github.com/mattpocock/skills |
| karpathy-wiki | 完整下载 | MIT（保存了全文） | https://github.com/SherwinQ/karpathy-wiki |
| imap-smtp-email | 完整下载 | 包内许可或发布者说明需逐项核对；不视为无条件开源 | https://github.com/gzlicanyi/mail-skills |
| contract-review | 完整下载 | MIT（保存了全文） | https://github.com/NOMOREKKK/contract-review-skill |
| research-paper-writer | 完整下载 | MIT（保存了全文） | https://github.com/ailabs-393/ai-labs-claude-skills |
| product-strategy | 完整下载 | MIT（保存了全文） | https://github.com/phuryn/pm-skills |
| pricing-strategy | 完整下载 | MIT（保存了全文） | https://github.com/phuryn/pm-skills |
| startup-canvas | 完整下载 | MIT（保存了全文） | https://github.com/phuryn/pm-skills |
| product-name | 完整下载 | MIT（保存了全文） | https://github.com/phuryn/pm-skills |
| review-resume | 完整下载 | MIT（保存了全文） | https://github.com/phuryn/pm-skills |
| create-prd | 完整下载 | MIT（保存了全文） | https://github.com/phuryn/pm-skills |
| business-case-builder | 完整下载 | MIT（保存了全文） | https://github.com/w95/awesome-claude-corporate-skills |
| job-description-writer | 完整下载 | MIT（保存了全文） | https://github.com/w95/awesome-claude-corporate-skills |
| nature-academic-search | 完整下载 | Apache-2.0（保存了全文） | https://github.com/Yuan1z0825/nature-skills |
| nature-response | 完整下载 | Apache-2.0（保存了全文） | https://github.com/Yuan1z0825/nature-skills |
| nature-reviewer | 完整下载 | Apache-2.0（保存了全文） | https://github.com/Yuan1z0825/nature-skills |
| dbs-chatroom | 完整下载 | CC BY-NC 4.0（保存条款，不当作MIT或无限制使用） | https://github.com/dontbesilent2025/dbskill |
| ai-news-aggregator | 完整下载 | MIT（保存了全文） | https://github.com/lanyasheng/ai-news-aggregator |
| competitive-analysis | 完整下载 | Apache-2.0（保存了全文） | https://github.com/anthropics/financial-services |
| patent-scanner | 完整下载 | MIT（保存了全文） | https://github.com/Obviously-Not/patent-skills |
| game-developer | 完整下载 | MIT（保存了全文） | https://github.com/Jeffallan/claude-skills |
| xyq-nest-skill | 完整下载 | MIT（保存了全文） | https://github.com/Pippit-dev/cli |
| ppt-generator | 完整下载 | MIT（保存了全文） | https://github.com/waytouniverse/ppt-generator |
| image-editing | 完整下载 | MIT（保存了全文） | https://github.com/SamurAIGPT/open-ai-image-agent |
| prd-generator | 完整下载 | MIT（保存了全文） | https://github.com/scalershare/prd-generator |
| image-ocr | 完整下载 | Apache-2.0（保存了全文） | https://github.com/benchflow-ai/skillsbench |
| remotion-video-generator | 组合ZIP已保存 | 组合包5份许可，含Remotion专门条款；未完成兼容性审核 | https://ai-daily.tech/skills/remotion-video-generator-v1.0.4.zip |
| travel-itinerary-planner | 固定版本ZIP已保存 | ClawHub作者发布页标MIT-0，包内无独立许可全文，仍待核 | https://clawhub.ai/api/v1/download?slug=travel-itinerary-planner&version=0.1.1 |
| fund-proposal-assistant | 固定版本ZIP已保存 | ClawHub作者发布页标MIT-0，包内无独立许可全文，仍待核 | https://clawhub.ai/api/v1/download?slug=fund-proposal-assistant&version=1.0.0 |

GitHub独立包位于public_skills/，ClawHub固定版本包位于clawhub_skills/，保存SKILL.md及原目录附带的脚本/引用/资源，补存可取得的上游许可/README。视频包位于publisher_archives/，保存原ZIP及完整静态解压目录：该包是scene-planner/video-generator等6个嵌套技能的组合，不能当作历史同名单包已还原。文件哈希、固定Git提交、来源强度见public_skill_downloads.json、remotion_archive.json、additional_archives.json和各包_download_provenance.json。image-editing另保存完整上游上下文到shared_repo_context/image-editing/，包含MODELS.md和外层引用；不证明其API工具已接通。

AutoEvoSkillCreate此次网页元数据与完整包都可取得，许可证MIT；修正10-05“当前页面读取失败/许可未知”的当时状态，旧记录保留。frontend-design实际包许可Apache-2.0，不能与同仓4个限制许可文档包混同。imap-smtp-email发布者市场页标MIT-0而GitHub README称MIT，保留差异；未取到适用完整许可不能凭同名赋予权利。四个Anthropic文档包pdf/docx/pptx/xlsx是源码可见参考，**不是通常意义上的开源包，也没有据此取得给DashScope/OpenClaw直接使用的许可认证**。下载资料与实际可启用包必须分开。[上游README](https://github.com/anthropics/skills)、[文档许可原文](https://github.com/anthropics/skills/blob/main/skills/pdf/LICENSE.txt)。

公开“可获取”也不代表“与历史运行包等价”：agent-browser返回文档指向上游，4个包曾有用户安装请求，部分是同名参考或合集。没有完整版本/包哈希比对，不将它们写成历史原包。合同公开参考来自NOMOREKKK，不能将它自动当作EvoMind的contract-review-cn。[公开合同参考](https://github.com/NOMOREKKK/contract-review-skill)。

额外来源边界：xyq-nest-skill目录同名而当前frontmatter为xyq-skill；patent-scanner当前名称为Patent Scanner；fund-proposal-assistant发布版本1.0.0与正文自报2.1不同，均保留差异。w95合集外源技能可能另有许可，不能按根MIT覆盖；本次两个下载项在其索引标Custom，competitive-analysis取官方Apache-2.0包。dbs-chatroom上游CC BY-NC 4.0并非MIT，未自动启用。image-ocr参考来自SkillsBench特定任务随附技能，不能无说明注入未来无技能/自动学习条件的盲测库；需隔离重叠或定义各方法相同的基础能力。[SkillsBench主源](https://github.com/benchflow-ai/skillsbench)。腾讯会议有[官方Skill说明](https://meeting.tencent.com/support/articles/14/index.html)，账号登录获取和适用许可未落实，不从无许可镜像代取。

本轮没有全局安装到Codex，未加入Demo自动加载目录、未安装这些包的Python/Node依赖、未执行远程仓库脚本或企业历史命令。使用官方skill-installer下载助手并指定项目资料目录；网络请求不携带本地GitHub令牌，企业会话未发送给公开仓库。

## 怎么把准备工作收束成可跑的评测环境

1. 固定一个执行环境及解释器：当前Windows可继续做轻量文本与文件处理；若实际技能依赖bash、/opt、/workspace，另建立固定Linux运行环境，而不是临场改脚本。
2. 按将要执行的主题核对依赖。最新单主题试跑方案建议表格生成与核验，应先冻结表格基础能力、公式计算/文件评分及Python/Node环境；合同/文档再确认输入附件、合同审查原包、PDF/Word、中文字体和产物输出。视频、企业邮箱、飞书等按纳入任务再接入，不等所有74项。
3. 平台提供完整专属技能包和服务契约，而非只给技能说明；第三方原样包给准确URL/commit，我们下载。默认无需kmagent全源码。
4. 对每个纳入的新任务先做一次“Agent读技能→真实工具调用→文件产物→业务/文件验收”，再冻结工具/模型/技能依赖。所有算法基线用同一个基础技能库和工具能力，学习阶段生成的技能单独记录；不能把环境掉链子记成算法失败。
5. **先从历史会话生成skills，不需要等历史附件、KM环境或历史skills全部齐备**；仅需原始正文、生成器依赖/模型、共同的有效弱草稿及格式检查，缺失内部方法和结果保留未知，不凭公开同名包补造历史。这里的执行工具、独立新文件和评分准备用于后续消费/收益验收。公开参考替换历史包要写明，不称精确重放。

## 文件与核验

- skills_全部获取清单.csv：74项，分来源证据、公开参考、补交路线及会话覆盖。
- skills_需平台确认与补交.csv：尚未取得可对应参考包的标识，含官方服务授权获取待落实项，不是原生认证表。
- skills_已下载公开参考.csv：下载目录、固定版本、许可、注册/执行未验证状态。
- private/retained_skill_coverage.json：受控关联索引和统计，可回查原证据，原文未复制入报告。
- public_source_findings.md、public_source_business_followup.md、public_source_integration_followup.md：首轮及剩余42个非品牌/非emerged标识定向检索与同名/变体边界；deep-research已不在当前74项，故未额外下载。
- verification.json：逐文件哈希与3份冻结来源检查。没有任何认证算法收益或真实业务成功的新结论。
