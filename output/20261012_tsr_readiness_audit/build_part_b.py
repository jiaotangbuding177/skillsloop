"""Read-only contract audit. Does not change benchmark or validator implementations."""
import collections
import hashlib
import json
from pathlib import Path

ROOT = Path('D:/skillloop/benchmark/enterprise_input_closed_v11_20261012/evaluation/validator_suite')
OUT = Path('D:/skillloop/output/20261012_tsr_readiness_audit/part_b.json')

# Manually reviewed against every complete user_source_texts sequence in this shard.
# Additional findings beyond the common unstructured-body acceptance issue.
MANUAL = {
 'conv_0862474221d5': [('delivery1:check1', 'document_noncompliance', 1, '安装 https://edu-skillhub.zzz4ai.com/skill/teacher/edsby-grades-board-2', '目标参数只有edsby / edsby-integration子串提示，没有冻结用户指定的grades-board-2来源或包身份；处理器以任一提示子串搜索目录，也接受直接绑定目录。', '独立记录下载来源及实际包身份，将指定链接对应包身份与最终目录关联；不要求真实业务登录。')],
 'conv_1344d32a1970': [('delivery1:check1', 'document_noncompliance', 2, '本协议签署完成后10个工作直接一次性支付完全部股权转让款', '只核非空，签署后10工作日、一次付款、付款日后工商变更配合等用户明确要求完全没有基本字段检验。', '对当前最终条款分别确认明示期限/起算事件/一次付款及工商配合条款的交付字段；不判断法律效力。')],
 'conv_19d90530d45a': [('delivery1:check1', 'document_noncompliance', 9, '股东有谁，主要管理人员给我', '多项独立企业/人物/产品查询共用一个文字对象和非空点；实现默认返回匹配轮次的最后回复，不能证明各独立结果交付。', '只在完整会话终态逐个核独立必要答复是否有对应结果正文；更正同一对象只取最终版。'), ('delivery4:check1', 'document_noncompliance', 28, '会议纪要，主要写商业模式、销售情况、利润、竞争力', '已有会议纪要文字对象只核非空，明确列出的四个内容组成部分未列结构要求。', '逐项核四个部分有正文或明确缺资料说明，不核事实/利润值准确性。')],
 'conv_271afc5da7d7': [('delivery4:check1', 'document_noncompliance', 4, '法定代表人和统一社会信用代码', '企业查询结果只有末尾文字非空，用户明确的法定代表人/信用代码/注册资本/成立日期/状态字段没有覆盖。', '检查实际检索答复包含各请求字段或明确未公开/未检出状态，不硬编码历史AI值。')],
 'conv_29325dd2d985': [('delivery1:check1', 'document_noncompliance', 1, '我写了一个邮件…我还需要给冯发消息吗', '邮件沟通草稿与微信执行人员消息建议合并成一个非空对象；只最后一段不等于两项独立文本均交付。', '分别绑定最终邮件文案及微信沟通答复，不要求实发邮件或微信。'), ('delivery3:check1', 'mechanical_scope_limitation', 15, '把下面的内容整理成一个文件', '文件可开证明实际载荷，但未对用户提供市场测算正文保留或必要组成字段做检验。', '可冻结用户正文的必要小节/数值表示并核基本保留；估值/市场合理性仍不评分。')],
 'conv_2a6e0203ce09': [('delivery2:check1', 'document_noncompliance', 9, '60例为本中心最大计划入组…超入组必须取得甲方书面确认…全部费用按实际发生病例结算', '三份Word数量/修订痕迹有检查；后续文字条款只有非空，明确60例、付款安排等字段没核。', '对最终文字条款预先列必需组成字段；避免将法律结论或风险质量硬评分。')],
 'conv_2d85bcabcb65': [('delivery1:check1', 'mechanical_scope_limitation', 2, '手机、电脑、浏览器都能打开，是2D跑酷', '当前HTML/ZIP原生可开不证明交付入口能在浏览器加载；但不宜由源码文本断言游戏功能正确。', '至少实际加载入口并核可访问和非空渲染；手机适配/可玩性留质量或另项，不升级为代码质量门槛。')],
 'conv_383a91943829': [('delivery1:check1', 'document_noncompliance', 1, '包括项目简介、技术优势、产品图片等内容', '非空不能确认明示的内容组成部分，且没有处理产品图片是否真实提供或明确图片位置说明的分支。', '冻结最低一页内容稿的三个组成部分和图片的接受形式；不强制用户未明确要的PPTX。')],
 'conv_3ae75a94697f': [('delivery1:audited1', 'document_noncompliance', 1, '预测期5年…WACC取12%，永续增长率3%，输出估值区间和敏感性表', '已有任意非空表格检查，但估值区间及指定假设字段未核；无关表格可满足此点。', '检查有可解析估值上下界/区间和敏感性表对象，明示假设字段5年/12%/3%等与输入对应；不核DCF计算质量。')],
 'conv_470d66397a7d': [('delivery1:audited1', 'document_noncompliance', 2, '内容：金桥吴彦祖，位置斜角铺满，透明度20%', '真实新增水印文字已覆盖，但透明度20%作为明确数值被ignored；图形状态参数可读取时属于基础参数而非美观。', '仅对原生可证的透明度20%核验，位置/覆盖若不可客观确定则明确受限，不以文字出现证明斜角铺满。')],
 'conv_4be7342d0195': [('delivery3:check1', 'mechanical_scope_limitation', 8, '帮我把这些都做到记忆里面', '有真实记忆文件读取，但本合同未启用new_or_changed_since_attempt_start，不能凭它确认这些新业务信息已进入记忆。', '保留同attempt初始/最终记忆快照及本源记录关联；不核叙事质量。')],
 'conv_53da91aa300a': [('delivery1:check1', 'document_noncompliance', 4, 'ctc材料是什么', '四个不同咨询结果被合为一个正文对象，默认只取最后一条匹配回复，不证明其余三项咨询答复交付。', '分开四个必要答复的终态对象，内容正确性不评分。')],
 'conv_69d3e6ed7587': [('delivery1:check2', 'document_noncompliance', 7, '入口点击左下角头像->购买套餐；Plus259/3000万/10GB；Pro359/6000万/20GB；补充包', '字段只做无位置字面集合，未覆盖入口变更及1000W/2000W补充包、资源包叠加月包的粗体提醒、最终要求恢复图片。', '按套餐/入口/提示段绑定必要字段；核图片可加载和提醒为粗体，已掩码价格不设期望。'), ('delivery2:check1', 'mechanical_scope_limitation', 8, '将html页面转成pdf文档', 'HTML和PDF分别可打开，不核它们是同一最终指南的转换结果。', '用当前HTML到当前PDF的独立转换来源及基本内容对应证据，仍不评排版质量。')],
 'conv_6f49be523ffa': [('delivery3:check1', 'document_noncompliance', 7, '把下面的提示词写成一个md', 'MD只非空可打开，没有核给定prompt文字的基本保留，非空其它MD也可通过。', '核用户给定prompt的规范化正文保留及明确输出格式语句；不检学术判断准确性。')],
 'conv_80ce11dd162c': [('delivery1:audited1', 'document_noncompliance', 4, '主要修改第四第五章以及培训定位…其他章节不要修改', '已有一二三六章与用户基线对照点，却被标mandatory=false；AND忽略其失败，因此明示保留要求并未约束成功。', '在基线确知的本源上将未修改章节的客观保留检查列必需，第四第五章语义质量仍不评分。')],
 'conv_8e2e43b43eb2': [('delivery2:audited1', 'mechanical_scope_limitation', 6, '三部分…AI能力自评、应用瓶颈、老板助手期待；问卷星导入格式', '三段、题型、跳转和≤8分钟已有检查；三个主题与问卷星实际可导入性未核，结构合格不认证导入成功。', '可核三主题字段和对应原生导入格式的最小语法；不评分题目设计质量。')],
 'conv_90e543b2e886': [('delivery1:check1', 'mechanical_scope_limitation', 4, '最近几天的会话自己去学习', 'final_state_readback只读任何状态文件/任意非空读回，无memory目标、变更基线或近期会话关联条件。', '指定当前实验记忆对象及初末快照来源；不要求用户未提出的未来定时任务。')],
 'conv_965cf7b2c858': [('delivery4:check1', 'mechanical_scope_limitation', 6, '把他们拼成一份PDF', '图片数有冻结prompt清单和至少4张约束，但PDF只可开，没核PDF收纳对应逐页图片及数量。', '核当前已交付页图清单到PDF的真实装配来源和覆盖，不硬设历史页数。')],
 'conv_a8922f4056c9': [('delivery1:audited4', 'document_noncompliance', 3, '新增FDE驻场费…数据脱敏需要依托自部署大模型，部署费用、设备费另计', '明示新增收费/脱敏/另计费用条款只列观测，处理器还scorable=false。已有数值点不能证明这些必要合同组成部分交付。', '核可确定的四个独立收费/备注字段组成及来源绑定，语义法律效力不评分；2000人日表述未消歧不得自造数值解释。')],
 'conv_add3892808ba': [('delivery1:check1', 'document_noncompliance', 2, '帮我做两套实施路径…方案1…方案2', '没有两套独立方案或两个分节结构的校验，单一短句即满足非空。', '核两套路径的独立正文对象/分节，不判断法律风险质量。')],
 'conv_b90e515e92ec': [('delivery3:check1', 'document_noncompliance', 15, '她占股50%，我占股40%，留10%给期权池和其他资源方', '合作协议正文只非空，已经明确的股权分配比例与主体对应没有基本字段验证。', '在最终合作协议核三方/池的50/40/10字段对应，不核股权结构优劣。')],
 'conv_bef70ee7b697': [('delivery1:check1', 'document_noncompliance', 1, '在IMA中查找AI产品经理笔记，标注最后更新时间/按时间排序', '既没有真实查询终态读回也没有更新时间/排序结构；允许未命中但未核确实查过对应目标。', '读独立查询结果的目标及命中/未命中状态；命中时核时间字段和声明采用的排序分支，不强制同时清单摘要对比三份。')],
 'conv_c08aefce64c5': [('delivery2:check1', 'mechanical_scope_limitation', 4, '把图中的爱心变成别的颜色', '可解码新图不证明爱心颜色改了；核心对象识别和局部颜色属于图像语义边界，不能用总图像SHA变化替代。', '本基本TSR标明只验图片交付；可独立提供已确认区域的颜色变化规则时再机械核，不强加未确认ROI。')],
 'conv_c73acc83eff3': [('delivery1:check1', 'mechanical_scope_limitation', 1, 'HTML样式PPT…检测糖类、脂肪、蛋白质', 'HTML可开不证明包含幻灯片结构或三类实验组成；后轮只是读现有HTML，不应强行另产新版。', '核已要求HTML幻灯片的最小结构和三种实验栏目；末轮无需擅自修改。')],
 'conv_e2f318f3b6fb': [('delivery1:check1', 'document_noncompliance', 1, '丰蕾信息科技介绍；下一轮研究国泰新点软件', '两个不同公司独立结果共用一个非空对象，默认只核最后回复，可能遗漏第一家公司。', '分别在会话终态核两家公司的当前查询结果正文，不判真实性或深度。')],
 'conv_fbed0e8da465': [('delivery2:check1', 'document_noncompliance', 3, '谭琨应该排第一，刘晔排第六或第七', '最终评分/排序任务只非空，没有可解析表格、逐项目分数或用户最终明示名次关系；输入本已带评分底稿。', '核实际结果表及最新名次关系：谭琨1、刘晔6或7；保留不冲突的此前名次要求，不从历史AI抄目标分值。')],
}

