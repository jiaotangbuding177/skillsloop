"""Resource-gated next-reference preparation; cannot launch an agent or evaluator."""
import fcntl,hashlib,json,os,shutil,subprocess,tarfile,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RESEARCH=ROOT.parents[1]
work=ROOT/'admission/vite_docs';work.mkdir(parents=True,exist_ok=True)
def write(j):
 p=work/'preparation_status.json';t=p.with_suffix('.tmp');t.write_text(json.dumps(j,indent=2));t.replace(p)
def main():
 lock=(work/'prepare.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not(work/'source_manifest.json').exists(),'Keep earlier reference attempt'
 source=RESEARCH/'reports/279_gui_acquisition/archives/web--vitejs--vite--fdb2e6f63894d8c458c1778f3df77afe537f2bb2.tar.gz'
 digest=hashlib.sha256(source.read_bytes()).hexdigest();assert digest=='af8e9929808b5414cc0a6e5b7287d07bc63e1404ca4d7ddee3cf721127febfd9'
 identity={'pid':os.getpid(),'start_ticks':Path(f'/proc/{os.getpid()}/stat').read_text().split(') ',1)[1].split()[19],'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'scope':'fixed Vite docs reference build only; no model/agent/evaluator calls'}
 (work/'preparation_identity.json').write_text(json.dumps(identity,indent=2))
 for _ in range(7200):
  if (ROOT/'private/STOP').exists():write({'state':'stopped_before_build','model_calls':0});return
  mem={k:int(v.split()[0]) for k,v in (line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines())}
  if mem['MemAvailable']//1024>=6144:break
  write({'epoch':time.time(),'state':'waiting_resource','required_available_mib':6144,'available_mib':mem['MemAvailable']//1024,'model_calls':0,'runtime_accepted':False});time.sleep(30)
 else:write({'state':'resource_wait_exhausted','model_calls':0});return
 native=Path(tempfile.mkdtemp(prefix='rw293-vite-reference-'))
 with tarfile.open(source) as t:t.extractall(native,filter='data')
 children=[p for p in native.iterdir() if p.is_dir()];assert len(children)==1;repo=children[0]
 manifest={'commit':'fdb2e6f63894d8c458c1778f3df77afe537f2bb2','source_archive_sha256':digest,
 'native_build_copy':str(repo),'source_archive_unchanged':True,'memory_mib':2048,'cpus':1,'node_heap_mib':1400,
 'build_entry_sha256':hashlib.sha256((ROOT/'reports/vite_reference_build_entry.py').read_bytes()).hexdigest(),
 'model_calls':0,'runtime_accepted':False}
 (work/'source_manifest.json').write_text(json.dumps(manifest,indent=2))
 cfg=json.loads((ROOT.parent/'288_rw_parallel_evolution_collection/parallel_config.json').read_text())
 name='rw293-vite-reference-build-'+str(time.time_ns());write({'epoch':time.time(),'state':'building_reference','container':name,'model_calls':0,'runtime_accepted':False})
 cmd=['docker','run','--name',name,'--memory','2048m','--memory-swap','2048m','--cpus','1','--pids-limit','512',
 '--mount',f'type=bind,src={repo},dst=/reference-build','--mount',f'type=bind,src={work},dst=/build-reports',
 '--mount',f'type=bind,src={ROOT}/reports/vite_reference_build_entry.py,dst=/build_entry.py,readonly',
 '--workdir','/reference-build','-e','NODE_OPTIONS=--max-old-space-size=1400','-e','PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1',
 '-e','SKIP_INSTALL_SIMPLE_GIT_HOOKS=1','-e','HUSKY=0',cfg['runtime_image_id'],'python3','/build_entry.py']
 with (work/'build.log').open('w') as log:rc=subprocess.call(cmd,stdout=log,stderr=subprocess.STDOUT)
 state={'epoch':time.time(),'state':'build_failed' if rc else 'build_completed_pending_gui_verifier','returncode':rc,'container':name,'model_calls':0,'runtime_accepted':False}
 if rc==0:
  dist=repo/'docs/.vitepress/dist';assert (dist/'index.html').is_file();shutil.copytree(dist,work/'site')
  state['site_files']={str(p.relative_to(work/'site')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (work/'site').rglob('*') if p.is_file()}
 write(state)
if __name__=='__main__':main()
