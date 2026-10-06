"""Free, source-preserving preparation of the current enterprise topic corpus.

This is an input/eligibility adapter, not Trace2Skill or an UNKNOWN analyzer.
It never imports a model client, executes source commands, or changes source data.
Existing task labels only propose outer experiment groups. Qualification remains
separate from source metadata, visible-condition checks, and business acceptance.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "research/datasets/evomind/task_topics_20261006"
OUT = Path(__file__).resolve().parent
PRIVATE = OUT / "private/enterprise"

# Frozen, inspectable label rules. These are proposals, not learned clusters,
# gold labels, skill counts, or permission to run a baseline on every match.
FAMILIES = [
    ("LEGAL", "contract_revision", "合同立场与条款修订", r"合同|协议|条款|委托", "conv_23bffc5f1e1b:learn01"),
    ("LEGAL", "corporate_filing", "股东与工商材料填报", r"股东|股权|工商|名册|登记", "conv_956c87eca622:learn01"),
    ("HR", "performance_policy", "绩效与评价方案修订", r"绩效|评价|考核|薪酬|工资", "conv_245a7b03a18b:learn01"),
    ("HR", "candidate_comparison", "简历提取与候选人比较", r"简历|候选|招聘|人才|面试", "conv_e17409b249a6:learn01"),
    ("OFFICE", "text_revision", "文字材料改写与压缩", r"文章|文风|文字|文案|压缩|精简|发言|祝福|改写|总结", "conv_bcae4fd64969:learn01"),
    ("OFFICE", "document_page_delivery", "文档页面制作与格式交付", r"页面|PDF|PPT|Word|文档|水印|排版|格式", "conv_61034c4c6675:learn01"),
    ("DATA", "accounting_budget", "财务核算与预算测算", r"财务|会计|预算|成本|费用|估值|凭证|核算|发票", "conv_80e86b5805f5:learn01"),
    ("DATA", "table_transform", "数据表去重合并与差异处理", r"去重|合并|比较|对比|脱敏|汇总|表格|表", "conv_ee979d0d59fb:learn01"),
    ("BIZ", "opportunity_screening", "申报机会与市场策略筛选", r"申报|机会|筛选|市场|代理|调研|渠道", "conv_c952411dbdfe:learn01"),
    ("BIZ", "investment_assessment", "投资与项目价值判断", r"投资|项目|价值|尽调|决策|估值", "conv_7c90fd36e5bf:learn01"),
    ("EDU", "teaching_material", "互动教学与课程材料制作", r"教学|课程|互动|五线谱|课堂|教材", "conv_71629b81db24:learn01"),
    ("EDU", "education_analysis", "教育问卷与教学评价分析", r"问卷|素养|评价|分析|评估", "conv_e1394bb92ca8:learn01"),
    ("TECH", "browser_interaction", "浏览器与交互页面验证", r"浏览器|交互|网页|页面|HTML|游戏|导航", "conv_9f975ffa392f:supp01"),
    ("TECH", "runtime_compatibility", "解释器依赖与运行兼容排障", r"Python|依赖|语法|编译|解释器|环境|兼容|安装", "conv_567a2331adcf:learn01"),
    ("NEWS", "market_date_check", "市场信息日期与时效核验", r"市场|日期|盘中|时效|行情", "conv_9bfd4928da60:learn01"),
    ("NEWS", "rumor_verification", "事件传闻与权威来源核查", r"传闻|事故|权威|核查|事件", "conv_fa8adda38d0c:learn01"),
    ("ASSIST", "skill_registration", "技能注册与调用定位", r"注册|水印|调用|定位|技能", "conv_f34d1eb4b810:learn01"),
    ("ASSIST", "skill_installation", "第三方技能安装与完整性检查", r"安装|第三方|完整性|更新|修复", "conv_5d1d5410135d:learn01"),
    ("KNOW", "knowledge_import", "知识库笔记导入", r"导入|笔记|IMA|知识库|同步", "conv_24bc635473a8:learn01"),
    ("KNOW", "index_consistency", "目录与索引一致性维护", r"目录|索引|Wiki|一致性|链接", "conv_83820ac2bbbe:learn01"),
    ("COMM", "meeting_reminder", "会议提醒与日程设置", r"会议|提醒|日程|通知|定时", "conv_3475f26df3d6:learn01"),
    ("COMM", "message_recipient", "消息收件人与发送边界确认", r"邮件|邮箱|收件人|发送|地址", "conv_2c2d2c4d0df1:learn01"),
    ("LIFE", "travel_planning", "出行与行程规划", r"行程|出行|旅游|自驾|旅行", "conv_d3b35bbaf6ed:learn01"),
    ("LIFE", "personal_communication", "个人与合伙人沟通修订", r"沟通|合伙|关系|脚本|修订", "conv_23a12ab71383:learn01"),
]

# These source-linked probes deliberately do not certify the complete candidate.
# No business truth is supplied for missing files or professional assertions.
PROBES = [
    {"probe_id": "salary_monthly_conversion", "candidate_id": "conv_bcf6044319f6:learn01",
     "user_id": "u_1827670ad949f9bf25", "assistant_id": "a_19c98d4fafef8b83f8",
     "scope": "每人年工资20万元折算每人月工资；排除团队/地区/现金/文件更新断言",
     "checker": "annual_to_monthly", "family_id": "DATA:annual_to_monthly",
     "coverage": "COMPLETE_EXPLICIT_LOCAL_SUBREQUEST_ONLY"},
    {"probe_id": "visible_one_paragraph", "candidate_id": "conv_41874c950938:learn01",
     "user_id": "u_5592d075b840be7936", "assistant_id": "a_fd5e45c7f61b41d72a",
     "scope": "完整回复中展示的引用段落是否只有一段；不判压缩的全部语义或Word字节",
     "checker": "one_quoted_paragraph", "family_id": "OFFICE:one_paragraph_conversion",
     "coverage": "VISIBLE_FORMAT_CONDITION_ONLY"},
    {"probe_id": "visible_negative_debit", "candidate_id": "conv_f74f7410ccfd:learn01",
     "user_id": "u_5126c2301b5fab90f1", "assistant_id": "a_572ea7a1697d58f47f",
     "scope": "可见凭证表中的手续费是否置于负借方；不认证真实DOCX或专业会计正确性",
     "checker": "negative_debit_table", "family_id": "DATA:explicit_table_representation",
     "coverage": "VISIBLE_TABLE_CONDITION_ONLY"},
]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def text_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def rows(path: Path):
    with path.open(encoding="utf-8-sig") as stream:
        for number, line in enumerate(stream, 1):
            if line.strip():
                yield number, json.loads(line)


def write_json(path: Path, data):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def judge(kind: str, requirement: str, output: str):
    if kind == "annual_to_monthly":
        if "每人一年20万" not in requirement or "月工资" not in requirement:
            return {"status": "UNKNOWN", "reason": "Expected source requirement missing"}
        expected = (Decimal("200000") / 12).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        amounts = re.findall(r"^[ \t-]*(?:每人月工资|月工资)\s*[：:]\s*[^\n]*?＝\s*\*{0,2}([\d,]+\.\d+)元", output, re.M)
        observed = [Decimal(amount.replace(",", "")) for amount in amounts]
        return {"status": "PASS" if observed and all(value == expected for value in observed) else "FAIL",
                "expected_yuan_per_person_per_month": str(expected),
                "observed_yuan_per_person_per_month": [str(value) for value in observed],
                "basis": "Decimal(200000)/12 rounded to 0.01 yuan; actual visible number, not completion claim"}
    if kind == "one_quoted_paragraph":
        if "整理成一段话" not in requirement:
            return {"status": "UNKNOWN", "reason": "Expected source requirement missing"}
        blocks, current = [], []
        for line in output.splitlines():
            if line.startswith("> "):
                current.append(line[2:])
            elif current:
                blocks.append("\n".join(current))
                current = []
        if current:
            blocks.append("\n".join(current))
        return {"status": "PASS" if len(blocks) == 1 and blocks[0].strip() else "FAIL",
                "visible_quote_block_count": len(blocks),
                "basis": "Count actual quoted text blocks; semantic preservation and Word bytes remain UNKNOWN"}
    if kind == "negative_debit_table":
        if not ("借：财务费用" in requirement and "-0.1" in requirement):
            return {"status": "UNKNOWN", "reason": "Expected source requirement missing"}
        fees = []
        for line in output.splitlines():
            if line.startswith("|") and "手续费" in line:
                cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
                if len(cells) == 4:
                    fees.append({"debit": cells[2], "credit": cells[3]})
        satisfied = bool(fees) and all(re.fullmatch(r"-\d+(?:\.\d+)?", fee["debit"]) and not fee["credit"] for fee in fees)
        return {"status": "PASS" if satisfied else "FAIL", "visible_fee_rows": fees,
                "basis": "Actual table debit/credit cells; no assertion about the claimed DOCX or economic equivalence"}
    raise ValueError(kind)


def controls():
    tests = [
        ("annual_to_monthly", "销售费用按照每人一年20万重新计算，折算成月工资", "每人月工资：20万÷12＝**16,666.67元**", "PASS"),
        ("annual_to_monthly", "销售费用按照每人一年20万重新计算，折算成月工资", "每人月工资：20万÷12＝**15,000.00元**", "FAIL"),
        ("one_quoted_paragraph", "请整理成一段话", "> 一个段落。", "PASS"),
        ("one_quoted_paragraph", "请整理成一段话", "> 第一段。\n\n> 第二段。", "FAIL"),
        ("negative_debit_table", "借：财务费用—手续费 -0.1", "| | 财务费用——手续费 | -0.1 | |", "PASS"),
        ("negative_debit_table", "借：财务费用—手续费 -0.1", "| | 财务费用——手续费 | | 0.1 |", "FAIL"),
    ]
    results = []
    for number, (kind, requirement, output, expected) in enumerate(tests, 1):
        actual = judge(kind, requirement, output)
        assert actual["status"] == expected, (kind, actual)
        results.append({"control_id": number, "checker": kind, "constructed_not_enterprise_episode": True,
                        "expected": expected, "actual": actual["status"]})
    return results


def main():
    if PRIVATE.exists() or (OUT / "enterprise_readiness.json").exists():
        raise SystemExit("Refusing to overwrite frozen enterprise preparation outputs")
    summary = json.loads((SOURCE / "summary.json").read_text(encoding="utf-8-sig"))
    annotations = {row["session_id"]: row for _, row in rows(SOURCE / "private/session_annotations.jsonl")}
    source_rows = list(rows(SOURCE / "private/learning_candidates.jsonl"))
    candidates = {row["candidate_id"]: row for _, row in source_rows}
    assert len(annotations) == 1224 and len(source_rows) == len(candidates) == 719
    by_session = defaultdict(list)
    for number, candidate in source_rows:
        by_session[candidate["session_id"]].append((number, candidate))

    selected_sessions = {candidates[p["candidate_id"]]["session_id"] for p in PROBES}
    selected_originals, member_checks = {}, {}
    source_session_count = 0
    for line, conversation in rows(SOURCE / "private/conversations.jsonl"):
        source_session_count += 1
        session = conversation["session_id"]
        source_messages = {}
        for source_message in conversation["messages"]:
            for identity in set([source_message["group_id"], *source_message.get("source_group_ids", [])]):
                assert identity not in source_messages
                source_messages[identity] = source_message
        assert session in annotations
        for candidate_line, candidate in by_session.get(session, []):
            checks = []
            for message in candidate["messages"]:
                actual = source_messages[message["group_id"]]
                assert message["content"].strip()
                assert message["role"] == actual["role"] and message["content"] == actual["content"]
                checks.append({"group_id": message["group_id"], "role": message["role"],
                               "content_characters": len(message["content"]), "content_sha256": text_hash(message["content"]),
                               "source_canonical_group_id": actual["group_id"],
                               "identity_match_basis": "EXACT_GROUP_ID" if actual["group_id"] == message["group_id"] else "DECLARED_SOURCE_GROUP_ALIAS_AND_EXACT_CONTENT",
                               "source_id_and_content_match": True})
            member_checks[candidate["candidate_id"]] = (line, checks)
        if session in selected_sessions:
            # Keep complete original session messages with exact source aliases.
            # No task/method answer annotations enter this raw export.
            selected_originals[session] = {
                "session_id": session, "source_path": rel(SOURCE / "private/conversations.jsonl"), "source_line": line,
                "messages": conversation["messages"],
                "dated_session_metadata": conversation.get("dated_session_metadata"),
                "file_references": conversation.get("file_references", []),
                "session_tool_record_ids": conversation.get("tool_record_ids", []),
                "tool_records_file": conversation.get("tool_records_file"),
                "tool_payloads_loaded": False, "tool_assignment_to_episode": "UNKNOWN_NOT_INFERRED",
                "chronology_verified": conversation.get("chronology_verified", False),
                "presentation": conversation.get("presentation"),
                "warning": "Source order/role view is preserved and is not asserted to be execution chronology",
            }
    assert source_session_count == 1224 and len(member_checks) == 719

    source_paths = [SOURCE / "summary.json", SOURCE / "topic_statistics.csv", SOURCE / "private/session_annotations.jsonl",
                    SOURCE / "private/learning_candidates.jsonl", SOURCE / "private/conversations.jsonl", SOURCE / "private/model_inputs.jsonl"]
    statistics, partition_locations = [], {}
    for expected in summary["topic_statistics"]:
        topic = expected["代码"]
        partition = SOURCE / "private/topics" / topic
        partition_rows = list(rows(partition / "learning_candidates.jsonl"))
        primary_rows = list(rows(partition / "conversations.jsonl"))
        chosen = [candidate for candidate in candidates.values() if candidate["research_annotations"]["task_topic"] == topic]
        primary = [a for a in annotations.values() if a["session_primary_topic"] == topic]
        states = Counter(a["screening"] for a in primary)
        assert len(chosen) == expected["具体任务学习片段"] == len(partition_rows)
        assert len(primary) == expected["可用会话素材"] == len(primary_rows)
        assert states["KEEP"] == expected["保留学习候选会话"] and states["HOLD"] == expected["暂存待补证会话"]
        assert {c["candidate_id"] for c in chosen} == {c["candidate_id"] for _, c in partition_rows}
        for line, c in partition_rows:
            assert c == candidates[c["candidate_id"]]
            partition_locations[c["candidate_id"]] = (rel(partition / "learning_candidates.jsonl"), line)
        statistics.append({"topic": topic, "name": expected["主题"], "sessions": len(primary),
                           "KEEP": states["KEEP"], "HOLD": states["HOLD"], "candidates": len(chosen)})
        source_paths.extend([partition / "conversations.jsonl", partition / "learning_candidates.jsonl"])
    assert len(statistics) == 13

    proposals = []
    for topic, suffix, name, pattern, example_id in FAMILIES:
        example = candidates[example_id]
        assert example["research_annotations"]["task_topic"] == topic
        matching = [c["candidate_id"] for c in candidates.values()
                    if c["research_annotations"]["task_topic"] == topic and re.search(pattern, c["task"], re.I)]
        assert example_id in matching
        # Seed examples are inspectable label evidence, not a claimed qualified population.
        proposals.append({"family_id": topic + ":" + suffix, "topic": topic, "proposed_name": name,
                          "status": "OUTER_LABEL_RULE_PROPOSAL_NOT_CLUSTER_OR_SKILL",
                          "task_label_regex": pattern, "matching_candidate_ids": matching,
                          "example_candidate_id": example_id, "example_task_original_string": example["task"],
                          "example_source_partition": partition_locations[example_id][0],
                          "example_source_line": partition_locations[example_id][1],
                          "membership_requires_review": True, "native_jobs_created": 0})
    assert len(proposals) == 24 and len({p["topic"] for p in proposals}) == 12

    probes = []
    for configured in PROBES:
        candidate = candidates[configured["candidate_id"]]
        messages = {m["group_id"]: m for m in candidate["messages"]}
        requirement, output = messages[configured["user_id"]], messages[configured["assistant_id"]]
        assert requirement["role"] == "user" and output["role"] == "assistant"
        associations = [a for a in candidate["included_associations"]
                        if a["user_group_id"] == configured["user_id"] and a["assistant_group_id"] == configured["assistant_id"]]
        assert len(associations) == 1
        checked = judge(configured["checker"], requirement["content"], output["content"])
        is_local_request = configured["coverage"] == "COMPLETE_EXPLICIT_LOCAL_SUBREQUEST_ONLY"
        probes.append({**configured, "session_id": candidate["session_id"],
                       "source_user_content_sha256": text_hash(requirement["content"]),
                       "source_assistant_content_sha256": text_hash(output["content"]),
                       "existing_content_associations": associations,
                       "chronology_verified": False, "new_relation_inference": False,
                       "existing_candidate_message_count": len(candidate["messages"]),
                       "existing_candidate_group_ids": [m["group_id"] for m in candidate["messages"]],
                       "condition_result": checked,
                       "local_request_outcome": checked["status"] if is_local_request else "UNKNOWN",
                       "whole_candidate_outcome": "UNKNOWN",
                       "business_outcome": "UNKNOWN", "artifact_bytes_outcome": "UNKNOWN",
                       "native_agentic_verified_pass": False,
                       "native_llm_only_failed_whole_task": False,
                       "native_job_prepared": is_local_request and checked["status"] == "PASS",
                       "native_job_executed": False,
                       "route_status": "READY_NATIVE_SUCCESS_LOCAL_TEXT_SUBREQUEST" if is_local_request and checked["status"] == "PASS" else "DIAGNOSTIC_ONLY_INCOMPLETE_OUTCOME_COVERAGE"})

    registry = []
    for global_line, candidate in source_rows:
        topic = candidate["research_annotations"]["task_topic"]
        conversation_line, checks = member_checks[candidate["candidate_id"]]
        family_ids = [p["family_id"] for p in proposals if candidate["candidate_id"] in p["matching_candidate_ids"]]
        attached = [p for p in probes if p["candidate_id"] == candidate["candidate_id"]]
        registry.append({"candidate_id": candidate["candidate_id"], "session_id": candidate["session_id"],
                         "topic": topic, "existing_task_label": candidate["task"],
                         "session_screening": annotations[candidate["session_id"]]["screening"],
                         "source_global_path": rel(SOURCE / "private/learning_candidates.jsonl"), "source_global_line": global_line,
                         "source_partition_path": partition_locations[candidate["candidate_id"]][0],
                         "source_partition_line": partition_locations[candidate["candidate_id"]][1],
                         "source_conversation_line": conversation_line,
                         "message_member_count": len(checks), "message_members": checks,
                         "source_task_success": candidate["task_success"],
                         "source_complete_trace_verified": candidate["complete_trace_verified"],
                         "source_chronology_verified": candidate["chronology_verified"],
                         "current_whole_candidate_outcome": "UNKNOWN",
                         "qualification": "ONE_SCOPED_LOCAL_SUCCESS_NATIVE_JOB_READY_WHOLE_CANDIDATE_UNKNOWN" if any(p["route_status"] == "READY_NATIVE_SUCCESS_LOCAL_TEXT_SUBREQUEST" for p in attached) else "NOT_ROUTED_NO_COMPLETE_EVALUATION_CONTRACT",
                         "proposed_outer_families": family_ids,
                         "family_assignment_status": "UNASSIGNED" if not family_ids else "MULTIPLE_RULE_MATCHES_REQUIRE_REVIEW" if len(family_ids) > 1 else "LABEL_RULE_MATCH_REQUIRES_REVIEW",
                         "linked_file_reference_ids": candidate.get("linked_file_reference_ids", []),
                         "session_tool_record_ids": candidate.get("session_tool_record_ids", []),
                         "tool_assignment_to_candidate": candidate.get("tool_assignment_to_candidate"),
                         "tool_payloads_inspected_this_preparation": False,
                         "local_probe_ids": [p["probe_id"] for p in attached],
                         "native_job_prepared": any(p["route_status"] == "READY_NATIVE_SUCCESS_LOCAL_TEXT_SUBREQUEST" for p in attached),
                         "native_job_executed": False})
    assert len(registry) == 719 and sum(r["message_member_count"] for r in registry) == 4042

    PRIVATE.mkdir(parents=True)
    write_json(PRIVATE / "task_family_proposals.json", {"method": "Frozen regex rules over existing task labels; no automatic algorithm clustering", "families": proposals,
                                                      "UNCLEAR": {"candidates": 0, "families": []}, "one_example_is_not_one_skill": True})
    with (PRIVATE / "qualification_registry.jsonl").open("x", encoding="utf-8") as stream:
        for entry in registry:
            stream.write(json.dumps(entry, ensure_ascii=False) + "\n")
    write_json(PRIVATE / "source_traces.json", {"schema": "source-message-collection-v1", "source_dataset": rel(SOURCE),
                                               "purpose": "Unabridged source material for eligibility audit; NOT formal native input",
                                               "sessions": list(selected_originals.values())})
    write_json(PRIVATE / "episode_checks.json", {"schema": "source-bound-free-eligibility-check-v1", "probes": probes,
                                                "constructed_checker_controls": controls(),
                                                "judge_is_not_native_trace2skill_analyzer": True,
                                                "limits": ["No UNKNOWN task is relabeled FAILED for the native LLM-only error prompt.",
                                                           "Format/arithmetic condition checks do not certify missing artifacts or professional correctness.",
                                                           "Existing accepted content correspondences retain false chronology/same-task verification flags."]})
    # The author Success analyzer discovers *_SUCCEED.md and reads raw text.
    # This export keeps both selected message bodies complete. It has no invented
    # execution step, tool call, repair, chronology, or artifact-success receipt.
    salary = next(p for p in probes if p["probe_id"] == "salary_monthly_conversion")
    assert salary["local_request_outcome"] == "PASS"
    salary_candidate = candidates[salary["candidate_id"]]
    message_map = {m["group_id"]: m for m in salary_candidate["messages"]}
    user_message = message_map[salary["user_id"]]
    assistant_message = message_map[salary["assistant_id"]]
    logs = PRIVATE / "native_success_logs"
    logs.mkdir()
    native_log = logs / "enterprise_salary-monthly_SUCCEED.md"
    native_text = "## User\n\n" + user_message["content"] + "\n\n## Assistant\n\n" + assistant_message["content"] + "\n"
    with native_log.open("x", encoding="utf-8") as stream:
        stream.write(native_text)
    native_job = {
        "schema": "source-bound-native-success-job-v1", "job_id": "DATA-annual-to-monthly-one-trace",
        "topic": "DATA", "family_id": "DATA:annual_to_monthly", "trace_count": 1,
        "status": "READY_FOR_AUTHOR_SUCCESS_ANALYZER_NOT_EXECUTED",
        "native_analysis_script": "research/baselines/Trace2Skill/analysis/run_success_analysis_llm.py",
        "native_logs_dir": rel(logs), "native_instance_id": "salary-monthly", "native_log": rel(native_log),
        "native_log_sha256": digest(native_log), "native_prompts_unchanged": True,
        "source_candidate_id": salary["candidate_id"], "source_session_id": salary["session_id"],
        "source_partition_path": partition_locations[salary["candidate_id"]][0],
        "source_partition_line": partition_locations[salary["candidate_id"]][1],
        "task_original_string": user_message["content"], "task_scope": salary["scope"],
        "source_user_group_id": salary["user_id"], "source_assistant_group_id": salary["assistant_id"],
        "source_messages_unabridged": [user_message, assistant_message],
        "parent_source_trace": rel(PRIVATE / "source_traces.json"),
        "scoped_success_evaluation": salary["condition_result"],
        "scope_is_local_subrequest_not_whole_existing_candidate": True,
        "source_task_success_metadata_preserved": salary_candidate["task_success"],
        "whole_candidate_outcome": "UNKNOWN", "business_outcome": "UNKNOWN", "artifact_bytes_outcome": "UNKNOWN",
        "chronology_verified": False, "existing_content_associations": salary["existing_content_associations"],
        "adapter_presentation": "Verbatim requirement followed by its existing content-associated complete reply; display is not certified chronology",
        "steps_or_tool_events_synthesized": False, "source_tools_required_for_scoped_arithmetic": False,
        "out_of_scope_response_claims_are_not_gold": ["cash/loan and market decisions", "quarter/team/regional calculations", "Excel update and file delivery"],
        "native_merge": {"reason_if_skipped": "Single actual trace/patch: original implementation may skip merge; do not manufacture a second historical episode", "verify_mechanism_separately": True},
        "creation_seed": "Runner-owned isolated parametric-knowledge creation reconstruction; no handwritten initial skill here",
        "analysis_and_skill_generation_executed": False,
    }
    write_json(PRIVATE / "native_success_job.json", native_job)
    source_hashes = {rel(path): digest(path) for path in source_paths}
    outputs = [PRIVATE / name for name in ("task_family_proposals.json", "qualification_registry.jsonl", "source_traces.json", "episode_checks.json", "native_success_job.json")]
    outputs.append(native_log)
    readiness = {
        "status": "READY_ONE_LOCAL_TEXT_NATIVE_SUCCESS_EXPLORATION_NOT_ALL_TOPIC_SKILLS",
        "source_dataset": rel(SOURCE), "source_only_current_1224_719": True,
        "sessions": 1224, "KEEP": 716, "HOLD": 508, "candidates": 719, "topics": 13,
        "message_member_count": 4042, "topic_statistics": statistics,
        "full_registry_source_identity_and_text_check": "PASS_719_OF_719",
        "source_alias_member_matches": sum(m["identity_match_basis"] != "EXACT_GROUP_ID" for r in registry for m in r["message_members"]),
        "free_preparation_preflight_correction": "First attempt stopped before writing outputs on a declared noncanonical source-group alias; corrected adapter to require explicit source_group_ids membership plus exact role/content. No source data changed.",
        "source_task_success_histogram": dict(Counter(str(c["task_success"]) for c in candidates.values())),
        "whole_candidate_unknown_retained": 719,
        "outer_family_proposals": 24, "topics_with_proposals": 12,
        "family_grouping_is_algorithmic_clustering": False,
        "local_exact_subrequest_passes": 1,
        "visible_condition_checks": {p["probe_id"]: p["condition_result"]["status"] for p in probes},
        "two_episode_family_ready": False, "two_episode_threshold_required_by_native_algorithm": False,
        "native_success_jobs_ready": 1, "native_formal_jobs_executed": 0,
        "native_agentic_verified_enterprise_passes": 0,
        "source_hashes": source_hashes, "output_hashes": {rel(path): digest(path) for path in outputs},
        "new_llm_calls": 0, "new_agent_rollouts": 0, "new_skills": 0,
        "new_recovery": False, "source_commands_executed": False, "credentials_read": False,
        "evaluation_labels_exported_to_generator": False,
        "initial_skill_status": "NOT_CREATED_THIS_PREPARATION_ISOLATED_CREATION_OWNED_BY_NATIVE_RUNNER",
        "scope": ["Entire current corpus retained, not resampled or replaced by old recovered cases.",
                  "Raw exports preserve complete current session message bodies, original group IDs/aliases and role view; no execution chronology asserted.",
                  "Session tool IDs retained; payloads are not loaded or assigned by nearest message.",
                  "This free input preparation does not execute the author analyzer, repair agent, MAP/MERGE/APPLY, or package skills.",
                  "One independently checked local arithmetic task is routable to the author Success analyzer; native algorithm permits one trace, so a two-episode gate is not imposed.",
                  "No all-theme multi-skill experiment has been completed; remaining UNKNOWN outcomes are not fed to a custom UNKNOWN analyzer or mislabeled FAILED.",
                  "Proposed families and task labels require outer grouping review before defining independent native skill jobs."],
    }
    write_json(OUT / "enterprise_readiness.json", readiness)
    # Confirm exact preservation after serialization, not merely source existence.
    exported = json.loads((PRIVATE / "source_traces.json").read_text(encoding="utf-8"))
    assert exported["sessions"] == list(selected_originals.values())
    assert all(digest(ROOT / path) == expected for path, expected in source_hashes.items())
    print(json.dumps({"status": readiness["status"], "sessions": 1224, "candidates": 719, "topics": 13,
                      "proposals": 24, "exact_local_subrequest_passes": 1, "native_success_jobs_ready": 1, "native_jobs_executed": 0,
                      "model_calls": 0, "skills": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
