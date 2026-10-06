"""Reproducible outer orchestration of unmodified author functions.

Public calibration and enterprise experiments have separate run directories.
No custom analyst, MAP prompt, MERGE prompt, or patch application is used.
"""
from __future__ import annotations
import argparse, dataclasses, hashlib, json, os, shutil, subprocess, sys, traceback
from types import SimpleNamespace
from pathlib import Path
from audited_runtime import (HERE,PROJECT,BASELINE,bootstrap_imports,dump,sha,
                             RequestAudit,instrument_sdk,platform_adapter,windows_bash_factory)

COMMIT='3d0b52a140f002a512930252b613c49048f7d5ac'
DATA=BASELINE/'data/spreadsheetbench_verified/spreadsheetbench_verified_400'

def json_safe(v):
    if dataclasses.is_dataclass(v): return json_safe(dataclasses.asdict(v))
    if isinstance(v,dict): return {str(k):json_safe(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)): return [json_safe(x) for x in v]
    if isinstance(v,Path): return str(v)
    return v

def guard_source():
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=BASELINE,text=True).strip()
    changed=subprocess.check_output(['git','diff','--name-only'],cwd=BASELINE,text=True).strip()
    if commit!=COMMIT or changed: raise RuntimeError('Author commit/source differs from frozen baseline')
    files=subprocess.check_output(['git','ls-files'],cwd=BASELINE,text=True).splitlines()
    return {'commit':commit,'tracked_diff':changed,'files':{
        f:sha(BASELINE/f) for f in files if (BASELINE/f).is_file() and (f.endswith('.py') or f.endswith('.txt') or f.startswith('gen_config/'))}}

def settings(phase, seed):
    from profiles import load_profile,generation_config_for
    native_phase={'error':'error_analysis','success':'success_analysis','consumer':'rollout'}.get(phase,phase)
    # Author README does not explicitly seed success/error analysis.
    return generation_config_for(load_profile('paper_v5'),native_phase,
                                 None if native_phase in {'error_analysis','success_analysis'} else seed)

def native_client(seed,phase,run):
    from src.react_agent.models import OpenAIClient
    return OpenAIClient(model=os.environ.get('TRACE2SKILL_MODEL','ecnu-plus'),
        api_key=os.environ.get('ECNU_API_KEY') or os.environ.get('OPENAI_API_KEY'),
        base_url=os.environ.get('TRACE2SKILL_BASE_URL','https://chat.ecnu.edu.cn/open/api/v1'),
        cache_path=str(run/'cache'/f'{phase}-seed-{seed}'),generation_config=settings(phase,seed))

def checker_ready():
    from skill_evolver.skill_evolving_agent import QUICK_VALIDATE_SCRIPT
    if not QUICK_VALIDATE_SCRIPT.is_file():
        raise RuntimeError(f'Real author checker missing at cwd-relative path: {QUICK_VALIDATE_SCRIPT}')

def apply_runtime_environment(path):
    doc=json.loads(Path(path).read_text(encoding='utf-8'))
    controls=doc.get('source_controls') or []
    if not doc.get('validated') or not doc.get('status','').startswith('READY_') or not controls or any(
            x.get('status')!='PASS' or x.get('actual_cached_value') is None for x in controls):
        raise RuntimeError('LibreOffice environment has not passed real cache controls')
    proof=Path(doc['proof_report'])
    if not proof.is_absolute():
        proof=(PROJECT if proof.parts[0]=='research' else HERE)/proof
    if sha(proof)!=doc['proof_report_sha256']:
        raise RuntimeError('Runtime cache-control proof changed')
    for key,value in doc['environment'].items():
        if key not in {'USERPROFILE','APPDATA','LOCALAPPDATA','PYTHONIOENCODING','PYTHONUTF8'}:
            raise RuntimeError('Unexpected runtime environment mutation')
        os.environ[key]=str(value)
    os.environ['PATH']=os.pathsep.join(doc['path_prepend']+[os.environ.get('PATH','')])
    old=os.environ.get('PYTHONPATH','')
    os.environ['PYTHONPATH']=os.pathsep.join(doc['pythonpath_append']+([old] if old else []))
    return {'file':str(path),'sha256':sha(path),'proof':str(proof),'status':doc['status']}