GROUPED_INDEPENDENT = {
 'conv_512bed807235': '审阅与关键内容总结被单一正文对象覆盖，缺独立基本结果的绑定。',
 'conv_70e8edb87e06': '财务资助咨询与另一保密协议修改是不同结果，不可用一条末尾答复遮盖前项。',
 'conv_e7ba7bb57e7c': '有真实报告文件检查，但独立统计咨询/技能扩展问题只核合并文本非空。',
 'conv_f22c3a85ffbb': '定向检索关键词与岗位候选方向是两项结果，单一最后非空回复可能漏关键词列表。',
}

NONEMPTY = {'delivered_body_nonempty','delivered_text_nonempty','text_body_nonempty', 'delivered_text_or_file_nonempty'}
artifact_scopes = {
 'conv_a071061ce0a7': '真实MD交付可核，但SCI论文组成及量子力学内容没有基本结构验收；不把发表可行性/科学质量当硬门槛。',
 'conv_33b2d5386dd3': '五页、图片载荷及PPTX真实文件可核；图片中题材与教学内容不由本机械规则证明。',
 'conv_ed7d6b939145': '五页、图片载荷及PPTX真实文件可核；图片中题材与教学内容不由本机械规则证明。',
 'conv_ccf77916e240': '真实图像可核；“专业/复杂”没有客观阈值，留质量评估，不自造门槛。',
 'conv_ac48282044f1': '真实新图像可核；是否圈在目标物上涉及未确认图像区域和语义，不能仅文件变化证明。',
}

