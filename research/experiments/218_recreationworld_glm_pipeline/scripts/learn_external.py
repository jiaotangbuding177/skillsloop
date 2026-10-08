"""Native AutoSkill trajectory entry for audited external canonical episodes.

No change to vendor extraction/maintenance, existing Co-Gym workers or libraries.
Text-based skills learning; visual provenance retained, no multimodal SDK claim.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT.parent/'115_cogym_spagent_full'
sys.path.insert(0,str(OLD/'scripts'));sys.path.insert(0,str(OLD/'vendor/AutoSkill'))
from autoskill_bootstrap import bootstrap
bootstrap()
from autoskill import AutoSkill
from autoskill.offline.trajectory.extract import extract_from_agentic_trajectory
from model_resource import get_model_id

def learn(manifest):
    if (ROOT/'private/STOP').exists(): raise RuntimeError('User STOP present')
    import fcntl
    lock=(ROOT/'learning.lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    audit=json.loads(manifest.read_text())
    if not audit.get('public_data_destination_approved') or not audit.get('family_disjoint_from_eval'):
        raise RuntimeError('Public provenance and family disjointness audit required')
    if not audit.get('inputs'): raise RuntimeError('No real inputs')
    acceptance=json.loads((ROOT.parent/'208_cogym_212_trajectory_learning/reports/embedding_acceptance.json').read_text())
    if not acceptance.get('passed') or acceptance.get('dimension')!=1024:
        raise RuntimeError('Real 1024-dimensional embedding acceptance required')
    label='218_external_'+str(time.time_ns())
    state=ROOT/'autoskill_state'/label
    state.mkdir(parents=True)
    resource=json.loads((ROOT.parent/'157_cogym_resource_completion/private/ecnu_embedding.json').read_text())
    if resource['model']!='ecnu-embedding-small': raise RuntimeError('Embedding identity changed')
    config=dict(llm=dict(provider='generic',model=get_model_id(),api_key='local',
        base_url=f'http://172.28.64.1:8129/{label}/learner/v1',timeout_s=240,max_tokens=8192,max_input_chars=1000000),
        embeddings=dict(provider='openai',model=resource['model'],base_url=resource['base_url'],api_key=resource['api_key'],
            timeout_s=60,max_batch_size=32,max_text_chars=10000,min_text_chars=512),
        store=dict(provider='local',path=str(state),include_libraries=False,include_legacy_root=False),
        namespace=label,maintenance_strategy='llm',max_context_chars=1000000)
    sdk=AutoSkill.from_config(config)
    # Reuse the already accepted ECNU evidence adapter without touching its old states.
    sys.path.insert(0,str(ROOT.parent/'196_cogym_212_ecnu_learning/scripts'))
    spec=importlib.util.spec_from_file_location('rw_ecnu_evidence',ROOT.parent/'196_cogym_212_ecnu_learning/scripts/learn_library_ecnu.py')
    prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
    evidence=prior.EmbeddingEvidence(sdk.store._embeddings,state/'embedding_operations.jsonl')
    sdk.store._embeddings=evidence
    for item in audit['inputs']:
        source=Path(item['path'])
        import hashlib
        if hashlib.sha256(source.read_bytes()).hexdigest()!=item['sha256']:raise RuntimeError('Input changed')
        data=json.loads(source.read_text())
        if not data.get('all_images_present'):raise RuntimeError('Incomplete multimodal provenance')
        for frame in data['frames']:
            if hashlib.sha256(Path(frame['screenshot']).read_bytes()).hexdigest()!=frame['screenshot_sha256']:
                raise RuntimeError('Screenshot provenance changed')
        result=extract_from_agentic_trajectory(sdk=sdk,user_id='pilot',file_path=str(source),
            success_only=False,include_tool_events=True,max_messages_per_record=0,max_events_per_record=0,
            continue_on_error=True,metadata={'phase_version':'rw_external_text_skills_v1','actual_outcome':data['task_outcome']},
            hint='Learn reusable execution workflows. Publisher observations are synthetic descriptions, not new verification. Preserve failure/unknown outcomes. Importer success means readable input, not task success. Images are provenance references; do not claim to have inspected their pixels.')
        with (state/'progress.jsonl').open('a') as f:f.write(json.dumps({'time':time.time(),'task_id':data['task_id'],'result':result})+'\n')
        if result['total_records']!=1 or result['processed']!=1 or result['failed'] or result['skipped'] or evidence.failed:
            raise RuntimeError('Native learning failed; partial attempt retained')
    target=ROOT/'libraries'/label;target.mkdir(parents=True)
    hashes={}
    for skill in sdk.list(user_id='pilot'):
        for name,text in sdk.export_skill_dir(skill.id).items():
            dest=(target/skill.id/name).resolve()
            if not dest.is_relative_to(target.resolve()):raise RuntimeError('Unsafe export')
            dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text,encoding='utf-8')
            hashes[str(dest.relative_to(target))]=hashlib.sha256(dest.read_bytes()).hexdigest()
    (state/'accepted_library.json').write_text(json.dumps({'processed':len(audit['inputs']),
        'embedding_errors':evidence.failed,'hashes':hashes,'empty_library':not hashes},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('audited_manifest',type=Path);a=p.parse_args();learn(a.audited_manifest)
