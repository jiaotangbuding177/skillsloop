"""One-session provenance review: separate retry controls and fold repeated AI for reading."""
from pathlib import Path
from collections import defaultdict,Counter
import json,html,hashlib

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'private'
BASE=ROOT.parent/'full_063/private/evomind_conversations.jsonl'
SID='conv_e09b70c51b19'
RETRY='Continue where you left off. The previous model attempt failed or timed out.'

def fence(t):
    import re
    marker='`'*(max([len(x) for x in re.findall(r'`+',t)]+[3])+1)
    return marker+'text\n'+t+'\n'+marker

def main():
    with BASE.open(encoding='utf-8') as f:
        for line in f:
            s=json.loads(line)
            if s['session_id']==SID:break
        else:raise ValueError('session not found')
    users=[];controls=[];groups={}
    for m in s['messages']:
        if m['role']=='user' and m['content'].strip()==RETRY:
            controls.append(m)
        elif m['role']=='user':users.append(m)
        elif m['role']=='assistant':
            groups.setdefault(m['content'],[]).append(m)
        else:raise ValueError('unexpected role in this reviewed case')
    data={'session_id':SID,'scope':'single_case_content_review_not_recovered_timeline',
          'source_title':s['session_metadata']['title'],
          'title_status':'NO_SUPPORTING_USER_REQUEST_IN_AVAILABLE_MESSAGES',
          'user_requests':users,'retry_control_events':controls,
          'distinct_ai_contents':[{'content':t,'occurrence_count':len(ms),'occurrences':ms} for t,ms in groups.items()],
          'source_order_diagnostics':s['order_diagnostics'],
          'notes':['Retry controls excluded from user task count; not evidence that no request was sent.',
                   'Identical AI bodies folded only for reading, all occurrences and payloads preserved.',
                   'AI contents are not assigned to user requests; original ordering remains unverified.']}
    ids=[m['id'] for m in users+controls]+[m['id'] for ms in groups.values() for m in ms]
    assert Counter(ids)==Counter(m['id'] for m in s['messages'])
    assert len(users)==6 and len(controls)==4 and len(groups)==13 and len(ids)==66
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'case_review.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    heading='会话正文核对：代码分析、资料下载、差旅与作业分析'
    note='此标题依据可见用户输入概括。下面是内容核对视图，不是已恢复的问答时间线；不强行把AI回答配给某次提问。'
    rawtitle='原始标题（保留作元数据；本包未见对应提问）：'+s['session_metadata']['title']
    md=['# '+heading,'',note,'',rawtitle,'',
        '原始66条记录：10条user中分离4条重试控制提示，剩6条用户需求；56条AI记录按完全相同正文折叠为13组，重复出现位置全部保留。','',
        '## 一、可见的6条用户需求（沿原导出顺序列出）','']
    hp=['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>会话内容核对</title><style>body{background:#f3f5f8;color:#243047;font:16px/1.8 system-ui,"Microsoft YaHei",sans-serif}main{max-width:1000px;margin:auto;padding:24px}section,details{padding:18px;background:white;border-radius:10px;margin:16px 0}.note{padding:18px;background:#fff0c8}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:15px/1.8 system-ui,"Microsoft YaHei",sans-serif}.meta{font-size:13px;color:#64748b;overflow-wrap:anywhere}summary{cursor:pointer}h1{font-size:26px}</style><main>',
        '<h1>'+heading+'</h1><p class="note">'+note+'</p><details><summary>原始标题与来源</summary>'+html.escape(rawtitle)+'</details>',
        '<p>66条原记录全部可追溯。4条重试控制提示单列；56条AI记录折叠成13种正文。没有把内容重复等同于底层执行重复。</p><h2>一、可见的6条用户需求</h2>']
    for i,m in enumerate(users,1):
        meta=f'{m["id"]} · 原文件第{m["source_line"]}行 · {m["user_created_at"]}'
        md+=['### 用户需求 '+str(i),meta,fence(m['content']),'']
        hp+=['<section><b>用户需求 '+str(i)+'</b><p class="meta">'+html.escape(meta)+'</p><pre>'+html.escape(m['content'])+'</pre></section>']
    md+=['## 二、13种AI正文（同文折叠，不宣称回复归属）','']
    hp+=['<h2>二、13种AI正文</h2><p>每种正文只展示一次，展开可查看全部原消息位置。不同任务中的同文可能有不同作用，因此原出现记录仍保留。</p>']
    for i,(t,ms) in enumerate(groups.items(),1):
        meta='；'.join(m['id']+'（原第'+str(m['source_line'])+'行）' for m in ms)
        label=f'AI正文 {i} · 出现{len(ms)}次'
        md+=['### '+label,meta,fence(t),'']
        hp+=['<section><b>'+label+'</b><details><summary>查看全部出现位置</summary><p class="meta">'+html.escape(meta)+'</p></details><pre>'+html.escape(t)+'</pre></section>']
    md+=['## 三、4条重试控制提示（不计用户需求）',fence(RETRY),'']
    hp+=['<details><summary>三、4条重试控制提示（不计用户需求）</summary><pre>'+html.escape(RETRY)+'</pre>']
    for m in controls:
        meta=m['id']+' · 原角色user · 原状态'+m['status']+' · 第'+str(m['source_line'])+'行'
        md+=[meta];hp+=['<p class="meta">'+html.escape(meta)+'</p>']
    hp+=['</details></main></html>']
    (OUT/'case_review.md').write_text('\n\n'.join(md)+'\n',encoding='utf-8')
    (OUT/'case_review.html').write_text('\n'.join(hp),encoding='utf-8')
    summary={'original_records':66,'original_user_records':10,'retry_controls':4,'visible_user_requests':6,
             'original_ai_records':56,'distinct_ai_bodies':13,'folded_repeat_occurrences':43,
             'specified_ai_body_occurrences':len(groups['从截图中我看到了仓库信息。让我通过 API 获取更详细的代码提交情况：']),
             'all_66_record_ids_accounted_for':True,'all_original_occurrences_preserved':True,
             'reply_links_inferred':False,'complete_chronology_verified':False,'llm_calls':0}
    (ROOT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
