"""Restore only proven LF/CRLF materialization differences; keep author commit/core."""
from pathlib import Path
import argparse, hashlib, json, subprocess, sys

PROJECT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
COMMIT='3d0b52a140f002a512930252b613c49048f7d5ac'

def digest(data):return hashlib.sha256(data).hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--baseline',type=Path,default=PROJECT/'research/baselines/Trace2Skill')
    parser.add_argument('--report',type=Path,default=HERE/'author_materialization_report.json')
    args=parser.parse_args();baseline=args.baseline.resolve()
    if not baseline.is_relative_to(PROJECT):raise RuntimeError('Author checkout must be inside this project')
    def git(*parts):return subprocess.check_output(['git',*parts],cwd=baseline)
    if Path(git('rev-parse','--show-toplevel').decode().strip()).resolve()!=baseline:raise RuntimeError('Initialize independent author submodule first')
    if git('rev-parse','HEAD').decode().strip()!=COMMIT:raise RuntimeError('Author commit mismatch')
    if git('diff','--name-only').strip() or git('diff','--cached','--name-only').strip():raise RuntimeError('Author checkout has tracked changes; refusing overwrite')
    native=PROJECT/'research/experiments/20261006_trace2skill_native_baseline/private'
    expected=json.loads((native/'enterprise_analysis_001/protocol.json').read_text(encoding='utf-8'))['source_before']['files']
    plan=[];records=[]
    process=subprocess.Popen(['git','cat-file','--batch'],cwd=baseline,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    try:
        for rel,wanted in expected.items():
            process.stdin.write(('HEAD:'+rel+'\n').encode());process.stdin.flush()
            header=process.stdout.readline().split()
            if len(header)!=3 or header[1]!=b'blob':raise RuntimeError('Missing author blob: '+rel)
            canonical=process.stdout.read(int(header[2]));process.stdout.read(1)
            existing=(baseline/rel).read_bytes();actual=digest(existing)
            canon_sha=digest(canonical)
            if canon_sha==wanted:target=canonical;representation='HEAD_BYTES'
            elif b'\r' not in canonical and digest(canonical.replace(b'\n',b'\r\n'))==wanted:
                target=canonical.replace(b'\n',b'\r\n');representation='STRICT_LF_TO_CRLF'
            else:raise RuntimeError('Historical SHA is not a proven author/EOL representation: '+rel)
            if actual not in {canon_sha,wanted}:raise RuntimeError('Unexpected existing file; refusing overwrite: '+rel)
            if actual!=wanted:plan.append((rel,target,actual))
            records.append({'path':rel,'head_blob_sha256':canon_sha,'historical_sha256':wanted,
                'representation':representation,'before_sha256':actual,'requires_materialization':actual!=wanted})
    finally:
        process.stdin.close();process.stdout.close();process.wait()
    seed=json.loads((native/'enterprise_evolution_001/initialization_manifest.json').read_text(encoding='utf-8'))['source_files']
    for rel,wanted in seed.items():
        if digest((baseline/'spreadsheet_agent/skills/xlsx'/rel).read_bytes())!=wanted:
            raise RuntimeError('Author S0 resource differs; no conversion allowed: '+rel)
    # Local normalization makes this representation clean to Git without editing any author algorithm.
    if plan:
        git('config','--local','core.autocrlf','true')
        for rel,target,before in plan:
            p=baseline/rel
            if digest(p.read_bytes())!=before:raise RuntimeError('Concurrent checkout modification: '+rel)
            p.write_bytes(target)
    for rel,wanted in expected.items():
        if digest((baseline/rel).read_bytes())!=wanted:raise RuntimeError('Historical SHA verification failed: '+rel)
    if git('rev-parse','HEAD').decode().strip()!=COMMIT or git('diff','--name-only').strip():raise RuntimeError('Author HEAD or clean state changed')
    report={'status':'PASS','model_calls':0,'author_commit':COMMIT,'checked_files':len(expected),
        'materialized_files':len(plan),'head_bytes_files':sum(r['representation']=='HEAD_BYTES' for r in records),
        'strict_eol_files':sum(r['representation']=='STRICT_LF_TO_CRLF' for r in records),
        'author_algorithm_changes':0,'source_manifest_modified':False,'author_s0_files_preserved':True,'files':records}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='files'},ensure_ascii=False))
    return 0

if __name__=='__main__':sys.exit(main())
