import subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1];cache=Path('/var/tmp/rw288-squoosh-cache');assert cache.is_dir()

image='sha256:603d4b4f22fc32a7d0bb2e034db9f9afc1d5597f6116cfb35d2fa1e244d34c3d'
cmd=['docker','run','--name','rw288-squoosh-native-build-v4','--network','none','--memory','2048m','--memory-swap','2048m','--cpus','2','--pids-limit','512','--mount',f'type=bind,src={root}/admission/squoosh/fixed_source.tar,dst=/source.tar,readonly','--mount',f'type=bind,src={cache},dst=/cache','--mount',f'type=bind,src={root}/admission/squoosh,dst=/publish','--mount',f'type=bind,src={root}/reports/build_native_v4.py,dst=/build.py,readonly',image,'python3','/build.py']
raise SystemExit(subprocess.call(cmd))
