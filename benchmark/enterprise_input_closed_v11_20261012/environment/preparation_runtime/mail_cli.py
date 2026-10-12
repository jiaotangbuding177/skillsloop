"""Real QQ source mailbox tools with authorized personal-recipient simulation."""
import argparse,email,email.policy,imaplib,json,smtplib,ssl
from pathlib import Path
from email.header import decode_header,make_header
from email.message import EmailMessage

def header(s):return str(make_header(decode_header(s or '')))
def execute(a):
    cfg=json.loads(Path(a.credentials).read_text(encoding='utf-8-sig'))['mail']
    plan_path=Path(a.plan)
    plan=json.loads(plan_path.read_text(encoding='utf-8')) if plan_path.is_file() else None
    if a.command=='send':
        msg=EmailMessage();msg['From']=cfg['address'];msg['To']=cfg['address'];msg['Subject']=a.subject
        msg.set_content(Path(a.body_file).read_text(encoding='utf-8'))
        for path in a.attachments:
            f=Path(path);msg.add_attachment(f.read_bytes(),maintype='application',subtype='octet-stream',filename=f.name)
        with smtplib.SMTP_SSL(cfg['smtp_host'],cfg['smtp_port'],timeout=35,context=ssl.create_default_context()) as server:
            server.login(cfg['address'],cfg['authorization_code']);rejected=server.send_message(msg)
        return {'sent':not rejected,'attachment_count':len(a.attachments),'recipient_mapping':'original source recipient -> configured personal account','original_external_recipient_used':False}
    if not plan or not plan.get('mailbox','').startswith('SkillLoop_20261009_conv_'):
        raise ValueError('Current source mailbox plan is required; no full private mailbox access fallback')
    with imaplib.IMAP4_SSL(cfg['imap_host'],cfg['imap_port'],timeout=35,ssl_context=ssl.create_default_context()) as server:
        server.login(cfg['address'],cfg['authorization_code']);typ,_=server.select(plan['mailbox'],readonly=True)
        if typ!='OK':raise RuntimeError('Source mailbox unavailable')
        if a.command=='status':return {'authenticated':True,'mailbox':plan['mailbox'],'source_isolated':True}
        if a.command=='list':
            typ,data=server.uid('search',None,'ALL');result=[]
            if typ!='OK':raise RuntimeError('Source mailbox search failed')
            for uid in reversed(data[0].split()[-a.limit:]):
                typ,raw=server.uid('fetch',uid,'(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM DATE MESSAGE-ID)])')
                msg=email.message_from_bytes(next(x[1] for x in raw if isinstance(x,tuple)))
                result.append({'uid':uid.decode(),'subject':header(msg['Subject']),'from':header(msg['From']),'date':msg['Date'],'message_id':msg['Message-ID']})
            return {'mailbox':plan['mailbox'],'messages':result}
        typ,raw=server.uid('fetch',a.uid,'(BODY.PEEK[])')
        if typ!='OK':raise RuntimeError('Source message read failed')
        msg=email.message_from_bytes(next(x[1] for x in raw if isinstance(x,tuple)),policy=email.policy.default)
        bodies=[];attachments=[]
        for part in msg.walk():
            if part.is_multipart():continue
            data=part.get_payload(decode=True) or b''
            if part.get_filename():
                f=Path(a.output_dir)/Path(part.get_filename().replace('\\','/')).name;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(data)
                attachments.append({'name':f.name,'path':str(f),'bytes':len(data)})
            elif part.get_content_type() in ('text/plain','text/html'):
                bodies.append({'type':part.get_content_type(),'text':data.decode(part.get_content_charset() or 'utf-8',errors='replace')})
        return {'uid':a.uid,'mailbox':plan['mailbox'],'subject':header(msg['Subject']),'body':bodies,'attachments':attachments}

def main():
    p=argparse.ArgumentParser();p.add_argument('--credentials',default='/run/secrets/services.json');p.add_argument('--plan',default='/workspace/services/source_mail.json')
    s=p.add_subparsers(dest='command',required=True);s.add_parser('status')
    q=s.add_parser('list');q.add_argument('--folder',default='INBOX');q.add_argument('--limit',type=int,default=10)
    q=s.add_parser('read');q.add_argument('--folder',default='INBOX');q.add_argument('--uid',required=True);q.add_argument('--output-dir',required=True)
    q=s.add_parser('send');q.add_argument('--to',required=True);q.add_argument('--subject',required=True);q.add_argument('--body-file',required=True);q.add_argument('--attachments',nargs='*',default=[])
    a=p.parse_args()
    try:print(json.dumps(execute(a),ensure_ascii=False));return 0
    except Exception as e:print(json.dumps({'ok':False,'error_type':type(e).__name__}));return 2

if __name__=='__main__':raise SystemExit(main())
