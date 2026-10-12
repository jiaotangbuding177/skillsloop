"""One-off research audit serializer. No validator, business task or model is run."""
from pathlib import Path
import json,hashlib,copy,re,collections

ROOT=Path('D:/skillloop')
IN=ROOT/'output/20261012_evaluation_task_checkpoints'
OUT=ROOT/'output/20261012_task_validator_suite/audit'
reviews=json.loads((IN/'review_artifacts_tech.json').read_text('utf-8'))
review={r['session_id']:r for r in reviews}
base=[x for x in json.loads((IN/'全部任务工作底稿.json').read_text('utf-8')) if x['session_id'] in review]
display=json.loads((IN/'逐任务评测点明细.json').read_text('utf-8'))
visible={(p['session_id'],p['deliverable_index'],p['check_index']):p for p in display['points']}
assert len(base)==74 and len(review)==74

def source(c,turns,quote):
    available=[c['users'][t-1]['text'] for t in turns]
    if not any(quote in s for s in available):
        raise ValueError(('quote_not_exact',c['session_id'],turns,quote))
    return {'user_turns_1_based':turns,'quote':quote}

def new(c,di,kind,params,turns,quote,reason,evidence,mandatory=True,limit=''):
    return {'deliverable_index':di,'object':c['deliverables'][di]['name'] if di<len(c['deliverables']) else '新增终态交付',
            'kind':kind,'params':params,'mandatory':mandatory,'requirement_basis':source(c,turns,quote),
            'reason':reason,'evidence':evidence,'coverage_limit':limit}

patches={}
def change(sid,di,ci,kind,params,turns,quote,reason,object_name=None,mandatory=True):
    patches[(sid,di,ci)]={'kind':kind,'params':params,'turns':turns,'quote':quote,'reason':reason,'object_name':object_name,'mandatory':mandatory}

# Corrections supported by human requests, not historical assistant output.
change('conv_28cc7559789d',0,0,'final_service_state',{'service':'gitee','min_records':1,'assignee':'zhangwen','created_by_current_attempt':True},[1],'根据这些改动点，给张文新建任务工作项。','六个改动主题不等于六个独立工单；至少一个新工作项并分配张文是明确基本交付，技术内容覆盖留质量链。')
change('conv_b69071f509d3',1,0,'final_file_native_open',{'allowed_formats':['pdf'],'required_distinct_file_count':1,'require_nonempty_payload':True,'resolve_from_current_attempt_delivery_declaration':True,'source_input_name':'2026-08-07_国内AI新闻热点速览.md'},[5],'转成pdf','第5轮实际附国内AI新闻MD，不是比亚迪答复。仅纠正目标绑定，原PDF格式/单份条件保留。','国内AI新闻Markdown转换的PDF')
change('conv_ab3863a19fb2',1,0,'skill_final_state',{'target_hints':['pdf-watermark'],'readable_final_entry':True,'must_be_changed':True,'baseline_scope':'same_attempt_initial_skill_manifest','export_link_required':False},[7,10],'更新到skill中','更新明确要求真实技能终态变更；不能以原有入口存在替代更新。变更质量及以后询问行为不评分。')
change('conv_abba8995a3a6',0,0,'code_artifact_present',{'accepted_forms':['source_file','archive_with_source','delivered_fenced_source'],'require_nonempty_code_payload':True,'resolve_from_current_attempt_delivery_declaration':True,'reject_plan_only':True,'reject_reused_input_documents':True},[1,2],'针对以上prd实施代码开发','用户明确实施代码开发，纯讨论非空不够；没有明示Web Demo、编程语言或包格式，接受真实代码文件、含源码的包或实际交付源码块。','基于PRD与设计规范的新代码交付')
change('conv_576b570b2ec8',0,0,'final_service_state',{'service':'cron_registration','expected':{'created':True,'schedule':{'frequency':'daily','hour':9,'minute':0,'timezone_from':'frozen_attempt_environment'},'payload_terms':['ima','知识库']},'actual_trigger_not_evaluated':True},[1],'每天9点帮我导入ima笔记，然后整理知识库','小时提示9不等于每天09:00，明示每日频率与任务内容应读取完整登记字段；时区沿冻结环境，不新增猜测时区。')
change('conv_b82c332f5f54',2,0,'selected_skill_identity_report_only',{'selection_source':'current_attempt_conversation_reference_resolution','target_hints':[],'record_final_skill_paths':True,'do_not_accept_arbitrary_skill_as_target':True},[5],'帮我把这个skill 安装到我的技能库','这个skill身份未在用户文字中明确，不能让任意目录过关；保留末项身份与安装观察，待本次可追溯目标解析补证，不计硬AND。',mandatory=False)
change('conv_edc9bbda3d45',3,0,'skill_final_state',{'readable_final_entry':True,'new_generated_skill_required':True,'entry':'SKILL.md','front_matter':['name','description'],'reject_preinstalled_builtin_as_new':True,'export_link_required':False},[3],'最后把本项工作的核心能力沉淀为一个skill。','用户要求本次沉淀新能力，任意预装技能入口不应作本次新技能。')
change('conv_737c4b010b18',1,1,'manifest_corresponding_artifacts',{'count_from':'current_attempt_prompt_page_manifest','manifest_source':'actually_delivered_prompt_text_for_turn_3','freeze_manifest_before_image_phase':True,'require_one_readable_final_image_per_page':True,'reject_terminal_self_declared_subsets':True},[3,4],'按照你的提示词，生成每一页的图','清单必须来自第3轮实际提示词，不能用临末自报子集或旧AI页数降要求。')
change('conv_965cf7b2c858',1,1,'manifest_corresponding_artifacts',{'count_from':'current_attempt_prompt_page_manifest','manifest_source':'actually_delivered_prompt_text_for_turn_1','freeze_manifest_before_image_phase':True,'require_one_readable_final_image_per_page':True,'final_version_per_page':True,'reject_terminal_self_declared_subsets':True},[1,2,5],'帮我先生成生图提示词','按本次实际提示词页清单验逐页图片；明确前三页及随后继续不允许终态随意少报页。')
change('conv_a196d952691c',0,2,'manifest_corresponding_artifacts',{'count_from':'user_explicit_storyboard_items','source_user_turns':[2,3],'deduplicate_repeated_storyboard':True,'require_one_readable_final_image_per_explicit_item':True,'ignore_unwritten_declared_extra_shot':True,'reject_agent_selected_subset':True},[2,3],'按照要求先生成高清图片','清单依据用户实际列出的片段/分镜，不允许助手挑选子集自减数量。Clip 1文字称3分镜但实际只列2项，未写出的额外分镜仅报告，不虚构第三项。')

