import json, re, hashlib
from pathlib import Path

ROOT = Path(r'D:\skillsgen-industry_track\research\datasets\evomind\matched_066\private\conversations')
OUT = Path(__file__).parent / 'taxonomy_review_samples.md'
THEMES = {
    '合同与法律': r'合同|协议|条款|律师|法律|签署|股权转让',
    '投资与经营分析': r'尽调|融资|基金|股权|估值|投资|市场|商业模式|行业|背调',
    '报告与申报': r'申报|申请书|公文|汇报|报告|简报|推荐函|评价|总结',
    '招聘与组织': r'简历|面试|招聘|岗位|职级|定薪|候选人|绩效|薪酬',
    'PPT与可视化': r'PPT|ppt|路演|演示|幻灯片|海报|图片|绘图|logo|图表',
    '会议与协作': r'纪要|会议|录音|转写|待办|日程|行动项|通知|催收',
    '数据与文档': r'表格|Excel|excel|PDF|pdf|word|Word|docx|提取|解析|统计',
    '招投标与项目': r'投标|招标|评分规则|规格书|WBS|里程碑|研发任务|齐套|项目启动',
    '软件与代码': r'代码|API|api|网页|网站|部署|仓库|git|python|程序|bug|Bug',
    '系统与技能': r'技能|skill|模型|配置|安装|定时|创建智能体|记忆|cron|agent',
    '个人生活与知识': r'旅游|酒店|餐厅|天气|高考|孩子|减肥|足球|旅行|景点|西双版纳|日本游|取名',
    '上下文继续与不明确': r'^.{0,20}(继续|好的|行|可以|确认|开始|你好|再来|谢谢|试试|给我|什么)(.{0,25})$',
}

def clean(text):
    text=re.sub(r'^\[(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[^\]]+\]\s*', '', text)
    text=re.sub(r'^【个人助手设定】.*?请在本轮及后续对话中始终遵循以上设定。\s*', '', text, flags=re.S)
    text=re.sub(r'^请使用中文回复，除非用户明确使用其他语言。\s*', '', text)
    text=re.sub(r'^请使用技能「[^」]+」协助当前任务。\s*', '', text)
    text=re.sub(r'<[^>]+>', '', text)
    return text.strip()

records=[]
for p in sorted(ROOT.glob('*.json')):
    d=json.loads(p.read_text(encoding='utf-8'))
    for u in d.get('user_requests', []):
        txt=clean(u.get('content', ''))
        if not txt: continue
        if txt.startswith(('你现在是一个专属智能体', 'Continue where you left off.', '[PromptGuard', '用户画像：','角色名称：','你正在模拟一场','请从现在开始按以下人格','你现在作为数字分身')): continue
        if '以下内容来自用户当前选中' in txt or '以下内容来自用户当前选择的知识图谱' in txt: continue
        records.append((d['session_id'], u['group_id'], txt))

lines=['# 本地任务类别语义抽样（非全量真值）', '',
       '输入：066去重会话的用户正文。忽略原会话标题；剥离固定语言/技能包装，代表请求保留附件标记。', '',
       f'可抽样用户需求 {len(records)} 条。以下每个主题选5条不同会话，按SHA稳定选择；主题仅用于分散抽样，不是最终标签。', '']
used=set()
for theme, pattern in THEMES.items():
    rx=re.compile(pattern)
    candidates=[r for r in records if rx.search(r[2]) and r[0] not in used]
    candidates.sort(key=lambda r:hashlib.sha256((theme+r[0]+r[1]).encode()).hexdigest())
    selected=[]
    for r in candidates:
        if r[0] in used: continue
        selected.append(r); used.add(r[0])
        if len(selected)==5: break
    lines.extend([f'## {theme}', ''])
    for sid, uid, txt in selected:
        lines.extend([f'### {sid} / {uid}', '', txt[:850].replace('\n\n\n','\n\n'), ''])
OUT.write_text('\n'.join(lines), encoding='utf-8')
print(json.dumps({'sample_conversations':len(used),'requests_available':len(records),'output':str(OUT)},ensure_ascii=False))
