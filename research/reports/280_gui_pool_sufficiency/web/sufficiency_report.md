# 50 Web评测构型与演化来源充足性审计

日期2026-10-04。范围是全部50 Web的公开首页身份和公开reference文件名，加10个代表性正常public HTML结构；没有读取tests/gold，没有运行候选源码、浏览器行为、模型、采轨迹或评分。37条旧映射不是250题覆盖率。

## 更正来源口径

根线程核对论文§4.2及C.3：50 Web为**44合成reference＋6公开网站**，合成构型包括dashboard/catalog/booking/checkout/mega-menu。与本地50 ID核对一致，6公开站是climatewatch.org、detox.github.io、keycloak.org、postgresql.org、rust-lang.org、webpack.js.org。因此279将.example整体解释为“匿名原始商业站”的说法过于保守，应更正：不能假设44题都存在未披露商业原站。共享模板/组件近重复仍未知，独立来源隔离依旧要审计。旧279报告保留，本轮作明确更正，不静默重写历史。

## 哪些依据支持缺口

[web50_capability_hints.json](web50_capability_hints.json)逐项列全50 ID、原public path样例和重叠的关键词构型线索。它们是文件名线索；例如book/event路径不自动证明实际预约流程，多页面数量也含cdn快照。**不输出来源池覆盖百分比**，不据此宣称所有私有测试已覆盖。

[public_web_structure_audit.json](public_web_structure_audit.json)实读10份正常reference HTML并仅保存结构/hash摘要。sonelio公开account-register含4个text、2个password、1个email、country select和3个required输入；aperlio首页有搜索form；sentorra首页有搜索form、public inventory有content-type＋topic组合query路径；climatewatch首页存在数据控制结构。它们支持“多字段校验/条件列表/数据视图是不可忽略的构型”，但未执行JavaScript，不把静态标签当已观测动态行为。cresvia的goals-quiz路径仅有名称，静态HTML没有input，不能据其路径伪称已经确认多步交互。

原4Web素材覆盖本地文件/图像异步处理（Squoosh）、菜单画布和撤销（miniPaint）、文档导航/编辑/持久化（StackEdit）、内容多路由/目录/锚点（Vite docs）。Vite首页亦有产品宣传布局，但**原4项没有明确的独立多步表单负校验＋多条件列表保存素材**。无需按50题数量复制50个应用；按构型补一个有真实本地逻辑的独立GUI即可形成首批更均衡来源池。

## 最小补项：Actual Budget

[Actual Budget v26.9.0 release](https://github.com/actualbudget/actual/releases/tag/v26.9.0)固定commit `59fe126f637d858c061e1eeedbef5436c8f2225a`。[完整MIT](https://github.com/actualbudget/actual/blob/59fe126f637d858c061e1eeedbef5436c8f2225a/LICENSE.txt)已保存并核对；其固定root/web package提供Yarn workspace、browser启动/构建，React/Vite和sql.js核心。不是只展示控件的UI套件。

官方[本地安装说明](https://actualbudget.org/docs/install/)有server-optional client和browser-local保存路径；这里只用合成预算、关闭bank sync和云集成，必要静态服务或原生插件服务均限loopback。仍须实际验证固定release的离线浏览器核心、WASM/worker与数据保存；文档不等于运行成功。

拟议流程与验收：

1. 本地Add Account步骤→空/重复name→type/on-budget/balance→保存重开。独立复刻字段依赖与反馈，验收拒绝无效名字、不多建记录、侧栏与金额一致；固定公开`accountValidation.ts`已确认trim、空名及重复名反馈，[账户文档](https://actualbudget.org/docs/accounts/)支持多步骤字段，但UI准确行为待准入。
2. 合成交易fixture→日期＋类别组合条件→命名保存→clear→重新应用。复刻条件—列表—合计关系，验收预定行集与重置/保存逻辑。[官方过滤说明](https://actualbudget.org/docs/transactions/filters/)支持组合与保存；不要擅自加入该版本不支持的排序行为。
3. 修改日期/金额→切换账户和报表/预算视图→时间边界→窄视口返回。验收所选context、数字/日期与数据一致；详细控件必须经公开观察后冻结。

预期素材是**agent观察→原创代码实现→自查/真实失败修正**的完整轨迹；不能将研究员写的上面建议直接当技能产物。三轮含首次上限保持。

## 暂停继续扩充的依据与仍未证明事项

补Actual后Web为3工具＋1文档＋1表单/数据流程应用，关键通用构型已有来源侧代表，建议**停止继续搜Web来源**，先把这5项实际准入与流程验收完成。不是宣称独立训练能通过全部50题；booking/checkout的特定业务规则、地图/图表绘制等仍可能失败，但当前无需以猜测私有测试为由不断扩充。运行后若出现整类“参考可用而演化素材完全缺失”的证据，再另开版本小幅补源。

Actual与200native canonical repo和50公开身份无明确重合；44synthetic仍需template/共享代码近重复检查，但不追查虚构的商业原站。本轮模型/运行/轨迹/技能为0，不恢复旧267 STOP，不改其他聊天服务。

机器化补项：[supplemental_candidate.json](supplemental_candidate.json)。固定证据：[actual_fixed_source_evidence.json](actual_fixed_source_evidence.json)。来源实际归档由根线程统一记录；运行accepted仍0。
