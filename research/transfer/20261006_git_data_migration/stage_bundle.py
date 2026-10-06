"""Stage the data bundle; redact credentials in Git blobs, keep local originals."""
from pathlib import Path
import hashlib, json, subprocess

from inventory_upload import PROJECT, HERE, PATTERNS

def git(*args, input=None):
    return subprocess.run(['git',*args],cwd=PROJECT,input=input,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).stdout

def index_files(items):
    if not items:return
    payload=b''.join(b'100644 '+oid.encode()+b'\t'+path.encode('utf-8')+b'\0' for path,oid in items)
    git('update-index','-z','--index-info',input=payload)

def main():
    manifest_path=HERE/'upload_inventory.json'
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    # Ordinary paths are staged normally, with large-data filters enabled.
    print('STAGING_NORMAL_FILES',flush=True)
    subprocess.run(['git','--literal-pathspecs','add','--force','--pathspec-from-file='+str(HERE/'stage_paths.txt'),'--pathspec-file-nul'],cwd=PROJECT,check=True)
    # Nested import repositories are historical data snapshots, not gitlinks.
    nested=(HERE/'nested_stage_paths.txt').read_bytes().split(b'\0')
    nested=[x.decode('utf-8') for x in nested if x]
    if nested:
        payload=''.join(x+'\n' for x in nested).encode('utf-8')
        hashes=git('hash-object','-w','--stdin-paths',input=payload).decode().splitlines()
        if len(hashes)!=len(nested):raise RuntimeError('Nested import hash count mismatch')
        index_files(list(zip(nested,hashes)))
    print('STAGED_NESTED_IMPORT_FILES '+str(len(nested)),flush=True)
    findings=json.loads((HERE/'secret_locations.json').read_text(encoding='utf-8'))['literal_locations_only']
    affected=sorted({x['path'] for x in findings})
    lookup={r['path']:r for r in manifest['files']}
    redactions=[]
    for relative in affected:
        source=PROJECT/relative;data=source.read_bytes()
        if hashlib.sha256(data).hexdigest()!=lookup[relative]['sha256']:raise RuntimeError('Source changed since inventory: '+relative)
        counts={}
        safe=data
        for kind,pattern in PATTERNS.items():
            if kind=='api_key_literal':raise_if=bool(pattern.search(safe))
            else:raise_if=False
            if raise_if:raise RuntimeError('Unexpected API literal requires explicit local review: '+relative)
            if kind=='github_token_literal':
                safe,n=pattern.subn(b'[REDACTED_GITHUB_TOKEN]',safe)
            elif kind=='credential_database_uri':
                safe,n=pattern.subn(lambda m:m.group(0).split(b'://',1)[0]+b'://[REDACTED_DATABASE_CREDENTIAL]@',safe)
            elif kind=='private_key_block':
                if pattern.search(safe):raise RuntimeError('Private key block requires separate full-block redaction')
                n=0
            else:n=0
            if n:counts[kind]=n
        if not counts:raise RuntimeError('Secret report entry had no reviewed redaction: '+relative)
        for pattern in PATTERNS.values():
            if pattern.search(safe):raise RuntimeError('Credential literal remains after redaction: '+relative)
        attr=git('check-attr','filter','--',relative).decode().strip()
        if attr.endswith(': lfs'):
            staged=git('lfs','clean','--',relative,input=safe)
            if not staged.startswith(b'version https://git-lfs.github.com/spec/v1'):raise RuntimeError('Expected LFS pointer')
        else:staged=safe
        oid=git('hash-object','-w','--stdin',input=staged).decode().strip()
        index_files([(relative,oid)])
        original=lookup[relative].copy()
        lookup[relative].update(local_original_sha256=original['sha256'],local_original_bytes=original['bytes'],
            sha256=hashlib.sha256(safe).hexdigest(),bytes=len(safe),credential_redactions=counts,
            local_original_preserved=True)
        redactions.append({'path':relative,'local_original_sha256':original['sha256'],
            'uploaded_sha256':lookup[relative]['sha256'],'counts':counts,'local_original_preserved':True})
    manifest['credential_redaction_file_count']=len(redactions)
    manifest['total_bytes']=sum(r['bytes'] for r in manifest['files'])
    manifest['local_originals_kept_for_redacted_files']=True
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (HERE/'credential_redaction_manifest.json').write_text(json.dumps({'no_secret_values':True,
        'local_originals_modified':0,'files':redactions},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'staged_manifest_files':len(manifest['files']),'credential_redacted_files':len(redactions),
        'local_originals_modified':0,'uploaded_bytes':manifest['total_bytes']},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
