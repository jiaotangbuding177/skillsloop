import sys,runpy,io,contextlib,re
from pathlib import Path
sid=sys.argv[1];start=int(sys.argv[2]) if len(sys.argv)>2 else 0;stop=int(sys.argv[3]) if len(sys.argv)>3 else 10000;limit=int(sys.argv[4]) if len(sys.argv)>4 else 320
root=Path(__file__).resolve().parents[2]
sys.argv=[str(root/'expand_review.py'),sid,'--limit','1']
class Quiet(io.StringIO):
    def reconfigure(self,**kwargs):pass
with contextlib.redirect_stdout(Quiet()):
    d=runpy.run_path(str(root/'expand_review.py'))
sys.stdout.reconfigure(encoding='utf-8')
for i,a in enumerate(d['source'][sid]['assistant_contents'][start:stop],start):
    t=d['redact'](a['content'])
    lines=[x.strip() for x in t.splitlines() if re.search('根因|修复|修改|不对|错误|实际上|公式|错误|必须|先|对齐|验证|校验|缓存|快照|原因|注意',x)]
    print(i,a['group_id'],t[:limit].replace('\n',' '))
    if lines:print('METHOD',(' / '.join(lines))[:limit])
