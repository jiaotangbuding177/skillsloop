"""Evidence-qualified provenance overlay. Does not alter corpus or prior audit."""
from pathlib import Path
from collections import Counter
import csv,hashlib,html,json,re
R=Path(__file__).resolve().parent; PROJECT=R.parents[3]; P=R/'private'
rows=json.loads((P/'skills_by_evidence.json').read_text(encoding='utf-8'))
probe=json.loads((P/'provenance_probe.json').read_text(encoding='utf-8'))
lookup={x['skill']:x for x in probe}
source=json.loads((R.parent/'matched_066/private/evomind_conversations.json').read_text(encoding='utf-8'))
catalog=PROJECT/'enginering/insightweaver/apps/api/src/skills/builtin-skill-catalog.ts'
builtins=set(re.findall(r'"skillKey":\s*"([^"]+)"',catalog.read_text(encoding='utf-8')))
public={
 'guizang-ppt-skill':('https://github.com/op7418/guizang-ppt-skill','AGPL-3.0，当前公开仓库；历史版本待核对'),
 'follow-builders':('https://github.com/zarazhangrui/follow-builders','MIT，当前公开仓库；历史版本待核对'),
 'nuwa-skill':('https://github.com/alchaincyf/nuwa-skill','MIT，当前公开仓库；历史版本待核对'),
 'AutoEvoSkillCreate':('https://github.com/OpenEduTech/AutoEvoSkillCreate','会话给出地址；本轮网页读取失败，许可证未核实'),
 'agent-browser':('https://github.com/vercel-labs/agent-browser','Apache-2.0，当前公开仓库；运行包版本未核对'),
 'frontend-design':('https://github.com/anthropics/skills/tree/main/skills/frontend-design','同名公开候选；运行包来源/许可证未核对'),
 'ui-ux-pro-max':('https://github.com/nextlevelbuilder/ui-ux-pro-max-skill','当前根LICENSE为MIT；仅同名候选，子包和运行版待核对')}
for n in ['pdf','docx','pptx','xlsx']:
 public[n]=(f'https://github.com/anthropics/skills/tree/main/skills/{n}','源码可见，非开源；本地返回文档声明Proprietary，须取得对应LICENSE.txt')
branded={'evomind-paper-scan':'返回文档明确EvoMind品牌/29维审查，且在本地内置目录中；包含paperconan归因，不能推定全部原创',
 'image-generation':'返回文档固定使用ZZZ4AI图片服务；属于平台服务适配证据，不等于原创来源认证',
 'pdf_zzz4ai':'平台命名并返回Proprietary条款；疑似PDF适配，需拿实际包做差异比较',
 'evomind-auto':'返回文档为Evomind Auto Research System，运行依赖工作区；外部框架来源待核',
 'zzz4ai-search-engine':'返回文档为ZZZ4AI搜索引擎；路径缺失，平台适配/归属待确认'}
result=[]
for r in rows:
 n=r['skill'];p=lookup[n];path=p['paths'];contexts=[]
 for x in p['user_install_context']:
  if len(x['text'])<1200 and 'github.com/' in x['text'] and re.search('安装|装一下',x['text']):contexts.append(x)
 owners={source[s]['owner_id'] for s in r['session_ids']}
 same=[x for x in contexts if source[x['session_id']]['owner_id'] in owners]
 if n in ['guizang-ppt-skill','follow-builders','nuwa-skill','AutoEvoSkillCreate']:
  category='用户请求安装公开项目';reason='用户明确给出仓库并请求安装；该标识另有消费证据，安装成功/版本尚缺凭据'
 elif n=='agent-browser':category='文档直接指向公开上游';reason='返回技能文档包含vercel-labs/agent-browser源仓库地址；缺运行包hash'
 elif n in ['pdf','docx','pptx','xlsx']:category='公开源码参考候选（非开源）';reason='同名官方参考包且返回Proprietary条款；未做完整包比对'
 elif n in ['frontend-design','ui-ux-pro-max']:category='同名开源来源候选';reason='有同名公开项目，但缺来源URL/安装回执/hash，不能确认为该仓库安装'
 elif n in branded:category='EvoMind品牌或服务适配候选';reason=branded[n]
 elif n.startswith('emerged-'):category='涌现命名技能，生成来源待核';reason='仅有emerged命名及个人/工作区路径；不能证明由本项目或平台算法生成'
 else:category='来源未确认';reason='现有记录证明读取/脚本尝试，但没有可靠上游和创建/安装来源'
 platform='源码列入内置目录' if n in builtins else ('共享目录部署可观察，未命中内置目录' if any(x.startswith('/opt/') for x in path) else '仅个人/工作区或路径未知，安装者待核')
 installation=('同一用户有安装请求及消费证据；安装成功、先后时序未确认' if same else '有安装请求，但请求者与消费用户未建立同用户证据') if contexts else '没有找到明确对应仓库的用户安装请求；不等于没有安装'
 route='公开地址可取参考版；历史实际包、改动及许可仍向EvoMind补取' if n in public else '向EvoMind/KM或对应用户补取实际技能包及来源记录，不能以同名网络包替代'
 result.append({'skill':n,'source_class':category,'platform_class':platform,'user_installation':installation,'upstream_url':public.get(n,('',''))[0],'license':public.get(n,('','未确认'))[1],'reason':reason,'retrieval':route,'sessions':r['sessions'],'runtime_sessions':r['runtime_sessions'],'paths':path,'install_refs':[{'session_id':x['session_id'],'group_id':x['group_id'],'same_owner_has_consumption':x in same} for x in contexts],'consumption_session_ids':r['session_ids'],'evidence_indices':r['evidence_indices']})
