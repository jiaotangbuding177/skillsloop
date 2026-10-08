import base64, io, json, secrets, urllib.request, re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]
cfg=json.loads((ROOT/'model_resource.json').read_text())
key=json.loads((ROOT/cfg['credential_file']).read_text())['api_key']
nonce=''.join(secrets.choice('23456789ABCDEFGHJKLMNPQRSTUVWXYZ') for _ in range(6))
im=Image.new('RGB',(480,150),'white'); ImageDraw.Draw(im).text((35,35),nonce,font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',60),fill='black')
b=io.BytesIO(); im.save(b,format='PNG')
p={'model':cfg['model_id'],'stream':True,'max_tokens':512,'temperature':0,'messages':[{'role':'user','content':[{'type':'text','text':'Read the six-character code in the image. Return only the code.'},{'type':'image_url','image_url':{'url':'data:image/png;base64,'+base64.b64encode(b.getvalue()).decode()}}]}]}
q=urllib.request.Request(cfg['upstream_base_url']+'/chat/completions',data=json.dumps(p).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+key})
r={'purpose':'vision_stream_admission_not_task','expected':nonce}; answer=''; done=False
try:
 with urllib.request.urlopen(q,timeout=1800) as response:
  r['content_type']=response.headers.get('Content-Type')
  for raw in response:
   line=raw.decode().strip()
   if not line.startswith('data:'): continue
   data=line[5:].strip()
   if data=='[DONE]': done=True; break
   f=json.loads(data)
   if f.get('error'):
    error=json.dumps(f['error']).replace(key,'[REDACTED]'); r['error']=re.sub(r'sk-[A-Za-z0-9_-]+','[REDACTED]',error)[:350]; break
   r['model_reported']=f.get('model') or r.get('model_reported')
   for c in f.get('choices',[]):
    answer+=c.get('delta',{}).get('content') or ''
    if c.get('finish_reason'): r['finish_reason']=c['finish_reason']
 r.update(answer=answer[:100],done=done,passed=done and answer.strip()==nonce)
except Exception as exc: r['error_class']=type(exc).__name__; r['passed']=False
(ROOT/'reports/stream_vision_admission.json').write_text(json.dumps(r,indent=2))
print(json.dumps(r))
