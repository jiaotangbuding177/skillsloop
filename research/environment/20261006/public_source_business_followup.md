# 商业、HR 与科研技能公开来源补查（2026-10-06）

本表为公开资料的只读核查记录。没有下载技能、执行技能或企业历史命令，没有修改平台补交清单或来源原始数据。它支持后续获取公开对照包，以及区分“公开同名参考可得”与“企业历史实际包已识别”两种证据。

**证据支持的观察：**本轮指定 20 个标识均仍在 `skills_需平台确认与补交.csv` 的本轮读取快照中。找到 14 个标识的作者、官方 GitHub 或作者 ClawHub 主发布参考，其中 12 个有 GitHub `SKILL.md` 与许可来源，2 个有 ClawHub 的 SKILL 页面和发布许可元数据。其余 6 个未定位精确标识的可验证公开主源。全部 20 个历史原包一致性均未确认；“未定位”不证明 EvoMind 原创或平台原生。

表中覆盖来自 [补交清单](D:/skillsgen-industry_track/research/environment/20261006/skills_需平台确认与补交.csv) 的 `技能标识`、`涉及会话`、`保留学习会话`、`暂存会话` 字段。各技能覆盖会重复，不能加总成独立会话。当前读取快照的 20 行覆盖次数之和为 46（KEEP 28、HOLD 18），这里只用于核对逐行合计，非会话并集。

