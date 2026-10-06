"""Replace existing method sections; do not append an upgrade diary to the paper."""
from pathlib import Path
import re
root=Path(__file__).resolve().parents[3]
reports=root/'research/reports'
source=reports/'022_论文概念文档.md'
text=source.read_text(encoding='utf-8')
archive=reports/'022_论文概念文档_v2_archive.md'
if not archive.exists(): archive.write_text(text,encoding='utf-8')
body=(reports/'025_technical_supplement.md').read_text(encoding='utf-8').split('## 八、',1)[1]
text=re.sub(r'## 八、.*?(?=## 十、)','## 八、'+body+'\n\n',text,flags=re.S)
text=text.replace('论文概念文档 v2 · 技术补充与Industry对标','论文概念文档 v3 · 多轨迹归纳与企业技能演化')
text=re.sub(r'^> v2更新：.*\n','',text,flags=re.M)
text=text.replace('当前通过词法与引用规则关联，拟进一步以增量索引和证据机制完成整理与去噪，再根据方法增量决定新建、更新、仅保留支持证据或延期处理。',
    '通过引用规则组织任务，按成员和技能版本隔离轨迹，以词法complete-link聚类形成学习池；成功、失败和未知结果分别提出有来源的方法修改，经多轨迹归纳与宿主校验应用，形成新建或更新候选，无增量和证据不足分别记录支持或延期。')
text=text.replace('原始运行记录丰富于当前学习输入，二者差距见第八节。','聚类、三类分析角色与受控patch应用已接入；语义归纳、长期收益与资源目标的边界见第八节。')
text=text.replace('### 3. 判断“有无方法”以及“是否值得现在沉淀”','### 3. 筛选方法材料，并聚合兼容的独立任务')
text=text.replace('先排除没有方法信息的材料，再检查精确重复与新增条件。高频应按独立任务发生次数计算，不按同一任务纠正了几轮计算。重要性要结合业务影响和角色优先级，不能由出现频率替代。',
    '先识别方法材料与可诊断失败，再检查精确重复。NEW在同成员内按规范化目标进行complete-link聚类；UPDATE按实际技能及基准hash聚池。默认每池最多8条独立任务，等待120秒吸收后续材料，单例到期也处理。同一任务多次纠正不算高频，聚类也不自动赋予共享权限。')
text=text.replace('### 5. 生成可审查的技能候选','### 5. 分角色提议，跨轨迹归纳，应用局部修改')
text=text.replace('只有通过筛选的NEW/UPDATE进入模型提炼。NEW抽象可复用方法，UPDATE只修订有证据支持的部分，并保留原包未涉及的文件与有效规则。候选应保留来源引用、适用范围、未知结果与版本依据，不能将半成品口吻改写成确定事实。',
    'NEW/UPDATE的冻结轨迹池进入OpenClaw。成功分析器提炼步骤，失败分析器检查原因和修正依据，未知结果分析器保留明确用户规则；各自输出方法提议，再合并重复和互补经验。宿主检查引用、全部提议归属、基准hash和修改锚点，实际应用add/append/replace，最后用官方skill-creator封装。没有验证的失败原因只延期，不作为确定规避经验。')
text=text.replace('条目级失效机制另见图5','多轨迹归纳及受控修改见图5')
text=text.replace('| 技能候选 | 提炼核对期间、处理退款、汇总与检查步骤 | 生成方法，而非记住这周具体金额 |',
    '| 技能候选 | 将多次同类任务中的期间、退款和订单状态经验共同归纳 | 去掉重复、保留互补条件；每条修改有依据 |')
text=text.replace('当前 SkillsLoop 是一个由规则状态控制、LLM 技能编写和可追踪执行组成的系统原型。',
    '当前 SkillsLoop 是由可修订轨迹、范围约束聚类、分角色分析与受控patch应用组成的系统原型。')
text=text.replace('它已经支持版本管理、技能封装、实际读取和反馈回流；方法价值判断、证据归纳、语义差分和旧能力保持，目前仍主要依靠启发式规则与模型提示，尚不足以证明独立的算法贡献。',
    '它具备多轨迹归纳与可执行修改契约，并接通封装、真实消费和反馈回流；语义归纳仍依赖模型，旧能力保持及企业净收益尚待独立评估。实现更完整不自动证明原创贡献。')
