# 2026-10-06 公开 skill 来源补充核查

## 范围与证据等级

本记录为 13 个历史 skill 标识的公开资料核查，只使用 skill 名称检索公开发布者 GitHub、ClawHub 与发布者页面，未将企业会话正文发送到外部检索服务。核查没有安装或执行公开包。此次发现的是目前可取得的公开参考实现，**全部尚未证明与 EvoMind 历史安装包等价**：缺少历史 SKILL.md、目录树、版本/commit、文件哈希或安装来源证据。同名不能证明同包；未找到公开来源也不能证明为 EvoMind 原生包。

用户要求已确认：公开可获取的 skills 优先直接取得，EvoMind 自有/私有包再索取。本文据此提供下载候选，但不把公开参考替代为历史原件。

## 13 项核查结果

| 历史标识 | 公开来源及相对 SKILL 路径 | 许可证据 | 当前可支持的判断 |
| --- | --- | --- | --- |
| imap-smtp-email | [gzlicanyi/mail-skills](https://github.com/gzlicanyi/mail-skills)，`skills/imap-smtp-email/SKILL.md`；[发布者 ClawHub](https://clawhub.ai/gzlicanyi/skills/imap-smtp-email) | ClawHub 当前页面标 MIT-0；GitHub README 标 MIT，根 LICENSE 网页本轮未取到 | 发布者主源明确，可作为同名参考；许可元数据冲突须保留。历史等价未知 |
| karpathy-wiki | [SherwinQ/karpathy-wiki](https://github.com/SherwinQ/karpathy-wiki/blob/main/SKILL.md)，根 `SKILL.md` | [根 LICENSE](https://github.com/SherwinQ/karpathy-wiki/blob/main/LICENSE) MIT 正文已核实 | 同名公开实现之一，另有不同实现。历史等价未知 |
| getnote-skill | [AaronWan/getnote-skill](https://github.com/AaronWan/getnote-skill)，根 `SKILL.md`，附 `assets/`、`references/`、`scripts/` | GitHub 根目录存在 LICENSE 并标 Apache-2.0；LICENSE 正文网页本轮获取失败 | 同名发布者包可下载；需在静态包内核实 LICENSE 字节。历史等价未知 |
| remotion-video-generator | [发布者文章](https://ai-daily.tech/p/remotion-video-generator-skill/)列 [v1.0.4 ZIP](https://ai-daily.tech/skills/remotion-video-generator-v1.0.4.zip) 与原始仓库 [addunt/short-video-blog](https://github.com/addunt/short-video-blog)；准确 SKILL 路径未核实 | 文章称 `license/` 包含五份第三方协议，协议正文未核实 | 当前仅为发布者下载线索，适合静态 archive 核验。市场目录另指向 zhizhunbao，不应与此包合并。历史等价未知 |
| pptx-generator | [MiniMax-AI/skills](https://github.com/MiniMax-AI/skills/blob/main/skills/pptx-generator/SKILL.md)，`skills/pptx-generator/SKILL.md` | [根 LICENSE](https://github.com/MiniMax-AI/skills/blob/main/LICENSE) MIT 正文和 SKILL 前言已核实；还应保留仓库 LICENSES、CREDITS | 官方同名参考，存在其他不同技术栈的同名实现。历史等价未知 |
| contract-review | [NOMOREKKK/contract-review-skill](https://github.com/NOMOREKKK/contract-review-skill/blob/main/SKILL.md)，根 `SKILL.md`，frontmatter `name: contract-review` | [根 LICENSE](https://github.com/NOMOREKKK/contract-review-skill/blob/main/LICENSE) MIT 正文已核实 | 中国法域同名参考；不是 contract-review-cn 来源证明。历史等价未知 |
| contract-review-cn | 本轮仅定位到市场目录条目，未定位到可核实的同名发布者仓库、可下载主源及许可 | 未确认 | 公开同名主源未定位；来源/所有权仍未知，不能标为 EvoMind 原生 |
| image-ppt-generation | 未定位可信同名主源；[LueXxxxxxx/gpt-image-ppt-creator-skill](https://github.com/LueXxxxxxx/gpt-image-ppt-creator-skill) 是另名功能参考 | 功能参考仓库标 MIT；未核实历史标识的许可 | 不将功能参考当同名原包；历史来源/所有权仍未知 |
| lark-doc | [larksuite/cli](https://github.com/larksuite/cli/blob/main/skills/lark-doc/SKILL.md)，`skills/lark-doc/SKILL.md`，附 references | [根 LICENSE](https://github.com/larksuite/cli/blob/main/LICENSE) MIT 正文已核实 | 官方同名参考；引用 lark-shared 和 lark-cli。历史等价未知 |
| grilling | [mattpocock/skills](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md)，`skills/productivity/grilling/SKILL.md` | [根 LICENSE](https://github.com/mattpocock/skills/blob/main/LICENSE) MIT 已核实 | 发布者同名参考。历史等价未知 |
| research-paper-writer | [ailabs-393/ai-labs-claude-skills](https://github.com/ailabs-393/ai-labs-claude-skills/blob/main/packages/skills/research-paper-writer/SKILL.md)，`packages/skills/research-paper-writer/SKILL.md` | [根 LICENSE](https://github.com/ailabs-393/ai-labs-claude-skills/blob/main/LICENSE) MIT 已核实 | 公开合集中的同名参考，原作者尚未确定，不能写成原创上游已确认。历史等价未知 |
| brainstorm-ideas-new | [phuryn/pm-skills](https://github.com/phuryn/pm-skills/blob/main/pm-product-discovery/skills/brainstorm-ideas-new/SKILL.md)，`pm-product-discovery/skills/brainstorm-ideas-new/SKILL.md` | [根 LICENSE](https://github.com/phuryn/pm-skills/blob/main/LICENSE) MIT 正文已核实 | 发布者同名参考。历史等价未知 |
| deep-research | [B143KC47/deep-research-skill](https://github.com/B143KC47/deep-research-skill/blob/main/deep-research/SKILL.md)，`deep-research/SKILL.md`；[同作者 ClawHub](https://clawhub.ai/b143kc47/skills/b143kc47-deep-research) | [GitHub 根 LICENSE](https://github.com/B143KC47/deep-research-skill/blob/main/LICENSE) MIT 已核实；ClawHub 标 MIT-0 | 多个不同同名实现中的公开参考；保留许可差异。历史等价未知 |

## 其他可保存但不能合并的参考

- 网易 [LobsterAI imap-smtp-email](https://github.com/netease-youdao/LobsterAI/blob/main/SKILLs/imap-smtp-email/SKILL.md)，路径 `SKILLs/imap-smtp-email/SKILL.md`，根 [MIT LICENSE](https://github.com/netease-youdao/LobsterAI/blob/main/LICENSE) 已核实。该版本含 LobsterAI 配置约定，应与 gzlicanyi 包分开保存。
- `karpathy-wiki` 另有 toolboxmd 实现；当前目录分拆、旧路径变更，不能仅凭名称拼入 SherwinQ 包。
- `contract-review` 有 hc938456 等其他实现，本轮未核实其根许可，不应据网页可见就称开源。
- Remotion 官方 best-practices 包与历史 `remotion-video-generator` 标识不同；不自动认定别名。

## 应保存的获取证据及后续

静态取得参考包后保留整项目录、引用的 references/scripts/assets、根许可证和有关第三方协议，记录 commit/version、每文件 SHA-256、原始 URL、获取时间。下载行为只证明该公开参考可获取，不证明企业历史使用的是它，也不证明 skill 的效果。

`NOMOREKKK/contract-review-skill` 下载选择根 `SKILL.md` 及其同级依赖目录；`ailabs-393/ai-labs-claude-skills` 下载选择 `packages/skills/research-paper-writer/`。不执行包内安装脚本。

本轮新增实证发现仅限公开来源存在、当前目录位置与网页许可标注；无新增系统效果、实验结果或企业历史来源实证发现。
