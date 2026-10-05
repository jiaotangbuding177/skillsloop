"""Deterministic AgentSkills export: scoped candidates, never a rewritten success story."""
import hashlib
import json
from pathlib import Path

from . import bootstrap, creator
from .pipeline import write_json
from .runtime import HEADINGS, digest, validate_bundle


def _line(value):
    # Model prose cannot inject new Markdown sections into the host's polarity layout.
    return ' '.join(str(value).split()).replace('<', '&lt;').replace('>', '&gt;')


def _condition(row):
    basis = {'PUBLIC_RULE':'公开规范（限所述版本）', 'USER_REQUIREMENT':'来源任务要求（复用时重新确认）',
             'OBSERVED':'当时观察到的条件，不等于必要条件', 'HYPOTHESIS':'尚待验证的条件'}.get(row.get('basis'), '条件来源未决')
    return f"{basis}：{_line(row.get('dimension',''))} = {_line(row.get('value',''))}"


def _checks(step):
    labels={'SATISFIED':'该项有支持', 'VIOLATED':'该项有反证', 'UNKNOWN':'该项未知', 'CONFLICT':'该项冲突'}
    return ['    - 核对 '+_line(c.get('criterion',''))+'：'+labels.get(c.get('status'),'未知')+
            ('；'+_line(c['unknownReason']) if c.get('unknownReason') else '') for c in step.get('checks',[])]


def _ordered(steps):
    remaining=list(steps);done=set();result=[]
    while remaining:
        ready=[s for s in remaining if set(s.get('dependsOn',[]))<=done]
        if not ready:raise ValueError('导出方法依赖缺失或形成环')
        for step in ready:
            result.append(step);done.add(step['id']);remaining.remove(step)
    return result


def _recipe_identity(variant):
    """Share identical instructional text; keep every witness in the audit JSON."""
    def clean(value):
        if isinstance(value,list):return [clean(v) for v in value]
        if not isinstance(value,dict):return value
        return {k:clean(v) for k,v in value.items() if k not in
                {'sourceRefs','supportRefs','counterRefs','sourceRef','evidenceClosure',
                 'traceId','methodId','pathWitness','stepMapping','reportedEvidence'}}
    return digest(clean({k:variant.get(k) for k in ('conditions','steps','unknowns')}))


def is_exportable(workflow):
    return any(s.get('kind') in ('ACTION','VISIBLE_OUTPUT')
               for v in workflow['variants'] for s in v['steps'])


