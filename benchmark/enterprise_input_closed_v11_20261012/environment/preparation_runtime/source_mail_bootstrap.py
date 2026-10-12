"""Personal QQ simulation for original imap-smtp-email account names."""
import json, os, sys
from pathlib import Path

def setup(credentials='/run/secrets/services.json',source_plan='/workspace/services/source_mail.json'):
    cfg=json.loads(Path(credentials).read_text(encoding='utf-8-sig'))['mail']
    plan=json.loads(Path(source_plan).read_text(encoding='utf-8'))
    values={'IMAP_HOST':cfg['imap_host'],'IMAP_PORT':str(cfg['imap_port']),'IMAP_USER':cfg['address'],'IMAP_PASS':cfg['authorization_code'],'IMAP_TLS':'true','IMAP_MAILBOX':plan['mailbox'],'SMTP_HOST':cfg['smtp_host'],'SMTP_PORT':str(cfg['smtp_port']),'SMTP_USER':cfg['address'],'SMTP_PASS':cfg['authorization_code'],'SMTP_SECURE':'true','SMTP_FROM':cfg['address'],'ALLOWED_READ_DIRS':'/workspace','ALLOWED_WRITE_DIRS':'/workspace'}
    lines=[]
    for prefix in ('','QQ_','163_','126_','VIP163_'):
        for key,val in values.items():
            if key.startswith('ALLOWED_') and prefix:continue
            os.environ[prefix+key]=val
            lines.append(prefix+key+'='+json.dumps(val,ensure_ascii=False))
    os.environ['NODE_PATH']='/usr/local/lib/node_modules'
    out=Path.home()/'.config/imap-smtp-email/.env';out.parent.mkdir(parents=True,exist_ok=True);out.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return {'account_provider':'QQ personal simulation','mailbox':plan['mailbox'],'legacy_account_aliases':['default','qq','163','126','vip163'],'credential_values_returned':False}

if __name__=='__main__':
    setup()
    if len(sys.argv)>1:os.execv(sys.executable,[sys.executable]+sys.argv[1:])
