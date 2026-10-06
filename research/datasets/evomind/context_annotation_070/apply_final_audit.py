"""Explicit text-grounded corrections following the second reading, not new human labels."""
import json
from pathlib import Path
P=Path(__file__).resolve().parent/'private'
d=json.loads((P/'review_data.json').read_text(encoding='utf-8')); labs=json.loads((P/'user_backup_original.json').read_text(encoding='utf-8'))['labels']
rows=json.loads((P/'direct_review.json').read_text(encoding='utf-8')); edits={(x['session'],x['key']):x for x in rows}
def put(c,n,targets=None,note='',decision=None):
 s=next(s for s in d['sessions'] if s['id'][5:].startswith(c) and any(x['id']==n for x in s['users']+s['assistants']));role='user' if n.startswith('u_') else 'assistant';key=role+':'+n
 assert any(x['id']==n for x in s['users']+s['assistants']),n
 if key not in labs[s['id']]:return
 assert labs[s['id']][key].get('basis')!='human_explicit_selection',(c,key)
 for t in targets or []:assert any(x['id']==t for x in (s['assistants'] if role=='user' else s['users'])),t
 edits[s['id'],key]={'session':s['id'],'key':key,'decision':decision or ('matched' if targets else 'none'),'targets':targets or [],'note':note}
def m(c,n,t,why):put(c,n,t,why)
def no(c,n,why):put(c,n,[],why)
def unsure(c,n,why):put(c,n,[],why,'uncertain')
m('1484','u_d75e662d3f0b6f78a8',['a_db65952d0968455719','a_691211425c880724cb'],'输入补齐车次酒店，回复记录这些信息并转向偏好询问；剔除更早索取车次的回复。')
m('1484','u_978bf8d691f2f751a4',['a_ddd6b6f58282a72d66','a_d95afb4d6ae35b610e','a_cb5c5dbb25cb736472'],'美食与景点适中偏好对应后续路线规划及搜索，不对应前一轮车次信息查询。')
for n in ['u_ea6f23b1d6da96fe7d','u_223d31616a1316ec27','u_de60c3914a69f30dea']:
 no('98d4',n,'完整检索可见回复，英文内容对应附件文档或报价单；未找到本次英文架构图生成的对应回复，不用其他交付物顶替。')
unsure('98d4','u_aee73c077a266fdd77','输入问这张图讲什么，但缺少图像；现有素材查找回复未解释该图，无法确定。')
m('98d4','u_c0a2a04176b90dde23',['a_2df057315a1ed63e32'],'要求生成PDF，对应已交付5.5MB、9张配图PDF的回复；不是询问要不要导出PDF。')
m('98d4','u_7f105cf7200a6c468d',['a_8574b45b286b6e07f8','a_075eaad5d0692b3906'],'重复内容组中的60分钟时限要求与具体修改过程及确认对应；不推断独立调用次数。')
for n in ['a_c97a6e0345875293e3','a_2faf3e5822ab902931']:
 no('a49d',n,'过程与交付明确为删除开源商业模式内容；全部可见用户输入中没有这一请求，不能配给后续绘页或转PDF。')
for n in ['a_6f4821fbc3c225c52a','a_e43595d2b4783a1566']:
 no('7b0e',n,'全部可见用户输入中没有此基准游戏/基准清单问题；不与公众号或L1到L5制图任务混配。')
m('7b0e','a_fc146c08a3d59bdb32',['u_acb0209ed476543ee6','u_810a60735104029f08'],'三张截图检查承接三页配三图的制作要求。')
unsure('7b0e','a_78c148d6bf9e3e9c9c','只有去掉了、重新发布，未写删除对象；附近混有PPT和公众号任务，无法确定。')
m('7b0e','u_4982e77571c4001ad6',['a_64af49385bf0c3a864'],'设计确认后要求绘制，回复交付新增L1至L5第6页的PPT；与更早设计方案区分。')
m('7b0e','u_e14e9b26ac1aba92b1',['a_29314e4f431a37477a'],'确认生成LLM到自主Agent页面，回复交付浅色第7页。')
m('7b0e','a_c483750ecdc20c4d4d',['u_217514c6baee31d528'],'L1到L5设计方案对应先设计一页的要求。')
m('7b0e','a_ca7d55d9fbe05f3258',['u_90ae86dc9486998305'],'LLM到自主Agent浅色页方案对应明确设计要求，不是确认生成后的交付。')
m('b4c2','a_e21bbbe85d640ea640',['u_cdc0d001de1f90cf6a','u_3b095388d4f8e5c295'],'替换教师端内容的交付只对应教师端改写要求，与创新点更新分开。')
for n in ['u_9093b7d4597d20809e','u_f83e977122a850c324']:
 m('b4c2',n,['a_67388fa04611418c1e','a_360bf6f9840c631bbf'],'创新点更新对应明确报告技术、模式、机制创新修订的两条回复。')