def files_for(workflow):
    if not is_exportable(workflow):
        raise ValueError('只有计划或自述的工作流留在候选记录，不封装成技能')
    name='workflow-'+digest(workflow)[:16]
    title=_line(workflow['title'])
    description=f'处理{title}时参考；按当前工具、条件和要求选择对应方法，保留失败边界并核验未知结果。'
    out=['---', 'name: '+name, 'description: '+json.dumps(description,ensure_ascii=False), '---',
         '# '+title, '', '## 使用范围',
         '这是从实际记录归纳的候选方法。局部检查不证明整条路径成功；语义对应尚未独立核验。',
         '只使用当前环境实际提供的工具。先绑定本次对象与要求，再选择一个条件相符的来源路径；'
         '不要将不同路径自由拼成一条已经验证成功的新路径。成功回执不能代替业务验收。',
         '', '## 可参考的方法']
    excluded=[];shown={}
    for n,variant in enumerate(workflow['variants'],1):
        identity=_recipe_identity(variant)
        if identity in shown:
            out+=['',f'来源路径 {n} 与上面的路径 {shown[identity]} 具有相同正文、条件和局部状态；来源分别保留，不重复列操作。']
            continue
        shown[identity]=n
        out+=['',f'### 条件路径 {n}']
        conditions=variant.get('conditions',{})
        conditions=conditions.get('allOf',[]) if isinstance(conditions,dict) else conditions
        out+=['以下条件是共同约束，不是任选一项：'] if conditions else ['原材料未给出完整前置条件，执行前核对当前政策及本次要求。']
        out+=['- '+_condition(c) for c in conditions]
        if any(s.get('effectiveVerdict',s.get('verdict')) in ('VIOLATED','CONFLICT') for s in variant['steps']):
            out+=['此来源路径含失败或冲突，只保留下列局部参考；不能当作已完成的整段示范。']
        blocked={s['id'] for s in variant['steps'] if s.get('kind') not in ('ACTION','VISIBLE_OUTPUT')
                 or s.get('effectiveVerdict',s.get('verdict')) in ('VIOLATED','CONFLICT')}
        dependency_blocked=set()
        while True:
            found={s['id'] for s in variant['steps'] if set(s.get('dependsOn',[])) & blocked}-blocked
            if not found:break
            blocked.update(found);dependency_blocked.update(found)
        usable=0
        for step in _ordered(variant['steps']):
            if step['id'] in blocked:
                excluded.append((n,{**step,'dependencyBlocked':step['id'] in dependency_blocked})); continue
            usable+=1
            out+=['- 步骤 '+_line(step['id'])+'：'+_line(step['action'])+'（'+_line(step.get('actor','未知行动方'))+'；对象：'+_line(step.get('objectRole','未知'))+'）']
            out+=['    - '+_condition(c) for c in step.get('conditions',[])]
            if step.get('dependsOn'):
                out+=['    - 依赖步骤：'+', '.join(_line(x) for x in step['dependsOn'])+'；先核对其输入确实可用。']
            out+=_checks(step)
            if step.get('verdict')!='SATISFIED':out+=['    - 可见记录不等于效果已验证；执行后按本次目标检查，不直接宣称完成。']
        if not usable:out+=['本路径没有可推荐的实际操作；仅保留下面的失败观察或未执行内容。']
    out+=['','## 失败、冲突与未执行内容']
    for n,step in excluded:
        label='前置依据尚未成立，暂不作为连贯执行建议' if step.get('dependencyBlocked') else '未执行计划或完成自述' if step.get('kind') in ('CLAIM','PLAN') else '失败或冲突观察'
        out+=['- '+label+f'（路径 {n}）：'+_line(step['action'])+'。此项不是推荐操作，也不是已验证补救。']
        out+=['    - '+_condition(c) for c in step.get('conditions',[])]+_checks(step)
    for warning in workflow.get('warnings',[]):
        if isinstance(warning,dict):
            check=warning.get('check',{})
            out+=['- '+_line(warning.get('message','保留局部失败边界，不扩大到整个任务。'))+
                  (' 核对标准：'+_line(check['criterion'])+'。' if check.get('criterion') else '')]
            out+=['    - '+_condition(c) for c in warning.get('conditions',{}).get('allOf',[])]
        else:out+=['- 归纳边界：'+_line(warning)]
    for conflict in workflow.get('conflicts',[]):
        criteria=list(dict.fromkeys(r.get('check',{}).get('criterion','未明标准') for r in conflict.get('checks',[])))
        out+=['- 相同条件下，'+_line('、'.join(criteria))+' 同时有支持和反证。相关操作已移出建议；不要按多数成功忽略反例。']
    if not excluded and not workflow.get('warnings') and not workflow.get('conflicts'):
        out+=['未记录局部失败，不代表所有条件下均有效。']
    unknowns=[*workflow.get('unknowns',[])]
    for variant in workflow['variants']:unknowns.extend(variant.get('unknowns',[]))
    out+=['','## 完成检查与未决项',
          '- 逐项核对当前需求、对象、实际工具回执和交付。用户感谢、助手完成声明均不替代客观结果。',
          '- 只针对有核验依据的标准报告通过；其他标准明确写未知，不能继承别的来源的成功。']
    unknown_text=[x.get('text',str(x)) if isinstance(x,dict) else str(x) for x in unknowns]
    out+=['- '+_line(u) for u in dict.fromkeys(unknown_text)]
    out+=['','## 来源结构',
          '条件路径对应原观察片段；结构与局部检查见 references/workflow.json。该文件是证据记录，'
          '包含失败尝试和未执行计划，不可将其所有动作作为执行指令。', '', '## 市场信息']
    values=['执行相同目标的Agent或分析人员', '条件、局部核验与失败边界同时保留',title,
            '本次目标：___；目标对象：___；有效要求：___；可用工具与政策：___',
            '按当次目标核验的交付，以及明确列出的未知项']
    for heading,value in zip(HEADINGS,values):out+=['### '+heading,value]
    return validate_bundle([{'path':'SKILL.md','content':'\n'.join(out)+'\n'},
        {'path':'references/workflow.json','content':json.dumps(workflow,ensure_ascii=False,indent=2)+'\n'}])


