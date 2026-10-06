# 2026-10-06 集成与剩余标识公开来源补检

## 范围、方法与边界

按研究端追加的 22 个标识逐项检索公开来源。读取当前 `skills_需平台确认与补交.csv`（本轮读取时为 52 条数据）确认下表 22 项仍在清单；未改该 CSV。首先核对研究 README/CHARTER/STATE，再进行精确名称检索及已发现作者页面核验。

仅 skill 名称、公开作者/仓库路径用于外部检索，没有企业会话正文、附件、账户数据或凭据出网。市场目录仅用于发现线索；下表支持下载的判断以作者 GitHub 或 ClawHub 页面为准。本子任务只读网络资料，未下载、安装、注册或执行技能。

**所有 22 项的 EvoMind 历史包一致性均未知**。公开同名包、目录同名包和历史原件分开；没有历史 SKILL.md、版本/commit、目录树与 hash 时，不确认包等价。限定检索未定位不是证明公开包不存在，也不是证明 EvoMind 原生所有权。

## 简表

| 标识 | 本轮公开证据 | skill 相对路径 / 名称情况 | 许可证据 | 处理建议与未知项 |
| --- | --- | --- | --- | --- |
| image-ppt-generation | 精确名称 GitHub/ClawHub 索引检索未定位可信主源；首轮功能参考仍见 `public_source_findings.md` | 未确认 | 未确认 | 保留待辨认；不将另名图片 PPT 工具视为历史原包 |
| contract-review-cn | 精确名称 GitHub/ClawHub 索引未定位发布者主源；此前仅市场条目 | 未确认 | 未确认 | 保留待辨认；不与 `contract-review` 自动合并 |
| dbs-chatroom | [dontbesilent2025/dbskill](https://github.com/dontbesilent2025/dbskill) 作者库 | [`skills/dbs-chatroom/SKILL.md`](https://github.com/dontbesilent2025/dbskill/blob/main/skills/dbs-chatroom/SKILL.md)，name 同标识 | [根 LICENSE](https://github.com/dontbesilent2025/dbskill/blob/main/LICENSE) 正文 **CC BY-NC 4.0**，非 MIT | 可保存同名公开参考；许可限制须单独保留，不等于允许商业使用；历史包未知 |
| netease-mail-connection | 精确名称 GitHub/ClawHub 索引未定位主源 | 未确认 | 未确认 | `imap-smtp-email` 不是本标识的来源证明；保留待辨认 |
| output-as-word | 精确名称 GitHub/ClawHub 索引未定位主源 | 未确认 | 未确认 | 不以通用 docx 功能替代原包身份 |
| wechat-ai-publisher | 精确名称 GitHub/ClawHub 索引未定位主源 | 未确认 | 未确认 | 保留待辨认，未知不标为平台原创 |
| wecom-connection | 精确名称 GitHub/ClawHub 索引未定位主源 | 未确认 | 未确认 | 保留待辨认；通用企业微信连接器不是同包证明 |
| feishu-connection | 精确名称 GitHub/ClawHub 索引未定位主源 | 未确认 | 未确认 | `lark-doc`、`lark-shared` 与本标识不自动视为别名 |
| ai-news-aggregator | [lanyasheng/ai-news-aggregator](https://github.com/lanyasheng/ai-news-aggregator) 作者库；[同作者 ClawHub](https://clawhub.ai/lanyasheng/skills/ai-news-aggregator) | [`SKILL.md`](https://github.com/lanyasheng/ai-news-aggregator/blob/main/SKILL.md) 根目录，附 `scripts/`；作者与历史路径 `@lanyasheng` 相符只是来源线索 | GitHub 根 LICENSE 存在、README/GitHub 标 MIT，许可正文网页本轮 cache miss；ClawHub 当前 v2.2.0 标 MIT-0 | 可取作者同名公开参考；保存渠道许可差异，下载后核对 LICENSE 字节；历史版本/hash 未知 |
| game-developer | [Jeffallan/claude-skills](https://github.com/Jeffallan/claude-skills) 作者库 | [`skills/game-developer/SKILL.md`](https://github.com/Jeffallan/claude-skills/blob/main/skills/game-developer/SKILL.md)，name 同标识，附 references | [根 LICENSE](https://github.com/Jeffallan/claude-skills/blob/main/LICENSE) MIT 正文和 SKILL 许可字段已核实 | 可取作者同名参考；另有不同同名实现，不合并；历史包未知 |
| gx-brand-content-production | 精确名称 GitHub/ClawHub 索引未定位主源 | 未确认 | 未确认 | 名称前缀不足以判断平台原创；保留待辨认 |
| nature-academic-search | [Yuan1z0825/nature-skills](https://github.com/Yuan1z0825/nature-skills) 发布者库 | [`skills/nature-academic-search/SKILL.md`](https://github.com/Yuan1z0825/nature-skills/blob/main/skills/nature-academic-search/SKILL.md)，name 同标识；manifest/static/references 为实际依赖 | [根 LICENSE](https://github.com/Yuan1z0825/nature-skills/blob/main/LICENSE) Apache-2.0 正文已核实 | 可取同名公开参考；`nature` 不表示 Nature 期刊官方发布；历史包未知 |
| nature-response | 同上发布者库 | [`skills/nature-response/SKILL.md`](https://github.com/Yuan1z0825/nature-skills/blob/main/skills/nature-response/SKILL.md)，name 同标识，附 manifest/static/references | 同上 Apache-2.0 | 可取同名公开参考；历史包未知 |
| nature-reviewer | 同上发布者库 | [`skills/nature-reviewer/SKILL.md`](https://github.com/Yuan1z0825/nature-skills/blob/main/skills/nature-reviewer/SKILL.md)，name 同标识，附 references | 同上 Apache-2.0 | 可取同名公开参考；存在另名领域审稿实现，勿混包；历史包未知 |
| nsfc-research-content-method | 精确名称 GitHub/ClawHub 索引未定位主源 | 未确认 | 未确认 | 通用 NSFC 写作包不等于该标识；保留待辨认 |
| qcc-company-connection | 精确名称 GitHub/ClawHub 索引未定位主源 | 未确认 | 未确认 | 通用企查查接口不等于历史 skill 包；保留待辨认 |
| tencent-meeting-mcp | [腾讯会议官方 MCP 说明](https://meeting.tencent.com/support/articles/14/index.html)明确官方 Skill 封装包；[AI Skill 入口](https://meeting.tencent.com/ai-skill) | 官方文档列 `SKILL.md`、`config.json`、`scripts/tencent_meeting.py`、`mcp_proxy.py`、`utils.py`、`references/`，但匿名可下载包与准确仓库路径未确认 | 官方包许可未知 | 官方包存在与安装流程可核实，但安装指令目前需个人账号登录生成；保留可下载文件/许可待提供。合集镜像不当原始主源；TinaDu-AI 同名库是独立 MCP server、没有 SKILL.md，不替代本技能 |
| early-tech-investment | 精确名称 GitHub/ClawHub 索引未定位主源 | 未确认 | 未确认 | 保留待辨认 |
| gx-tender-response-workbench | 精确名称 GitHub/ClawHub 索引未定位主源 | 未确认 | 未确认 | 不据前缀判断平台所有权；保留待辨认 |
| xyq-nest-skill | [Pippit-dev/cli](https://github.com/Pippit-dev/cli) 发布者库 | [`skills/xyq-nest-skill/SKILL.md`](https://github.com/Pippit-dev/cli/blob/main/skills/xyq-nest-skill/SKILL.md) **目录同名，当前 frontmatter name 为 `xyq-skill`**，附 scripts/references | [根 LICENSE](https://github.com/Pippit-dev/cli/blob/main/LICENSE) MIT 正文已核实 | 可保存目录同名、当前名称已变的公开参考；不能确认别名或历史等价。之前 `Pippit-dev/pippit-skills` 旧路径本轮未取到 |
| ppt-generator | [waytouniverse/ppt-generator](https://github.com/waytouniverse/ppt-generator) 发布者库 | [`SKILL.md`](https://github.com/waytouniverse/ppt-generator/blob/main/SKILL.md) 根目录，name 同标识 | 根 LICENSE 存在；GitHub/README 标 MIT，许可正文网页本轮 cache miss | 可取同名公开参考，下载后核对许可。anbeime/skill、ddpie/agent-skills 另有明显不同同名实现，勿混包；历史包未知 |
| image-editing | [SamurAIGPT/open-ai-image-agent](https://github.com/SamurAIGPT/open-ai-image-agent) 发布者库 | [`agents/image-editing/SKILL.md`](https://github.com/SamurAIGPT/open-ai-image-agent/blob/main/agents/image-editing/SKILL.md)，目录与 `slug: image-editing` 相符、name 显示 `Image Editing` | 根 LICENSE 存在；GitHub/README 标 MIT，许可正文网页本轮超时 | 可取同 slug 公开参考；SKILL 引用仓库外层 MODELS.md 与 MuAPI 工具参考，需要共享文件；历史包未知 |

## AI News Aggregator 静态获取接口依据

优先可取作者 GitHub 仓库的根 skill 及 scripts、README、LICENSE。ClawHub 官方 [API 文档](https://github.com/openclaw/clawhub/blob/main/docs/api.md)明确 base `https://clawhub.ai` 与公开读端点 `GET /api/v1/download?slug=&version=&tag=`，也说明响应可能为 ZIP 或 `public-github` 来源描述；不能不看响应类型就按 ZIP 解压。

以已核实页面的 slug 与当前版本填入文档端点的请求形式为 `https://clawhub.ai/api/v1/download?slug=ai-news-aggregator&version=2.2.0`。这是依官方接口规范构造的请求，本子任务未获取响应、未认证实际下载成功；若采用该渠道，需要核对响应元数据的 owner 为 lanyasheng，版本及许可随来源保存。作者 GitHub 标 MIT 与 ClawHub 标 MIT-0 的差异不能静默合并。

ClawHub 官方精确搜索 API 在本轮 web 工具中不可访问，错误不当作空结果。上述“未定位”基于已执行的逐项精确公开索引检索，适用范围限定为本轮可见资料。

## 结果口径与下一步

22 项中，9 项定位到作者发布的同名/同目录/同 slug 公开参考（包括 xyq 当前名称变更及 image-editing 显示名差异），1 项腾讯会议定位到官方包说明但没有核实匿名下载与许可，12 项本轮未定位可信同名主源。未改变原始来源标签、原会话或历史版本判断。

根任务随后静态下载和保存 hash 的结果应以其总 manifest 为准；本表只提供来源线索及网络核查证据。对未定位项先请平台辨认归属，第三方原样包给准确 URL/commit；平台原创或改造包给实际完整包与使用条件。没有可核实来源前不标为 EvoMind 原生。

本轮没有新增效果实验、企业历史来源认证或技能用途成功认证；新增实证仅为公开页面存在、目录/名称与许可文字或元数据的可核实观察。