extras={}
def add(sid,entry):extras.setdefault(sid,[]).append(entry)
byid={c['session_id']:c for c in base}

sid='conv_0c5f19d450fa';c=byid[sid]
add(sid,new(c,0,'literal_fields_presence',{'scope':'generated_skill_and_examples','literals':['100kΩ','10μF','1N4148','红色'],'numeric_fields':['5000','2000','3000','1500','500'],'number_match':'token_after_grouping_separator_normalization','unicode_normalization':'NFKC'},[1],'商品清单：','在已有供应商/商品名外保留明示规格和数量；不推断商品价格或报价算法。','新技能或随包样例的原生字段命中；数值匹配须按完整数字token，不能500命中5000。',limit='只核字段出现，不认证商品数量归属或计算。'))
sid='conv_3ae75a94697f';c=byid[sid]
add(sid,new(c,0,'delivered_table_present',{'accepted_forms':['markdown_table','html_table','docx_table','xlsx_table','plain_text_matrix'],'minimum_table_count':1,'require_nonempty_table_body':True},[1],'输出估值区间和敏感性表。','敏感性表是明确组成部分，可核非空表格结构；不得强制Excel或判断金融数值。','本次交付正文/文件内原生可解析表格，记录表位置。',limit='不证明估值区间、计算正确或表格语义为敏感性。'))
sid='conv_ded32a098c17';c=byid[sid]
add(sid,new(c,0,'literal_fields_presence',{'scope':'generated_skill_and_references','literals':['教科书'],'trigger_examples':['我在读一本书','怎么做读书笔记','如何精读'],'trigger_examples_mode':'report_only'},[2],'教科书场景，知识卡片','教科书是明示组成，可核词项出现；具体触发行为不能由短语命中证明，触发例句只报告以避免等价措辞误杀。','本次技能正文/参考资料可读文本与词项位置。',limit='不运行触发或评价读书方法有效性。'))
sid='conv_e0ea2802f1e7';c=byid[sid]
add(sid,new(c,1,'persisted_memory_present',{'readable_nonempty_record':True,'new_or_changed_since_attempt_start':True,'request_user_turns':[5],'storage_scope':'current_attempt_memory_state','separate_export_required':False,'exact_historical_ai_wording_required':False},[5,6,7],'多提供情绪价值，多喊喊我，记住','明确记住偏好，文字承诺不能代替持久记录；初态非空USER.md也不能自动算本次已保存。','本attempt初态与终态记忆清单、记录路径/ID、可读正文及请求关联。',limit='只核新的可读持久记录，不判断情绪价值或人格表达。'))
sid='conv_edc9bbda3d45';c=byid[sid]
add(sid,new(c,0,'literal_fields_presence',{'scope':'final_feedback_report','literals':['填写日期','问卷编号','账号'],'section_scope':'second_chapter_if_machine_identifiable_else_full_report'},[6],'填写日期、问卷编号与账号','三个字段属于用户明示的基本报告组成；不核逐问题匹配质量。','最终Markdown第二章或结构化表头位置；章节无法可靠解析则全报告查字段并披露边界。',limit='出现不证明逐问题归属、日期准确或研发任务映射正确。'))
sid='conv_fcee61c6481d';c=byid[sid]
add(sid,new(c,16,'spreadsheet_image_dimensions_and_anchors',{'all_photo_objects_same_display_width_and_height':True,'equality':'exact_normalized_OOXML_display_units','require_valid_cell_anchor':True,'native_cell_image_relationships_accepted':True,'photo_count_from':'source_photo_manifest','preserve_original_photo_count':True},[52,56],'要求每张图片的大小保持一致，并以此迁入单元格中','明确尺寸一致与单元格锚定可原生核；图片数量按源表清单，不允许删除照片剩一张满足一致性。','XLSX drawing/anchor/cell-image关系、归一化EMU显示尺寸及源照片数量清单。',limit='不核姓名照片语义关系及主观视觉效果，不编像素容差。'))
sid='conv_e09b70c51b19';c=byid[sid]
add(sid,new(c,1,'download_scope_report_only',{'source_url':'https://cwc.ecnu.edu.cn/_s300/32974/list.psp','expected_document_manifest':None,'expected_count':None,'scope_from':'preflight_frozen_current_site_document_manifest','unknown_scope_does_not_pass_complete_download':True},[4],'里面的所有文档下载下来','所有文档目标仍需披露完整性；对象清单未冻结时只报告范围、已下载文件及缺证，不设硬数量。','预检抓取范围/运行时点冻结清单与本次文件映射；本轮未重抓网站。',mandatory=False,limit='至少一份文件可读不等于所有下载完成；补齐清单后另冻结机械覆盖条件。'))

