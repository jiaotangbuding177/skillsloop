# 给 EvoMind 的技能原包和服务契约请求

日期：2026-10-06。范围为筛选后1224条真实会话，不要求重新跑历史任务或补造已遗失中间产物。

我们已自行下载有明确公开地址的参考包。请优先提供下列5项平台品牌/服务适配的实际原包，并明确来源；目前仅有品牌/适配证据，尚不能认证全部由EvoMind原创。

| 技能标识 | 用途线索 | 涉及会话 |
|---|---|---|
| image-generation | 平台图片生成服务调用 | 35 |
| evomind-paper-scan | 论文检索与研读的 EvoMind 适配 | 27 |
| pdf_zzz4ai | 平台 PDF 处理服务适配 | 17 |
| evomind-auto | EvoMind 自动研究流程 | 1 |
| zzz4ai-search-engine | 平台搜索服务适配 | 1 |

每项请交：完整SKILL.md、scripts、references、assets、许可证；当前可提供版本及SHA256（历史版本保留则额外提供）；Python/Node/系统程序依赖和版本；调用服务的非秘密接口说明、参数和返回样例、错误码及测试开通方式。不要把密钥写入导出包。说明与历史运行包的差异，不要求恢复不存在的历史版本。

图片/搜索/PDF/自动研究涉及专属服务时，仅有SKILL.md不足以执行。请提供可独立调用的测试接口或可本地部署的实现及依赖；无需默认交付整个kmagent源码。

以下实际包来源或获取方式尚未落实。请先按技能标识给一份来源表：平台原创、平台改造第三方、原样第三方、用户自建/系统生成及实际包拥有者。只有平台原创/改造包需要平台交原包；原样公开第三方请给准确仓库URL、子目录和commit，我们继续自行下载。个人自建包可由拥有者导出，请平台帮助定位。腾讯会议已有官方Skill说明，但须账号登录后获取，请走官方授权或已有合法包导出，不称EvoMind原生。列表不是“全部EvoMind原生”的认证，也不是要求全部成为评测前置条件。

| 技能标识 | 用途线索 | 涉及会话 |
|---|---|---|
| image-ppt-generation | 图片式演示文稿生成 | 39 |
| contract-review-cn | 中文合同审阅 | 7 |
| concept-verification-report | 概念验证报告 | 4 |
| emerged-job_description_learning | 岗位描述学习候选 | 4 |
| human-resources-recruitment | 招聘工作 | 3 |
| netease-mail-connection | 网易邮箱连接 | 3 |
| output-as-word | Word格式输出 | 3 |
| emerged-dfbadf6e297bf6de67a5e5d3 | 涌现命名候选，用途待原包确认 | 2 |
| human-resources-compliance | 人事合规 | 2 |
| human-resources-departures | 离职事务 | 2 |
| wechat-ai-publisher | 微信内容发布 | 2 |
| wecom-connection | 企业微信连接 | 2 |
| early-tech-investment | 早期科技投资分析 | 1 |
| emerged-12c473344e84b1c9d850c849 | 涌现命名候选，用途待原包确认 | 1 |
| emerged-38e6b2915d9c4b7588e54d37 | 涌现命名候选，用途待原包确认 | 1 |
| emerged-5833d138e66097ffbeb0de98 | 涌现命名候选，用途待原包确认 | 1 |
| feishu-connection | 飞书连接 | 1 |
| gx-brand-content-production | 品牌内容生产 | 1 |
| gx-tender-response-workbench | 投标响应工作台 | 1 |
| human-resources-performance | 人事绩效管理 | 1 |
| nsfc-research-content-method | 科研内容与方法撰写 | 1 |
| project-quotation | 项目报价 | 1 |
| qcc-company-connection | 企业查询服务连接 | 1 |
| tencent-meeting-mcp | 腾讯会议连接 | 1 |

已有公开参考的标识见本目录 skills_已下载公开参考.csv。请仅补其运行版本与上游对应关系；若有改造再补原包。不要用同名公开最新版代替历史运行版本而不说明。

另有3条脱敏技能读取/脚本记录：请按关联工具事件补真实技能标识映射；它们不代表已确认3种额外skills。来源锚点在 private/retained_skill_coverage.json，原正文无需再次导出。

优先级由将要执行的任务实际依赖决定，不把所有74项都列成必须先齐备。若执行最新单主题试跑方案的表格生成与核验，应先冻结可用表格基础技能、Python/Node库、公式计算及文件评分能力，不必等这5个专属服务全部到齐。若做合同/文档任务，则先确认contract-review-cn、contract-review（已有公开同名参考）、PDF/Word处理及产物交付依赖，再按其他主题扩展。
