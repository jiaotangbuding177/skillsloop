"""Source-scoped real draft facade; token state never enters workspace exports."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path

SOURCE='conv_a999f104e767'
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--workspace',default='/workspace')
    sub=parser.add_subparsers(dest='command',required=True)
    for name in ['ready','token']:sub.add_parser(name)
    for name in ['upload-cover','upload-image']:sub.add_parser(name).add_argument('--file',required=True)
    sub.add_parser('draft-add').add_argument('--articles',required=True)
    sub.add_parser('draft-get').add_argument('--media-id',required=True)
    a=parser.parse_args()
    try:
        workspace=Path(a.workspace).resolve()
        scope=json.loads((workspace/'services/source_wechat.json').read_text('utf8'))
        if scope.get('source_session_id')!=SOURCE:raise ValueError('source_scope_mismatch')
        if a.command!='ready':
            active=json.loads((workspace/'services/wechat_live_activation.json').read_text('utf8'))
            if active.get('source_session_id')!=SOURCE or active.get('available_from_dispatch_index')!=3 or active.get('allowed_scope')!='test_upload_and_draft_only':
                raise ValueError('live_test_not_activated_at_reviewed_turn')
        if a.command=='draft-add':
            articles=json.loads(Path(a.articles).read_text('utf-8-sig')).get('articles',[])
            if len(articles)!=1 or articles[0].get('title')!='【EvoMind API TEST｜请勿发布】':raise ValueError('only_explicit_test_draft_allowed')
        token=hashlib.sha256(str(workspace).encode()).hexdigest()[:16]
        core=Path(__file__).resolve().with_name('wechat_cli.py')
        argv=[sys.executable,str(core),'--config','/run/secrets/wechat_official_account.json','--state','/tmp/wechat-private/'+token,a.command]
        if a.command.startswith('upload-'):argv+=['--file',a.file]
        elif a.command=='draft-add':argv+=['--articles',a.articles]
        elif a.command=='draft-get':argv+=['--media-id',a.media_id]
        return subprocess.run(argv).returncode
    except Exception as e:
        print(json.dumps({'ok':False,'command':a.command,'error_type':type(e).__name__,'source_scope_verified':False,'no_mock_success':True}))
        return 2
if __name__=='__main__':raise SystemExit(main())
