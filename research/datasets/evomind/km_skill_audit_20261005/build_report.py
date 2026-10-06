"""Freeze observable skill evidence; do not claim complete KM inventory or applied methods."""
from pathlib import Path
from collections import defaultdict
import csv,hashlib,html,json,sys
ROOT=Path(__file__).resolve().parent;P=ROOT/'private';PROJECT=ROOT.parents[3]
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    events=json.loads((P/'classified_events.json').read_text(encoding='utf-8'))
    tools=json.loads((P/'normalized_skill_tools.json').read_text(encoding='utf-8'))
    rows=json.loads((ROOT/'skill_evidence_counts.json').read_text(encoding='utf-8'))
    positive={'successful_read','successful_shell_doc_read','script_execution_attempt'}
    known=[e for e in events if e['kind'] in positive and '*' not in e['skill']]
    runtime=[e for e in known if e['runtime_skill_path']]
    masked=[e for e in events if e['kind'] in positive and '*' in e['skill']]
    byname=defaultdict(list)
    for e in known:byname[e['skill']].append(e)
    result=[]
    for name,es in byname.items():
        rs=[e for e in es if e['runtime_skill_path']]
        reads=[e for e in es if e['kind'] in ['successful_read','successful_shell_doc_read']]
        scripts=[e for e in es if e['kind']=='script_execution_attempt']
        txt=[]
        for e in reads:
            out=tools[e['index']]['output']
            if isinstance(out,dict):txt.extend(x.get('text','') for x in out.get('content',[]) if isinstance(x,dict))
            elif isinstance(out,str):txt.append(out)
        result.append({'skill':name,'scope':'KM/OpenClaw明确运行技能目录' if rs else '工作区/相对路径或路径未知','sessions':len({e['session_id'] for e in es}),'runtime_sessions':len({e['session_id'] for e in rs}),'read_sessions':len({e['session_id'] for e in reads}),'script_sessions':len({e['session_id'] for e in scripts}),'has_returned_content':any(t.strip() and not t.strip().startswith('[已读取') for t in txt),'has_read_receipt':any(t.strip().startswith('[已读取') for t in txt),'session_ids':sorted({e['session_id'] for e in es}),'evidence_indices':sorted({e['index'] for e in es})})
    result.sort(key=lambda x:(x['runtime_sessions']==0,-x['runtime_sessions'],-x['sessions'],x['skill']))
    summary={'corpus_sessions':1466,'known_consumption_skill_identifiers':len(byname),'known_consumption_sessions':len({e['session_id'] for e in known}),'known_runtime_skill_identifiers':len({e['skill'] for e in runtime}),'known_runtime_sessions':len({e['session_id'] for e in runtime}),'outside_runtime_or_path_unknown_identifiers':len({e['skill'] for e in known}-{e['skill'] for e in runtime}),'masked_skill_read_sessions':len({e['session_id'] for e in masked}),'known_read_skill_identifiers':len({e['skill'] for e in known if e['kind'] in ['successful_read','successful_shell_doc_read']}),'known_script_attempt_skill_identifiers':len({e['skill'] for e in known if e['kind']=='script_execution_attempt'}),'deduplication':'skill directory identifier; versions and aliases not independently verified','complete_inventory':False,'applied_methods_or_task_success_verified':False}
    assert summary['known_consumption_skill_identifiers']==81 and summary['known_runtime_skill_identifiers']==74
    assert summary['known_consumption_sessions']==399 and summary['known_runtime_sessions']==386
    dump(ROOT/'summary.json',summary);dump(P/'skills_by_evidence.json',result)
    with (ROOT/'skills.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['技能标识','位置范围','有消费证据的会话数','明确运行目录会话数','有读取记录的会话数','有脚本执行尝试的会话数','返回过正文或资源内容','有简化读取回执','会话编号'])
        w.writerows([r['skill'],r['scope'],r['sessions'],r['runtime_sessions'],r['read_sessions'],r['script_sessions'],r['has_returned_content'],r['has_read_receipt'],'|'.join(r['session_ids'])] for r in result)
    lines=['# EvoMind真实数据：KM/OpenClaw技能消费记录统计','日期：2026-10-05。范围为现有1,466条会话。没有连接KM或生产，没有运行技能。',
    '**按已导出工具记录，目前能识别74种位于明确KM/OpenClaw技能运行目录的技能，涉及386条会话。** 统计的是已完成读取技能说明/参考资源或实际发起脚本调用的记录，不是完整库存、版本数、业务成功或方法执行正确率。',
    '扩大到工作区技能包和路径缺失的技能文档后，共81个可识别标识、399条会话：其中74种有明确运行目录，6种只有工作区或相对路径证据，1种只有返回技能文档但缺路径。另有4条会话读取了技能名被脱敏的文件，身份无法可靠恢复，不并入唯一技能数。',
    '## 为什么需要更正上一轮说法',
    '此前根据用户“agent没有skills”的说明，将本批历史会话按无真实技能处理；这不能继续扩成“KM底层没有技能消费”。本轮查看工具载荷和原始工具样本，发现明确读取及脚本调用。用户文字中的“技能已创建”“请使用技能”仍然不作为使用证据；新更正来自工具层记录，而不是这些声明。',
    '这也不证明这些技能由本项目算法生成、组织审核通过或在某任务上起效。`emerged-`前缀只能作为名称，生成来源、版本、真实采纳和权限仍待补证。旧报告与原初判保留，本报告及最新STATE为更正入口。',
    '## 统计口径和数据来源',
    '- 读取：read工具有技能文件/资源路径、完成状态及非空输出；返回可以是部分正文或简化“已读取”回执，不能称完整SKILL.md注入。cat等命令读取文档也单独识别。',
    '- 脚本：实际发起技能目录内的脚本命令；不把列目录、复制、写技能、安装依赖或--help计为消费。执行尝试不自动当脚本成功或业务成功。',
    '- 唯一技能按目录标识去重，同标识不同用户/版本不另加；同一会话读多次只计一个覆盖会话。没有bundle hash和正式库存，不能证明别名与内容级唯一性。',
    '- 来源一：066保留的1,466条会话中rawPayload.toolActivity活动快照。来源二：原始导出raw_payload_sample.jsonl，共1,391条结构抽样记录，1,373条归本批会话；它不是完整工具日志。',
    '- 纳入运行目录：/opt/openclaw-shared-skills/、/opt/evomind-shared-skills/、/opt/evomindskills/、用户.openclaw/.evomind及/home/km-agent/skills。目录证据不代替KM正式注册表。',
    '- 原包约9.3万行工具及返回未导出，因此74是当前可观测的目录标识数量；实际历史总量、完整使用频次和库存数量仍未知。本文不按抽样比例外推。',
    '## 各技能和会话覆盖',
    '此表包含81个可识别标识。运行目录列用于区分主要74种；涉及会话数不是使用次数，也不是成功任务数。',
    '| 技能标识 | 有证据会话数 | 明确运行目录会话数 | 脚本尝试会话数 | 范围 |','|---|---:|---:|---:|---|']
    for r in result:lines.append(f"| {r['skill']} | {r['sessions']} | {r['runtime_sessions']} | {r['script_sessions']} | {'运行技能目录' if r['runtime_sessions'] else '工作区/路径未知'} |")
    lines+=['## 当前能证明和不能证明什么',
    '有目录+读取记录，可以说“已导出日志记录过读取这类技能”。例如PDF、Word、图片生成、论文资料、合同审查等技能可定位到会话和工具调用。只有简化读取回执的案例，仍应向KM补当时技能正文和版本。',
    '不能据此说“74种技能全部有效使用”“有386个成功任务”“本项目生成74种技能”，也不能用技能读取覆盖率代替业务收益。没有读取记录的会话也不能当无技能对照：可能有自动注入，或对应日志没有导出。',
    '## 如何补齐KM侧实际完整数量',
    '数据方按会话—用户—agent实例—KM原生会话键映射，补完整history及当时技能库存/版本。当前GET /api/km/skills只说明当前可见库存；结合GET /api/km/skills/{id}/bundle、个人revisions及历史备份才能核对当时状态。平台skill_inventory_snapshots和skill_usage_events可辅助，但选中不等于消费，原schema需线上核对。',
    '每种技能交技能ID/目录标识、版本/hash、生效区间与全包；每次使用交会话/请求/真实调用编号及注入、读取、脚本调用分别的证据。只有这样才能补成完整历史计数和可靠的有/无技能分组。',
    '## 交付',
    '- [技能清单CSV](../datasets/evomind/km_skill_audit_20261005/skills.csv)；[逐技能来源查看页](../datasets/evomind/km_skill_audit_20261005/private/index.html)。',
    '- [原数据补交说明](2026-10-05_evomind_data_supplement_request.md)及[本轮统计JSON](../datasets/evomind/km_skill_audit_20261005/summary.json)。旧补交说明中的历史无技能假定由本报告更正，其他文件/工具/时间缺口仍成立。',
    '原始输出留在本地受控目录，不复制凭据到报告或记忆。没有改写原数据、071标注、全量主题标签或用户当前人工标注。']
    report=PROJECT/'research/reports/2026-10-05_evomind_km_skill_usage.md';report.write_text('\n\n'.join(lines[:lines.index('| 技能标识 | 有证据会话数 | 明确运行目录会话数 | 脚本尝试会话数 | 范围 |')])+'\n\n'+'\n'.join(lines[lines.index('| 技能标识 | 有证据会话数 | 明确运行目录会话数 | 脚本尝试会话数 | 范围 |'):lines.index('## 当前能证明和不能证明什么')])+'\n\n'+'\n\n'.join(lines[lines.index('## 当前能证明和不能证明什么'):])+'\n',encoding='utf-8')
    body=[]
    for r in result:
        refs=[]
        for i in r['evidence_indices']:
            es=[e for e in byname[r['skill']] if e['index']==i]
            for e in es:
                refs.append('<p><a href="../../matched_066/private/conversations/'+html.escape(e['session_id'])+'.html">'+html.escape(e['session_id'])+'</a> · '+html.escape(e['kind'])+' · '+html.escape(str(e['tool_call_id'] or '无调用编号'))+'<br>'+html.escape('；'.join(e['paths']) or '路径缺失，依据返回技能文档')+'</p>')
        body.append('<tr><td>'+html.escape(r['skill'])+'</td><td>'+html.escape(r['scope'])+'</td><td>'+str(r['sessions'])+'</td><td>'+str(r['runtime_sessions'])+'</td><td><details><summary>查看来源</summary>'+''.join(refs)+'</details></td></tr>')
    page='<!doctype html><meta charset="utf-8"><title>KM技能消费记录核查</title><style>body{font:15px Microsoft YaHei;background:#f4f7fa;padding:30px;color:#25425c}table{border-collapse:collapse;width:100%;background:white}th,td{padding:12px;border-bottom:1px solid #dce4ee;text-align:left;vertical-align:top}a{color:#276b9f}summary{cursor:pointer}details p{font-size:12px;overflow-wrap:anywhere}input{padding:10px;width:400px;max-width:100%}</style><h1>KM/OpenClaw技能消费记录</h1><p>74种明确运行技能目录，386条会话；扩大到其他技能材料共81种、399条会话。读取不等于有效使用，原工具日志未导全。</p><p><a href="../../../../reports/2026-10-05_evomind_km_skill_usage.md">完整报告</a> · <a href="../skills.csv">技能清单CSV</a></p><input id="q" placeholder="搜索技能名称或会话编号"><table><thead><tr><th>技能</th><th>位置范围</th><th>有证据会话数</th><th>运行目录会话数</th><th>工具来源</th></tr></thead><tbody>'+''.join(body)+'</tbody></table><script>document.getElementById("q").oninput=function(){let q=this.value.toLowerCase();document.querySelectorAll("tbody tr").forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q))}</script>'
    (P/'index.html').write_text(page,encoding='utf-8')
    inputs=[ROOT.parent/'matched_066/private/evomind_conversations.json',Path('C:/Users/39835/Downloads/zkys-raw-export-20260925/raw_payload_sample.jsonl')]
    manifest={'inputs':{str(p):sha(p) for p in inputs},'summary':summary,'unique_names_do_not_include_masked_identities':True,'outputs':{str(p.relative_to(PROJECT)):sha(p) for p in [report,ROOT/'skills.csv',ROOT/'summary.json',P/'index.html',P/'classified_events.json']}}
    dump(ROOT/'manifest.json',manifest)
    sys.stdout.reconfigure(encoding='utf-8');print(json.dumps({'summary':summary,'top_runtime_skills':[{k:r[k] for k in ['skill','runtime_sessions']} for r in result[:12]],'outside_runtime':[r['skill'] for r in result if not r['runtime_sessions']]},ensure_ascii=False))
if __name__=='__main__':main()