def publish(root, workflows, official=True):
    root=Path(root); rows=[]
    for workflow in workflows:
        files=files_for(workflow)
        name='workflow-'+digest(workflow)[:16]
        directory=root/'skills'/name
        for item in files:
            path=directory/item['path'];path.parent.mkdir(parents=True,exist_ok=True)
            data=item['content'].encode('utf-8')
            if path.exists() and path.read_bytes()!=data:raise ValueError('不覆盖不同的已导出技能')
            path.write_bytes(data)
        receipt=None
        if official:
            workspace=root/'packaging'/name;workspace.mkdir(parents=True,exist_ok=True)
            receipt_path=workspace/'receipt.json'
            receipt=json.loads(receipt_path.read_text(encoding='utf-8')) if receipt_path.exists() else bootstrap.package(workspace,files)
            creator.verify_archive(workspace,receipt,files)
            write_json(receipt_path,receipt)
        rows.append({'id':name,'title':workflow['title'],'entry':f'skills/{name}/SKILL.md',
                     'workflowId':workflow['id'],'memberCount':len(workflow['memberIds']),
                     'semanticValidation':'NOT_INDEPENDENTLY_VERIFIED',
                     'validation':'STRUCTURAL_AND_OFFICIAL_PACKAGE' if official else 'STRUCTURAL_ONLY',
                     'package':f'packaging/{name}/'+receipt['path'].replace('\\','/') if receipt else None})
    write_json(root/'skills/index.json',{'skills':rows,'status':'CANDIDATE_LIBRARY',
        'note':'实验消费者可读取；效果需在独立任务上评测，不等于个人或组织正式发布。'})
    return rows


def _inventory(root):
    directory=root/'skills';result={}
    for path in sorted(directory.rglob('*')):
        if path.is_symlink():raise ValueError('冻结库不允许符号链接')
        if path.is_file():result[path.relative_to(root).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def freeze(root, skills, provenance):
    root=Path(root)
    manifest={'version':'skillsloop-frozen-library-v2','status':'READY_FOR_EXPERIMENT',
              'skills':skills,'files':_inventory(root),'provenance':provenance,
              'semanticValidation':'NOT_INDEPENDENTLY_VERIFIED'}
    manifest['manifestHash']=digest(manifest)
    write_json(root/'frozen_manifest.json',manifest)
    return manifest


def verify_frozen(root,require_completed_run=True):
    root=Path(root)
    manifest=json.loads((root/'frozen_manifest.json').read_text(encoding='utf-8'))
    if (manifest.get('manifestHash')!=digest({k:v for k,v in manifest.items() if k!='manifestHash'})
            or manifest.get('files')!=_inventory(root)):
        raise ValueError('冻结库文件、文件集合或清单已变化；不能混入同一实验批次')
    if manifest.get('status')!='READY_FOR_EXPERIMENT':raise ValueError('冻结库尚未完成')
    fingerprint=manifest.get('provenance',{}).get('runFingerprint')
    if require_completed_run and fingerprint:
        run_path=root/'run.json'
        run=json.loads(run_path.read_text(encoding='utf-8')) if run_path.exists() else {}
        if run.get('status')!='COMPLETED' or run.get('fingerprint')!=fingerprint:
            raise ValueError('冻结库所属运行未完成或身份不一致')
    return {'valid':True,'manifestHash':manifest['manifestHash'],'skillCount':len(manifest['skills'])}