def shell_check(output):
    bootstrap_imports(); output.mkdir(parents=True,exist_ok=True)
    from spreadsheet_agent.tools.bash import create_bash_tool
    native=create_bash_tool(str(output))
    adapted=windows_bash_factory(str(output)) if os.name=='nt' else native
    command="python -c \"import sys,diskcache,openpyxl; print(sys.executable); print('DEPENDENCIES_OK')\""
    result=adapted.execute(command=command)
    if 'DEPENDENCIES_OK' not in result: raise RuntimeError('Adapted POSIX shell dependency check failed: '+result)
    if native.description!=adapted.description or json_safe(native.parameters)!=json_safe(adapted.parameters):
        raise RuntimeError('Platform adapter changed original tool description/schema')
    dump(output/'shell_adapter_check.json',{'status':'PASSED','actual_output':result,
        'same_tool_description_and_schema':True,'adapter_only_on_windows':os.name=='nt'})
    print(json.dumps({'shell_check':'PASSED'},ensure_ascii=False))

def isolate_seed(run,initial=None):
    parent=run/'initial_skills'; parent.mkdir()
    initial=Path(initial) if initial else BASELINE/'spreadsheet_agent/skills/xlsx'
    dest=parent/initial.name; shutil.copytree(initial,dest)
    # only one top-level SKILL: selection cannot accidentally pick another skill
    found=list(parent.glob('*/SKILL.md'))
    if len(found)!=1: raise RuntimeError('Consumer seed isolation failed')
    dump(run/'initialization_manifest.json',{'mode':'Self-deepening of supplied existing skill',
        'creation_bootstrap_reproduced':False,'source_directory':str(initial.resolve()),
        'isolated_directory':str(dest.resolve()),'source_files':{
            str(p.relative_to(initial)):sha(p) for p in initial.rglob('*') if p.is_file()},
        'copied_files':{str(p.relative_to(dest)):sha(p) for p in dest.rglob('*') if p.is_file()}})
    return parent,dest

def effective_answer(item):
    position=item.get('answer_position',''); sheet=item.get('answer_sheet','')
    if '!' not in position and sheet:
        return f"'{sheet}'!{position}" if ' ' in sheet else f'{sheet}!{position}'
    return position

def prepare_public(run, ids):
    from spreadsheetbench_support import load_dataset,find_spreadsheet_dir
    rows=load_dataset(str(DATA)); by_id={str(r['id']):r for r in rows}
    selected=[]
    root=run/'public_data'; root.mkdir()
    for task_id in ids:
        raw=by_id[task_id]; item=dict(raw)
        directory=Path(find_spreadsheet_dir(str(DATA),raw))
        dest=root/task_id; shutil.copytree(directory,dest)
        item['spreadsheet_path']=task_id
        item['answer_position']=effective_answer(raw)
        selected.append(item)
    dump(root/'dataset.json',selected)
    dump(run/'public_input_manifest.json',{'calibration_only':True,'enterprise_main_data_replaced':False,
        'task_ids':ids,'source_dataset_sha256':sha(DATA/'dataset.json'),
        'answer_position_adaptation':[{ 'id':r['id'],'original':by_id[str(r['id'])].get('answer_position'),
             'answer_sheet':by_id[str(r['id'])].get('answer_sheet'),'effective':r['answer_position']} for r in selected]})
    return root,selected

