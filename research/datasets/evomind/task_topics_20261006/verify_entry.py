from pathlib import Path
from html.parser import HTMLParser
import json
R=Path(__file__).resolve().parent
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.rows=0
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='tr' and 'data-topic' in a:self.rows+=1
  self.links.extend(v for k,v in attrs if k in ['href','src'])
p=Links();p.feed((R/'private/index.html').read_text(encoding='utf-8'))
assert p.rows==1224
assert all((R/'private'/x).exists() for x in p.links)
assert len(list((R/'private/conversations').glob('*.md')))==1224
v=json.loads((R/'verification.json').read_text(encoding='utf-8'));v['checks'].extend(['检索页1224条记录','全部1226本地文件链接存在','1224会话全文MD存在']);v['verification_notes']='首次内联shell核对因引号解析失败；改为独立Python脚本核对通过。网页未实点击。'
(R/'verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Entry verified:',p.rows,'rows;',len(p.links),'local links; 1224 text views.')
