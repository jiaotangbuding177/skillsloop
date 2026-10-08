import json,subprocess,time,shutil,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT.parents[1]/'reports/279_gui_acquisition/sources/web--GoogleChromeLabs--squoosh'
def main():
 work=ROOT/'admission/squoosh';work.mkdir(exist_ok=True)
 manifest=ROOT.parents[1]/'reports/279_gui_acquisition/inventories/web--GoogleChromeLabs--squoosh.json'
 # Work copy preserves immutable acquisition source.
 copy=work/'source'
 if copy.exists():raise RuntimeError('Retain existing reference build')
 shutil.copytree(SOURCE,copy)
 status={'state':'building','source_commit':'e8d35e0fb66eb16eff6fe8fc773eabcbb7128de3','started_epoch':time.time(),'memory_limit':'1g','source_mutated':False,'model_called':False}
 (work/'build_status.json').write_text(json.dumps(status,indent=2))
 cmd=['docker','run','--name','rw288-squoosh-build','--memory','1g','--cpus','1','--pids-limit','512','--mount',f'type=bind,src={copy},dst=/reference-build','--workdir','/reference-build','-e','NODE_OPTIONS=--max-old-space-size=640','-e','HUSKY=0','skillloop-rw-web:218-v2','bash','-lc','npm ci --no-audit --no-fund && npm run build']
 with (work/'build.log').open('w') as log:rc=subprocess.call(cmd,stdout=log,stderr=subprocess.STDOUT)
 status.update(state='build_finished' if rc==0 else 'build_failed',returncode=rc,ended_epoch=time.time())
 if rc==0:
  output=copy/'build';assert (output/'index.html').is_file()
  site=work/'site';shutil.copytree(output,site)
  status['site_files']={str(p.relative_to(site)):hashlib.sha256(p.read_bytes()).hexdigest() for p in site.rglob('*') if p.is_file()}
 (work/'build_status.json').write_text(json.dumps(status,indent=2));print(json.dumps({k:v for k,v in status.items() if k!='site_files'}))
if __name__=='__main__':main()