manifest = json.loads((ROOT/'manifest.json').read_text('utf-8'))
selected = [v for i,v in enumerate(sorted(manifest['tasks'],key=lambda v:v['source_session_id'])) if i % 3 == 1]
tasks=[]
for shard_index, row in enumerate(selected):
    path=ROOT/row['contract']
    contract=json.loads(path.read_text('utf-8'))
    sid=contract['sid']
    findings=[]
    for check in contract['checks']:
        if check['kind'] in NONEMPTY and check.get('mandatory',True):
            basis=check.get('requirement_basis',{})
            turns=basis.get('user_turns_1_based',[]) if isinstance(basis,dict) else []
            quote=basis.get('quote','') if isinstance(basis,dict) else str(basis)
            findings.append({
                'point_id':check['point_id'], 'type':'document_noncompliance',
                'user_turns_1_based':turns, 'user_requirement_basis':quote,
                'gap':'该必需点实际只判去空白非空；完成声明、计划或拒绝正文可替代所需结果正文。终态对象绑定能防错对象，不能证明结果已交付。'+GROUPED_INDEPENDENT.get(sid,''),
                'minimal_recommendation':'为该结果预先列最低可证交付形态/必要组成并逐对象取证；只给完成状态的短句不能作正文结果。无法形成稳定结构时明确仅非空为受限代理，不能认证文档定义的任务成功；不臆造字数或专业准确性门槛。',
                'evidence':'vendor/final_state_scorer.py:293-310,401-402; _runtime.py:278-307',
            })
    for suffix,typ,turn,quote,gap,suggestion in MANUAL.get(sid,[]):
        point=sid+':'+suffix
        assert point in {c['point_id'] for c in contract['checks']}, (sid,point)
        findings.append({'point_id':point,'type':typ,'user_turns_1_based':[turn],
                         'user_requirement_basis':quote,'gap':gap,'minimal_recommendation':suggestion,
                         'evidence':row['contract']+'; source user_source_texts; pinned implementation'})
    if sid in artifact_scopes:
        findings.append({'point_id':contract['checks'][0]['point_id'],
                         'type':'mechanical_scope_limitation',
                         'user_turns_1_based':list(range(1,len(contract['user_source_texts'])+1)),
                         'user_requirement_basis':'完整用户序列已逐读，未从历史AI提取要求。',
                         'gap':artifact_scopes[sid],
                         'minimal_recommendation':'保留可核格式/数量等基本条件，明确机械范围，图像语义/专业内容留后续质量评估。',
                         'evidence':row['contract']})
    status='fail' if any(f['type']=='document_noncompliance' for f in findings) else 'limited' if findings else 'pass'
    tasks.append({
        'source_session_id':sid,'shard_index':shard_index,'title':contract['title'],
        'category':contract['category'],'category_name':contract.get('category_name'),
        'contract':str(path),'contract_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'status':status,'interpretation':'校验合同就绪性审核，非企业任务运行成功/失败标记',
        'full_user_input_read':True, 'user_turn_count':len(contract['user_source_texts']),
        'original_ai_used_as_requirement':False,
        'deliverable_count':len(contract['final_deliverables']),
        'check_count':len(contract['checks']),
        'mandatory_check_count':sum(c.get('mandatory',True) for c in contract['checks']),
        'nonmandatory_check_count':sum(not c.get('mandatory',True) for c in contract['checks']),
        'checked_point_ids':[c['point_id'] for c in contract['checks']],
        'findings':findings,
        'coverage_positive':'已列交付对象及显式格式/数量/原生状态条件依合同核对；只评价必要结果末态，不核调用过程或历史AI答案。',
        'quality_policy':'不核事实正确性、法律/科学/投资质量、主观风格或中间失败；图像语义不能因字面标签或哈希变化被认证。',
    })