# Exact watermark content is a basic explicit field; visual style is excluded.
for sid,di,literals,turns,quote in [
 ('conv_470d66397a7d',0,['金桥吴彦祖'],[2],'内容：金桥吴彦祖'),
 ('conv_5785a8ce4b6a',0,['金桥吴彦祖'],[2],'水印内容：金桥吴彦祖'),
 ('conv_ab3863a19fb2',0,['EvoMind','金桥吴彦祖'],[1,12],'水印打：金桥吴彦祖')]:
    c=byid[sid]
    p={'literals':literals,'scope':'source_to_final_pdf_added_text','text_normalization':'NFKC_whitespace','mapping':'first_pdf_EvoMind_last_pdf_金桥吴彦祖' if len(literals)>1 else 'each_input_pdf','on_unextractable_watermark':'unknown_not_false','reject_same_input_bytes_as_modified_output':True}
    add(sid,new(c,di,'pdf_added_literal_text_presence',p,turns,quote,'用户明确水印内容，可检查新增可提取文字；图像栅格化不能机械证明时unknown，不把仅PDF存在视作水印已完成。','比较本次输入/输出PDF原生可提取文本及文本对象；输入原有同名词项不能冒充新增水印。',limit='水印位置、斜角铺满、美观及不可靠栅格OCR另列限制。'))