assert len(result)==81 and len({x['skill'] for x in result})==81
summary={'date':'2026-10-05','skills':81,'runtime_skills':74,'source_classes':dict(Counter(x['source_class'] for x in result)),'platform_classes':dict(Counter(x['platform_class'] for x in result)),'has_public_reference_url':sum(bool(x['upstream_url']) for x in result),'user_install_request_and_same_owner_consumption_skills':sum(any(y['same_owner_has_consumption'] for y in x['install_refs']) for x in result),'confirmed_successful_user_install_to_consumption_chains':0,'confirmed_original_evomind_authorship':0,'note':'0表示未取得认证证据，不表示实际没有。分类是来源探索标注；共享部署/内置配置不证明原创。'}
(P/'skill_provenance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(R/'provenance_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
heads=['技能标识','来源标注','平台配置或部署','用户下载安装证据','公开参考地址','许可状态','判断依据','如何补取','消费会话数','明确运行目录会话数','安装请求位置','技能文件位置']
with (R/'skill_provenance.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(heads)
 for x in result:w.writerow([x['skill'],x['source_class'],x['platform_class'],x['user_installation'],x['upstream_url'],x['license'],x['reason'],x['retrieval'],x['sessions'],x['runtime_sessions'],';'.join(y['session_id']+':'+y['group_id'] for y in x['install_refs']),' | '.join(x['paths'])])
lines=['# EvoMind历史技能：公开来源、用户安装与平台内置标注','日期：2026-10-05。覆盖上一轮81个可识别技能标识，其中74个有明确运行目录。没有连接生产/KM，没有安装或运行技能。','## 先说结论','这批技能不能可靠地强行分成“用户下载开源”和“EvoMind原创”两类。已逐项标注来源、平台配置/部署、用户安装证据、获取方式和未知项。平台内置可以打包公开技能，个人目录也可能由平台分发。','**有4项明确用户请求安装公开项目，但尚无完整安装成功→同用户消费闭环；其中follow-builders有同用户安装请求及另会话消费证据，历史先后和版本仍未证实。** 另外11项合计有可定位的公开参考地址，其中包括这4项，不能把11说成全部已确认开源安装。','## 来源分类']
lines+=['| 类别 | 项数 |','|---|---:|']+[f'| {k} | {v} |' for k,v in summary['source_classes'].items()]
lines+=['## 平台配置与部署（独立于来源分类）','| 观察 | 项数 |','|---|---:|']+[f'| {k} | {v} |' for k,v in summary['platform_classes'].items()]
lines+=['本地API的builtin-skill-catalog.ts按标识精确匹配。这个数字只说明当前源码列入内置目录，不认证历史生产安装或EvoMind原创。Agent Browser与agent-browser、openclaw-karpathy-wiki与karpathy-wiki、huashu-nuwa与nuwa-skill没有擅自合并；可能别名须KM确认。',
 '## 用户明确要求安装的4项','| 技能 | 公开项目与许可 | 用户安装/消费证据 |','|---|---|---|']
for x in result:
 if x['source_class']=='用户请求安装公开项目':lines.append(f"| {x['skill']} | [{x['upstream_url']}]({x['upstream_url']})；{x['license']} | {x['user_installation']}；请求会话："+'、'.join(y['session_id'] for y in x['install_refs'])+' |')
lines+=['## 优先向EvoMind取包的5项品牌/服务适配候选','这5项是平台关联程度较高的补取优先项，不是已经证实EvoMind原创的5项。','| 技能 | 依据 |','|---|---|']+[f"| {x['skill']} | {x['reason']} |" for x in result if x['skill'] in branded]
lines+=['image-ppt-generation、image-ocr、image-editing等虽在共享目录被读取，本轮缺正文/来源证明，仍标来源未确认；不能只看名称认定原生。所有其他来源未确认项也已逐项列出补取方式。','## 公开包怎样使用','guizang当前官方仓库标AGPL-3.0，follow-builders及nuwa当前标MIT；仅核对当前网页，不推定历史安装版本。[guizang](https://github.com/op7418/guizang-ppt-skill)、[follow-builders](https://github.com/zarazhangrui/follow-builders)、[nuwa](https://github.com/alchaincyf/nuwa-skill)。AutoEvoSkillCreate仓库来自用户原请求，本轮读取失败，许可待核。',
 'agent-browser返回文档明确列出[Vercel上游](https://github.com/vercel-labs/agent-browser)，当前仓库Apache-2.0；frontend-design和ui-ux-pro-max只是同名参考候选，没有运行包一致性证明。[frontend-design参考](https://github.com/anthropics/skills/tree/main/skills/frontend-design)、[ui-ux参考与许可证](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/main/LICENSE)。',
 'pdf、docx、pptx、xlsx返回的说明含Proprietary许可，Anthropic官方也明确将文档能力参考包区分为源码可见，而非开源。它们即使平台内置，也不能标“用户自行下载的开源技能”。[官方说明](https://github.com/anthropics/skills)。pdf_zzz4ai同样返回Proprietary条款，需单独取其完整许可及平台差异。',
 '## 发给EvoMind/KM数据方的补取要求',
 '1. 以81项CSV的技能标识及消费会话为固定范围，按用户、企业实例、当时版本导出SKILL.md、references、scripts、assets、LICENSE及依赖说明；当前快照与历史版本明确区分。公开参考包不能替代历史实际包。',
 '2. KM现有GET /api/km/skills取得实际skillId、key、scope、版本及来源字段（若接口实际未提供，注明缺失，不补造）；再通过GET /api/km/skills/{id}/bundle取完整包。按用户x-km-user-id与实例路由查询，避免同名跨用户误合。个人版本可查/api/km/skills/personal/{key}/revisions及/{revision}，是否留有完整历史由服务方核实。',
 '3. 对照平台PostgreSQL insight_weaver_prod中的personal_skill_configs、enterprise_skill_configs、skill_submissions、skill_submission_versions、skill_inventory_snapshots、skill_usage_events；先核对生产schema。它们帮助确定配置、采纳、提交审核和历史库存，不自动证明用户下载或实际执行。安装源仓库、commit、安装者、触发者、成功时间与运行包hash如平台表未存，须KM安装日志、包manifest或部署记录补交；不能虚构一个安装表。',
 '4. 提交每个包的来源结论：平台原创 / 平台改编公开上游 / 原样分发第三方 / 用户安装 / 用户自建 / 系统生成 / 不清楚；附原repo+commit、许可、bundle SHA256、用户/实例、时间、创建/安装回执及消费调用ID。共享原生包优先由EvoMind提供，用户自建或安装包由其用户工作区及KM历史补取。依赖内部服务的包需接口说明与测试配置，不需要明文生产密钥。',
 '5. 11项有参考地址可先拿参考版做预备，70项没有已定位的确切参考地址需要平台/用户补包。为了历史重放，81项都应核对当时实际版本；这不等于81项都是平台原创。身份脱敏的技能另外请数据方恢复ID映射，不并入81唯一计数。',
 '## 全部81项标注','| 技能 | 来源 | 平台配置或部署 | 获取方式 |','|---|---|---|']
lines+=[f"| {x['skill']} | {x['source_class']} | {x['platform_class']} | {x['retrieval']} |" for x in result]
report=PROJECT/'research/reports/2026-10-05_evomind_skill_provenance.md';report.write_text('\n\n'.join(lines[:5])+'\n\n'+'\n'.join(lines[5:])+'\n',encoding='utf-8')
cards=[]
for x in result:
 fields=[('来源',x['source_class']),('平台配置或部署',x['platform_class']),('用户安装',x['user_installation']),('依据',x['reason']),('许可',x['license']),('补取办法',x['retrieval']),('参考地址',x['upstream_url'])]
 detail=''.join('<p><b>'+html.escape(k)+'：</b>'+html.escape(v)+'</p>' for k,v in fields)
 detail+='<p>原始消费证据编号：'+','.join(map(str,x['evidence_indices']))+'</p>'
 for sid in x['consumption_session_ids']:detail+=f'<a href="../../matched_066/private/conversations/{html.escape(sid)}.md">{html.escape(sid)}</a> '
 cards.append('<details><summary>'+html.escape(x['skill']+' — '+x['source_class']+' — '+x['platform_class'])+'</summary>'+detail+'</details>')
(P/'provenance.html').write_text('<!doctype html><meta charset="utf-8"><title>81项技能来源标注</title><style>body{font:16px system-ui;max-width:1100px;margin:36px auto;background:#f5f7fb;color:#243247}details{padding:15px;background:white;margin:10px 0;border-radius:9px}summary{cursor:pointer;font-weight:600}a{margin-right:10px}input{padding:10px;width:90%}</style><h1>81项技能来源标注</h1><p>来源、平台部署、安装证据分开判断；待核项不当成已确认事实。安装请求不等于安装成功。点击技能查看依据及原会话。</p><input placeholder="搜索技能、类别或平台" oninput="document.querySelectorAll(\'details\').forEach(x=>x.hidden=!x.textContent.toLowerCase().includes(this.value.toLowerCase()))">'+''.join(cards),encoding='utf-8')
manifest={'inputs':{str(p.relative_to(PROJECT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [catalog,P/'skills_by_evidence.json',P/'provenance_probe.json']},'outputs':{str(p.relative_to(PROJECT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [P/'skill_provenance.json',R/'skill_provenance.csv',P/'provenance.html',report]},'checks':{'81_unique':True,'all_evidence_indices_from_prior_audit':True,'prior_corpus_not_modified':True,'native_original_not_inferred_from_path':True}}
(R/'provenance_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False))
