"""Make upstream Darwin screenshot commands work with installed Chromium."""
from pathlib import Path
import argparse,json,os,re,sys
SOURCES={'conv_073150ee30be','conv_2d755771f0da','conv_b4adad3e5e84','conv_143452559f75'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--source-id');p.add_argument('--request',type=Path,default=Path('/transport/request.json'));a,chain=p.parse_known_args()
    if chain and (not chain[0].endswith('.py') or not Path(chain[0]).is_file()):p.error('Following bootstrap must be an existing Python script')
    sid=a.source_id
    if not sid and a.request.is_file():
        r=json.loads(a.request.read_text(encoding='utf-8-sig'))
        found=re.search(r'conv_[0-9a-f]{12}',str(r.get('task_id',r.get('source_session_id',''))))
        sid=found.group(0) if found else None
    if sid in SOURCES:
        adapter=Path(__file__).with_name('darwin_runtime_compat.cjs').resolve()
        if not adapter.is_file():raise ValueError('Darwin Chromium adapter missing')
        addition='--require='+str(adapter)
        previous=os.environ.get('NODE_OPTIONS','')
        if addition not in previous:os.environ['NODE_OPTIONS']=(previous+' '+addition).strip()
        os.environ.setdefault('NODE_PATH','/opt/node-tools/lib/node_modules')
    print(json.dumps({'darwin_system_chromium_compatibility':sid in SOURCES,'skill_source_files_preloaded':False,'model_calls':0}))
    if chain:
        sys.stdout.flush();os.execv(sys.executable,[sys.executable,*chain])
    return 0


if __name__=='__main__':raise SystemExit(main())
