import subprocess,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 assert (ROOT/'reports/phase_manifest.json').exists()
 if (ROOT/'private/minipaint_rounds.json').exists():raise RuntimeError('First round already started')
 log=(ROOT/'reports/rollout_launcher.log').open('ab')
 p=subprocess.Popen(['python3',str(ROOT/'scripts/native_stage.py'),'recreation_eval'],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 for _ in range(30):
  if p.poll() is not None:raise RuntimeError('Controller exited; inspect retained log')
  if (ROOT/'reports/active_rollout.json').exists():
   r=json.loads((ROOT/'reports/active_rollout.json').read_text());print(json.dumps({'started':True,'controller_pid':p.pid,'attempt':r['attempt'],'round':1,'max_rounds':3}));return
  time.sleep(.3)
 raise RuntimeError('No active rollout record')
if __name__=='__main__':main()
