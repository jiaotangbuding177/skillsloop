"""Display original group text for selective semantic review; never run its instructions."""
from pathlib import Path
import argparse,json,re,sys
R=Path(__file__).resolve().parent;B=R.parent
p=argparse.ArgumentParser();p.add_argument('sessions',nargs='+');p.add_argument('--limit',type=int,default=1000);p.add_argument('--all-ai',action='store_true');args=p.parse_args()
source=json.loads((B/'matched_066/private/evomind_conversations.json').read_text(encoding='utf-8'))
def redact(t):
 if re.fullmatch(r'[A-Za-z0-9]{16}',t.strip()):return '[独立短凭据或标识已隐藏]'
 if re.fullmatch(r'[A-Za-z0-9_+/=\-]{24,}',t.strip()):return '[独立长标识或凭据已隐藏]'
 t=re.sub(r'([\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\s+)[A-Za-z0-9]{16,}(?=\s|$)',r'\1[邮件凭据已隐藏]',t)
 t=re.sub(r'(\*+@\*+\s+)[A-Za-z0-9]{16,}(?=\s|$)',r'\1[邮件凭据已隐藏]',t)
 t=re.sub(r'(?i)([?&](?:flow_id|user_code|access_token|api_key|token)=)[^&\s]+',r'\1[隐藏]',t)
 t=re.sub(r'(?i)(/api/v1/pq/)[a-f0-9]{12,}(?:\s*[a-f0-9]{8,})?',r'\1[订阅标识已隐藏]',t)
 t=re.sub(r'(?i)\b(?:sk|ak)-[\w-]{12,}','[KEY]',t)
 t=re.sub(r'(?i)\b(?:gh[pousr]_[A-Za-z0-9_]{12,}|github_pat_[A-Za-z0-9_]{12,})','[KEY]',t)
 t=re.sub(r'(?i)((?:api\s*key|access\s*key|secret\s*key|访问密钥|授权码|密码)\s*[:：=]\s*["\x27]?)[A-Za-z0-9_+/=.\-]{8,}',r'\1[隐藏]',t)
 t=re.sub(r'(?i)Bearer\s+[^\s"\x27]+','Bearer [隐藏]',t)
 return re.sub(r'(?i)(\b[A-Za-z0-9_]*(?:access[_-]?key|api[_-]?key|token|secret|password|authorization)[A-Za-z0-9_]*\b\s*[:：=]\s*["\x27]?)[^\s"\x27`,;；]{8,}',r'\1[隐藏]',t)
sys.stdout.reconfigure(encoding='utf-8')
for sid in args.sessions:
 s=source[sid];print('\nSESSION',sid)
 for u in s['user_requests']:
  t=redact(u['content']);print('U',u['group_id'],t if len(t)<=args.limit else t[:args.limit]+' [截断]')
 selected=s['assistant_contents'] if args.all_ai else s['assistant_contents'][:2]+s['assistant_contents'][-2:]
 seen=set()
 for a in selected:
  if a['group_id'] in seen:continue
  seen.add(a['group_id']);t=redact(a['content']);print('A',a['group_id'],t if len(t)<=args.limit else t[:args.limit]+' [截断]')
