import json,subprocess,socket,time,os,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 with socket.socket() as s:s.bind(('127.0.0.1',8193))
 log=(ROOT/'reports/relay.log').open('ab')
 p=subprocess.Popen(['python3',str(ROOT/'scripts/relay.py')],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 for _ in range(30):
  if p.poll() is not None:raise RuntimeError('Relay exited; retained log')
  try:
   health=json.load(urllib.request.urlopen('http://127.0.0.1:8193/health',timeout=1));break
  except Exception:time.sleep(.3)
 else:raise RuntimeError('Relay not ready')
 ticks=Path(f'/proc/{p.pid}/stat').read_text().split(') ',1)[1].split()[19]
 (ROOT/'reports/relay_identity.json').write_text(json.dumps({'pid':p.pid,'start_ticks':ticks,'port':8193,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'health':health},indent=2));print(json.dumps({'relay_ready':True,'pid':p.pid,'port':8193}))
if __name__=='__main__':main()
