"""Zero-LLM host revalidation of immutable run03 creator output in a new workspace."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

PROJECT=Path(r'D:/skillsgen-industry_track')
DEMO=PROJECT/'enginering/demo'
SOURCE=PROJECT/'research/cases/038_contract_multi_review/private/051-first5-run03'
OUTPUT=Path(__file__).resolve().parent
CANDIDATE='candidate-95e6a640341d673176ebb04b'
sys.path.insert(0,str(DEMO))
sys.stdout.reconfigure(encoding='utf-8')
from skilldemo.runtime import parse_object, digest
from skilldemo.creator import verify_files, verify_archive
from skilldemo.bootstrap import initialize, draft_files, package, CREATOR


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def write(name,value):
    (OUTPUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
def tree_hashes(path):
    return {p.relative_to(path).as_posix():sha(p) for p in sorted(path.rglob('*')) if p.is_file()}


def main():
    before=tree_hashes(SOURCE)
    summary={'mode':'HOST_ONLY_REVALIDATION_AFTER_PARSER_FIX','sourceRun':str(SOURCE),
        'candidateId':CANDIDATE,'modelCalls':0,'incrementalModelTokens':0,
        'incrementalProviderCharges':0,'sourceOfficialAcceptanceUnchanged':True,
        'sourceRunPromotedToPass':False,'businessOutcome':'UNKNOWN',
        'professionalQuality':'NOT_EVALUATED','semanticCoverage':'NOT_INDEPENDENTLY_VERIFIED'}
    work=OUTPUT/'workspace'
    try:
        if work.exists():raise ValueError('Refuse to overwrite previous revalidation workspace')
        work.mkdir()
        candidate=next(c for c in read(SOURCE/'stage-5.json')['candidates'] if c['id']==CANDIDATE)
        run_id=candidate['runId']
        original_work=SOURCE/'workspaces'/run_id
        control=SOURCE/'workspaces'/(run_id+'-control')
        raw=read(control/'stdout.json')
        text=raw['final']
        parsed=parse_object(text)
        if parsed.get('decision')!='CREATE':raise ValueError('Original creator output is not CREATE')
        source_states=read(SOURCE/'request-states.json')
        analysis=next(a for a in source_states['workflow_analysis'] if a['id']==candidate['analysisId'])
        phrases=[v['text'] for v in analysis.get('catalog',{}).values()]
        initialize(work)
        original_files={}
        for source in sorted((original_work/'draft').rglob('*')):
            if source.is_symlink():raise ValueError('Source draft symlink is not allowed')
            if not source.is_file():continue
            relative=source.relative_to(original_work/'draft')
            dest=work/'draft'/relative
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source,dest)
            original_files[relative.as_posix()]=sha(source)
            if sha(dest)!=sha(source):raise ValueError('Draft copy bytes changed')
        files=draft_files(work)
        checked=verify_files(files,candidate['input']['workflow']['includedMethodIds'],phrases,
            methods=candidate['input']['methods'],coverageManifest=parsed.get('coverageManifest'))
        scripts=('scripts/package_skill.py','scripts/quick_validate.py')
        official_same=all(sha(original_work/'.foundation/skill-creator'/p)==sha(CREATOR/p) for p in scripts)
        if not official_same:raise ValueError('Official packaging script differs from original run foundation')
        receipt=package(work,files)
        archive=verify_archive(work,receipt,files)
        run=next(r for r in read(SOURCE/'model-runs.json') if r['id']==run_id)
        result=run.get('result') or {}
        if isinstance(result,str):result=json.loads(result)
        foundation=result.get('foundationRead',{})
        if foundation.get('status')!='FILE_READ':raise ValueError('Original actual creator read receipt absent')
        config=read(control/'openclaw.json')
        providers=config.get('models',{}).get('providers',{})
        model_configs=[m for provider in providers.values() for m in provider.get('models',[])]
        has_pricing=any(any(k in m for k in ('cost','pricing','inputCost','outputCost')) for m in model_configs)
        summary.update(status='PASS',originalCandidateStatus=candidate['status'],runId=run_id,
            sourceFinalSha256=hashlib.sha256(text.encode('utf-8')).hexdigest(),
            parsedDecision=parsed['decision'],title=parsed.get('title'),rawDraftHashes=original_files,
            hostValidation=checked,officialPackage=archive,packageReceipt=receipt,
            originalCreatorRead=foundation,officialPackagerMatchesRun03=official_same,
            sourceUsage=raw.get('usage'),sourceReportedCostUsd=raw.get('costUsd'),
            sourcePricingConfigured=has_pricing,sourceCashCost='UNKNOWN',
            costInterpretation='OpenClaw reported zero with no model price configuration; historical real provider charges are unknown.',
            deliverable=str((work/receipt['path']).resolve()),canonicalContentHash=digest(files))
        (OUTPUT/'original-final.txt').write_bytes(text.encode('utf-8'))
        write('parsed-original-final.json',parsed)
        write('source-inputs.json',{'candidateId':CANDIDATE,'sourceAnalysisId':candidate['analysisId'],
            'methodIds':candidate['input']['workflow']['includedMethodIds'],'methodCount':len(candidate['input']['methods']),
            'catalogPhraseCount':len(phrases),'sourceHashes':{p:before[p] for p in before if p in
                ('stage-5.json','request-states.json','model-runs.json') or p.startswith('workspaces/'+run_id+'/draft/')
                or p=='workspaces/'+run_id+'-control/stdout.json'},
            'currentHostSourceHashes':{p:sha(DEMO/'skilldemo'/p) for p in ('runtime.py','creator.py','bootstrap.py')}})
    except Exception as exc:
        summary.update(status='FAILED',error=type(exc).__name__+': '+str(exc))
    after=tree_hashes(SOURCE)
    summary['allSourceFileBytesUnchanged']=before==after
    summary['sourceFileCountChecked']=len(before)
    if before!=after:
        summary['status']='FAILED';summary['sourceChanges']=[p for p in set(before)|set(after) if before.get(p)!=after.get(p)]
    write('summary.json',summary)
    print(json.dumps({k:summary.get(k) for k in ('status','error','candidateId','modelCalls','allSourceFileBytesUnchanged','deliverable','sourceCashCost')},ensure_ascii=False,indent=2))
    return 0 if summary['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