notes={
 'conv_04d4f8d415e0':['保留ZIP与说明；只核包可解开且有实际运行入口。Windows音频播放、连续收音与个人API可用性为功能/环境测量，当前不纳入硬AND；不能称语音问题已被验证解决。'],
 'conv_383a91943829':['用户要求一页PPT内容，最低为内容稿；不强制PPTX、一页实际文件或锁字数。项目简介/技术优势/产品图片信息的语义覆盖质量后测。'],
 'conv_514f6d8693d2':['最终仅一份PPT及演讲稿。第23轮仍修改第十页，最低10页有用户依据；不固定恰好10页。图标/文字删除改名在图片型PPT中依赖图像语义，不纳入本轮硬检查。'],
 'conv_56aa032f17a8':['搜狗方案替代百度细节；两种效果图第4轮明示仍有效，不强制安装版皮肤、14套图或旧AI章节。'],
 'conv_965cf7b2c858':['第7轮只改第四页图，未要求重新拼PDF；逐页图片、前三图拼图和已请求PDF各自保留，PDF不追加同步新版强制条件。最低4页图片依据用户指向第四页。'],
 'conv_a196d952691c':['先生成高清图片推迟最初动图/视频；视频时长74秒不成为当前图片交付参数。Clip 1宣称3分镜但正文只列2，未写的分镜不新增硬检查。4K维度沿现有常见基础定义，无额外清晰度或瑕疵容差。'],
 'conv_a52e0748557e':['原生XLSX正文明确声明原文件名保留清霜、银行主体按用户原称紫衫构造，银行主体行也为紫衫。本轮撤回仅凭文件名推断公司对象错配的疑虑；它仍是具名合成输入，不认证历史业务数值。'],
 'conv_ab3863a19fb2':['字号220/340/320被300pt取代，不能同时验多稿。第二份PDF水印内容未明确新值：只验产生修改后的可读最终PDF，不能假定沿用EvoMind；首份与末份文字按明确值验。自动分析页大小及以后主动问内容是技能行为/语义，仅保存变更不证明实现效果。'],
 'conv_b82c332f5f54':['末项目标身份不清，首项kangkona仍可核安装；不能把同一技能算两个独立安装成果。selected target观察待本次引用解析证明，未证明时报告限定基础交付，不声称全安装意图完成。'],
 'conv_bb5e39c2a2aa':['用户明确要求输入ZIP成员复制/解压到目标目录，此处允许字节与输入成员相同；目录须AI工作区顶层，不能把ZIP本身当解压成员。'],
 'conv_c618f1f9fb24':['恰好一页PPT是明确机械条件；内容完全相同为图文保真质量，未据输入Word或历史AI追加可编辑要求。'],
 'conv_d702dce9aea0':['末轮要求每页文字/画面内容和总结，取消详细技术方案与背景音乐；只是脚本，不新增实际视频。纯数字画面风格为内容要求，不用字面禁止词替代语义验证。'],
 'conv_e09b70c51b19':['所有财务网站文档缺冻结下载对象清单。至少1文件仅可为最低可用文件检查，不能称所有下载完成；完整范围需预检冻结真实链接集合后覆盖核验。不擅自设固定文档数量。'],
 'conv_edc9bbda3d45':['六个有效产物保留；用户反馈MD末轮新版替代旧版；之前PDF没有明确要求再转最新版，不自动加末轮PDF同步。新增字段仅检基础组成，反馈到根因/工作项的正确匹配留质量链。'],
 'conv_fcee61c6481d':['节点配对/连接被第5/32轮取消，不评分真实连接。重复两项月度提醒仅保留各一条终态登记；未明示具体小时不虚构时刻。营业执照是明确取原件，不要求另生成新内容。照片姓名对应准确性后测，几何与图像数量保存是基本检查。']
}

