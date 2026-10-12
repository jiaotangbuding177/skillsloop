"""Read-only manual contract audit projection; does not change a scorer or benchmark."""
import collections
import hashlib
import json
from pathlib import Path

ROOT = Path('D:/skillloop/benchmark/enterprise_input_closed_v11_20261012/evaluation/validator_suite')
OUT = Path('D:/skillloop/output/20261012_tsr_readiness_audit')
data = json.loads((OUT / 'part_c_read_sources.json').read_text(encoding='utf-8'))
manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
selected = sorted(manifest['tasks'], key=lambda x: x['source_session_id'])[2::3]
assert len(data) == len(selected) == 75

def issue(x, suffixes, basis, finding, suggestion, cls='document_noncompliance', severity='blocking', turns=None):
    existing = [c['point_id'] for c in x['checks'] if any(c['point_id'].endswith(s) for s in suffixes)]
    return {'issue_class': cls, 'severity': severity, 'point_ids': existing,
            'user_turns_1_based': turns or [], 'user_requirement_basis': basis,
            'finding': finding, 'minimum_recommendation': suggestion,
            'quality_requirement_added': False}

# These notes were written after reading all source users, including long embedded
# reference excerpts. No historical assistant content is used to establish a target.
notes = {
2: [('delivery1:check1','首轮：三份文档进行OCR，分别输出完整的识别文字',
     '三个OCR对象被混在17轮咨询正文集合中，非空只能证明一份文字出现，未检三个独立识别结果。',
     '分别绑定三个OCR结果，核对对象数量及对应输入身份；不评分OCR准确率。',[1])],
9: [('delivery1:check1','唯一有效用户输入：Continue where you left off. The previous model attempt failed or timed out.',
     '合同将续接目的命名为AI大赛/政府项目，但有效用户序列中未给前置任务；只凭此输入无法冻结该任务交付要求。',
     '核对是否存在可向actor投递的原用户前置需求；没有则列上下文不可判定，不能从历史AI填要求。',[1])],
11: [('delivery1:check1','涵盖研发、产品、销售三个岗位序列；量化KPI和行为评级两个维度；附绩效面谈话术指引',
      '三个岗位、两个评价维度和独立面谈指引均未进入检查；一句确认即可替代完整绩效方案。',
      '只增加三个岗位组、两个维度和面谈指引的结构存在检查；不判断KPI合理性。',[6])],
17: [('delivery1:check1','不要写成表格…去掉贵州的内容',
      '实际PDF和学生资料目录已核，但明确禁用的“贵州”未核；非表格约束亦未有可靠证据。',
      '原生PDF正文增加贵州字面禁词；PDF表格识别另列机械范围限制，不用不可靠启发式强判。',[6])],
21: [('delivery1:check1','把相关的内容补充进去；继续看看这个对应的技术协议内容；请修改',
      '合同只验文本集合，不提供实际修改后的原技术方案/协议或明确替换条文的对应定位，操作末态不能由“已修改”证明。',
      '至少要求实际替换正文和对应章节/条款定位；若执行文件修改则绑定最终DOCX读回。',[2,3,4])],
27: [('delivery1:check1','陈佳慧_上海云知师_代码提交总结_完整版v4吧，你给我生成一个新文件',
      '已有新文件存在/可打开检查，但用户明确提出的v4命名未覆盖。',
      '增设文件名包含用户给定版本标记v4；不核贡献归因。',[14,18])],
29: [('delivery1:check2','剥离后可转债投资协议中，不含有丙方及丙方担保内容',
      '两份独立正文数量已核，但主协议明示不得含“丙方”的字面要求未覆盖。',
      '把主协议与担保补充协议分开绑定，在主协议正文检查“丙方”字面缺席；不判担保条款剥离法律质量。',[1])],
35: [('delivery1:audited1','不要表格形式',
      'no_tables虽为必需点，但文件格式未固定且non_docx_policy=report_only；须明确非DOCX是否真正得到0/1或UNSCORED，不能以观测替代必要条件。',
      '对支持的原生格式执行表格检测；无法检测则保留缺测并不宣布整体成功。',[2])],
41: [('delivery1:check1','管理方员工改为合世家；去掉反洗钱的说法；第一个方案的时间可能要3个月',
      '字体行距已覆盖，但末轮明确替换的合世家及禁用反洗钱字面要求未检；无需判断法律风险质量即可核。',
      '增加最终DOCX“合世家”存在、“反洗钱”缺席的字面检查；3个月关联到第一方案的语义归属仅保留观察。',[7])],
55: [('delivery1:check1','绘制个人画像；第4轮设计2035数字大脑并生成图片；输出一段300字以内中文描述',
      '两项图片各可打开，却未要求两个独立文件对象；同一新PNG可能同时充当个人画像和数字大脑。字数已核，但一段约束未核。',
      '增加两图片交付对象去重以及数字大脑说明单段落检查；不判断人物相似度或科技隐喻。',[1,4])],
60: [('delivery1:audited2','就这31家，然后加审核问询函；配对看看；开始吧',
      '31条记录数量已核，但明确的问询函配对只列观测点，不参与成功AND；不存在配对字段的结果仍可能通过。',
      '冻结当前运行31对象及资料清单，再逐对象核资料引用/配对字段是否交付；身份来源及缺失项具名，不能以术语出现认证对应正确。',[41,42,44])],
61: [('delivery1:check1','提取推荐的餐厅、食物、地址和近6个月的评论做个总结；我们有agent browser技能么',
      '四类明确正文组成与独立技能能力问句合入一个非空集合；只答最后的有/没有可覆盖掉餐饮和评论交付。',
      '分别绑定餐饮提取结果与技能问句回复；基本字段包括餐厅/食物/地址/评论摘要，允许明确无法取得但不能冒充已提取。',[3,6])],
65: [('delivery1:check1','重点检查29维质量评估/源数据一致性/表格数值/科研诚信风险，输出word内部审查报告',
      '只有DOCX可打开；29维及三项独立审查栏目存在没有进入基本验收。可不评结论质量但要证明这些组成已交付。',
      '从当前环境evomind-paper-scan的既定29维清单冻结维度名，只核29记录及三栏目存在；不检科学结论正确性。',[1])],
66: [('delivery2:audited1','网站里面的所有文档下载下来',
      '必需点仅至少一个可打开文件，“所有”的动态范围/覆盖率为观测点，不能认证完全下载。',
      '下载前由独立控制器冻结当前网页可下载条目清单，再核全清单路径/非空/原生可开；未采到范围保持缺测，禁止杜撰固定数量。',[4])],
67: [('delivery1:check2','一段300字以内…最后提出1–2项可立即执行的决策建议',
      '300字、单段、无标题格式已核，但“已完成。”也满足全部检查；必要建议数量/建议正文未绑定。',
      '为汇报正文添加实际建议片段及1–2项数量绑定，不以方案准确性或说服力作为判定。',[2])],
69: [('delivery1:check1','针对吴钊志和张佳铭…报告中不用出现其他人的对比文字，以word输出',
      'Word存在已核，但两目标姓名及其他候选对比的明确禁项均未核。',
      '原生抽取DOCX核两姓名存在；禁止其他已给候选姓名作为保守字面检查需明确允许引用边界，不判推荐正确性。',[2])],
71: [('delivery2:check2','针对每一个反馈问题匹配根因与改进建议核心内容列；所有问题类型/描述匹配日期、问卷编号与账号',
      '六类交付及标题字段存在覆盖较好，但根因/建议只验表头，行数据可空；MD仅三个字面字段出现不证明每问题基本记录均已给出。',
      '基于首轮投递18条反馈的独立ID清单核行覆盖和根因/建议非空，第二章每问题核日期/编号/账号字段非空；不判匹配与根因质量。',[3,6])],
74: [('delivery5:check1','上海未来5天天气；照片大小一致并迁入单元格；对齐人名和照片上的名字',
      '照片数量/尺寸/锚点覆盖较好；五天数量未覆盖，照片与人名对应未认证。后者目前没有独立可靠身份映射，不可静默假定已经对齐。',
      '天气只加五日期记录覆盖；照片对应若可从输入冻结身份/单元格映射则末态比较，否则具名列机械限制，不加入视觉质量。',[24,47,52,57])],
}