def public_rollouts(run,skills_root,data,audit,phase='rollout'):
    import run_spreadsheetbench as native
    from spreadsheet_agent.runner import SpreadsheetBenchRunner
    parser=native.build_arg_parser()
    args=parser.parse_args(['--data_path',str(data),'--model',os.environ.get('TRACE2SKILL_MODEL','ecnu-plus'),
        '--agent','cli_skill_preloaded','--skills_dir',str(skills_root),'--max_turns','100',
        '--workers','1','--seeds','41','--log_dir',str(run/phase/'logs'),'--log_format','markdown',
        '--generation_config',json.dumps(settings('rollout',41))])
    args.current_seed=41
    # Existing entrypoint reads OPENAI env; credentials remain in process only.
    os.environ['OPENAI_API_KEY']=os.environ.get('ECNU_API_KEY') or os.environ.get('OPENAI_API_KEY','')
    os.environ['OPENAI_BASE_URL']=os.environ.get('TRACE2SKILL_BASE_URL','https://chat.ecnu.edu.cn/open/api/v1')
    agent=native.create_agent(args)
    rendered=agent.get_system_template()
    seed=list(Path(skills_root).glob('*/SKILL.md'))
    if len(seed)!=1: raise RuntimeError('Consumer skill root must have exactly one target skill')
    # Native consumer strips YAML. Independently derive the nonempty source body
    # so silent native decoding failure cannot pass an empty-string assertion.
    from spreadsheet_agent.agents.cli_skill_preloaded_agent import read_skill_content
    source=seed[0].read_text(encoding='utf-8')
    expected=source.split('---',2)[2].strip() if source.startswith('---') else source.strip()
    if len(agent._skills)!=1 or Path(agent._skills[0][0].file_path).resolve()!=seed[0].resolve():
        raise RuntimeError('Actual consumer selected a different target skill')
    loaded=read_skill_content(agent._skills[0][0])
    if not expected or expected!=loaded.strip() or expected not in rendered:
        raise RuntimeError('Actual template does not include target skill body')
    dump(run/phase/'skill_loaded.json',{'skill_path':str(seed[0]),'skill_sha256':sha(seed[0]),
        'body_sha256':hashlib.sha256(expected.encode()).hexdigest(),
        'system_template_sha256':hashlib.sha256(rendered.encode()).hexdigest(),'target_body_present':True,
        'source_native_loaded_body_equal':True,'nonempty_body':True})
    runner=SpreadsheetBenchRunner(agent=agent,data_path=str(data),output_dir=str(run/phase/'outputs'),
                                 working_dir=str(run/phase/'work'))
    instances=runner.load_data(); results=[]; audit.phase=phase
    for instance in instances:
        results.append(json_safe(runner.run_instance(instance)))
    dump(run/phase/'runner_results.json',results)
    # Outcome flags in original runner describe execution completion; true scores
    # are computed next with the author local task verifier.
    return results

def judge_public_outputs(run,rows,phase):
    from analysis.evaluate_output import compare_workbooks
    from analysis.run_error_analysis import find_gold_file
    # Signature is verified when this stage runs; no model receives gold here.
    verdicts=[]
    for item in rows:
        task_id=str(item['id']); gold=find_gold_file(str(run/'public_data'),item)
        outputs=list((run/phase/'outputs'/task_id).glob('*.xlsx'))
        if not outputs: outputs=list((run/phase/'outputs').glob(f'*{task_id}*.xlsx'))
        if not gold or not outputs:
            verdicts.append({'id':task_id,'status':'OUTPUT_OR_GOLD_MISSING','outputs':[str(p) for p in outputs]})
            continue
        # compare_workbooks returns its exact native report structure.
        result=compare_workbooks(str(gold),str(outputs[0]),item['answer_position'])
        verdicts.append({'id':task_id,'output':str(outputs[0]),'gold':str(gold),
                         'answer_position':item['answer_position'],'native_evaluation':json_safe(result)})
    dump(run/phase/'verdicts.json',verdicts); return verdicts

