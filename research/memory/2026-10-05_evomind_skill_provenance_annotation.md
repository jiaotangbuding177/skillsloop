# EvoMind技能来源与安装归属标注

日期：2026-10-05。科研数据审计；未开发应用、安装技能或连接生产。

## 用户已确认要求

在上一轮技能清单上进一步区分：用户自行下载纳入并使用的开源技能，以及需要向EvoMind取包的系统原生技能。

## 证据支持的观察

- 覆盖既有81标识，74明确运行目录，原统计不变。逐项检查消费路径、返回文档来源/许可、全量会话短安装请求、本地API内置catalog和官方仓库页面。
- 按当前本地catalog精确匹配20内置标识；27其他共享部署；34个人/工作区/路径未知。这是配置和部署观察，不是原创归属，也不认证历史生产配置。
- guizang-ppt-skill、follow-builders、nuwa-skill、AutoEvoSkillCreate共4项有明确用户公开仓库安装请求及标识消费证据；只有follow-builders请求者与消费用户一致（不同会话）。无完整安装成功/版本/顺序链条认证，不能称4项均“用户下载后自行使用”。前三项当前官方网页可读，许可AGPL-3.0/MIT/MIT；AutoEvo网页读取失败，许可未知。
- agent-browser返回文档直接指向Vercel仓库。pdf/docx/pptx/xlsx返回Proprietary，官方将文档包归为源码可见非开源；未完整包比对。frontend-design/ui-ux-pro-max仅同名公开候选。合计11有公开参考地址，不等于11已确认开源。
- evomind-paper-scan、image-generation、pdf_zzz4ai、evomind-auto、zzz4ai-search-engine为5项平台品牌或服务适配候选，优先向EvoMind补包；不能认证全部原创。5个emerged标识生成来源待核，60其余来源未确认。

## 建议与未知

来源、平台内置/部署和安装者三轴标注，避免强行二分。70项没有已定位的公开参考地址，应平台/用户补包；11项可取参考版，历史重放仍需要81项实际版本及hash/许可。KM接口及平台表沿用已审计补交路线；线上schema、历史可用性、作者、安装者、版本、完整日志均未知。未观察安装不证明没有安装。

## 产物与核验

- [来源报告](../reports/2026-10-05_evomind_skill_provenance.md)
- [81项CSV](../datasets/evomind/km_skill_audit_20261005/skill_provenance.csv)
- [私有查看页](../datasets/evomind/km_skill_audit_20261005/private/provenance.html)
- 来源标注JSON、summary、manifest及可复算脚本位于同目录；原工具索引/消费会话、安装请求组ID可回查，记忆不复制私有正文或凭据。
- 运行81唯一覆盖/CSV与JSON一致/源索引有效/页面本地链接/旧统计源hash检查，结果见provenance_verification.json；无新效果实验、模型调用、生产请求或上传。

本轮新增来源证据观察，不新增算法收益结论。下一步由数据方按报告补来源manifest和实际技能包，再提升待核标签；不把公开当前版本当历史版本。
