"""Verify uploaded files and the independent fixed author checkout; zero model calls."""
from pathlib import Path
import hashlib, json, subprocess, sys

PROJECT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def main():
    manifest=json.loads((HERE/'upload_inventory.json').read_text(encoding='utf-8'))
    errors=[];checked=0
    for item in manifest['files']:
        p=PROJECT/item['path']
        if not p.is_file():errors.append({'path':item['path'],'error':'MISSING'});continue
        with p.open('rb') as f:prefix=f.read(128)
        if prefix.startswith(b'version https://git-lfs.github.com/spec/v1'):
            errors.append({'path':item['path'],'error':'LFS_POINTER_NOT_DOWNLOADED'});continue
        if p.stat().st_size!=item['bytes'] or sha(p)!=item['sha256']:
            errors.append({'path':item['path'],'error':'SIZE_OR_SHA_MISMATCH_OR_LFS_POINTER'})
        else:checked+=1
    baseline=PROJECT/manifest['baseline_submodule']['path']
    count=0
    try:
        root=subprocess.check_output(['git','rev-parse','--show-toplevel'],cwd=baseline,text=True).strip()
        if Path(root).resolve()!=baseline.resolve():raise RuntimeError('Author directory is not an independent Git checkout; initialize submodule')
        commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=baseline,text=True).strip()
        if commit!=manifest['baseline_submodule']['commit']:raise RuntimeError('Author commit mismatch')
        protocol=PROJECT/'research/experiments/20261006_trace2skill_native_baseline/private/enterprise_analysis_001/protocol.json'
        source=json.loads(protocol.read_text(encoding='utf-8'))['source_before']['files']
        for rel,digest in source.items():
            p=baseline/rel
            if not p.is_file() or sha(p)!=digest:errors.append({'path':'research/baselines/Trace2Skill/'+rel,'error':'AUTHOR_SHA_MISMATCH'})
            else:count+=1
    except Exception as exc:errors.append({'path':'research/baselines/Trace2Skill','error':str(exc)})
    print(json.dumps({'status':'PASS' if not errors else 'FAIL','ordinary_and_lfs_files_checked':checked,
        'author_source_files_checked':count,'model_calls':0,'errors':errors},ensure_ascii=False,indent=2))
    return 1 if errors else 0

if __name__=='__main__':sys.exit(main())
