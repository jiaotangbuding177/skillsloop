"""Safe runtime roles and resource summary; no arguments, private inputs or secrets."""
import json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]; s=json.loads((root/'reports/pipeline_status.json').read_text())
code=r'''
import json,os,time
from pathlib import Path
up=float(Path('/proc/uptime').read_text().split()[0]); hz=os.sysconf('SC_CLK_TCK'); processes=[]
for d in Path('/proc').iterdir():
 if not d.name.isdigit(): continue
 try:
  stat=(d/'stat').read_text().rsplit(')',1)[1].split(); args=(d/'cmdline').read_bytes().replace(b'\x00',b' ').decode(errors='replace'); comm=(d/'comm').read_text().strip()
  if comm in ['tar','gzip','python3','node','npm','bash','setpriv','bwrap'] or 'playwright' in args:
   role='official_scorer' if '--skip-agent' in args else 'archive_extract' if comm in ['tar','gzip'] else 'agent' if ('claude-original' in args or comm=='claude') else 'browser_or_test' if 'playwright' in args or comm=='node' else 'runtime'
   processes.append({'pid':int(d.name),'comm':comm,'role':role,'state':stat[0],'age_seconds':round(up-int(stat[19])/hz,1),'cpu_seconds':round((int(stat[11])+int(stat[12]))/hz,1)})
 except (OSError,IndexError,ValueError): pass
v=os.statvfs('/workspace'); print(json.dumps({'processes':processes,'disk_available_bytes':v.f_bavail*v.f_frsize}))
'''
r=subprocess.run(['docker','exec','rw238-'+s['attempt'],'python3','-c',code],capture_output=True,text=True)
assert r.returncode==0,r.stderr[-500:]
data=json.loads(r.stdout); (root/'reports/process_snapshot.json').write_text(json.dumps(data,indent=2)); print(json.dumps(data))