preflight={
 'conv_299aa1b64659':{'status':'missing_input','missing':['111.png待修改原图'],'evidence':'底稿与原v10运行dependencies只有一份222参考图，未找到111对象绑定。','effect':'最终单张image格式/数量设计可通过，执行前应补本attempt输入映射；未知输入不记算法失败。'},
 'conv_6ad7c7eaf079':{'status':'missing_input','missing':['用户所指另一份报告身份及正文'],'evidence':'底稿input_files与原运行dependencies均为空。','effect':'仅能有限检查文字交付；内容对象未知，不声称报告已审。'},
 'conv_bd39d19c227c':{'status':'missing_input','missing':['表格数据对象','文档正文对象'],'evidence':'底稿input_files与原运行dependencies均为空。','effect':'两项基本文字仍可设计非空检查，但对象未知。'},
 'conv_edc9bbda3d45':{'status':'missing_input_binding_evidence','missing':['首两轮用户反馈.xlsx的实际投递/挂载证据'],'evidence':'对象库有用户反馈.xlsx，但底稿与原运行dependencies仅绑定第4轮工作项表和第5轮MD。文件存在不能证明派发。','effect':'最终MD/XLSX/PDF/skill/MD/HTML基本格式设计可通过；执行前核prepare清单和原路径映射，不新恢复环境。'},
 'conv_e09b70c51b19':{'status':'missing_download_scope_manifest','missing':['财务网站运行时点全部文档URL集合'],'evidence':'用户要求所有，当前评分参数只min_files=1，没有完整对象清单。','effect':'预检需冻结可访问范围；否则完整下载覆盖仅report_only，最低文件交付可评分但不得冒充所有。'},
 'conv_b82c332f5f54':{'status':'unresolved_selected_skill_identity','missing':['末轮这个skill指向的本次可追溯身份'],'evidence':'末项target_hints=[]；用户没具名。','effect':'首项安装与正文可检查，末项观察目标解析而不接受任意技能。'},
 'conv_ab3863a19fb2':{'status':'requires_initial_skill_manifest','missing':['本attempt开始时pdf-watermark文件清单/SHA'],'effect':'缺初态不能证明更新；终态变更比较应unknown，非技能失败。'},
 'conv_e0ea2802f1e7':{'status':'requires_initial_memory_manifest','missing':['本attempt初态SOUL/USER/memory清单及最终记录关联'],'effect':'只验新的持久记录存在/改变，不能用旧USER内容冒充本轮保存。'}
}

quality={
 'conv_0066cb5f2347':['高达机体/朝向/眼睛/武器/金光/美观'],
 'conv_299aa1b64659':['参考风格配色一致及海报标题图像语义'],
 'conv_470d66397a7d':['斜角铺满视觉效果；20%透明度若原生alpha无法关联具体水印对象则只报告，不能伪造可靠测量'],
 'conv_5785a8ce4b6a':['默认水印视觉布局'],
 'conv_ab3863a19fb2':['字号实际视觉、页面自适应与主动询问行为；原生文本对象可定位时可报告300pt，不编视觉容差'],
 'conv_fcee61c6481d':['姓名照片语义匹配、税务正确性、天气真实性、游戏建议、主观情绪价值']
}

def disposition(c,item,typ,index):
    sid=c['session_id'];key=item.get('check') or item.get('type') or item.get('kind') or typ
    # Decide every prior item separately; no prior proposal automatically enters AND.
    mode='accepted_as_scope_note';why='保留此前依据和测量边界；不新增主观质量或过程条件。'
    if typ=='proposed_addition':
        mode='accept_basic_check_with_limits';why='纳入本轮明示基础组成或终态持久交付；新增kind/params见新增检查，不按旧建议措辞直接执行。'
        if sid=='conv_e09b70c51b19':mode='conditional_report_only';why='所有下载对象未冻结，完整覆盖检查须预检清单后才可硬计分；不凭一文件宣称完整。'
        if sid=='conv_ded32a098c17':why='仅教科书词项纳入基础组成；触发例句等价措辞/实际行为为观察，不强制逐字照抄。'
    if sid=='conv_a52e0748557e':mode='resolved_by_input_evidence';why='读取原生XLSX正文确认构造主体紫衫，文件名不等于公司对象；合成事实限制仍保留。'
    if sid in ('conv_299aa1b64659','conv_6ad7c7eaf079','conv_bd39d19c227c'):mode='execution_preflight_issue';why='输入身份缺口单列，不改错验收对象，也不以缺环境宣称模型失败。'
    if sid=='conv_28cc7559789d':mode='replace_unjustified_count';why='min_records=6改为至少1，新分配张文目标有用户依据，六主题内容覆盖不当硬工单数。'
    if sid=='conv_b69071f509d3':mode='replace_wrong_object';why='明确第5轮附国内AI新闻MD，PDF验收对象改为该转换产物。'
    if sid=='conv_abba8995a3a6':mode='replace_text_only_completion';why='代码实物是明确开发最低交付，纯讨论不能过开发检查；不强制历史AI自行选择的Web Demo。'
    if sid=='conv_b82c332f5f54':mode='limit_target_unknown_to_observation';why='不得任意skill充数；目标身份缺证时观察，基础安装成功不能外推全部意图满足。'
    if sid=='conv_ab3863a19fb2':mode='accept_final_update_comparison';why='技能终态入口可读且相对同attempt初态改变，规则执行效果和旧字号不加入硬AND。'
    if sid=='conv_fcee61c6481d' and item.get('type')=='cancelled_request':mode='accept_cancellation';why='节点连接取消；重复提醒不重复计分，其余独立交付保留。'
    return {'prior_type':typ,'prior_index':index,'identifier':key,'decision':mode,'reason':why,'prior_item':item}