pass_indices = {0,1,3,23,36,38,46,47,50,52,53,58,59,63}
limited_indices = {14,42,56,57,64}
special_block = {2,9,11,17,21,27,29,41,55,60,61,65,66,67,69,71,74}
text_kinds = {'text_body_nonempty','delivered_text_nonempty','delivered_body_nonempty'}
tasks = []
for x, t in zip(data, selected):
    assert x['sid'] == t['source_session_id']
    contract_path = ROOT / t['contract']
    d = json.loads(contract_path.read_text(encoding='utf-8'))
    assert x['users'] == d['user_source_texts']
    weak = [c for c in x['checks'] if c['mandatory'] and c['kind'] in text_kinds]
    findings = []
    text_dids = {c['delivery_id'] for c in weak}
    protected = {c['delivery_id'] for c in x['checks'] if c['mandatory'] and c['kind'] not in text_kinds}
    unprotected = [c for c in weak if c['delivery_id'] not in protected]
    if unprotected:
        basis_turns = sorted({i+1 for di in x['deliveries'] if di['id'] in {c['delivery_id'] for c in unprotected}
                              for i in di.get('turn_indices',[])})
        findings.append({'issue_class':'document_noncompliance','severity':'blocking_for_actual_text_delivery_claim',
                         'point_ids':[c['point_id'] for c in unprotected],
                         'user_turns_1_based':basis_turns,
                         'user_requirement_basis':'原用户要求见完整合同user_source_texts；本轮文档要求不得以完成声明代替实际结果。',
                         'finding':'此独立文字交付只核去空白非空，passing_condition或实现明确不区分计划、完成声明和实质正文；能承接“已完成。”而无实际任务正文。',
                         'minimum_recommendation':'分别绑定本次最终正文，并按用户已明确的对象/数量/必要组成设最小存在检查；自由咨询无法可靠机械区分时如实标注有限正文交付，不称已认证任务完成。不得新增质量Judge、任意字数或历史AI金标。',
                         'quality_requirement_added':False})
    for suffix,basis,finding,rec,turns in notes.get(x['index'],[]):
        cls = 'mechanical_scope_limitation' if x['index']==35 else 'document_noncompliance'
        findings.append(issue(x,[suffix],basis,finding,rec,cls,
                              'integration_or_unobservable' if cls=='mechanical_scope_limitation' else 'basic_requirement_not_covered',turns))
    if x['index'] in limited_indices:
        findings.append({'issue_class':'mechanical_scope_limitation','severity':'declared_basic_scope',
                         'point_ids':[c['point_id'] for c in x['checks']],
                         'user_turns_1_based':list(range(1,len(x['users'])+1)),
                         'user_requirement_basis':'完整用户输入已读；只按文件类型/本次实际正文等基础末态机械范围审核。',
                         'finding':{
                             14:'水印文字已检，水印实际存在仅观测；浅色及角色归属不能由普通字面存在证明。文字解释仍有非空限制。',
                             42:'投标文件可开且新交付可核；未从招标附件冻结必填栏目，不能认证模板组成齐全或投标内容质量。',
                             56:'能核当前MD文件；“md格式输出”也可能允许聊天中的Markdown，文件唯一接受形式存在口径需明示；论文必要栏目未由用户具名规定，不自造SCI质量门槛。',
                             57:'能核DOCX文件实际存在与新交付；申请表必填字段未从输入模板独立冻结，不能认证已填写所有必要空位。',
                             64:'能核PPTX可开，原“图表最好”是偏好，不硬造表数门槛；不能据文件存在认证行业分析质量。'
                         }[x['index']],
                         'minimum_recommendation':'保持专业/视觉质量不评分；有输入模板且基础字段清单可确定时预先冻结组成，无法确定则明确限定结论。',
                         'quality_requirement_added':False})
    if x['index'] in pass_indices:
        status='pass'
    elif x['index'] in special_block:
        status='fail'
    elif x['index'] in limited_indices or (weak and any(c['kind'] not in text_kinds and c['mandatory'] for c in x['checks'])):
        status='limited'
    elif unprotected:
        status='fail'
    else:
        status='limited'
    tasks.append({'source_session_id':x['sid'],'title':x['title'],'category':x['category'],
                  'audit_status':status,'status':status,
                  'review_scope':'all_user_source_texts_final_deliverables_and_checks',
                  'all_user_source_texts_read':True,'user_turn_count':len(x['users']),
                  'user_text_total_characters':sum(map(len,x['users'])),
                  'contract_sha256':hashlib.sha256(contract_path.read_bytes()).hexdigest(),
                  'mandatory_point_ids':[c['point_id'] for c in x['checks'] if c['mandatory']],
                  'observer_point_ids':[c['point_id'] for c in x['checks'] if not c['mandatory']],
                  'completion_declaration_risk_points':[c['point_id'] for c in unprotected],
                  'findings':findings,
                  'verdict': '基础可机械末态条件覆盖；专业/视觉质量不在本轮认证。' if status=='pass' else
                             '已有基础核验能力但范围/采证限制须明示。' if status=='limited' else
                             '存在明确未覆盖基本要求或无法排除纯完成声明，未满足本文档完整交付判定口径。',
                  'business_executed':False})

summary={'task_count':75,'status_counts':dict(collections.Counter(t['status'] for t in tasks)),
         'all_user_turns_read':sum(t['user_turn_count'] for t in tasks),
         'all_user_text_characters_read':sum(t['user_text_total_characters'] for t in tasks),
         'tasks_with_unprotected_nonempty_text':sum(bool(t['completion_declaration_risk_points']) for t in tasks),
         'issue_class_counts':dict(collections.Counter(f['issue_class'] for t in tasks for f in t['findings'])),
         'scope':'source_session_id sorted task indices modulo 3 = 2; only independent requirements audit',
         'business_tasks_run':0,'model_calls':0,'external_service_calls':0,
         'benchmark_or_scoring_files_modified':False,
         'not_a_measured_task_success_rate':True}
payload={'schema':'independent_tsr_requirement_audit_part_v1','part':'c','summary':summary,'tasks':tasks}
(OUT/'part_c.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False))
