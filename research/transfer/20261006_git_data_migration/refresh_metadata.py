"""Update only upload receipts/docs; prove all previously audited data OIDs stay fixed."""
from pathlib import Path
import hashlib, json, subprocess
from inventory_upload import PROJECT,HERE,PATTERNS,literal_matches

def git(*args,input=None):
    return subprocess.run(['git',*args],cwd=PROJECT,input=input,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).stdout

def main():
    target=HERE/'upload_inventory.json';manifest=json.loads(target.read_text(encoding='utf-8'))
    records={r['path']:r for r in manifest['files']}
    fixed=[PROJECT/x for x in ('research/README.md','research/STATE.md',
        'research/memory/2026-10-07_git_full_data_migration.md','research/reports/2026-10-07_git_data_migration.md')]
    fixed+=sorted(HERE.glob('*.py'))+[HERE/'upload_receipt.json',HERE/'independent_review.json']
    updated=[]
    for p in fixed:
        rel=p.relative_to(PROJECT).as_posix();data=p.read_bytes()
        for kind,pattern in PATTERNS.items():
            if literal_matches(kind,pattern,data):raise RuntimeError('Credential in metadata: '+rel)
        oid=git('hash-object','-w','--stdin',input=data).decode().strip()
        git('update-index','--add','--cacheinfo','100644,'+oid+','+rel)
        old=records.get(rel)
        if not old or old['sha256']!=hashlib.sha256(data).hexdigest():updated.append(rel)
        records[rel]={'path':rel,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),
            'lfs':False,'git_blob_oid':oid}
    rows={}
    for raw in git('ls-files','--stage','-z').split(b'\0'):
        if not raw:continue
        head,path=raw.split(b'\t',1);mode,oid,stage=head.split();rows[path.decode()]=(mode.decode(),oid.decode(),stage.decode())
    for rel,r in records.items():
        if rows.get(rel,())[1:3]!=(r['git_blob_oid'],'0'):raise RuntimeError('Unexpected index change after full audit: '+rel)
    if rows.get('research/baselines/Trace2Skill')!=('160000','3d0b52a140f002a512930252b613c49048f7d5ac','0'):raise RuntimeError('Author gitlink changed')
    manifest.update(files=[records[x] for x in sorted(records)],file_count=len(records),
        total_bytes=sum(r['bytes'] for r in records.values()),metadata_followup_only=True)
    target.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    result={'status':'METADATA_DELTA_PASS_ALL_DATA_BLOB_OIDS_UNCHANGED','model_calls':0,
        'data_commit':'80f54800574e308772e5fc63e56515da8e2bb7a0','final_manifest_file_count':len(records),
        'final_manifest_bytes':manifest['total_bytes'],'updated_metadata_paths':updated,
        'lfs_file_count':manifest['lfs_file_count'],'lfs_bytes':manifest['lfs_total_bytes'],
        'data_and_lfs_payloads_changed':0}
    audit=HERE/'metadata_delta_verification.json';audit.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for p in (target,audit):
        oid=git('hash-object','-w','--stdin',input=p.read_bytes()).decode().strip()
        git('update-index','--add','--cacheinfo','100644,'+oid+','+p.relative_to(PROJECT).as_posix())
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