tasks=[]
for c in sorted(base,key=lambda x:x['session_id']):
    sid=c['session_id'];r=review[sid];decisions=[]
    for di,d in enumerate(c['deliverables']):
        for ci,chk in enumerate(d['checks']):
            v=visible[(sid,di,ci)];k=chk.get('kind') or chk.get('method');p=copy.deepcopy(v['parameters'])
            item={'deliverable_index':di,'check_index':ci,'original_object':d['name'],'original_kind':k,'original_params':p,'action':'keep','reason':'只验会话终态的本次必要交付及明示基本格式/数量/结构/字段；不判中间过程或专业质量。','effective_object':d['name'],'effective_kind':k,'effective_params':p,'mandatory':v['mandatory'],'requirement_basis':{'user_turns_1_based':[i+1 for i in d.get('turn_indices',[])],'quote':v['requirement_basis']},'evidence_scope':'current_attempt_terminal_deliverable_only'}
            if (sid,di,ci) in patches:
                q=patches[(sid,di,ci)]
                item.update({'action':'replace' if q['mandatory'] else 'report_only','reason':q['reason'],'effective_object':q['object_name'] or d['name'],'effective_kind':q['kind'],'effective_params':q['params'],'mandatory':q['mandatory'],'requirement_basis':source(c,q['turns'],q['quote'])})
            if k in ('delivered_text_nonempty','delivered_body_nonempty') and item['action']=='keep':
                item['coverage_limit']='仅文字交付非空，不证明内容覆盖、实质完成或事实正确；不编最低字数，也不接受运行器silent_reply控制哨兵作用户正文。'
            if k in ('delivered_file_open','file_delivery_open','final_file_native_open'):
                item['provenance_policy']='真实交付声明关联本attempt可读取文件；生成/修改/转换目标排除未改输入与旧运行合成产物。明确取原件/解压成员按来源对应例外，不滥加必须改字节。'
            decisions.append(item)
    old_dispositions=[disposition(c,it,typ,i) for typ in ('review_notes','proposed_additions') for i,it in enumerate(r.get(typ,[]))]
    added=extras.get(sid,[])
    changed=any(d['action']!='keep' for d in decisions) or bool(added)
    text_unknown=sid in ('conv_6ad7c7eaf079','conv_bd39d19c227c')
    status='limited_text_delivery/content_target_unknown' if text_unknown else ('approved_basic_with_revisions' if changed else 'approved_basic')
    gaps=[]
    for d in decisions:
        if d['action']!='keep':gaps.append(d['reason'])
    for a in added:gaps.append(a['reason'])
    if text_unknown:gaps.append('最终正文可作最低交付观察，所分析对象身份未知；不能声称文件内容任务充分成功。')
    if sid=='conv_e09b70c51b19':gaps.append('所有下载覆盖尚缺清单；当前基本文件可读检查通过不代表用户全部文档目标充分成功。')
    if sid=='conv_b82c332f5f54':gaps.append('末项skill身份未证，任何任务得分应注明只覆盖已解析基本目标。')
    limits=quality.get(sid,[])+c.get('ignored_details',[])
    tasks.append({'session_id':sid,'title':r['title'],'audit_status':status,'design_audit_passed_for_limited_basic_delivery':True,
        'audit_scope':'完整用户序列已逐轮读取；最终一次验收，质量后测。此处设计审核通过不表示模型已运行或产物已实际交付。',
        'source_user_turn_count':len(c['users']),'all_user_turns_reviewed_1_based':list(range(1,len(c['users'])+1)),
        'original_check_decisions':decisions,'basic_delivery_gaps':gaps,'approved_new_checks':added,
        'execution_preflight':preflight.get(sid,{'status':'requires_current_attempt_evidence','note':'本轮未重验环境或执行任务；脚本须读当前attempt实际交付/服务状态。'}),
        'limited_scope_notes':notes.get(sid,[]),'quality_or_unverifiable_not_in_AND':limits,
        'prior_notes_and_candidate_decisions':old_dispositions,'frozen_benchmark_modified':False,'actual_delivery_verified':False})

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result={'schema':'task_validator_design_audit_v1','group':'artifacts_tech','audited_tasks':len(tasks),'original_checks_reviewed':sum(len(t['original_check_decisions']) for t in tasks),
    'prior_notes_reviewed':sum(len(r.get('review_notes',[])) for r in reviews),'prior_candidates_reviewed':sum(len(r.get('proposed_additions',[])) for r in reviews),
    'scope':'Audit only; no validator implementation, model or business task execution. Approved amendments are for a separate suite, not frozen v10 or original scorer.',
    'global_evidence_rules':['每检查绑定本attempt真实终态交付，不能仅路径名/扩展名/口头宣称；合成输入与历史AI既有产物不自动算新产物。','生成/修改对象需终态交付归属及初态资源去重；明确取文件/解压是例外，允许源字节，但必须正确对象和目标位置。','skill创建核本次新入口；更新核同attempt初态与末态变更；输入和状态基线只为终态比较，不给中间出错扣分。','缺输入、服务读回、解析器或必要基线是预检/测量缺口，输出unknown/UNSCORED，不能自动失败或伪造成功。','文字非空只作最低交付；运行器silent_reply等明确控制哨兵不计正文；不引入主观语义完成、最低字数和自创容差。','本组没有用户明确要求保留旧Word修订的来源；Word仅按各自有效终态输出格式验，不擅加接受全部修订动作或历史AIgold。'],
    'source_sha256':{str(IN/n):sha(IN/n) for n in ['逐任务评测点明细.json','review_artifacts_tech.json','全部任务工作底稿.json']},
    'tasks':tasks,'summary':{'audit_status_counts':dict(collections.Counter(t['audit_status'] for t in tasks)),
        'check_action_counts':dict(collections.Counter(d['action'] for t in tasks for d in t['original_check_decisions'])),
        'approved_new_check_count':sum(len(t['approved_new_checks']) for t in tasks)},'actual_business_runs':0,'model_calls':0}