def success_analysis(run,logs,audit,domain_system=None,domain_user=None):
    import openai
    from analysis import run_success_analysis_llm as native
    from analysis.report_parsing import collect_success_records
    system=(Path(domain_system) if domain_system else native.SYSTEM_PROMPT_PATH).read_text(encoding='utf-8')
    template=(Path(domain_user) if domain_user else native.USER_PROMPT_PATH).read_text(encoding='utf-8')
    output=run/'success_analysis'; output.mkdir()
    client=openai.OpenAI(api_key=os.environ.get('ECNU_API_KEY') or os.environ.get('OPENAI_API_KEY'),
        base_url=os.environ.get('TRACE2SKILL_BASE_URL','https://chat.ecnu.edu.cn/open/api/v1'),timeout=1800)
    audit.phase='success_analysis'
    for instance_id,logfile in native.find_logs(str(logs),succeed_only=True).items():
        inputs,report=native.analyze_instance(client,os.environ.get('TRACE2SKILL_MODEL','ecnu-plus'),
            system,template,logfile,generation_config=settings('success',41))
        native.write_prompt_log(output/f'success_analysis_{instance_id}_prompt.md',inputs,report)
        (output/f'success_analysis_{instance_id}.md').write_text(report,encoding='utf-8')
    records=collect_success_records(str(output))
    dump(run/'parsed_success_records.json',records)
    return records

def enterprise_analysis(run,audit):
    """One source-bound local episode, not whole-session success or replay."""
    from analysis import run_success_analysis_llm as native
    job_path=HERE/'private/enterprise/native_success_job.json'
    job=json.loads(job_path.read_text(encoding='utf-8'))
    logs=PROJECT/job['native_logs_dir']
    logfile=PROJECT/job['native_log']
    if sha(logfile)!=job['native_log_sha256'] or job['scoped_success_evaluation']['status']!='PASS':
        raise RuntimeError('Frozen local enterprise episode evidence differs')
    prompts=run/'domain_interface'; prompts.mkdir()
    system=native.SYSTEM_PROMPT_PATH.read_text(encoding='utf-8')
    adapted=system.replace('spreadsheet manipulation tasks.', 'enterprise numerical calculation tasks.')
    adapted=adapted.replace('`input.xlsx`, the task description, and others mentioned by its system prompt.',
        'the visible task description and reply in the log. No input workbook or delivered artifact is available here.')
    # Outcome qualification is the domain scorer interface, not a new analyst:
    # original mission, strict item format, 3-item limit and single call remain.
    scope='''\n\n# Evaluated Task Boundary\nThe independently qualified local task is ONLY converting annual pay per person to monthly pay per person. The reply is kept verbatim, including surrounding claims that have NOT been verified. Extract winning steps and memories only for that local task. Do not learn quarterly/team/regional budgets, cash-flow/loan/market decisions, or asserted file updates from this episode. Do not invent tool execution or access to a spreadsheet. The historical log is a content-associated exchange; its chronology is not independently certified.\n'''
    (prompts/'success_system.txt').write_text(adapted+scope,encoding='utf-8')
    shutil.copy2(native.USER_PROMPT_PATH,prompts/'success_user.txt')
    dump(run/'enterprise_input_manifest.json',{'job':str(job_path),'job_sha256':sha(job_path),
        'log':str(logfile),'log_sha256':sha(logfile),'topic':job['topic'],
        'candidate_id':job['source_candidate_id'],'whole_candidate_outcome':'UNKNOWN',
        'qualification':'Only per-person annual-to-monthly arithmetic independently passed',
        'historical_tasks_rerun':False,'main_enterprise_dataset_replaced':False,
        'native_success_algorithm_unchanged':True,
        'domain_prompt_interface_adapted':True,'original_system_sha256':sha(native.SYSTEM_PROMPT_PATH),
        'adapted_system_sha256':sha(prompts/'success_system.txt'),
        'user_template_unchanged':sha(prompts/'success_user.txt')==sha(native.USER_PROMPT_PATH),
        'diff_description':['Task-domain noun phrase','Available evidence sentence','Scorer-qualified task boundary'],
        'initialization_for_following_evolution':'Author released human xlsx; Self-deepening, NOT reconstructed Creation'})
    records=success_analysis(run,logs,audit,prompts/'success_system.txt',prompts/'success_user.txt')
    if not records: raise RuntimeError('Native success parser produced no admissible items')
    dump(run/'analysis_scope_review_required.json',{'status':'REVIEW_BEFORE_EVOLUTION',
        'purpose':'Prevent unverified neighboring business/file claims becoming success memories',
        'native_records_sha256':sha(run/'parsed_success_records.json')})
    return records

