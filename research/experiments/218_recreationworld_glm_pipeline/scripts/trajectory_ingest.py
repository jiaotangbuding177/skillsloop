"""Normalize one official AgentNet episode, requiring every screenshot.

Preserve unknown/failed outcomes; publisher-synthesized observations are labelled.
No screenshot caption invention, score filtering, private reasoning, or truncation.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

def normalize(item, images, family):
    if not family.strip(): raise ValueError('Source family required for split audit')
    if not item.get('task_id') or not item.get('traj'): raise ValueError('Empty trajectory')
    frames=[]
    for number,step in enumerate(item['traj']):
        if step.get('index')!=number: raise ValueError('Noncontiguous source ordering')
        name=step.get('image')
        if not name or Path(name).name!=name: raise ValueError('Unsafe screenshot name')
        candidates=list(images.rglob(name))
        if len(candidates)!=1: raise ValueError(f'Missing or ambiguous screenshot at step {number}')
        picture=candidates[0].resolve()
        with Image.open(picture) as decoded: decoded.verify()
        value=step.get('value',{})
        if not value.get('code'): raise ValueError('Missing demonstrated action')
        frames.append({'step':number,'screenshot':str(picture),
            'screenshot_sha256':hashlib.sha256(picture.read_bytes()).hexdigest(),
            'publisher_observation':value.get('observation'),
            'observation_origin':'publisher-synthesized, not a newly verified observation',
            'executed_action':value['code'],'publisher_action_description':value.get('action'),
            'publisher_last_step_correct':value.get('last_step_correct')})
    return {'schema':'rw_external_execution_v1','source':'xlangai/AgentNet',
        'source_revision':'d76ee50a63fad81cfdbe576416757d7c2091ed50',
        'task_id':item['task_id'],'family':family,'instruction':item['instruction'],
        'task_outcome':{'publisher_task_completed':item.get('task_completed'),
            'benchmark_score':None,'outcome_source':'publisher label, not RecreationBench score'},
        'trajectory_type':'human demonstration with synthetic enrichment',
        'frames':frames,'all_images_present':True,'learning_representation':'text actions and labelled publisher observations; images retained as provenance, not claimed ingested by text AutoSkill'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--record',type=Path,required=True)
    p.add_argument('--image-root',type=Path,required=True);p.add_argument('--family',required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists(): raise RuntimeError('Refuse overwrite of canonical input')
    data=normalize(json.loads(a.record.read_text()),a.image_root,a.family)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'task_id':data['task_id'],'frames':len(data['frames']),'complete':True}))
