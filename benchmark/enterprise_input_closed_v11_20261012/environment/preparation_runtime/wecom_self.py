"""Resolve the authenticated experiment owner's actual WeCom single-chat target."""
import argparse
import json
import subprocess
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('operation',choices=['show','send']);p.add_argument('--mapping',default='/run/secrets/experiment-wecom-self.json')
    p.add_argument('--message-file');p.add_argument('--dry-run',action='store_true');p.add_argument('--output')
    a=p.parse_args();m=json.loads(Path(a.mapping).read_text(encoding='utf-8-sig'))
    if m.get('verified_authenticated_owner') is not True:raise ValueError('Mapping has not been matched to authenticated owner')
    if a.operation=='show':
        print(json.dumps({'target':'experiment_account_owner','chat_type':'single','verified':True}));return 0
    text=Path(a.message_file).read_text(encoding='utf-8-sig')
    req={'chat_id':m['chat_id'],'msg_type':'markdown','markdown':{'content':text}}
    argv=['/opt/node-tools/bin/wecom-cli','message','aibot','send','--json',json.dumps(req,ensure_ascii=False)]
    if a.dry_run:argv.append('--dry-run')
    if a.output:argv+=['--output',a.output]
    proc=subprocess.run(argv,capture_output=True,text=True,timeout=40)
    if proc.returncode:
        print(json.dumps({'passed':False,'exit_code':proc.returncode,'stderr':proc.stderr[-1800:]},ensure_ascii=False));return proc.returncode
    print(json.dumps({'passed':True,'dry_run':a.dry_run,'actually_sent':not a.dry_run,'receiver':'experiment_account_owner','native_cli_exit_code':proc.returncode},ensure_ascii=False));return 0

if __name__=='__main__':raise SystemExit(main())