def adjudicate_logs(run, verdicts):
    """Rename COPIES by true local scores; never trust TASK_COMPLETE as success."""
    from analysis.run_error_analysis import find_log_file
    root=run/'adjudicated_logs'; root.mkdir()
    decisions=[]
    for verdict in verdicts:
        task_id=verdict['id']; result=verdict.get('native_evaluation')
        log=find_log_file(str(run/'rollout/logs'),task_id)
        if not result or not log:
            decisions.append({'id':task_id,'outcome':'UNKNOWN','reason':'Missing output/score/log'}); continue
        outcome='SUCCEED' if result[0] else 'FAILED'
        target=root/f'cli_skill_preloaded_agent_{task_id}_{outcome}.md'
        shutil.copy2(log,target)
        decisions.append({'id':task_id,'outcome':outcome,'source':log,'copy':str(target),
                          'source_sha256':sha(log),'copy_sha256':sha(target)})
    dump(run/'outcome_decisions.json',decisions); return root,decisions

def error_analysis(run,logs,rows,audit):
    from analysis import run_error_analysis as native
    from analysis.report_parsing import collect_error_records
    args=SimpleNamespace(output_dir=str(run/'error_analysis'),logs_dir=str(logs),
        work_dir=str(run/'rollout/work'),data_path=str(run/'public_data'),
        model=os.environ.get('TRACE2SKILL_MODEL','ecnu-plus'),max_turns=100,
        base_url=os.environ.get('TRACE2SKILL_BASE_URL','https://chat.ecnu.edu.cn/open/api/v1'),
        api_key=os.environ.get('ECNU_API_KEY') or os.environ.get('OPENAI_API_KEY'),
        generation_config_dict=settings('error',41),llm_client='openai',api_chat_config='',verbose=False)
    index={str(r['id']):r for r in rows}; results=[]; audit.phase='agentic_error_analysis'
    from analysis.run_success_analysis_llm import find_logs
    failed=find_logs(str(logs),succeed_only=False)
    for task_id,logfile in failed.items():
        if not logfile.endswith('_FAILED.md'): continue
        results.append(native.run_single_instance(task_id,args,index,log_path_override=logfile))
    root=Path(args.output_dir); root.mkdir(exist_ok=True)
    records,passed,total=collect_error_records(str(root))
    dump(run/'error_analysis_execution.json',{'executions':results,'directories_passed':passed,
         'directories_total':total,'native_directory_pass_gate_preserved':True})
    dump(run/'parsed_error_records.json',records); return records

def complete_public(run,rows,seed_dir,audit,merge_batch):
    verdicts=judge_public_outputs(run,rows,'rollout')
    logs,decisions=adjudicate_logs(run,verdicts)
    success=success_analysis(run,logs,audit)
    from cache_isolation import isolate_error_analysis_cache
    with isolate_error_analysis_cache(run):
        error=error_analysis(run,logs,rows,audit)
    if not success and not error: raise RuntimeError('No parsed admissible native analysis records')
    _,_,result=evolve(run,seed_dir,success,error,audit,merge_batch)
    dump(run/'native_chain_coverage.json',{'native_success_records':len(success),'native_error_records':len(error),
        'agentic_error_exercised':any(d['outcome']=='FAILED' for d in decisions),
        'unknown_outcomes':sum(d['outcome']=='UNKNOWN' for d in decisions),
        'map_patches':len(result.get('patches',[])),'model_calls_not_counted_from_algorithm_estimate':True,
        'independent_holdout_performance':'NOT_MEASURED'})

