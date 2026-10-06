"""Build the authorized upload inventory, hash files and report secret locations only."""
from pathlib import Path
import hashlib, json, os, re

PROJECT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SKIP_DIRS = {'.git', 'node_modules', '.runtime', '.venv', 'venv', '__pycache__',
             '.cache', 'cache', '.pytest_cache', 'dist', 'build',
             'libreoffice_runtime', '安装资源', 'cli_shim_bin', 'profile_shim_bin'}
EXCLUDED_NAMES = {'.env', '.git', 'credentials.json', 'secrets.json'}
PATTERNS = {
    'api_key_literal': re.compile(rb'sk-(?:sp-)?[A-Za-z0-9_-]{20,}'),
    'github_token_literal': re.compile(rb'(?:ghp_|github_pat_)[A-Za-z0-9_]{30,}'),
    'private_key_block': re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'credential_database_uri': re.compile(rb'(?:mongodb(?:\+srv)?|postgres(?:ql)?|mysql)://[^\s"\x27<>]+:[^\s"\x27<>]+@'),
}
TEXT_EXTENSIONS = {'.md','.txt','.py','.mjs','.js','.json','.jsonl','.html','.yaml','.yml','.toml','.csv','.tsv','.sh','.ps1','.xml','.conf','.sql'}

def literal_matches(kind,pattern,data):
    matches=list(pattern.finditer(data))
    if kind=='api_key_literal':
        matches=[m for m in matches if m.start()==0 or data[m.start()-1] not in b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789']
    return matches

def eligible(p):
    rel=p.relative_to(PROJECT)
    if rel.parts[:3] == ('research','baselines','Trace2Skill'): return False
    if p.name in EXCLUDED_NAMES or p.name.startswith(('secrets.','credentials.')) or (p.name.startswith('.env.') and p.name != '.env.example'): return False
    return not any(x in SKIP_DIRS for x in rel.parts[:-1])

def files():
    result=[]
    for base in (PROJECT/'research', PROJECT/'enginering/demo'):
        for directory,dirs,names in os.walk(base):
            dirs[:]=[d for d in dirs if d not in SKIP_DIRS and not (base.name=='demo' and d=='artifacts')]
            if Path(directory) == PROJECT/'research/baselines':
                dirs[:]=[d for d in dirs if d!='Trace2Skill']
            for name in names:
                p=Path(directory)/name
                if eligible(p):result.append(p)
    result.extend(PROJECT/x for x in ('AGENTS.md','.gitignore','.gitattributes','.gitmodules','MIGRATION.md') if (PROJECT/x).is_file())
    # The single original checker is a portable source file, not a vendored runtime.
    checker=PROJECT/'enginering/demo/.runtime/node_modules/openclaw/skills/skill-creator/scripts/quick_validate.py'
    if checker.is_file():result.append(checker)
    ignored_self={HERE/'upload_inventory.json',HERE/'secret_locations.json',HERE/'stage_paths.txt',HERE/'nested_stage_paths.txt',HERE/'staged_verification.json'}
    return sorted(set(result)-ignored_self)

def main():
    records=[]; findings=[]; excluded=[]; nested=[]
    selected=files()
    print(json.dumps({'inventory_started':len(selected)}),flush=True)
    for number,p in enumerate(selected,1):
        data=p.read_bytes(); rel=p.relative_to(PROJECT).as_posix()
        records.append({'path':rel,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
        if p.suffix.lower() in TEXT_EXTENSIONS or p.name in ('Dockerfile','.gitignore','.gitattributes','.gitmodules'):
            for kind,pattern in PATTERNS.items():
                matches=literal_matches(kind,pattern,data)
                if matches:
                    findings.append({'path':rel,'kind':kind,'count':len(matches),
                        'lines':sorted({data.count(b'\n',0,m.start())+1 for m in matches[:30]})})
        if rel.startswith('research/imports/') and ('repository/' in rel or 'repository_complete/' in rel): nested.append(rel)
        if number%1000==0:print(json.dumps({'inventoried':number,'total':len(selected),'literal_location_records':len(findings)}),flush=True)
    HERE.mkdir(parents=True,exist_ok=True)
    (HERE/'upload_inventory.json').write_text(json.dumps({'model_calls':0,'files':records,
        'file_count':len(records),'total_bytes':sum(r['bytes'] for r in records),
        'baseline_submodule':{'path':'research/baselines/Trace2Skill','commit':'3d0b52a140f002a512930252b613c49048f7d5ac'},
        'excluded':'Credentials, package/runtime/cache files and Windows installed binaries; data and saved request/response evidence retained.'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (HERE/'secret_locations.json').write_text(json.dumps({'literal_locations_only':findings,'no_values_disclosed':True},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    normal=[r['path'] for r in records if r['path'] not in nested]
    (HERE/'stage_paths.txt').write_bytes(b''.join(x.encode('utf-8')+b'\0' for x in normal))
    (HERE/'nested_stage_paths.txt').write_bytes(b''.join(x.encode('utf-8')+b'\0' for x in nested))
    print(json.dumps({'files':len(records),'bytes':sum(x['bytes'] for x in records),'literal_findings':findings,
        'nested_file_count':len(nested),'over_50_mib':[r for r in records if r['bytes']>=50*1024*1024]},ensure_ascii=False))

if __name__=='__main__':main()