no('e5c7','a_bd451f4e41b5a3731a','属于初始成绩计算Excel过程；可见用户只有之后请假考勤纠正，不能将旧成绩生成配作纠正结果。')
m('e5c7','a_e963651dc1af355ffb',['u_b7847c9b8e91d59edf','u_f3ad8196ccf57391be'],'两条重复要求均为正式对外的课程详细docx；回复对应该详细方案。')
m('e5c7','a_8076edb6ae2f7a80ef',['u_5e830259381ddbedbe'],'用户询问最终版本在哪里，回复说明4个文件和完整路径；不等于生成Word。')
m('e5c7','u_1608b96b221cef5c38',['a_3644b5e0e4bb3a1096'],'要求解释案例对应设计思维哪方面，回复逐案例映射共情、定义、原型等阶段。')
m('e5c7','u_2a9b8d6fb68b5af0e8',['a_023e6e85dd506b856b'],'要求最终课程方案转Word，对应20KB最终版docx交付。')
m('e5c7','a_cabec4cf39eeef520e',['u_d6a5850c55696f6cf2','u_a3c58c9973aa169ea1'],'该交付为更新Day1时间线后的课程方案docx/pdf，不是对外课程详细介绍。')
for n in ['u_a8665e1012cc27c41b','u_7c4751b1f86dca011c']:
 m('271a',n,['a_374964cd52e832408a'],'要求使用下载好的尽调技能查询，回复明确使用全面尽调技能逐一搜索；安装完成不是执行回答。')
for n in ['a_e24d2a9a0f9934979b','a_5f85bd327a1ee7f28b','a_732fefcc812e1a1fde','a_54d71a3c3f471a441e','a_b403df92fa1c96ff30']:
 m('fcee',n,['u_21e06791a1bbd4e80f','u_c66f0cbc4eac874490'],'回复均围绕企业一般纳税人资格查询及替代查询途径，对应两条同义查询输入。')
m('8e70','a_76af6003629240dedc',['u_defbedc381e68156f8'],'回复明确处理左半甬江人才徽章遮挡，对应同一具体遮挡反馈。')
m('8e70','a_205f7a19184f4fa49a',['u_5445edee43530e5aee'],'徽章浅色文字检测问题承接甬江人才文字丢失反馈。')
m('8e70','a_244f8eff3f8e2a8a04',['u_0433afcb7186e1e474'],'徽章裁剪后明确识别甬江人才/顶格项目团队并覆盖顶格，属于去掉顶格的编辑过程。')
m('8e70','a_25508efdfeb818fbfa',['u_38fdc7bce516af5576'],'字体JP回退排错对应全文错字乱码检查，不对应第8页遮挡。')
for n in ['a_6632faf7568e262eaa','a_bfc02c5227bb319ae1','a_8de7fef5ce5d0c8ec8']:
 m('ae36',n,['u_ebb3fd6832044b3b78'],'相邻具体过程指出论坛15页PPT数据页文字对比度和审计页拥挤，属于要点速览与PPT制作任务。')
unsure('ae36','a_3b6e49a16de37db106','编辑未落到文件的简短过程位于多个文档制作任务之间，未说明编辑对象，无法唯一归属。')
m('58cb','a_de05fd9600d4444c15',['u_6bc963958d2bea821b'],'回复明确不要具象人形、可以用手，逐项承接用户这轮更具体的Logo意见。')
m('f128','u_7b650061b7a5ccc14d',['a_8bcc2622b726dcae14','a_3e69b5bad71ea67129','a_ff91ae8b54383c2ca3','a_db73102ab037a20909'],'确认需求后开始制作HTML，保留执行链；不把之前请求确认清单当作确认后的回复。')
no('da7d','u_615694fe791a3c5f80','遍查本会话可见回复，没有回答一页纸篇幅是否适合公众号的问题；12页PPT空白检查属于不同任务。')
no('a08c','a_f8f7a4d4338f1fac0d','这是初始股东会框架建议，可见输入没有这一初始请求；不能与后续成品文件生成混配。')
for n in ['a_92397b28b5d1d6bd9d','a_2e3398914360121964']:
 m('a08c',n,['u_f2697c7ada8eda5512'],'表头主题色及247处文字不变检查对应四页商务风美化，非只改标题或另存文件。')
m('a08c','a_0763bdc2a7bb006d74',['u_0e1e56559f241c5536'],'预览保存与一页预期对实际经营对比PPT交付连续，对应初次一页制作。')
m('a08c','a_5b329c442ee1d6fb6a',['u_3d6860b139d9d521ba'],'渲染检查在三项纠正/黑白简约样式修改过程中，对应该次改版。')
m('0e5f','u_ea0c62aa51420b4e4f',['a_b53c3a31463445ebf2'],'选择起步平台问题对应平台玩法差异调研过程；该回复是过程，未据此声称已有完整结论。')
m('2007','a_eedc785b1757bd71b9',['u_3460cc46f05bff243c'],'回复引用连个商量的人都没有并分析offer，承接这段原始长对话；不是之后纠正不会接offer的回复。')
m('81cd','u_cbe11a39b0787c1b65',['a_52d2f96d2c2998ea97','a_190bfdee8945403b51'],'更正为三(1)材料后重新检查与交付，不包含被纠正前旧稿。')
no('27c2','a_ae115efd1b2c252402','只有任务中止状态，没有实际业务回复；按用户清理失败提示要求标记无有效匹配。')
m('23','u_d08cb14d058713234e',['a_365b8af54acbfa6bcb'],'要求整理沟通计划，回复给出具体五步计划，属于可确认的对应关系。')
m('81cd','a_5a71311ca29e309bee',['u_404ef5ecfb214bf938'],'全量35问交付对应把全部问题都回复的要求；不是之后更正附件的回复。')
unsure('079','u_3741fe3eb02bd4528b','同一句我已经搞定了折叠了多次出现，会话同时有凭据配置、扫码和文章导入；可见回复不足以确定这组对应哪一步，不用已配好的配置说明倒配。')
(P/'direct_review.json').write_text(json.dumps(list(edits.values()),ensure_ascii=False,indent=2),encoding='utf-8')
print('Saved',len(edits),'source review decisions')
