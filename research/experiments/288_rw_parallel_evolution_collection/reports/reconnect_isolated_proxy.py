import subprocess,json,time,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1];record={'version':'v2.5_transport_reconnect','expected_host_pid':130246,'source_port':54448,'old_destination_port':8788,'new_proxy':8791,'actor_restarted':False,'full_round_remains':3,'old_freeze_untouched':True,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'started_epoch':time.time()}
manifest=json.loads((root/'reports/live_transport_v25_manifest.json').read_text());assert manifest['state']=='new_connections_isolated'
log=root/'runs/squoosh_recreation_eval_1791129536850164583/model_proxy.log';before=log.stat().st_size;deadline=time.time()+50
while time.time()<deadline:
 lines=log.read_text()[before:]
 if '127.0.0.1:54448 - "POST /v1/messages?beta=true HTTP/1.1" 200 OK' in lines:
  # Wait until the compatible proxy has delivered this complete upstream result;
  # close only this actor's old keep-alive transport, not its model/session process.
  time.sleep(.3)
  ss=subprocess.check_output(['ss','-tnp'],text=True);matches=[l for l in ss.splitlines() if '127.0.0.1:54448' in l and '127.0.0.1:8788' in l and 'pid=130246,' in l]
  if not matches:record['state']='old_socket_already_closed';break
  cmd=['ss','-K','dst','127.0.0.1','dport','=',':8788','sport','=',':54448']
  r=subprocess.run(cmd,capture_output=True,text=True);record.update(state='targeted_transport_reconnected' if r.returncode==0 else 'socket_close_failed',returncode=r.returncode,socket=matches[0],result=r.stdout.strip(),stderr=r.stderr.strip());break
 time.sleep(.15)
else:record['state']='no_new_completed_response_before_deadline_no_socket_killed'
record['ended_epoch']=time.time();(root/'reports/live_transport_reconnect_result.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