| 标识 | 覆盖（KEEP/HOLD） | 本轮核查结果 | 主源与包路径 | 许可证据与边界 |
|---|---:|---|---|---|
| business-case-builder | 3（0/3） | GitHub 精确 frontmatter name | [w95/awesome-claude-corporate-skills](https://github.com/w95/awesome-claude-corporate-skills/tree/main/07-operations/business-case-builder)，`07-operations/business-case-builder/SKILL.md` | [根 LICENSE](https://raw.githubusercontent.com/w95/awesome-claude-corporate-skills/main/LICENSE) 为 MIT；作者 README 将该项标为 Custom |
| competitive-analysis | 3（2/1） | 官方 GitHub 精确 frontmatter name | [anthropics/financial-services](https://github.com/anthropics/financial-services/tree/main/plugins/vertical-plugins/financial-analysis/skills/competitive-analysis)，`plugins/vertical-plugins/financial-analysis/skills/competitive-analysis/SKILL.md` | [根 LICENSE](https://raw.githubusercontent.com/anthropics/financial-services/main/LICENSE) 为 Apache-2.0；优先官方主源，不能沿用转载仓库的根 MIT |
| job-description-writer | 5（4/1） | GitHub 精确 frontmatter name | [w95/awesome-claude-corporate-skills](https://github.com/w95/awesome-claude-corporate-skills/tree/main/03-human-resources/job-description-writer)，`03-human-resources/job-description-writer/SKILL.md` | [根 LICENSE](https://raw.githubusercontent.com/w95/awesome-claude-corporate-skills/main/LICENSE) 为 MIT；作者 README 将该项标为 Custom |
| travel-itinerary-planner | 6（6/0） | 作者 ClawHub 精确发布 slug，已读 SKILL 页面 | [@daiwk 发布页](https://clawhub.ai/daiwk/skills/travel-itinerary-planner)，版本 `v0.1.1`；作者页声明包含 `scripts/build_trip_plan.py` 与两个 references 文件 | 发布页 License 为 MIT-0；未读取下载包内 LICENSE，包内容和版本仍须获取后复核 |
| human-resources-recruitment | 3（2/1） | 未定位精确主源 | 精确 slug + `SKILL.md` / GitHub / ClawHub 检索未找到可核主源 | 未知；`human-resources-recruiter` 等相近名称不算同名 |
| human-resources-compliance | 2（2/0） | 未定位精确主源 | 精确 slug + `SKILL.md` / GitHub / ClawHub 检索未找到可核主源 | 未知；一般 HR 合规文章与不同名技能不算来源证据 |
| human-resources-departures | 2（1/1） | 未定位精确主源 | 精确 slug + `SKILL.md` / GitHub / ClawHub 检索未找到可核主源 | 未知；`exit-interview`、`hr-offboard` 等不同标识不算同名 |
| human-resources-performance | 1（0/1） | 未定位精确主源 | 精确 slug + `SKILL.md` / GitHub / ClawHub 检索未找到可核主源 | 未知；`human-resources-performance-manager`、`performance-review-assistant` 不算同名 |
| product-strategy | 1（0/1） | 作者 GitHub 精确 frontmatter name | [phuryn/pm-skills](https://github.com/phuryn/pm-skills/tree/main/pm-product-strategy/skills/product-strategy)，`pm-product-strategy/skills/product-strategy/SKILL.md` | [根 LICENSE](https://raw.githubusercontent.com/phuryn/pm-skills/main/LICENSE) 为 MIT，Pawel Huryn |
| pricing-strategy | 1（1/0） | 作者 GitHub 精确 frontmatter name | [phuryn/pm-skills](https://github.com/phuryn/pm-skills/tree/main/pm-product-strategy/skills/pricing-strategy)，`pm-product-strategy/skills/pricing-strategy/SKILL.md` | [根 LICENSE](https://raw.githubusercontent.com/phuryn/pm-skills/main/LICENSE) 为 MIT |
| product-name | 1（0/1） | 作者 GitHub 精确 frontmatter name | [phuryn/pm-skills](https://github.com/phuryn/pm-skills/tree/main/pm-marketing-growth/skills/product-name)，`pm-marketing-growth/skills/product-name/SKILL.md` | [根 LICENSE](https://raw.githubusercontent.com/phuryn/pm-skills/main/LICENSE) 为 MIT |
| project-quotation | 1（1/0） | 未定位精确主源 | 精确 slug + `SKILL.md` / GitHub / ClawHub 检索未找到可核主源 | 未知；`software-quotation-skill`、`vendor-estimate-creator` 与 Microsoft 项目报价文档不算同名 |
| startup-canvas | 1（0/1） | 作者 GitHub 精确 frontmatter name | [phuryn/pm-skills](https://github.com/phuryn/pm-skills/tree/main/pm-product-strategy/skills/startup-canvas)，`pm-product-strategy/skills/startup-canvas/SKILL.md` | [根 LICENSE](https://raw.githubusercontent.com/phuryn/pm-skills/main/LICENSE) 为 MIT |
| create-prd | 3（1/2） | 作者 GitHub 精确 frontmatter name | [phuryn/pm-skills](https://github.com/phuryn/pm-skills/tree/main/pm-execution/skills/create-prd)，`pm-execution/skills/create-prd/SKILL.md` | [根 LICENSE](https://raw.githubusercontent.com/phuryn/pm-skills/main/LICENSE) 为 MIT |
| prd-generator | 1（1/0） | 作者 GitHub 精确 frontmatter name；存在多个同名实现 | [scalershare/prd-generator](https://github.com/scalershare/prd-generator)，根 `SKILL.md` | [LICENSE 原文](https://github.com/scalershare/prd-generator/blob/main/LICENSE) 为 MIT，HermanLee；不同作者同名包不能据名称合并 |
| fund-proposal-assistant | 1（1/0） | 作者 ClawHub 精确发布 slug，已读 SKILL 页面 | [@jirboy 发布页](https://clawhub.ai/jirboy/skills/fund-proposal-assistant)，发布版本 `v1.0.0` | 发布页 License 为 MIT-0；SKILL 正文内部版本写 `v2.1` / `2026-03-04`，与发布版本字段不同，须保留该差异并读取实际包 |
| review-resume | 4（2/2） | 作者 GitHub 精确 frontmatter name | [phuryn/pm-skills](https://github.com/phuryn/pm-skills/tree/main/pm-toolkit/skills/review-resume)，`pm-toolkit/skills/review-resume/SKILL.md` | [根 LICENSE](https://raw.githubusercontent.com/phuryn/pm-skills/main/LICENSE) 为 MIT |
| concept-verification-report | 4（1/3） | 未定位精确主源 | 精确 slug + `SKILL.md` / GitHub / ClawHub 检索未找到可核主源 | 未知；通用 concept verification 文档、专利文本与 `verification-report` 不是本标识的技能包 |
| patent-scanner | 1（0/1） | 作者 GitHub 目录精确 slug；frontmatter 名称不同 | [Obviously-Not/patent-skills](https://github.com/Obviously-Not/patent-skills/tree/main/patent-scanner)，`patent-scanner/SKILL.md`；frontmatter `name: Patent Scanner` | [根 LICENSE](https://raw.githubusercontent.com/Obviously-Not/patent-skills/main/LICENSE) 为 MIT，Obviously Not LLC；仅目录同名参考，不能称 frontmatter 完全相同 |
| image-ocr | 2（2/0） | 基准作者 GitHub 精确 frontmatter name | [benchflow-ai/skillsbench](https://github.com/benchflow-ai/skillsbench/tree/main/tasks/jpg-ocr-stat/environment/skills/image-ocr)，`tasks/jpg-ocr-stat/environment/skills/image-ocr/SKILL.md` | [根 LICENSE](https://raw.githubusercontent.com/benchflow-ai/skillsbench/main/LICENSE) 为 Apache-2.0；未认证其为企业历史来源 |

补充同名歧义：`prd-generator` 另有 [le700/prd-generator-skill 的 SKILL.md](https://raw.githubusercontent.com/le700/prd-generator-skill/main/SKILL.md) 和 [README 许可声明](https://github.com/le700/prd-generator-skill/blob/main/README.md)（MIT，但本轮 LICENSE 原文抓取失败）；另有 casperkwok 的同名候选。`image-ocr` 另有 [lisong2003-lgtm/image-ocr](https://github.com/lisong2003-lgtm/image-ocr)，作者 README 声明代码文档为 CC BY-NC-SA 4.0，语言模型另有 NOTICE；本轮其 SKILL.md / LICENSE.md 原文抓取失败，故保留为次级候选，不能当宽松许可包登记。存在多个同名实现进一步说明不能仅用名字判断历史来源。

## w95 仓库额外核查

读取了 [完整 README](https://github.com/w95/awesome-claude-corporate-skills) 和 [INDEX.md](https://raw.githubusercontent.com/w95/awesome-claude-corporate-skills/main/INDEX.md)。在追加要求核对的 12 个标识中，库存表只有 `competitive-analysis`，路径为 `01-executive-leadership/competitive-analysis`，来源列为 Anthropic FSP。其余 11 个指定 slug 未列出；这是一项当前公开库存表观察，并非穷尽所有历史分支的不存在证明。

HR 库存的 9 个标识为 `job-description-writer`、`interview-kit-builder`、`onboarding-planner`、`performance-review-assistant`、`compensation-benchmarking`、`employee-handbook-builder`、`dei-strategy`、`employee-engagement-survey`、`resume-generator`，不能拿来替代 4 个精确 HR 标识。PRD 项为 `prd-writer`，不是 `prd-generator`。仓库 README 明确外部来源技能可能有自己的许可，因此复制的 Anthropic FSP 项应追溯官方 Apache-2.0，而非统一记录为 w95 根 MIT。

## 方法、建议与未知项

- 搜索仅提交公开技能标识，没有提交企业会话正文。每个指定标识至少使用精确名称搭配 `SKILL.md`、GitHub 或 ClawHub 搜索，并优先读取官方/作者仓库与作者发布页；每次搜索不超过 4 个 query。
- Web 的抓取失败只记录为该次取证失败，不等于资源不存在。未命中也不等于私有、原生、原创或无法从平台获取。
- 建议后续公开参考包固定 commit 或发布版本，保存完整技能目录和对应许可；2 个 ClawHub 项需复核实际包内文件与许可。公开包只用作新评测对照或待比对候选。
- `image-ocr` 候选来自 SkillsBench 特定任务 `jpg-ocr-stat` 的环境目录。它应单独标记为基准派生参考：不得把该任务的题目、样例、解答或评测文件纳入技能材料；若未来基准包含该任务或其衍生任务，应排除该参考或另建隔离对照，防止把任务定制知识混入评测。这是后续评测设计边界，不是已发生泄露的结论。
- 如果要复现企业历史使用，20 项仍应向平台索取实际使用包及版本/哈希、改造归属、依赖资源和工具契约；公开同名参考不会解除历史一致性未知。
- 这份补查不改变 2026-10-05 历史来源审计，也未将新的公开参考追溯为历史来源。与历史原包的内容比对、版本年代匹配及工具可运行性均未验证。
