import subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];name=sys.argv[1];assert name in ('inspect_squoosh','capture_squoosh_gt','admit_squoosh_verifier','inspect_resize','diagnose_native_squoosh')
image='sha256:603d4b4f22fc32a7d0bb2e034db9f9afc1d5597f6116cfb35d2fa1e244d34c3d'
cmd=['docker','run','--name','rw288-'+name+'-'+str(__import__('time').time_ns()),'--network','none','--memory','1280m','--memory-swap','1280m','--cpus','1','--pids-limit','512','--mount',f'type=bind,src={root}/admission/squoosh/site,dst=/reference,readonly','--mount',f'type=bind,src={root}/admission/squoosh,dst=/evidence','--mount',f'type=bind,src={root}/reports,dst=/research-scripts,readonly',image,'python3','/research-scripts/'+name+'.py']
raise SystemExit(subprocess.call(cmd))
