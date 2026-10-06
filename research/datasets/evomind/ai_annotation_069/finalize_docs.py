"""Write delivery notes from measured annotation counters; no model calls."""
from pathlib import Path
import json
R=Path(__file__).resolve().parent;research=R.parents[2]
s=json.loads((R/'summary.json').read_text(encoding='utf-8'))
text=f'''# 069 按人工样例完成AI辅助标注

[打开标注页：默认只看剩余项](private/index.html)

你提供的28项人工选择已原样装入新页面，不需要重新导入。原来505条会话中有2,674项需要判断，现在{ s['sessions_resolved'] }条会话已有明确判断，**还剩{s['sessions_needing_human']}条会话、{s['remaining_human_items']}项需要你决定**。

| 口径 | 数量 |
|---|---:|
| 纳入本轮的会话 | 505 |
| 用户原人工标注 | 28（21匹配、7无匹配） |
| 最终匹配项，含原人工选择 | {s['matched']} |
| 最终无匹配项，含原人工选择 | {s['none']} |
| 仍无法判断 | {s['uncertain']} |

“项”是一个用户输入或一个AI回复正文组，不等于一条会话，也不等于独立问答数量。一问多答只选不同的正文组，原始重复出现记录仍可回查。语义相近但要求不同，不能只因话题相同就配对。

## 怎么继续

1. 打开新页面，默认只列仍需你判断的会话和具体项。
2. 对照用户正文与候选回复，可单选、多选、选无匹配或无法判断，然后确认。
3. 想检查AI结果，切换会话筛选及“查看原待核验项全部判断”。AI结果可以修改；确认后记录为你的人工判断。
4. 离开前点“导出标注备份”。浏览器暂存不能替代备份。后续可导入该备份继续，新页面使用独立暂存空间，不覆盖068页面。

## 本次具体做了什么

先阅读10条会话中的28项人工样例，采用“是否直接回应当前需求”的尺度：澄清、过程说明、失败回复、部分完成也可以匹配，不能把匹配误解成任务成功。

复用601项旧模型已经给出语义匹配、但被严格引文校验退回的判断；21项当前会话没有另一侧正文，记为当前材料范围内无匹配。剩余2,024项用真实模型分112批判断。随后复核345项可能存在动作错配的结果，并逐项盲审55项短请求多选结果；两类复核清单不重叠，共400项。短请求复核54项取得可用结果，1项两次输出均无法解析为单一JSON，保留原响应并转入无法判断，没有强行沿用旧预测。

抽查确实发现错误，且批量复核仍可能重复原错配。一例通过直接阅读全文改到真正回答当前动作的回复；另一例短请求可能指正文也可能指文件位置，保留无法判断。两项修正明确记为AI助理来源，没有伪装成人工标注。反向匹配冲突先尊重用户原选择，其余无法协调的留人工。

没有重新生成任何企业对话正文，也未把这些标注作为独立测试真值。原1466条会话主集不变，本页面只处理此前的505条待核验会话；其余961条本轮未复核。

## 执行证据与限制

- 实际调用{s['api_attempts']}次；失败尝试{s['failed_attempts']}次。服务返回输入用量{s['reported_input_tokens']:,}、输出{s['reported_output_tokens']:,} tokens；实际金额未知。调用上限224，未触及上限。
- 原28人工标签、原505会话正文、2674项覆盖、目标编号与去重、双向一致性、导入导出及页面脚本检查见[verification.json](verification.json)。这些检查不代表语义准确率。
- 浏览器工具此前拒绝file页面访问，因此实际浏览器视觉、点击和下载没有重新验收；本轮只完成纯数据、状态和脚本检查，没有绕过限制。
- 用户样例参与标注标准与提示，不是独立测试集；本轮没有独立准确率。剩余量减少仅表示AI接管初标，不等于错误率下降或全部正确。

## 文件与复查

- [最终完整标注JSON](private/ai_assisted_annotations.json)：包含来源，可回查或导入。
- [剩余人工项](private/remaining_human_review.json)、[统计](summary.json)、[文件校验](manifest.json)。
- private中的初标／复核请求、响应、账本、原人工备份及修正日志保留；full text仅在private，普通研究记录不复制敏感正文。
- 从保存响应重新生成页面：`python research/datasets/evomind/ai_annotation_069/publish_annotations.py`；纯检查：`node research/datasets/evomind/ai_annotation_069/verify_delivery.cjs`。两者不发模型请求。
'''
(R/'README.md').write_text(text,encoding='utf-8')
memory=research/'memory/069_2026-09-28_example_guided_ai_annotation.md'
with memory.open('a',encoding='utf-8') as f:
 f.write(f'''\n## 完成交付与更正\n\n112批初标、37批定向复核均完成；55项短请求逐项盲审中54项完成、1项两次结构失败后留无法判断。复核清单共400项，最终原505会话／2674项中，匹配{s['matched']}、无匹配{s['none']}、不确定{s['uncertain']}；{s['sessions_resolved']}会话已有明确判断，剩{s['sessions_needing_human']}会话／{s['remaining_human_items']}项交人工。原28项人工选择逐项完全一致，源正文与066／068未变。\n\n先前阶段性54会话／172项不是最终数字，由本节及summary.json替代。直接原文抽查证实批量复核也可能重复错误，非发布映射失败：一例请求分析却匹配计划，改成对应分析回复；一例短请求含糊，标无法判断。完整证据在private/assistant_review_overrides.json，仍为AI来源。55项短请求多选此前因长度门槛漏入复核，追加单问题盲审，不把筛选器当正确性保证。\n\n实际{s['api_attempts']}次调用，失败{s['failed_attempts']}，已报告输入{s['reported_input_tokens']:,}、输出{s['reported_output_tokens']:,} tokens，金额未知。源28人工保持、覆盖、编号、双向约束、导入导出与脚本检查通过；真实浏览器点击未验收，沿用file限制不绕过。UI默认剩余队列，全部AI结果仍可查看修改并导出。\n\n[交付说明](../datasets/evomind/ai_annotation_069/README.md)。此为研究数据准备，不是独立算法效果实验；AI与人工标签分开，准确率仍未知。下一步由用户处理剩余项并导出备份；如用于论文恢复指标，还须独立参考及抽查。\n''')