def evolve(run,seed_dir,success,error,audit,merge_batch=32):
    from skill_evolver.parallel_success_evolving_agent import CombinedParallelSkillEvolver,normalize_mixed_records
    checker_ready()
    root=run/'evolved_skills'; root.mkdir(); target=root/Path(seed_dir).name
    shutil.copytree(seed_dir,target)
    client=native_client(41,'evolution',run)
    evolver=CombinedParallelSkillEvolver(client=client,skill_dir=target,batch_size=1,
        merge_batch_size=merge_batch,max_workers=4,max_merge_levels=5,temperature=0.6,
        verbose=False,prompt_variant='generic',output_dir=run/'intermediates',
        parse_failure_dir=run/'parse_failures',skip_translation=False,
        enable_json_format_self_fix=True,max_verification_rounds=3,patch_pipeline='json')
    audit.phase='native_evolution'
    result=evolver.run(normalize_mixed_records(error,success),input_mode='records')
    dump(run/'evolution_result.json',json_safe(result))
    return root,target,result

def probe(run,audit):
    import openai
    client=openai.OpenAI(api_key=os.environ.get('ECNU_API_KEY') or os.environ.get('OPENAI_API_KEY'),
        base_url=os.environ.get('TRACE2SKILL_BASE_URL','https://chat.ecnu.edu.cn/open/api/v1'),timeout=600)
    rows=[]
    for phase in ('instruct','thinking'):
        cfg=settings('rollout' if phase=='instruct' else 'success',41)
        cfg['max_tokens']=512  # calibration only; never used for native generation
        audit.phase='model_probe_'+phase
        reply=client.chat.completions.create(model=os.environ.get('TRACE2SKILL_MODEL','ecnu-plus'),
            messages=[{'role':'user','content':'Return exactly the word READY.'}],**cfg)
        value=reply.model_dump()
        rows.append({'phase':phase,'accepted':True,'served_model':value.get('model'),
            'finish_reason':value['choices'][0].get('finish_reason'),
            'reasoning_visible':bool(value['choices'][0]['message'].get('reasoning_content')),
            'response':value['choices'][0]['message'].get('content')})
    dump(run/'model_probe.json',{'mode_acceptance':rows,'original_model_identity_verified':False,
         'successful_extra_parameter_acceptance_does_not_prove_mode_effect':True})
    return rows

