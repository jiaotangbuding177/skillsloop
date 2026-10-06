"""Save this fixed, source-grounded supplemental semantic review; no APIs."""
import json
from pathlib import Path
R = Path(__file__).resolve().parent
root = R.parents[2]
selection = json.loads((R/'selection.json').read_text(encoding='utf-8'))
source = json.loads((root/'matched_066/private/evomind_conversations.json').read_text(encoding='utf-8'))
ranges = json.loads((R/'read_ranges.json').read_text(encoding='utf-8'))

# Manually authored semantic decisions. Rank is the frozen selection rank.
decisions = {
1: ('KEEP_CANDIDATE','LOCAL_REPAIR_IN_FAILED_SESSION','后续视频渲染仍然失败，但前段明确描述 JSX 与 .ts 扩展名不匹配、改名及编译检查。只保留编译准备的局部修订，不保留 OOM 根因认定或完整交付成功。'),
2: ('KEEP_CANDIDATE','METHOD_AND_MISSING_FIELD_BOUNDARY','项目整合正文中可见字段清单、缺项标注及最后再次列出的三个信息缺口；不把公司自述指标当核实事实。OCR 仅为提出的补充动作，执行是否完成未知。'),
3: ('KEEP_CANDIDATE','LOCAL_FORMATTING_FALLBACK','同一会话的人事判断未核实；独立的 PDF 制作请求则有 reportlab 不可用时改 Chromium HTML→PDF、检查页数及保留 HTML 源稿的具体处理。只保留文件封装方法。'),
4: ('HOLD','UNSUPPORTED_DATA_REWRITING','完整读取两次修改回复，主要将账单总量和人均值改到用户指定数字，并以“真实版”称呼；未见原账单依据、统计口径或可验证的数据计算过程。不得把数值造型当真实分析方法。'),
5: ('HOLD','DEPENDENCY_DIAGNOSIS_WITHOUT_OBSERVED_REPAIR','完整读取 ec-crm 两段诊断，依赖缺失、安装源 500 和企业账户限制均为 AI 汇总；未见对应检查命令回执或后续替代查询执行。技能安装声明与方法能力必须分开。'),
6: ('HOLD','CONTRADICTORY_TEST_REPORTS','同一批搜索测试前称知乎通过，后称知乎 400；未见稳定对应的请求、错误或修正。新闻汇总及安装声明不足以说明修复步骤。内部子代理运行上下文不当新用户任务。'),
7: ('HOLD','READ_FAILURE_NO_METHOD','法律评估和翻译都止于“PDF 是二进制不能读”及让用户粘贴、转换文件的建议，未见具体解析、OCR 或翻译处理。定时提醒只见创建回执。'),
8: ('HOLD','CONFLICTING_DELIVERY_CLAIMS','图片改风格出现 PPT/PNG/HTML 多轮交付自述和工具不可用说法；未见能消解失败与中文字体限制的具体实现。知识图谱技能建议及技能列表为另一目标，不能拼成制图成功轨迹。'),
9: ('HOLD','REQUIREMENTS_OR_PLAN_ONLY','单个用户输入提供开发改动点；回复列出六个工作项及修复方案，没有实际 Gitee 创建、代码修改或验证过程。可用于需求识别，尚不足作执行方法经验。'),
10: ('HOLD','DELIVERY_AND_PROPOSED_REVISION_ONLY','两版架构图回复主要给出布局、模块数量及复杂度对照；后续连线、颜色改动仍是提议，没有技术关系核验或实际修订证据。'),
11: ('HOLD','CONFIGURATION_CONTRADICTION','图片接口、密钥来源与默认模型说明前后纠正；最终承认接口不可用。HTML 替代图只见保存和场景描述，未见能复用的实际绘制步骤，不能固化平台能力判断。'),
12: ('KEEP_CANDIDATE','SOURCE_PRESERVING_AGGREGATION_AND_CHECK','完整回复中有多来源原话保留、重复需求保留多引用、冲突值待澄清、表头偏移后调整校验范围等局部方法。输入文件和最终表格未独立读取；22 条及 SUCCESS 都只能记为 AI 自述。'),
13: ('HOLD','ANALYSIS_OR_CONTENT_REVISION_ONLY','竞品、行情及战略文稿有大量事实与观点内容；资产分类的文字修订可见，但未呈现可复算取数、比较判断程序或核验过程。不能把战略看法包装成落地执行技能。'),
14: ('HOLD','UNEXECUTED_FEASIBILITY_PLAN','输入法皮肤的隐私方案、PRD 与视觉稿为方案和交付摘要；关键 ssf 多状态能力始终存疑，POC 被反复列为未来行动，尚不能学习关键词切换已可运行。'),
15: ('KEEP_CANDIDATE','LOCAL_KNOWLEDGE_INDEX_METHOD','Gitee 建任务未执行，保持未知；另一目标“初始化/整理知识库”出现待处理源清单、索引与日志、两篇带来源元数据的文章正文及链接。只保留知识组织流程，未认证文件写入或全库收录完成。'),
16: ('KEEP_CANDIDATE','OBSERVED_INPUT_GATE_BOUNDARY','真实请求为用模板生成周报；回复对旧基线、关注对象、时间范围与取数来源做缺口检查并暂停生成。保留输入检查及不编造变化的局部边界，补齐后的取数与周报流程仍是计划。'),
17: ('HOLD','IDENTITY_UNRESOLVED_AND_SOURCE_MISUSE','高校项目查询混入无关旧项目，用户明确要求不用现有工作区；随后只给公开检索未找到和方向推测。未锁定项目身份、未产生具体项目评审，不能学习确定对应或无公开信息即新公司的结论。'),
18: ('HOLD','SKILL_CREATION_AND_SYNTHETIC_DEMONSTRATION','完整扩读演示与三项测试总结，仍是技能创建/安装声明、按人工设置规则做的样例演示和自述基线对照；无真实学习资料执行或有依据的失败后修订。不得把宣称收益当评测结果。'),
19: ('KEEP_CANDIDATE','LOCAL_BROWSER_INTERACTION_PROTOCOL','安全试用、安装、删除及模型身份查询不连成一条方法；独立浏览器测试回复给出了打开页面、快照定位 ref、点击、等待、检查目的地址及关闭的具体序列。仅提取交互验证流程，不认证“全部通过”或跨工具修复成功。'),
20: ('HOLD','FAILED_FALLBACK_AND_FEATURE_ONLY_DELIVERY','新闻检索的浏览器/串行替代仍未取到资料；超级玛丽只见完成声明和玩法特色，没有实现步骤或纠正。两个目标分开，不能以游戏声明补全搜索失败。'),
21: ('HOLD','MISSING_CREDENTIALS_AND_SIMPLE_RECEIPTS','笔记导入停在缺 API 凭证，未见分页、去重、格式转换或批量导入；两个提醒任务只见创建回执。具体目标保留，但没有新的可复用处理经验。'),
22: ('HOLD','ENTITY_NOT_CONFIRMED','公司拼写经用户纠正后仍不能锁定真实主体；访谈与交易案例核验只为建议，没有对应核验输出。不能把搜索未命中、业务组合或推测风险当已证实企业结论。'),
23: ('HOLD','MULTITASK_SUMMARY_WITHOUT_EVIDENCED_METHOD','安装、视频、团队产出、课程作业及申报规划多目标混杂；主要是交付摘要，飞书安装也仍失败。未见能够从摘要复原的具体方法修订，不能把权限/网络猜测或申报时间表当已验证流程。'),
24: ('KEEP_CANDIDATE','PYTHON_INTERPRETER_DEPENDENCY_MISMATCH','卡片遗漏的短 AI 中明确指出 pip 安装到 3.12 而默认 python3 为 3.11，随后改用已有 requests 的解释器。只保留环境依赖匹配修订；图像质量、文件存在和最终成功未独立验证。'),
25: ('HOLD','BLOCKED_VIDEO_AND_UNSPECIFIED_INSTALL_REPAIR','前段安装的手动绕行没有具体参数或命令回执；教学视频因积分不足停止。未读取教案却使用模型熟知课程不是正确替代方法，充值与重跑仍为未来建议。')
}

