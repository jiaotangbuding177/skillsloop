import json,re
from pathlib import Path
base=Path(r'D:\skillsgen-industry_track\research\datasets\evomind\analysis_20261005\private')
d=json.loads((base/'local_cluster_evidence.json').read_text(encoding='utf-8'))
lines=['# 14个本地文本簇代表语义审阅','']
for c in d:
    lines += [f"## 簇{c['cluster']}（{c['count']}会话）", '']
    for r in c['representatives']:
        req=r['requests']
        substantive=[];flags=set()
        for t in req:
            if '以下内容来自用户当前选中' in t or '以下内容来自用户当前选择的知识图谱' in t:
                flags.add('知识库/图谱注入');continue
            if t.startswith(('角色名称：','你正在模拟一场','你现在作为数字分身','请从现在开始按以下人格')):
                flags.add('角色/模拟包装');continue
            t=re.sub(r'^\[(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[^\]]+\]\s*','',t)
            t=re.sub(r'^【个人助手设定】.*?请在本轮及后续对话中始终遵循以上设定。\s*','',t,flags=re.S)
            t=re.sub(r'^请使用中文回复，除非用户明确使用其他语言。\s*','',t)
            t=re.sub(r'^请使用技能「[^」]+」协助当前任务。\s*','',t)
            t=re.split(r'All generated deliverable files',t)[0]
            t=re.sub(r'\[附加文件:[^\]]+\]','[附件]',t)
            t=re.sub(r'(?:授权码|AppSecret|api[_ -]?key|apikey)\s*(?:是|为)?[:：]?\s*[^\s，,。;；]+','[凭据已遮蔽]',t,flags=re.I)
            t=re.sub(r'(?<![A-Za-z0-9])[A-Za-z0-9]{16,}(?![A-Za-z0-9])','[长标识已遮蔽]',t)
            if t.strip():substantive.append(t.strip())
        chosen=substantive[:3]
        if len(substantive)>3:chosen += substantive[-1:]
        lines += [f"### {r['session_id']} | {len(req)}条需求 | 标记：{','.join(sorted(flags)) or '无'}",'']
        for i,t in enumerate(chosen,1):lines += [f'{i}. {t[:300].replace(chr(10)," / ")}','']
        if not chosen:lines += ['只有包装输入，不能据此当业务任务。','']
(base/'cluster_semantic_review_excerpt.md').write_text('\n'.join(lines),encoding='utf-8')
print(len(d),sum(len(c['representatives']) for c in d))