a=text.index('## 十一、');b=text.index('## 十二、',a)
text=text[:a]+'''## 十一、技术实质与研究边界

| 维度 | 当前机制 | 仍需证据 |
| --- | --- | --- |
| 任务与聚类 | 引用和词法关联，NEW完整链接聚类，UPDATE实际版本聚池 | 真实任务召回、误合并、语义不同表述 |
| 证据一致性 | 多来源hash，迟到修订阻止采纳，未变化来源重新排队 | 已发布条目的局部撤销与方法保留 |
| 经验提炼 | 成功/失败/未知角色，来源原文引用，假设延期 | 归纳正确性、失败诊断的独立验证 |
| 修改执行 | 提议全覆盖，局部操作，基准与唯一锚点校验，官方封装 | 语义矛盾和旧能力退化 |
| 资源 | 等待聚池、统一学习额度、幂等运行和用量记录 | 同预算优势、内部token硬限制和现金费用 |
| 工业证据 | 可运行原型及构造数据功能验证 | 企业工作负载、真实员工及长期净收益 |

### 11.1 模型负责什么，代码保证什么

模型负责从证据解释方法、判断条件、提出修改并作跨轨迹归纳。代码负责材料与版本隔离、聚类门槛、引用存在性、提议处理完整性、局部修改应用、过期拦截和审批。来源引用有效不证明语义推导正确，格式验证不证明业务能力保持。

因此，当前技术超出单次文本prompt：同一模型输出可能因不存在的引用、遗漏提议、过期基准或冲突锚点而被拒绝，其修改必须经过宿主实际应用。但这些控制机制单独并不新颖，仍需证明它们在企业可修订会话下带来的可重复净收益。

### 11.2 与Trace2Skill的关系

逐轨迹patch、成功/失败分工和many-to-one合并借鉴Trace2Skill，应在论文中明确归因。当前选择一次Agent派发内的批量角色分析与小池归纳，补UNKNOWN和迟到修订处理；没有复现其独立并行子Agent与多层merge，也没有新增模型训练。不能将同一机制重新命名作为创新。[Trace2Skill方法](https://arxiv.org/html/2603.25158v5#S2)

### 11.3 原创性仍由什么决定

AutoSkill已覆盖交互经验提取和持续维护；Trace2Skill已覆盖轨迹归纳。差异应落在证据会被撤销、结果未知、无额外用户标记操作和学习预算受限时的方法保留策略。完整会话强摘要、强批量摘要和近邻适配必须作为对照；若效果相当，应缩小机制主张。

'''+text[b:]
text=text.replace('| P1 机制落地 | 条目依据、依赖索引、局部失效、方法差分规范 | 每次保留/撤销/更新能回溯到源事件；歧义明确延期 | 超出整段prompt的技术实质 |',
    '| P1 机制深化 | 在已有聚类、提议和patch应用上补局部撤销及独立诊断验证 | 修改来源可回溯；未失效方法保留；假设和结果分开 | 新增机制是否产生额外收益 |')
text=text.replace('## 本轮参考来源与核查位置','## 参考来源与实现依据')
text=text.replace('本轮未改demo代码、未调用付费模型、未新增企业实验。以上文献评估与技术建议不等于效果实证。',
    '当前多轨迹实现见learning.py、MULTITRACE_SPEC.md及测试记录；历史024数字不作为新算法效果。文献评估和功能验收不等于企业效果实证。')
text=text.replace('作者摘要及版本记录；仅用于近邻范围定位。\n\n本地技术依据','方法第2节及版本记录；用于界定借鉴机制和实现差异。\n\n本地技术依据')
source.write_text(text,encoding='utf-8')
# The canonical source must remain authoritative; never regenerate it from v1.
builder=root/'research/figures/025/build_report.py'
code=builder.read_text(encoding='utf-8')
start=code.index("source=REPORTS/'022_论文概念文档.md'")
end=code.index('# --- Chinese publication layout ---',start)
code=code[:start]+"source=REPORTS/'022_论文概念文档.md'\ntext=source.read_text(encoding='utf-8').replace('<ama-doc>','').replace('</ama-doc>','')\n\n"+code[end:]
code=code.replace('RESEARCH CONCEPT 02','RESEARCH CONCEPT 03').replace('概念讨论稿 v2','概念讨论稿 v3').replace('研究讨论稿 v2','研究讨论稿 v3')
code=code.replace('实线图示已有原型；虚线图示研究建议。','聚类、分角色分析和局部修改已接入；收益仍待评估。')
code=code.replace('输入、状态、候选路由、真实执行与版本回流','轨迹聚类、成功/失败分析、Patch归纳与真实复用')
builder.write_text(code,encoding='utf-8')
print('Replaced canonical method sections and switched PDF builder to canonical source.')