overrides={}
for task in tasks:
    sid=task['session_id'];c=byid[sid]
    entry={'retain':[],'replacements':[],'removals':[],'additions':[],'new_deliverables':[],
           'audit_status':task['audit_status'],'execution_preflight':task['execution_preflight']}
    for d in task['original_check_decisions']:
        ident={'point_id':visible[(sid,d['deliverable_index'],d['check_index'])]['point_id'],
               'deliverable_index':d['deliverable_index'],'check_index':d['check_index']}
        if d['action']=='keep':entry['retain'].append(ident)
        else:
            replacement={**ident,'name':d['effective_object'],'kind':d['effective_kind'],
                         'parameters':d['effective_params'],'mandatory':d['mandatory'],
                         'requirement_basis':d['requirement_basis'],'reason':d['reason']}
            if sid=='conv_abba8995a3a6':
                replacement['delivery_metadata']={'name':d['effective_object'],'kind':'file_or_code_text',
                                                   'format':['source','zip','fenced_source'],'turn_indices':[0,1]}
            entry['replacements'].append(replacement)
    for a in task['approved_new_checks']:
        amendment={'deliverable_index':a['deliverable_index'],'name':a['object'],'kind':a['kind'],
                   'parameters':a['params'],'mandatory':a['mandatory'],'requirement_basis':a['requirement_basis'],
                   'reason':a['reason'],'evidence':a['evidence'],'coverage_limit':a['coverage_limit']}
        if a['deliverable_index']>=len(c['deliverables']):
            meta={'name':'用户协作偏好的本次持久保存记录','kind':'service','format':'persistent_memory_state',
                  'turn_indices':[4,5,6,7,8,9,10]}
            amendment['name']=meta['name'];amendment['delivery_metadata']=meta
            entry['new_deliverables'].append({**meta,'checks':[{'kind':a['kind'],'parameters':a['params'],'mandatory':a['mandatory'],
                                                               'requirement_basis':a['requirement_basis']}]})
        entry['additions'].append(amendment)
    overrides[sid]=entry
result['overrides']=overrides
result['new_kind_list']=sorted({d['effective_kind'] for t in tasks for d in t['original_check_decisions'] if d['action']!='keep'}|{a['kind'] for t in tasks for a in t['approved_new_checks']})
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'artifacts_tech.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps({'tasks':len(tasks),'points':result['original_checks_reviewed'],'summary':result['summary']},ensure_ascii=True))
