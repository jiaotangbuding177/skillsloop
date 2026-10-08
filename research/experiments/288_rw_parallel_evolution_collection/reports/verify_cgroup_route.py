import subprocess,json,time
from pathlib import Path
root=Path(__file__).resolve().parents[1];cg='c7a6ed9cc851e1cf70f68f2cee7ade9bec495455fee6fe53b580f4f82035c726'
def stats():return [l for l in subprocess.check_output(['iptables','-t','nat','-L','OUTPUT','-nv'],text=True).splitlines() if cg in l]
before=stats();cmd=['docker','exec','rw288-minipaint_recreation_eval_1791129685783416430','python3','-c',"import urllib.request; r=urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8788/v1/models',headers={'Authorization':'Bearer local'}),timeout=3); print(r.status)"]
r=subprocess.run(cmd,capture_output=True,text=True);after=stats();obj={'epoch':time.time(),'before':before,'after':after,'health_status':r.stdout,'returncode':r.returncode,'stderr':r.stderr,'model_called':False};(root/'reports/cgroup_route_verification.json').write_text(json.dumps(obj,indent=2));print(json.dumps(obj))
