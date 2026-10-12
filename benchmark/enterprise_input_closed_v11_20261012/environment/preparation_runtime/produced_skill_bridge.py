"""Source-bound current-episode generated skill continuity; no business preset."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re

SOURCE_ID='conv_8bf9b42a552b'
REQUESTED_NAME='ali-iron-sales-method'


def write_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')


def trial_location(transport,trial_id):
    identity=hashlib.sha256(str(trial_id).encode()).hexdigest()[:24]
    return Path(transport)/'episode_created_skills'/identity


def fingerprints(workspace):
    workspace=Path(workspace).resolve();result={}
    for root in ('outputs','skills'):
        parent=workspace/root
        if not parent.is_dir():continue
        for file in sorted(parent.rglob('SKILL.md')):
            if file.is_symlink() or not file.is_file():continue
            resolved=file.resolve()
            if not resolved.is_relative_to(workspace/root):continue
            text=file.read_text('utf-8-sig')
            name=re.search(r'(?m)^name:\s*[\"\x27]?([^\n\r\"\x27]+)',text[:1500])
            result[file.relative_to(workspace).as_posix()]={
                'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),
                'bytes':file.stat().st_size,'frontmatter_name':name.group(1).strip() if name else None}
    return result


def handle_turn(context,workspace,transport,trial_id,dispatch_index,phase):
    """Bookend the creation turn; expose only that trial's actual changed SKILL."""
    if not isinstance(context,dict):return None
    creation=context.get('same_episode_skill_creation')
    consumption=context.get('same_episode_created_skill')
    condition=creation if dispatch_index==0 else consumption
    if not isinstance(condition,dict) or condition.get('required') is not True:return None
    if condition.get('session_id')!=SOURCE_ID:
        raise ValueError('Produced skill bridge is restricted to its declared complete source')
    if phase not in ('before_turn','after_turn'):raise ValueError('Unknown episode phase')
    workspace=Path(workspace).resolve();transport=Path(transport).resolve()
    location=trial_location(transport,trial_id)
    common={'schema':'current-episode-created-skill-v7','session_id':SOURCE_ID,
        'native_trial_id':str(trial_id),'dispatch_index':dispatch_index,'phase':phase,
        'historical_skill_body_injected':False,'original_business_answer_injected':False,
        'baseline_skill_injected':False}
    if dispatch_index==0:
        if phase=='before_turn':
            before=fingerprints(workspace)
            if (location/'before_creation.json').exists():
                raise ValueError('A native trial creation boundary cannot be restarted silently')
            receipt={**common,'before':before,'guide':
                '本轮如按用户要求总结并沉淀skill，请依据你实际读取的材料创建本次方法论。'
                '将带YAML name的SKILL.md保存到/workspace/outputs/skills/<你选定的名称>/SKILL.md，'
                '同一会话后续可以实际读取这个新产物；不要把历史答复或预写销售方案当作产物。'}
            write_json(location/'before_creation.json',receipt)
            return {k:v for k,v in receipt.items() if k!='before'}
        before=json.loads((location/'before_creation.json').read_text('utf8'))['before']
        after=fingerprints(workspace)
        candidates={path:item for path,item in after.items() if path not in before}
        receipt={**common,'current_actor_created_skills':candidates,
            'candidate_count':len(candidates),'available':bool(candidates)}
        write_json(location/'after_creation.json',receipt)
        return receipt
    if dispatch_index!=1 or phase!='before_turn':return None
    saved=location/'after_creation.json'
    if not saved.exists():
        receipt={**common,'available':False,'reason':'no_completed_current_trial_creation_boundary'}
    else:
        captured=json.loads(saved.read_text('utf8'))
        if captured.get('native_trial_id')!=str(trial_id):raise ValueError('Different native trial identity')
        current=fingerprints(workspace)
        candidates={path:item for path,item in captured['current_actor_created_skills'].items()
            if current.get(path,{}).get('sha256')==item['sha256']}
        exact=[path for path,item in candidates.items()
            if item.get('frontmatter_name')==REQUESTED_NAME or Path(path).parent.name==REQUESTED_NAME]
        selected=exact[0] if len(exact)==1 else next(iter(candidates)) if not exact and len(candidates)==1 else None
        receipt={**common,'available':selected is not None,'candidate_count':len(candidates)}
        if selected:
            source=workspace/selected
            alias=workspace/'environment_skills'/REQUESTED_NAME
            alias.parent.mkdir(parents=True,exist_ok=True)
            if alias.is_symlink():
                if alias.resolve()!=source.parent.resolve():raise ValueError('Current generated skill alias targets another directory')
            elif alias.exists():
                raise ValueError('Current generated skill alias would overwrite an existing input')
            else:alias.symlink_to(source.parent,target_is_directory=True)
            receipt.update({'current_generated_skill_path':str(source),
                'read_path':str(alias/'SKILL.md'),'alias_directory':str(alias),
                'current_generated_skill_sha256':candidates[selected]['sha256'],
                'current_generated_frontmatter_name':candidates[selected]['frontmatter_name'],
                'requested_skill_name':REQUESTED_NAME,'skill_bytes_modified':False,
                'alias_origin':'current_actor_output_from_canonical_dispatch_0',
                'guide':'当前用户提到的ali-iron-sales-method是本次上一轮产出的销售方法论。'
                    '本次路径映射仅建立名称别名，未预置旧skill、未改写正文。'
                    '请先用原生read完整读取 '+str(alias/'SKILL.md')+'，再结合本轮用户需求实际应用。'})
        else:
            receipt['reason']='missing_or_ambiguous_actual_current_trial_skill'
    if receipt.get('available') is not True:
        receipt['guide']='本次第一轮尚未留下唯一可映射的SKILL.md；没有提供历史沉淀包作替代。'
        receipt['guide']+='请先将你在本次上一轮依据已读材料形成的方法论实际保存为SKILL.md，再完整读取并用于本轮需求。'
    write_json(location/'turn_0002.created_skill_mapping.json',receipt)
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--context-file',required=True)
    parser.add_argument('--workspace',default='/workspace')
    parser.add_argument('--transport',default='/transport')
    parser.add_argument('--trial-id',required=True)
    parser.add_argument('--dispatch-index',type=int,required=True)
    parser.add_argument('--phase',choices=('before_turn','after_turn'),required=True)
    args=parser.parse_args()
    result=handle_turn(json.loads(Path(args.context_file).read_text('utf-8-sig')),
        args.workspace,args.transport,args.trial_id,args.dispatch_index,args.phase)
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