definitions = {
1: dict(task='制作视频并交付时修正渲染前的 TypeScript/JSX 编译问题',lesson='在进入视频渲染前先检查源码内容和文件类型是否一致：含 JSX 却采用 .ts 时修正文件类型，再处理导入/路径并检查编译。局部编译修订与最终渲染结果分开记录。',u=['u_dae100032a1b1918aa'],a=['a_cc27e80fca9bd6a4c5','a_de48c603ab2d006779','a_9366536f5975a6d48a'],quote='TS 报错是因为 Root.ts 含 JSX 但扩展名是 .ts，改名修复。',limits='这是 AI 当时对编译原因和通过情况的正文报告，未核验源码及编译回执；完整视频后来仍渲染失败。137 不能单独证明 OOM，内存归因与飞书发送成功均未知。',outcome='局部编译通过为 AI 自述；最终视频交付未完成/未核验。'),
2: dict(task='将项目材料整理为统一字段的项目画像并保留信息缺口',lesson='按项目名称、主体、行业、联系人、电话、技术/融资/合作状态等字段逐项填写；正文中无法确定的电话、融资和合作方式显式标未提供或待确认，在最终交付中再次列出这些缺口，不补造答案。',u=['u_47cf6f42b2e10c480e'],a=['a_7d18499a612ec2d756','a_8f18ba4da66ab792e0'],quote='三个缺口需要你补充确认',limits='原 PPT/公司材料与整理文件未独立核验；公司指标及合作宣传不是认证事实。图片页 OCR 只见提出，不能记为已执行完成。最终缺项标注属于正文可见的方法，业务结果未知。',outcome='正文结构化交付和缺项标注可见；来源内容及实际采用未知。'),
3: dict(task='将正式内部文稿封装成 PDF',lesson='主 PDF 库不可用时选择当前可用的 HTML→PDF 引擎；生成后检查可识别页数，保存 HTML 源稿以便继续修改。只迁移文档封装处理，不迁移未经核实的人事/法律判断。',u=['u_e1fec489d83ea028cd'],a=['a_24ce6ec9bb759553ea','a_d6dbe2a68d9a555547','a_6ac2809e0d8c0c8ced'],quote='当前环境没有 reportlab，我改用 Chromium 的 HTML→PDF 方式生成，中文排版会更稳。',limits='环境依赖缺失、3 页生成与保存均为 AI 自述；未读取 PDF/HTML 或执行日志。不得将试用期解除建议的合法性视为已验收。',outcome='替代引擎及页数检查在正文中明确；文件有效性与业务处理未知。'),
12: dict(task='合并多份客户需求为带来源的统一技术需求表',lesson='逐条保留客户原话，合并重复需求时保留多个来源引用；冲突参数和缺失验收条款标待确认，不自动确定满足度。检查完整落表、来源编码和原话，若元数据导致表头下移，则依实际表头调整校验范围。',u=['u_fa62d046b82c33f4b7'],a=['a_ab415b8aee6c528d3f'],quote='表头在第 12 行（元数据区之后），调整校验范围重跑。',limits='方法从单条 AI 回复抽取，三份附件与生成文件未读取，22 条计数、SUCCESS、保存和权限均是 AI 自述；项目编号/来源真实性未独立认证。组织批准、报价、产品满足度及正式共享均未知。',outcome='方法与待确认边界可读；生成文件、完整性和业务交付未独立核验。'),
15: dict(task='初始化并整理个人知识库的源文件、索引和文章',lesson='建立主题/实体/概念索引、操作日志和待处理源清单，扫描文件后更新待处理队列；源文整理为文章时保留来源元数据和关联链接，并同步索引与日志。文章正文是知识内容，不能自动升级为经实践验证的方法。',u=['u_6754b99cca46f2c160','u_d3518bc10583b170f2'],a=['a_c5126ef34dd3aa4b4b','a_a5025a581da4920e1c','a_cf12fb8dd87ffd3bb0','a_83857c94778d6bfc1a','a_443eafb974ec26d28c','a_f91aec96321279a3fe','a_9c2340c10011329c2c'],quote='更新了 Unprocessed Sources，新增 18 个文件',limits='只保留知识组织片段；源文内容的心理/商业断言未认证。AI 的文件创建及数量为自述，文章末段及索引更新文本不完整；Gitee 创建未执行，不与该片段合并成功。历史时间与完整回合顺序未认证。',outcome='两篇文章及来源格式、索引队列方法在正文可见；落盘和全库处理未知。'),
16: dict(task='用既有模板生成行业与竞品周报时处理输入不完整',lesson='先确认本期范围、关注对象、上期已确认基线和真实取数来源；模板本身不能支撑可复算的新增/变化比较。缺基线与来源时明确暂停，列出缺失项及补交位置，禁止凭模型记忆补成当前新闻。',u=['u_5985e7d092e98f0ef6'],a=['a_03c0fd56d937ec742f','a_5fe8680eedeac8bae5'],quote='没有上期周报、竞品档案或任何情报素材，无法支撑真实取数和 Diff 对比。',limits='工作区确实只有模板及缺项检查的执行均为 AI 自述，未核验目录/工具回执；可见的是当时按缺口暂停的边界处理。补齐后取数、周报生成和下游流转都是计划，未发生验收。',outcome='输入缺口及暂停回复明确；未生成完整周报，后续补齐与效果未知。'),
19: dict(task='测试浏览器自动化的元素交互及导航结果',lesson='打开页面后获取交互快照，通过快照中的元素引用选择链接并点击，等待加载后检查目的地址，再关闭浏览器；区分已演示的导航操作与尚待测试的表单、录屏等能力。',u=['u_dcd77f3d34a17c022a'],a=['a_e74e473269c3bfdb74'],quote='3. 点击 @e2 (Learn more 链接)\n   ↓\n4. 等待页面加载\n   ↓\n5. 验证导航 → 跳转到 iana.org',limits='流程和示例结果来自 AI 测试总结，未读取浏览器工具回执或截图，不能认证“全部通过”。不能据此认定 browser-use 的故障已被 agent-browser 修复；不迁移安全试用、安装或删除声明。',outcome='交互验证序列在正文可见；实际执行与截图、跨工具替代成功未知。'),
24: dict(task='生成图片时修正 Python 多解释器的依赖错配',lesson='遇到缺 requests 后，不只看 pip 安装成功；核对安装目标 Python 与执行脚本的 Python 是否同一环境。已经装到 3.12 而默认 python3 为 3.11 时，改用具备该依赖的解释器执行，并单独检查产物尺寸。',u=['u_c4b4027567fd16cd83'],a=['a_4c81552bbef52d428e','a_3e5018cfdd12396a9e','a_c57c885ccea549e9b5','a_90ba5b9040aa5124df','a_142deb0b5280dff903','a_187a70925a9fc94d5f'],quote='pip 装到了 Python 3.12，但默认 python3 是 3.11。检查一下：',limits='解释器诊断、请求发出及图像结果均是 AI 当时的正文自述，未核验命令日志或实际图片；不能认证视觉质量、物种识别或文件已保存。输出像素尺寸是否达用户的 4K 要求也未验收。',outcome='依赖错配与换解释器修订明确；图像生成、尺寸及视觉质量未独立核验。')
}

