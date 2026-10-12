"""Read-only audit of partition A; constructed controls, no enterprise actor or API."""
from pathlib import Path
import json
import hashlib
import importlib.util
from collections import Counter

B = Path('D:/skillloop/benchmark/enterprise_input_closed_v11_20261012/evaluation/validator_suite')
O = Path('D:/skillloop/output/20261012_tsr_readiness_audit')
O.mkdir(parents=True, exist_ok=True)
manifest = json.loads((B/'manifest.json').read_text('utf-8'))
tasks = sorted(manifest['tasks'], key=lambda t:t['source_session_id'])[::3]
assert len(tasks) == 76
simple_text = {'delivered_body_nonempty','text_body_nonempty','delivered_text_nonempty','delivered_text_or_file_nonempty'}

# Each entry was written after reading all user_source_texts in the selected contract.
# Tuple: index, classification, point selectors, user turns (1-based), specific gap, minimal change.
specific = [
(2,'mechanical_scope_limitation',[1],[1], '唯一有效输入是Continue；该合同没有提供可直接读到的被续接任务要求。任务概要不能替代原用户要求。', '补充冻结的前置用户需求/中断任务状态作为真实输入；来源不明确时只报告续接答复交付，不能认证大赛查询完成。'),
(7,'document_noncompliance',[1],[2,5,6], '明确的6月18日到21日行程、19日12点华膳楼预约、20日早康美中药城等基础字段均未覆盖；非空点可接受纯完成声明。', '从最终行程结构读取指定日期及预约名称/时间，并拒绝只含计划或完成声明的正文；不核餐厅质量与事实。'),
(8,'document_noncompliance',[1],[1,2], '三天工作记录只验DOCX非空，没有检查7月18/19/20三个日期的记录组成。', '检查最终DOCX三日期段存在且各有非空记录；不核工作事实正确性。'),
(13,'mechanical_scope_limitation',[1],[1], '真实新建及张文负责人可验证；六项主题覆盖被明确移至质量链，因此成功只说明有分配工单，不说明改动项均被记录。六主题不等于必须六工单。', '保留至少一工单，报告限定为工单创建与分配；如纳入完整交付，可只检查六主题标识/条目，不判断技术修复。'),
(14,'mechanical_scope_limitation',[1,2],[1], '图片数量与可打开已覆盖，指定EvoMind标题未检查；风格配色一致属于视觉质量，不应并入本轮机械成功。', '图中文字有可信提取时仅核指定标题；否则明示标题为未验证项，不将画风设硬门槛。'),
(16,'document_noncompliance',[1],[1,2,3], '新闻、身份答复被合并为单一非空集合；一个身份回答可替代新闻交付。HTML只验证非空网页不认证游戏功能，功能属于已排除细节。', '新闻与身份保留两个独立正文绑定，各拒绝纯声明；网页只验真实HTML入口，不加游戏质量。'),
(18,'document_noncompliance',[1],[2,5,6], '路径查询与云市场查询合并为一非空对象，单个工作区路径就可满足该点，遗漏独立市场查询交付。清理缺失/保留哈希及MD索引已有实证规则。', '分开路径答复与市场份额答复的最终绑定，各独立检验基本交付；不核份额事实。'),
(19,'document_noncompliance',[1],[1,3,4], '协议仅验一个可打开DOCX，未检查明示主体、600万元、投前2.2亿、5工作日、2027-08-30、提前30天通知这些基础字段及后续替代旧利率。', '核最终原生正文中的主体/金额/日期及通知字段；10%替代旧6%按最新要求解析，法律充分性不评分。'),
(21,'document_noncompliance',[1],[1,4], '四名候选对比与面试推荐仅非空，无候选条目/推荐对象的最低交付结构。', '读取实际对比条目和至少一个推荐对象或明确无推荐结论，拒绝纯声明；不判断推荐优劣。'),
(24,'document_noncompliance',[1],[1,2], '两轮面试与题目、30分钟初面和约60分钟复试只留非空；原需求的筛选、评分、背景清单、Offer流程也无基础组成验证。', '检查两轮结构、初面30分钟和复试约60分钟的明确展示、题目/评分/背景/Offer组成；约60分钟不自行编容差。'),
(25,'document_noncompliance',[1,3],[1,14,15,16,24,27], '安全文章与产品叙事合并；X书签方法、体育预测、模型身份合并，最后一个非空文本可掩盖其他独立交付未完成。真实持久化记忆点已有保护。', '按独立文章/叙事/两个方法说明/模型身份分别绑定最终正文，拒绝纯声明；不核叙事专业质量和风格。'),
(26,'document_noncompliance',[4],[1,23,29], '演讲稿仅非空，纯已完成可替代实际稿。PPT图片和至少10页已覆盖；页面名称和删改等图中文字未验证。', '演讲稿设置可辨识实际正文；PPT文字删改在可信OCR可用时核字面字段，否则列机械范围限制，画风不评分。'),
(38,'document_noncompliance',[1,2,3],[1,2,3,4], '三正文点均仅非空；第四种成果转化方式有明示四项，但没有四组成；BP特点/竞争力/估值与最后产品方向被合并。', '分别绑定独立分析并检查转让、许可、作价入股、自主创业四项；只验结构存在，不核商业结论。'),
(39,'document_noncompliance',[1],[1,2,3], 'Word只验可读，P/T/M逻辑和M6依据两项明示正文组成没有最低存在验证。', '读取最终DOCX并检查P/T/M和M6两个对应段落/组成均非空，不核职级依据正确性。'),
(41,'document_noncompliance',[1,3,6],[1,3,4,7], '10条提示词/10图/Word数字与引用结构已核，但城市介绍与产业观点合并且仅非空，提示词正文仍可出现条目全部为完成声明。', '两个独立说明分绑，逐页条目拒绝空泛完成/计划占位；不验产业数据及引用真实性。'),
(42,'document_noncompliance',[1],[1], '补齐签署页的关键操作只通过新PDF非空证明，任意不同内容PDF也可通过，未证明签署组成或与补充协议的相应人员绑定。', '从输入签署页冻结最小主体/签署条目清单，最终决议校验这些签署条目或可信页面对应；不判签章法律效力和视觉质量。'),
(46,'document_noncompliance',[1],[1], '用户明确重点四部分并要求29维审查，实际Word只验非空，不检查内部审查报告的必要组成。', '检查29维条目及源数据一致性/表格数值/科研诚信风险基本组成，不核各结论和专业质量；维度由输入skill冻结，不从历史AI取。'),
(48,'document_noncompliance',[1],[2,3], '仅非空，无会计分录的借贷/金额结构和2026-04-07指定起点身份；声明即可通过。', '检查最终分录至少有日期、借/贷、金额字段及指定起点标识；不核会计科目/金额事实。'),
(50,'document_noncompliance',[1,2,4],[4,5,6,7,12], '多PDF对应、水印指定文本和技能真实更新已验；首PDF用户最终确认300pt字号没有校验，任意字体尺寸亦可通过。', '针对首PDF最终水印运行或等价绘制对象验证有效300pt字号；不得把历史220/340/320当最终值，其余文件不继承未经要求的300pt。'),
(51,'document_noncompliance',[1,2,3],[1,2,3,5,6], 'Word格式已有完整检查，但最终240万元/甲乙方及产品身份和明确合同章节不核；两个合作分析/横向协议合并一非空。', '检查最终240万元、甲乙全称/产品名称和必要章节；前面分析独立绑定，宋体等现规则保留，不核法律质量。'),
(52,'document_noncompliance',[1],[1], '答辩状与公司待备证据两份独立正文合为一非空点，一份只列证据的回复也可掩盖答辩状未交付。', '答辩正文及证据清单分独立交付点并拒绝纯完成声明；不核劳动法论证。'),
(53,'document_noncompliance',[1,3],[1,3,5,7], '20提示词/20图/20PDF页及源图顺序均已有检查，但盲盒设计/球员名单和提示词最小正文仍仅非空；参赛队列未在输入冻结时不得猜定球队数。', '保留20及图源校验，文本拒纯声明；如要求每队球员配对，先冻结本次用户时点公开队伍集合，不能凭历史AI定数。'),
(54,'document_noncompliance',[2,3],[3,4,5,6,7,8,9,10], '多个财经/段落定位/识图方法/两图解释合并单一非空正文；PDF只核文件格式，未证明来源MD内容有实际转换。', '各独立答复分绑定；转换PDF读取源MD最小文本覆盖或可信原生转换清单，不判财经/图像解释质量。'),
(58,'document_noncompliance',[2,3,5,6,7,8,9,10],[6,7,9,10,11,12,13,14], '多个Word对象列出且部分另行文件有防重，但16新增岗位、5总监、3委员会办公室、2中心6部门这些明确组成不检；生产专员文字仅非空。', '分别验指定岗位/部门条目和5总监/3委员会办公室等明确集合，文字拒纯声明；解释性岗位内容质量不评分。'),
(59,'mechanical_scope_limitation',[1,2],[1,2], '一页PPT和原生载荷覆盖；内容与参考图完全一致未验证，任意新一页可通过基本文件门槛。', '优先采用参考图真实嵌入的像素/哈希对应证据；允许等价重绘时应另注明内容一致不在机械评分范围。'),
(63,'document_noncompliance',[1,2],[1,3,4,5,6], '定位/GTM、产品页面/BP大纲分别是合并非空集合，单一完成声明可通过文本点；图片数对当前大纲有规则，但冻结大纲是否独立于末态需额外采证。', '文本按必要独立组成绑定并拒纯声明；在图生成前冻结本次大纲，终态不可缩减大纲匹配图片数。'),
(64,'document_noncompliance',[1],[3,4], '最终每页文字、画面和总结是明示必要组成，只核非空；没有基本逐页结构。', '检查逐页条目每项的文字/画面与总结存在，拒纯声明；不判画面创意，也不强制用户未指定页数。'),
(66,'document_noncompliance',[1],[1,2,3], '六个项目PDF只核文件可读，没有检查六项目覆盖与各项目问题/转化路径这两个必要组成。', '按提供的六项目身份验项目条目及问题/转化路径组成；不判断专家分析质量。'),
(67,'document_noncompliance',[1],[2,4,6,7,8,10,11], '记忆真实持久记录已核；SOUL/USER/BOOTSTRAP、新闻等独立答复仍合并为单一非空，可以少答多项。', '独立需求分离最终文字绑定或按明确组成检查；不强制用户未请求的SOUL重写，不评分情绪价值。'),
(70,'document_noncompliance',[1,2],[4,5,6,8,11,12,13], '13轮多个独立法律问题仅一个非空正文；明确事实+风险分析+建议、随后两段结构和双报告比较等必要组成遗漏。Excel仅原生打开未检查给定模板列/表头。', '逐独立交付拆分，并核3段/2段最新对应结构；Excel核从实际输入模板可冻结的列名/必要结构，不核法律判断。'),
(71,'mechanical_scope_limitation',[1,2],[1], '实际一图交付覆盖，但八条新闻在图中文字/八个块的组成无法由解码器证明。', '可信OCR或结构图像清单可用时核八项标识；新闻事实及视觉排版交质量链，不用原AI作金标。'),
(72,'document_noncompliance',[1,2,3],[2], '一页/图片已覆盖，项目简介与技术优势两项必要组成未查；指定模板特征也未绑定最小可读特征。', '最终PPT文本或可信提取检查项目简介/技术优势两个组成，产品图本次来源可验证；模板只核明确结构，不核视觉像不像。'),
(75,'document_noncompliance',[1],[1], '两公式对比与说服投资人的沟通建议合并非空；没有最低两个组成。', '分别核两公式对比及谈判建议实际正文并拒纯声明；不评分数学/法律优劣结论。'),
]
by_index = {}
for row in specific:
    by_index.setdefault(row[0], []).append(row[1:])

