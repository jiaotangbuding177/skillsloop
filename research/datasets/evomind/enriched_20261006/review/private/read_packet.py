import sys,json,runpy,io,contextlib,re
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
R=Path(__file__).resolve().parent
data_root=R.parents[2]
selection=json.loads((R/'selection.json').read_text(encoding='utf-8'))['sessions']
start,stop=int(sys.argv[1]),int(sys.argv[2])
class Quiet(io.StringIO):
    def reconfigure(self,**kwargs):pass
old_argv=sys.argv[:]
sys.argv=['expand_review.py',selection[0]['session_id'],'--limit','1']
with contextlib.redirect_stdout(Quiet()):d=runpy.run_path(str(data_root/'screening_20261006/expand_review.py'))
sys.argv=old_argv
src=d['source'];redact=d['redact']
ranges_path=R/'read_ranges.json'
ranges=json.loads(ranges_path.read_text(encoding='utf-8')) if ranges_path.exists() else {}
cue=re.compile('原因|根因|错误|报错|失败|修正|修复|改用|改为|改成|检查|核对|核查|不兼容|区分|矛盾|误|冲突|不匹配|重新|实际|发现|不得|不能|边界|限制|渲染|验证|保留|映射|重复|因此|所以|步骤|先.*再')
for item in selection[start-1:stop]:
 sid=item['session_id'];s=src[sid]
 print('\n###',item['rank'],sid,item['title'],'OLD',item['old_reason'])
 saved=[]
 for role,key,prefix in [('user','user_requests','u'),('assistant','assistant_contents','a')]:
  for i,x in enumerate(s[key]):
   t=x['content'];head=min(len(t),260 if role=='user' else 190)
   print(prefix+str(i),x['group_id'],'LEN',len(t),redact(t[:head]).replace('\n',' '))
   parts=[dict(start=0,end=head,kind='head')]
   n=0
   for m in re.finditer(r'[^\n]+',t):
    line=m.group(0)
    if m.end()<=head or not cue.search(line):continue
    if n >= (2 if role=='user' else 4):break
    a=m.start();b=min(m.end(),a+210)
    print(' CUE',redact(t[a:b]).replace('\n',' '));parts.append(dict(start=a,end=b,kind='cue_line'));n+=1
   saved.append(dict(role=role,group_id=x['group_id'],source_index=i,content_chars=len(t),ranges=parts,full_text_read=head==len(t)))
 ranges[sid]=saved
ranges_path.write_text(json.dumps(ranges,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
