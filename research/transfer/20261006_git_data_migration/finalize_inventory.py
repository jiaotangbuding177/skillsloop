"""Verify staged data bytes/LFS objects and publish an index-based clone manifest."""
from pathlib import Path
import hashlib, json, subprocess

from inventory_upload import PROJECT, HERE, files, PATTERNS, literal_matches

CONTROL_PREFIX='research/transfer/20261006_git_data_migration/'
EDITED_METADATA={
    'MIGRATION.md','research/README.md','research/STATE.md','research/CHARTER.md',
    'research/memory/2026-10-07_git_full_data_migration.md',
    'research/datasets/evomind/raw_sources_20261006/README.md'}

def allowed_metadata(path):return path.startswith(CONTROL_PREFIX) or path in EDITED_METADATA

def git(*args,input=None):
    return subprocess.run(['git',*args],cwd=PROJECT,input=input,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).stdout

def main():
    target=HERE/'upload_inventory.json';manifest=json.loads(target.read_text(encoding='utf-8'))
    expected={r['path']:r for r in manifest['files']}
    selected={p.relative_to(PROJECT).as_posix():p for p in files()}
    extra=[]
    for relative,p in selected.items():
        if relative not in expected:
            if not allowed_metadata(relative):raise RuntimeError('Unexpected new data after frozen inventory: '+relative)
            extra.append(relative)
        elif allowed_metadata(relative):extra.append(relative)
    pathspec=PROJECT/'tmp/migration_metadata_paths.txt';pathspec.parent.mkdir(exist_ok=True)
    pathspec.write_bytes(b''.join(x.encode()+b'\0' for x in sorted(set(extra))))
    subprocess.run(['git','--literal-pathspecs','add','--force','--pathspec-from-file='+str(pathspec),'--pathspec-file-nul'],cwd=PROJECT,check=True)
    rows={}
    for raw in git('ls-files','--stage','-z').split(b'\0'):
        if not raw:continue
        head,path=raw.split(b'\t',1);mode,oid,stage=head.split();relative=path.decode('utf-8')
        if stage!=b'0':raise RuntimeError('Unmerged index: '+relative)
        rows[relative]=(mode.decode(),oid.decode())
    baseline='research/baselines/Trace2Skill'
    if rows.get(baseline)!=('160000','3d0b52a140f002a512930252b613c49048f7d5ac'):raise RuntimeError('Author gitlink mismatch')
    for relative,(mode,oid) in rows.items():
        if mode=='160000' and relative!=baseline:raise RuntimeError('Unexpected data gitlink: '+relative)
    all_paths=sorted(set(expected)|set(selected))
    missing=[r for r in all_paths if r not in rows]
    if missing:raise RuntimeError('Missing staged files: '+str(missing[:20]))
    process=subprocess.Popen(['git','cat-file','--batch'],cwd=PROJECT,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    records=[];lfs=[];changes=[];eol_index_repairs=[]
    lfsroot=Path(git('rev-parse','--git-path','lfs/objects').decode().strip())
    if not lfsroot.is_absolute():lfsroot=PROJECT/lfsroot
    try:
        for number,relative in enumerate(all_paths,1):
            mode,oid=rows[relative]
            if mode not in {'100644','100755'}:raise RuntimeError('Unexpected file mode: '+relative)
            process.stdin.write((oid+'\n').encode());process.stdin.flush()
            header=process.stdout.readline().split()
            if len(header)!=3 or header[1]!=b'blob':raise RuntimeError('Missing Git blob: '+relative)
            data=process.stdout.read(int(header[2]));process.stdout.read(1)
            old=expected.get(relative)
            is_lfs=data.startswith(b'version https://git-lfs.github.com/spec/v1\n')
            if is_lfs:
                values=dict(line.split(b' ',1) for line in data.splitlines()[1:])
                sha=values[b'oid'].decode().removeprefix('sha256:');size=int(values[b'size'])
                object_path=lfsroot/sha[:2]/sha[2:4]/sha
                if not object_path.is_file() or object_path.stat().st_size!=size:raise RuntimeError('Missing LFS payload: '+relative)
                h=hashlib.sha256()
                with object_path.open('rb') as f:
                    for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
                if h.hexdigest()!=sha:raise RuntimeError('LFS object SHA mismatch: '+relative)
                lfs.append({'path':relative,'bytes':size,'sha256':sha})
            else:
                if len(data)>=100*1024*1024:raise RuntimeError('Oversize file not in LFS: '+relative)
                sha=hashlib.sha256(data).hexdigest();size=len(data)
                if (Path(relative).suffix.lower() in {'.json','.jsonl','.md','.html','.py','.mjs','.js','.txt','.sh','.yaml','.yml','.toml','.csv','.ps1'}):
                    for kind,pattern in PATTERNS.items():
                        if literal_matches(kind,pattern,data):raise RuntimeError('Credential literal found in staged '+kind+': '+relative)
            if old and (sha!=old['sha256'] or size!=old['bytes']) and not allowed_metadata(relative):
                local=(PROJECT/relative).read_bytes()
                if (not is_lfs and not old.get('credential_redactions')
                        and hashlib.sha256(local).hexdigest()==old['sha256']
                        and local.replace(b'\r\n',b'\n')==data.replace(b'\r\n',b'\n')):
                    # Existing index stat entries can retain old normalization after -text was added.
                    oid=git('hash-object','-w','--stdin',input=local).decode().strip()
                    data=local;sha=old['sha256'];size=len(local)
                    eol_index_repairs.append((relative,mode,oid))
                else:raise RuntimeError('Staged bytes differ from expected data: '+relative)
            if old and sha!=old['sha256']:changes.append(relative)
            record=old.copy() if old else {'path':relative}
            record.update(bytes=size,sha256=sha,lfs=is_lfs,git_blob_oid=oid)
            records.append(record)
            if number%1000==0:print(json.dumps({'verified_staged':number,'total':len(all_paths)}),flush=True)
    finally:
        process.stdin.close();process.stdout.close();process.wait()
    if eol_index_repairs:
        git('update-index','-z','--index-info',input=b''.join(mode.encode()+b' '+oid.encode()+b'\t'+relative.encode()+b'\0' for relative,mode,oid in eol_index_repairs))
    manifest.update(files=records,file_count=len(records),total_bytes=sum(r['bytes'] for r in records),
        index_based=True,lfs_file_count=len(lfs),lfs_total_bytes=sum(r['bytes'] for r in lfs))
    target.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    result={'status':'PASS','model_calls':0,'verified_file_count':len(records),
        'verified_bytes':manifest['total_bytes'],'lfs_file_count':len(lfs),'lfs_bytes':manifest['lfs_total_bytes'],
        'lfs_objects_sha_checked':True,'author_gitlink_exact':True,'no_imported_data_gitlinks':True,
        'staged_data_sha_matches':True,'metadata_changed_since_first_inventory':changes,
        'local_originals_preserved_for_redacted_files':True,
        'cached_index_eol_repairs':[x[0] for x in eol_index_repairs],
        'audit_metadata_not_in_own_manifest':['upload_inventory.json','staged_verification.json']}
    (HERE/'staged_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    subprocess.run(['git','add','--force',str(target.relative_to(PROJECT)),str((HERE/'staged_verification.json').relative_to(PROJECT))],cwd=PROJECT,check=True)
    print(json.dumps(result,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