spec = importlib.util.spec_from_file_location('audit_a_validator', B/'_runtime.py')
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)
probe_workspace = O/'part_a_constructed_empty_workspace'
probe_workspace.mkdir(exist_ok=True)
probe_results = []
out_tasks = []
for i, task in enumerate(tasks):
    cp=B/task['contract']; raw=cp.read_bytes(); c=json.loads(raw.decode('utf-8'))
    assert hashlib.sha256(raw).hexdigest()==task['contract_sha256']
    checks=c['checks']; users=c['user_source_texts']; issues=[]
    nonempty = [x for x in checks if x.get('mandatory',True) and x['kind'] in simple_text]
    if nonempty:
        issues.append({
            'classification':'document_noncompliance',
            'code':'nonempty_body_accepts_completion_statement',
            'point_ids':[x['point_id'] for x in nonempty],
            'user_basis': [{'user_turn_1based': j+1, 'excerpt':t[:210]} for j,t in enumerate(users) if j in set(v for d in c['final_deliverables'] if d['id'] in {x['delivery_id'] for x in nonempty} for v in d.get('turn_indices',[]))],
            'gap':'必需正文点仅去空白后非空；实际handler无完成声明/计划占位拒绝，纯“已完成”可当该正文通过。这直接不满足“不以Agent完成声明代替实际结果”。',
            'evidence':['vendor/final_state_scorer.py:293-306读取delivery.text或最后相关turn_answer','vendor/final_state_scorer.py:401-434仅非空/指定格式，无完成声明拒绝','_runtime.py:context_class未新增正文过滤'],
            'minimal_suggestion':'保留纯文字任务，不用质量Judge；增加最小实际正文证据及纯完成声明/计划占位负例，明确独立必要组成仅验有无。不能保证测量的任务报告范围受限或UNSCORED，不认定已完成。'
        })
    for classification,selectors,turns,gap,suggestion in by_index.get(i,[]):
        issues.append({'classification':classification, 'code':'individual_user_requirement_coverage',
            'point_ids':[checks[s-1]['point_id'] for s in selectors if s<=len(checks)],
            'user_basis':[{'user_turn_1based':j,'excerpt':users[j-1][:450]} for j in turns if j<=len(users)],
            'gap':gap,'minimal_suggestion':suggestion})
    # Controlled negative evidence is deliberately synthetic, not a business attempt.
    # Probe only real one-check pure-text contracts; do not fabricate service evidence.
    probe=None
    if len(checks)==1 and checks[0]['kind'] in simple_text:
        sid=c['sid']; did=checks[0]['delivery_id']
        request={'task_id':sid,'source_session_id':sid,'workspace':str(probe_workspace),
                 'result':{'answer':'已完成','turn_answers':['已完成']*len(users)},
                 'evidence':{'schema':'final-state-evidence-v1','source_session_id':sid,'conversation_complete':True,
                             'workspace':str(probe_workspace),'deliveries':{did:{'text':'已完成'}}}}
        result=runtime.score_task_request(request,c)
        probe={'case':'constructed_declaration_only_no_real_answer','declared_text':'已完成',
               'valid':result['valid'],'score':result['score'],
               'task_success_status':result['task_success_status'],
               'point_results':[{'point_id':x['point_id'],'status':x['status'],'passed':x['passed']} for x in result['checks']],
               'business_actor_calls':0,'external_api_calls':0,'constructed_control':True}
        assert probe['valid'] is True and probe['score']==1
        probe_results.append({'source_session_id':sid,**probe})
    status='fail' if any(x['classification']=='document_noncompliance' for x in issues) else 'limited' if issues else 'pass'
    out_tasks.append({'partition_index':i,'source_session_id':c['sid'],'title':c['title'],
                      'category':c['category_name'],'status':status,
                      'contract':str(cp),'contract_sha256':hashlib.sha256(raw).hexdigest(),
                      'complete_user_source_texts_read':True,'user_turn_count':len(users),
                      'user_source_character_count':sum(len(s) for s in users),
                      'user_source_texts_sha256':hashlib.sha256(json.dumps(users,ensure_ascii=False,separators=(',',':')).encode()).hexdigest(),
                      'check_count':len(checks),'mandatory_check_count':sum(x.get('mandatory',True) for x in checks),
                      'final_deliverable_count':len(c['final_deliverables']),
                      'findings':issues,'constructed_negative_control':probe,
                      'accepted_scope':'必要实际交付、可机械读取的数量/格式/字段/终态；事实正确性、专业质量和画风不评分；过程错误不评分。'})

