import json,re,sys,io,runpy,contextlib
from pathlib import Path
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')
R=Path(__file__).resolve().parent
base=R.parents[2]
assigned=json.loads((R/'assigned_ids.json').read_text(encoding='utf-8'))
source=json.loads((base/'matched_066/private/evomind_conversations.json').read_text(encoding='utf-8'))
cards={x['session_id']:x for x in json.loads((R.parent/'all_cards.json').read_text(encoding='utf-8'))}
rows=json.loads((R/'review_labels.json').read_text(encoding='utf-8'))
partial='--partial' in sys.argv
if not partial:
    for name,expected in [('tail17_19_review_labels.json',75),('root_tail_labels.json',13)]:
        add=json.loads((R/name).read_text(encoding='utf-8'))
        assert len(add)==expected,(name,len(add))
        rows += [x for x in add if x['session_id'] not in {r['session_id'] for r in rows}]
by={x['session_id']:x for x in rows}
assert len(by)==len(rows)
if not partial:
    assert len(rows)==488
    assert set(by)==set(assigned)
rows=[by[sid] for sid in assigned if sid in by]
old_args=sys.argv[:]
sys.argv=['expand_review.py','conv_602668379442','--limit','1']
class Quiet(io.StringIO):
    def reconfigure(self,**kwargs): pass
with contextlib.redirect_stdout(Quiet()):
    d=runpy.run_path(str(R.parents[1]/'expand_review.py'))
sys.argv=old_args
redact=d['redact']
extended=0
for row in rows:
    sid=row['session_id']
    raw={x['group_id']:x['content'] for x in source[sid]['user_requests']+source[sid]['assistant_contents']}
    for c in row['candidates']:
        quote=c['evidence_quote']
        if len(quote)<14:
            texts=[raw[x] for x in c['assistant_ids']+c['user_ids'] if quote in raw[x]]
            if not texts: continue
            t=texts[0]; idx=t.index(quote)
            start=max(t.rfind('\n',0,idx)+1,idx-42)
            if start>0:
                marks=[m.end() for m in re.finditer(r'[。！？；，]',t[start:idx])]
                if marks: start += marks[-1]
            stop=t.find('\n',idx+len(quote));stop=len(t) if stop<0 else stop
            stop=min(stop,idx+len(quote)+74)
            marks=list(re.finditer(r'[。！？；]',t[idx+len(quote):stop]))
            if marks: stop=idx+len(quote)+marks[0].end()
            new=t[start:stop].strip()
            if len(new)>len(quote) and redact(new)==new:
                c['evidence_quote']=new;extended+=1
    if sid in ['conv_7f5a1845d742','conv_c53070032f4c','conv_e27d804e80f0','conv_ac00eb28fce5','conv_9a05b37ae6e2','conv_8685cb6739a8','conv_81cbeb7e8662']:
        for c in row['candidates']: c['limitations'].append('项目日期及输入材料真实性未独立认证')

def candidate(sid,task,lesson,quote,uis,aids,limitations=[]):
    if any(c['task']==task for c in by[sid]['candidates']): return
    c=dict(task=task,lesson=lesson,evidence_quote=quote,user_ids=[cards[sid]['users'][i]['id'] for i in uis],assistant_ids=aids,
        limitations=['历史执行顺序未核准','任务成功及新任务复用收益未独立验证']+limitations)
    raw={x['group_id']:x['content'] for x in source[sid]['user_requests']+source[sid]['assistant_contents']}
    assert all(x in raw for x in c['user_ids']+aids)
    assert any(quote in raw[x] for x in c['user_ids']+aids)
    by[sid]['candidates'].append(c)
candidate('conv_5257d244a423','修复投研PDF分页与跨页表格',
    '逐页核正文空白比例并排除页眉页脚干扰；封面尺寸须适应打印内容区，表格用thead保证跨页重复，章节和大块元素整体推移时恢复流式分页，最后核章节顺序、字符和表头。',
    '每章强制分页反而制造了更多尾巴页', [3,4,5], ['a_5ddd36bb628cd27da5','a_244a11dc02b91f7a1c','a_1b7a8c011f43bfd432'])
candidate('conv_6205973ae0f0','修复中文合同审阅PDF乱码',
    '用文本提取和渲染OCR两层区分真实字形乱码与文本编码；字体拆分仍失效时改Chromium打印，并用CDP设置A4和页码，最后再核文本、页面尺寸和渲染，不能只改字体文件就宣称成功。',
    '说明是weasyprint对CJK的编码问题而非字体问题',[1,3], ['a_d78729747c58abb7f1','a_d333791c688e2dad54','a_344353b6af5912627f'])
candidate('conv_2b5c66ef9795','缺依赖环境调用图像接口',
    '请求库缺失时用标准库urllib完成HTTP请求、base64处理接口返回，并将结果直接写用户可见成果目录；不额外转码，验文件存在、大小与格式，接口处理和交付路径都要核。',
    'requests 没装，我用 Python 标准库（urllib + base64）直接调',[2,3],['a_a814f035884e150f4b','a_726030c2536811c93a','a_e921a1da556dbe5171'])
errors=[]
for row in rows:
    raw={x['group_id']:x['content'] for x in source[row['session_id']]['user_requests']+source[row['session_id']]['assistant_contents']}
    if row['decision']=='KEEP': assert row['candidates']
    for c in row['candidates']:
        assert c['user_ids'] and c['assistant_ids']
        assert all(x in raw for x in c['user_ids']+c['assistant_ids'])
        assert any(c['evidence_quote'] in raw[x] for x in c['user_ids']+c['assistant_ids']),(row['session_id'],c['task'],len(c['evidence_quote']))
(R/'review_labels.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('complete',len(rows),'decisions',dict(Counter(x['decision'] for x in rows)))
print('basis',dict(Counter(x['review_basis'] for x in rows)),'candidates',sum(len(x['candidates']) for x in rows),'quotes_extended',extended)
