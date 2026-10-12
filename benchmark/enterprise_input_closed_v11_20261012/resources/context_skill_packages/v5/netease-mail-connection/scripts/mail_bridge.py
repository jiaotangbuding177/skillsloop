"""Forward genuine mail CLI calls or extract a local MIME message, without credentials."""
import argparse, email, hashlib, json, re, subprocess, sys
from email import policy
from email.header import decode_header, make_header
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

def header(value):
    return str(make_header(decode_header(str(value or ''))))

class Links(HTMLParser):
    def __init__(self): super().__init__();self.urls=[]
    def handle_starttag(self,tag,attrs):
        for key,val in attrs:
            if tag.lower()=='a' and key.lower()=='href' and val:
                if urlparse(val).scheme.lower() in ('http','https'):self.urls.append(val)

def extract_eml(source, output_dir):
    msg=email.message_from_bytes(Path(source).read_bytes(),policy=policy.default)
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    body=[];attachments=[];links=[];used={'message.json'}
    for part in msg.walk():
        if part.is_multipart():continue
        content=part.get_payload(decode=True) or b''
        filename=part.get_filename()
        if filename:
            name=Path(header(filename).replace('\\','/')).name
            if name in ('','.','..'):name='attachment.bin'
            candidate=name;i=1
            while candidate in used or (out/candidate).exists():
                i+=1;candidate=f'{Path(name).stem}_{i}{Path(name).suffix}'
            used.add(candidate);target=out/candidate;target.write_bytes(content)
            attachments.append({'name':candidate,'path':str(target),'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest(),'content_type':part.get_content_type()})
        elif part.get_content_type() in ('text/plain','text/html'):
            text=content.decode(part.get_content_charset() or 'utf-8',errors='replace')
            body.append({'type':part.get_content_type(),'text':text})
            if part.get_content_type()=='text/html':
                parser=Links();parser.feed(text);links.extend(parser.urls)
            else:links.extend(re.findall(r'https?://[^\s<>\"]+',text))
    result={'schema':'local-eml-extraction-v1','origin':'local_eml','remote_mail_accessed':False,'subject':header(msg.get('Subject')),'from':header(msg.get('From')),'to':header(msg.get('To')),'date':str(msg.get('Date','')),'message_id':str(msg.get('Message-ID','')),'body':body,'attachments':attachments,'cloud_links':list(dict.fromkeys(links)),'cloud_attachment_bytes_downloaded':False}
    (out/'message.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result

def parser():
    p=argparse.ArgumentParser();p.add_argument('--backend',default='/opt/real-services/mail_cli.py');p.add_argument('--credentials',default='/run/secrets/services.json')
    subs=p.add_subparsers(dest='command',required=True);subs.add_parser('status')
    s=subs.add_parser('list');s.add_argument('--folder',default='INBOX');s.add_argument('--limit',type=int,default=10)
    s=subs.add_parser('read');s.add_argument('--folder',default='INBOX');s.add_argument('--uid',required=True);s.add_argument('--output-dir',required=True)
    s=subs.add_parser('send');s.add_argument('--to',required=True);s.add_argument('--subject',required=True);s.add_argument('--body-file',required=True);s.add_argument('--attachments',nargs='*',default=[])
    s=subs.add_parser('eml');s.add_argument('--file',required=True);s.add_argument('--output-dir',required=True)
    return p

def main():
    a=parser().parse_args()
    if a.command=='eml':print(json.dumps(extract_eml(a.file,a.output_dir),ensure_ascii=False));return
    if not Path(a.backend).is_file():raise FileNotFoundError('Real mail backend is not mounted')
    args=[sys.executable,a.backend,'--credentials',a.credentials,a.command]
    if a.command in ('list','read'):args+=['--folder',a.folder]
    if a.command=='list':
        if a.limit<1:raise ValueError('limit must be positive')
        args+=['--limit',str(a.limit)]
    if a.command=='read':args+=['--uid',a.uid,'--output-dir',a.output_dir]
    if a.command=='send':args+=['--to',a.to,'--subject',a.subject,'--body-file',a.body_file,'--attachments',*a.attachments]
    result=subprocess.run(args,check=False)
    raise SystemExit(result.returncode)

if __name__=='__main__':main()