summary={'task_count':len(out_tasks),'status_counts':dict(Counter(x['status'] for x in out_tasks)),
         'user_turns_read':sum(x['user_turn_count'] for x in out_tasks),
         'user_source_characters_read':sum(x['user_source_character_count'] for x in out_tasks),
         'document_noncompliance_tasks':sum(any(v['classification']=='document_noncompliance' for v in x['findings']) for x in out_tasks),
         'mechanical_scope_limitation_tasks':sum(any(v['classification']=='mechanical_scope_limitation' for v in x['findings']) for x in out_tasks),
         'pure_completion_statement_false_positive_offline_controls':len(probe_results),
         'offline_controls_all_returned_pass':all(x['score']==1 for x in probe_results),
         'formal_task_success_rate_calculated':False,'business_actor_runs':0,'model_calls':0,'enterprise_api_calls':0,
         'frozen_benchmark_or_validator_mutations':0,
         'historical_ai_used_as_requirement':False}
out={'schema':'tsr-readiness-independent-audit-part-a-v1','partition':'sorted source_session_id index % 3 == 0',
     'benchmark':str(B.parent.parent),'summary':summary,'tasks':out_tasks,
     'audit_basis':'用户当轮TSR定义、各完整user_source_texts及冻结checks/final_deliverables；不把非空/格式认证提升为完整业务成功。',
     'constructed_control_scope':'只运行合成缺交付反例下的既有评分函数；没有运行企业任务，没有伪造真实业务成果。'}
(O/'part_a.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