def consumer_acceptance(run,initial,evolved,audit):
    from salary_controls import prepare
    rows=prepare(run/'public_data')
    results={}
    for label,skill in [('S0',initial or BASELINE/'spreadsheet_agent/skills/xlsx'),('S1',evolved)]:
        if skill is None: raise RuntimeError('Explicit evolved target skill required')
        parent=run/f'{label}_skills'; parent.mkdir()
        shutil.copytree(Path(skill),parent/Path(skill).name)
        public_rollouts(run,parent,run/'public_data',audit,phase=label)
        results[label]=judge_public_outputs(run,rows,label)
    dump(run/'paired_functional_acceptance.json',{'origin':'Synthetic new salary tasks; not enterprise benchmark gold',
        'conditions':'Same author consumer, tools, data, model and seed41; isolated exact S0/S1 target',
        'results':results,'training_validation_seed_selection':'NOT_DONE',
        'statistical_skill_advantage':'NOT_ESTABLISHED_BY_FOUR_CASES'})

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['shell-check','probe','public-calibration','full-public','enterprise-analysis','evolve-records','consumer-acceptance'])
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--task-ids',default='13-1')
    parser.add_argument('--initial-skill',type=Path)
    parser.add_argument('--evolved-skill',type=Path)
    parser.add_argument('--runtime-env',type=Path,help='Free-validated run-local LibreOffice environment')
    parser.add_argument('--success-records',type=Path)
    parser.add_argument('--error-records',type=Path)
    parser.add_argument('--max-requests',type=int,default=40)
    parser.add_argument('--merge-batch',type=int,default=32)
    args=parser.parse_args()
    if args.action in {'public-calibration','full-public','consumer-acceptance'} and not args.runtime_env:
        raise RuntimeError('Formula-task runs require --runtime-env with actual cache controls PASS; no model call allowed')
    runtime=apply_runtime_environment(args.runtime_env) if args.runtime_env else None
    bootstrap_imports()
    if not sys.flags.utf8_mode:
        raise RuntimeError('Start Python with -X utf8; late env changes cannot repair author UTF-8 reads')
    os.environ['PYTHONIOENCODING']='utf-8'
    if args.action=='shell-check': shell_check(args.output); return
    if args.output.exists(): raise RuntimeError('Run output already exists; immutable runs never overwritten')
    if not (os.environ.get('ECNU_API_KEY') or os.environ.get('OPENAI_API_KEY')):
        raise RuntimeError('Runtime API key absent; no credentials are stored in source')
    args.output.mkdir(parents=True); source=guard_source()
    local_source={p.name:sha(p) for p in HERE.glob('*.py')}
    local_source['profiles.json']=sha(HERE/'profiles.json')
    snapshots=args.output/'orchestration_snapshot'; snapshots.mkdir()
    for name,expected_sha in local_source.items():
        shutil.copy2(HERE/name,snapshots/name)
        if sha(snapshots/name)!=expected_sha:
            raise RuntimeError('Source snapshot copy differs before any model call')
    dump(args.output/'protocol.json',{'action':args.action,'commit':COMMIT,'seed':41,
         'model':os.environ.get('TRACE2SKILL_MODEL','ecnu-plus'),'merge_batch':args.merge_batch,
         'max_turns':100,'map_batch':1,'max_workers':4,'paper_workers':128,
         'consumer_workers':1,
         'max_requests':args.max_requests,'defaults_preserved':{'translation':True,'json_self_fix':True,
             'verification_rounds':3,'continuation_rounds':2},
         'source_before':source,
         'verified_runtime_environment':runtime,
         'local_code_sha256':local_source,
         'calibration_is_not_enterprise_main_data':args.action in {'public-calibration','full-public'}})
    audit=RequestAudit(args.output,max_requests=args.max_requests)
    try:
        with instrument_sdk(audit),platform_adapter():
            if args.action=='probe': probe(args.output,audit)
            elif args.action=='enterprise-analysis': enterprise_analysis(args.output,audit)
            elif args.action=='consumer-acceptance': consumer_acceptance(args.output,args.initial_skill,args.evolved_skill,audit)
            elif args.action in {'public-calibration','full-public'}:
                skills,seed=isolate_seed(args.output,args.initial_skill)
                data,rows=prepare_public(args.output,args.task_ids.split(','))
                public_rollouts(args.output,skills,data,audit)
                if args.action=='full-public': complete_public(args.output,rows,seed,audit,args.merge_batch)
                else: judge_public_outputs(args.output,rows,'rollout')
            else:
                success=json.loads(args.success_records.read_text(encoding='utf-8')) if args.success_records else []
                error=json.loads(args.error_records.read_text(encoding='utf-8')) if args.error_records else []
                if not success and not error: raise RuntimeError('No admissible native analysis records')
                dump(args.output/'analysis_input_manifest.json',{'success_source':str(args.success_records),
                    'success_sha256':sha(args.success_records) if args.success_records else None,
                    'error_source':str(args.error_records),'error_sha256':sha(args.error_records) if args.error_records else None,
                    'native_parser_records_preserved_without_rewrite':True})
                dump(args.output/'input_success_records.json',success); dump(args.output/'input_error_records.json',error)
                _,seed=isolate_seed(args.output,args.initial_skill)
                evolve(args.output,seed,success,error,audit,args.merge_batch)
        after=guard_source()
        if after!=source: raise RuntimeError('Author source changed during run')
        if {name:sha(HERE/name) for name in local_source}!=local_source:
            raise RuntimeError('Frozen local orchestration/configuration changed during run')
        dump(args.output/'completion.json',{'status':'COMPLETED','source_unchanged':True,
            'local_orchestration_and_config_unchanged':True,
            'action':args.action,'task_benefit_measured':False,'paper_numeric_reproduction':False})
    except Exception as exc:
        dump(args.output/'failure.json',{'status':'FAILED_PRESERVED','error_type':type(exc).__name__,
            'error':str(exc).replace(audit.secret,'[REDACTED]') if audit.secret else str(exc),
            'traceback':traceback.format_exc().replace(audit.secret,'[REDACTED]') if audit.secret else traceback.format_exc()})
        raise
    finally: audit.save()

if __name__=='__main__': main()
