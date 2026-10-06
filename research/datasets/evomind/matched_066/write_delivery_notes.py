"""Create human-readable delivery notes from completed counters, without model calls."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent

def main():
    s = json.loads((ROOT / 'summary.json').read_text(encoding='utf-8'))
    verification = json.loads((ROOT / 'independent_delivery_verification.json').read_text(encoding='utf-8'))
    assert verification['status'] == 'PASS'
    review_count = len(json.loads((ROOT / 'private/association_review_queue.json').read_text(encoding='utf-8')))
    jobs = json.loads((ROOT / 'private/prepared_jobs.json').read_text(encoding='utf-8'))
    truncated_users = len({(j['session_id'], u['u']) for j in jobs for u in j['payload']['users'] if u['truncated']})
    text = f'''# EvoMind：去重与逐输入回复匹配版

本版覆盖全部 **{s['sessions']:,}条真实用户会话**。按你的要求，先移走重试提示、空AI，再折叠重复正文；阅读时以每组不重复用户输入为中心，展示对应的一条或多条AI回复。

[打开全部会话目录](private/index.html) · [查看你指出的案例](private/conversations/conv_e09b70c51b19.html) · [该案例Markdown](private/conversations/conv_e09b70c51b19.md)

## 本次实际清理了多少

| 项目 | 数量与处理 |
|---|---:|
| 用户会话 | {s['sessions']:,}条，全部保留 |
| 原记录 | {s['original_record_count']:,}条，均可回查 |
| 重试控制提示 | {s['removed_retry_controls']:,}条，从有效问答移走 |
| 空AI正文 | {s['removed_empty_ai']:,}条，从阅读主线移走 |
| 重复用户正文 | 折叠{s['folded_user_occurrences']:,}次重复出现 |
| 重复AI正文 | 折叠{s['folded_ai_occurrences']:,}次重复出现 |
| 去重后的用户正文 | {s['user_groups']:,}组 |
| 去重后的AI正文 | {s['ai_groups']:,}组 |

这里只合并同会话内完全相同的正文，用户输入还要求已导出的附件信息相同。修改条件、不同金额、用户批评和AI承认失败都保留。相同短句可能在不同阶段发生，因此正文组数不能当作任务数或真实回合数。全部原始出现记录在结构化数据中保留。

## 怎么给用户输入找回复

1. 原文件位置与消息编号先提供候选位置；重试提示不再打断回复段。
2. 对顺序有歧义的会话，比较同一会话里的用户要求、回复内容及位置支持，不能只把相邻消息机械拼成问答。
3. 对仍无法挂接的部分调用真实模型逐条判断，并要求引用原文。不存在的编号不能通过；引文不一致的那条留待核验。
4. 同一要求可以挂多条AI过程说明、失败说明和最终回答。没有足够依据的回复单独放在页面末尾。

| 回复对应结果 | 数量 |
|---|---:|
| 已有对应用户输入候选的AI正文 | {s['assigned_ai_groups']:,}组 |
| 仍未确定归属的AI正文 | {s['unassigned_ai_groups']:,}组 |
| 含未归属AI的会话 | {s['sessions_with_unassigned_ai']:,}条 |
| 暂未挂接AI的用户正文 | {s['user_groups_without_ai']:,}组 |
| 原来136条顺序冲突会话中，全部AI都有对应候选 | {s['original_conflict_sessions_all_ai_have_candidates']:,}条 |
| 原来136条顺序冲突会话中，仍有AI未归属 | {s['original_conflict_sessions_with_unassigned_ai']:,}条 |

“有对应候选”不是“已证明正确”，“暂未挂接AI”也不证明原系统没回复。原始136条顺序冲突标记保留，本版改善阅读与可核对的回复归属，没有把缺少可靠事件时间的问题伪装成彻底解决。页面会区分原位置候选、词面与位置候选、模型匹配和本轮案例校对。

综合核验清单共{review_count}条会话：它同时收录“AI未归属”和“用户输入暂无AI”两种情况，不能把它与上表{s['sessions_with_unassigned_ai']}条“含未归属AI的会话”混用。后一种用户暂无AI可能涉及空回复已清理、历史缺失或当前匹配不足，不直接判定源系统回复失败。

## 你指定的案例如何变化

`conv_e09b70c51b19`原66条记录中，4条重试提示已移出问答；56条AI折叠成13种正文，重复43次不再刷屏。6条真实用户输入全部保留，围绕它们挂接11组AI正文。

例如代码分析要求下放代码分析的过程说明和结果；追问是否读取资料下放AI承认没有读取PDF的回答。这些失败承认对后续轨迹恢复有价值，不能作为重试垃圾删掉。

还剩2组没有硬配：一组相同OCR说明出现在两次相似要求附近，无法确定具体归属；另一组总结提到历史任务，但当前导出缺少对应用户提问。原始标题只作元数据展示，不用标题补造问题。

## 文件与后续使用

- [按会话编号为键的完整JSON](private/evomind_conversations.json)：正文、候选对应、重复出现位置和隔离记录都在。
- [逐会话JSONL](private/evomind_conversations.jsonl)：便于按会话读取。
- [剩余核验会话清单](private/association_review_queue.json)：包含未归属AI、用户暂无对应AI或批次未完成的会话。
- [方法与限制](METHOD.md)、[统计](summary.json)、[独立来源核对结果](independent_delivery_verification.json)、[输出哈希清单](delivery_manifest.json)。

另保留19条内部用途会话、39条仅元数据会话，不混入1,466条用户会话正文主集。063原版及064、065历史产物保留。

后续任务识别可以消费这里的问答候选，但不能把这些推断直接作为评价任务识别或轨迹恢复准确率的标准答案。没有对应AI的用户输入与未归属AI也应保留，避免只选完整会话。

## 本轮模型运行与边界

语义续接计划290批，已取得有效结构结果{s['model_jobs_validated']}批，未完成{s['model_jobs_incomplete']}批；针对169会话中的5,968组疑难AI正文。有效结构结果仍可能返回“无法确定”。长正文存在截断、长会话存在候选召回范围限制，标记保留在数据中。

本次实际有{truncated_users}组用户输入在模型请求中截断；AI正文截断{s['model_items_with_truncated_ai_input']}组，{s['model_items_with_incomplete_user_candidate_set']}组AI的候选没有覆盖该会话全部用户输入。{s['model_items_with_failed_quote_validation']}项引文未通过逐字核验并留待复核，{s['model_items_without_written_reason']}项未提供文字理由。两批结构异常通过删除完全相同的重复返回项、拒绝本批不存在的编号后离线恢复，未新增调用，也未改写合法编号的原判断；见方法说明。

请求账本记录{s['api_requests_documented_including_probes']}次调用（含2个小探针），初始中断另有至多4次在途调用未完整登记。服务已返回的输入用量合计{s['reported_input_tokens_including_probes']:,} tokens，输出{s['reported_output_tokens_including_probes']:,} tokens；未返回用量的超时或中断不在此数中，金额未知。此次运行经历过超时、限流和引文校验粒度调整，失败与旧配置全部保留，不能称为冻结配置首次完整成功。

全量核对通过：所有原记录逐条一致、会话集合不变、去重分组与隔离记录完整覆盖、对应目标有效、选中的模型引文经过程序核验、页面与结构化文件齐全。没有测得独立语义准确率，也没有开展技能生成效果实验。
'''
    (ROOT / 'README.md').write_text(text, encoding='utf-8')
    research = ROOT.parents[2]
    report = f'''# 066 全量会话去重与回复归属整理

本轮按用户要求，将“先清理重复与重试，再围绕每个用户输入寻找一个或多个AI回复”应用到全部1,466条主集会话。没有修改Demo或进行skills生成。

[完整交付说明](../datasets/evomind/matched_066/README.md) · [全部会话目录](../datasets/evomind/matched_066/private/index.html) · [指定案例](../datasets/evomind/matched_066/private/conversations/conv_e09b70c51b19.html)

清理137条重试控制、11,775条空AI正文；折叠480次相同用户正文、5,878次相同AI正文。全部46,224条原记录保留来源，形成8,202组用户正文和19,734组AI正文，组数不等于任务数。

匹配采用原位置／数字编号弱线索、会话内内容比较以及真实模型疑难续接。最终{s['assigned_ai_groups']:,}组AI有对应候选，{s['unassigned_ai_groups']:,}组仍未归属，分布于{s['sessions_with_unassigned_ai']:,}条会话；原136条歧义会话中{s['original_conflict_sessions_all_ai_have_candidates']}条全部AI有候选，{s['original_conflict_sessions_with_unassigned_ai']}条仍有未归属AI。所有对应关系都是可核对的推断，不能把挂接数报告成恢复正确数。

指定案例56条AI折叠为13组、4条重试控制隔离；6组用户输入挂接11组AI，另2组保留未归属。缺失提问不会用标题补造，失败承认和真实修订反馈保留。

源记录一致性和交付完整性核对通过；独立语义准确率、真实时间线以及skills收益均未验证。模型批次{s['model_jobs_validated']}/290取得结构有效结果，{s['model_jobs_incomplete']}批未完成。运行包含中断、超时与限流等失败历史，成本不能只算成功响应；具体账本与限制见交付说明及本轮记忆。
'''
    (research / 'reports/066_dedup_and_reply_alignment.md').write_text(report, encoding='utf-8')

if __name__ == '__main__':
    main()