reviews, candidates = [], []
for rank, selected in enumerate(selection['sessions'],1):
    sid = selected['session_id']
    decision, code, reason = decisions[rank]
    row = {'review_id':sid+':supplemental-review', 'selection_rank':rank,
           'session_id':sid, 'original_decision':'HOLD',
           'recommendation':decision, 'reason_code':code, 'reason':reason,
           'review_basis':'targeted_original_group_review',
           'evidence_scope':'所有组的开头及有限诊断/修订位置；候选依据组按 read_ranges 定向扩读。长正文不宣称全读。',
           'read_ranges':ranges[sid], 'candidate_ids':[],
           'reviewer_type':'AI语义复核，非人工黄金标签',
           'chronology_verified':False, 'execution_verified':False}
    if rank in definitions:
        d = definitions[rank]
        users={g['group_id']:g for g in source[sid]['user_requests']}
        ais={g['group_id']:g for g in source[sid]['assistant_contents']}
        assert all(x in users for x in d['u']), (sid,'user ids')
        assert all(x in ais for x in d['a']), (sid,'assistant ids')
        assert any(d['quote'] in ais[x]['content'] for x in d['a']), (sid,'literal quote')
        c={'candidate_id':sid+':supp01','session_id':sid,
           'task':d['task'],'learning_candidate':d['lesson'],
           'evidence_quote':d['quote'],'limitations':d['limits'],
           'source_user_ids':d['u'],'source_assistant_ids':d['a'],
           'review_basis':'expanded_supplemental',
           'original_decision':'HOLD','supplemental_review_id':row['review_id'],
           'qualification':'AI补漏复核的有条件学习候选，未认证为完整黄金轨迹或有效技能',
           'outcome':d['outcome'],'chronology_verified':False,
           'execution_verified':False}
        candidates.append(c)
        row['candidate_ids'].append(c['candidate_id'])
    reviews.append(row)
assert len(reviews)==25 and len({r['session_id'] for r in reviews})==25
(R/'supplemental_review.json').write_text(json.dumps(reviews, ensure_ascii=False, indent=2),encoding='utf-8')
(R/'supplemental_candidates.jsonl').write_text(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in candidates),encoding='utf-8')
print(json.dumps({'reviewed':len(reviews),'keep_candidates':len(candidates),'hold':sum(r['recommendation']=='HOLD' for r in reviews),'literal_quotes_and_ids':'passed'},ensure_ascii=False))