assert len(tasks)==75
all_findings=[f for t in tasks for f in t['findings']]
report={
    'schema':'tsr-readiness-independent-contract-audit-part-b-v1',
    'source_suite':str(ROOT),'partition':'sorted(source_session_id), global_index % 3 == 1',
    'scope':'75 complete evaluation sources; every complete user_source_texts sequence manually read; frozen benchmark/rules unchanged',
    'summary':{
        'tasks':len(tasks),'user_turns_read':sum(t['user_turn_count'] for t in tasks),
        'checks':sum(t['check_count'] for t in tasks),
        'mandatory_checks':sum(t['mandatory_check_count'] for t in tasks),
        'observed_checks':sum(t['nonmandatory_check_count'] for t in tasks),
        'statuses':dict(collections.Counter(t['status'] for t in tasks)),
        'finding_types':dict(collections.Counter(f['type'] for f in all_findings)),
        'task_success_rate_measured':False,'business_tasks_run':0,'enterprise_api_calls':0,
        'business_model_calls':0,'frozen_contract_or_implementation_mutations':0,
        'key_result':'必要文本只非空的合同不能满足不得以完成声明代替实际结果；部分明确基本字段及已能机械核的保留规则未覆盖或被降为观测。',
    },
    'implementation_notes':[
        'text()在多轮同对象且不重叠时取matching[-1]，不能穷尽多个独立任务；必须区分同一对象改稿与不同对象。',
        'skill_check的target_hints是OR子串且直接directory可越过hints，因此指定包应冻结实际来源身份。',
        'mandatory=false及handler scorable=false检查不会进入任务AND；不能用观测覆盖已确认且可客观检验的必要条件。',
        '全文非空/文件可开不等于语义正确；该审核只建议用户已明确且可证的最低组成，不新增质量评分。',
    ],
    'tasks':tasks,
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps(report['summary'],ensure_ascii=False))
