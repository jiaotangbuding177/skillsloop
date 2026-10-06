"""Render the private acceptance snapshot for source-by-source inspection."""
import json
from pathlib import Path
import sys

root=Path(sys.argv[1]).resolve()
data=json.loads((root/'private-snapshots.json').read_text(encoding='utf-8'))
out=['# 047 前三阶段真实案例逐项查看（受控材料）','','本文包含企业原始用户正文，仅保存在案例 private 目录。不会随组织技能提审共享。',
     '', '输入：038/private/raw_messages.jsonl 的70条原事件＋source_index.json 的源行序与可用时间。没有人工任务轨迹或 replyTo 输入。',
     '', 'sourceMessageIds 表示问答上下文来源；任务自己的交付以 observations 的引用区间为准。']
for label,state in data.items():
    out.extend(['',f'## {label}：'+('真实企业会话' if label=='real' else '独立构造控制，不代表企业实证')])
    for status in state['stageStatus']:
        session=status['session'];out.extend(['',f'### 会话 `{session}`','',f"阶段状态：{status['stage1']} → {status['stage2']} → {status['stage3']}"])
        pairs=sorted((p for p in state['pairs'] if p['session']==session),key=lambda p:p['sourceOrder'])
        for i,p in enumerate(pairs,1):
            out.extend(['',f'#### 问答 {i}：阶段1输出／阶段2输入', '',f"- 问答ID：`{p['id']}`；用户原ID：`{p['sourceUserMessageId']}`",f"- 助手消息数：{len(p['assistantSegments'])}；正文状态：{p['contentStatus']}；用途：{p['purposeSplit']}",'','用户原文：','',p['user'],'','阶段2候选标注：'])
            for a in state['pairAnnotations']:
                if a['pairId']==p['id']:
                    for f in a['fragments']:out.append(f"- `{f['kind']}` · {f['intent']} · 候选 `{f['taskId']}`；目标片段 `{f['id']}`")
            out.extend(['','助手原消息ID：', '', ', '.join('`'+s['sourceId']+'`' for s in p['assistantSegments'])])
        for t in state['traces']:
            if t['session']!=session or t['state']=='SUPERSEDED':continue
            out.extend(['',f"#### 阶段3任务输出：{t['goal']}",'',f"任务ID：`{t['id']}`；{len(t['members'])} 个成员片段／{len(t['attempts'])} 次回合尝试。业务结果 `{t['businessOutcome']}`。",'', '**要求时间线**'])
            for v in t['requirementTimeline']:out.append(f"- v{v['version']} · `{v['scope']}` · {v.get('requestedText',v.get('delta',''))}")
            out.extend(['','**反馈与修订关系**'])
            for e in t['feedbackEdges']:out.append(f"- `{e['kind']}` · {e['explanation']}（{e['sourcePairId']} → {e['targetPairId']}）")
            out.extend(['','**实际可见文本与助手声称分列**'])
            for o in t['observations']:
                r=o['evidenceRef'];out.extend([f"- `{o['kind']}`／`{o['status']}` · {o['description']}",f"  - 原文：{r['quote']}",f"  - 来源：`{r['pairId']}` · `{r.get('sourceId','pair-level')}` · offset {r['viewOffset']} · `{r['precision']}`"])
            out.extend(['','**未决与产物**',f"- 缺失输入元数据：{len(t['artifactAvailability']['missingInputs'])}；可核验交付文件：{len(t['artifactAvailability']['verifiedFiles'])}。",f"- 后续交接：`{t['learningHandoff']}`。"])
            out.extend('- '+u['reason'] for u in t['unresolved'])
path=root/'047_case_walkthrough.md';path.write_text('\n'.join(out)+'\n',encoding='utf-8')
print(str(path))
