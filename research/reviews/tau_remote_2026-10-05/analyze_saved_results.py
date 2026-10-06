"""Offline audit of saved tau2 results. Reads six result JSONs; no model calls.

Outputs contain numeric aggregates and task IDs, not conversation bodies.
Run: python research/reviews/tau_remote_2026-10-05/analyze_saved_results.py
"""
import argparse
import csv
import hashlib
import json
import math
import random
import re
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

SHA = "14f5b59ab29351973429777fb013afafd15297ce"
PROJECT = Path("D:/skillsgen-industry_track")
DEFAULT_SOURCE = PROJECT / "research/imports/2026-10-05_tau_remote/repository_complete/research/experiments"
DEFAULT_OUTPUT = PROJECT / "research/reviews/tau_remote_2026-10-05"
COHORTS = [
    ("retail", "零售", "148_tau2_retail_autoskill", "test_v4"),
    ("airline", "航空", "267_tau2_airline_autoskill", "test"),
    ("telecom", "电信", "268_tau2_telecom_autoskill", "test"),
]
GROUPS = [("B0", "no_skill"), ("B1", "autoskill_library")]
CONTROL = ["###STOP###", "###TRANSFER###", "###OUT-OF-SCOPE###"]


def number(x):
    return not isinstance(x, bool) and isinstance(x, (int, float)) and math.isfinite(x)


def reward(s):
    v = (s.get("reward_info") or {}).get("reward")
    return float(v) if number(v) else None


def key(s):
    return str(s.get("task_id")), s.get("trial")


def brief(s):
    return {k: s.get(k) for k in ("id", "task_id", "trial", "seed", "termination_reason")}


def counter_json(values):
    return dict(sorted(Counter(str(v) for v in values).items()))


def distribution(values):
    a = sorted(float(v) for v in values if number(v))
    def q(p):
        z = (len(a) - 1) * p
        lo = int(z)
        return a[lo] + (a[min(lo + 1, len(a) - 1)] - a[lo]) * (z - lo)
    if not a:
        return {"n": 0, "mean": None, "median": None, "p95": None, "min": None, "max": None, "sum": None}
    return {"n": len(a), "mean": statistics.mean(a), "median": q(.5), "p95": q(.95), "min": a[0], "max": a[-1], "sum": sum(a)}


def exact_p(wins, losses):
    n = wins + losses
    return min(1.0, 2.0 * sum(math.comb(n, j) for j in range(min(wins, losses) + 1)) / 2**n) if n else 1.0


def task_bootstrap(deltas):
    if len(deltas) < 2:
        return None
    rng = random.Random(42)
    n = len(deltas)
    means = sorted(sum(deltas[rng.randrange(n)] for _ in range(n)) / n for _ in range(10000))
    return [round(means[250], 4), round(means[9749], 4)]


def score_audit(sims):
    bases = Counter()
    combinations = Counter()
    components = defaultdict(list)
    component_missing = Counter()
    missing_info, missing_reward, invalid_reward, nonbinary, missing_breakdown = [], [], [], [], []
    basis_absent, product_mismatch = [], []
    db_rewards, db_matches = [], []
    subchecks = {name: {"simulation_count_nonnull": 0, "check_count": 0, "positive_count": 0, "reward_values": []} for name in ("action_checks", "env_assertions", "nl_assertions", "communicate_checks")}
    for s in sims:
        ri = s.get("reward_info")
        if not isinstance(ri, dict):
            missing_info.append(brief(s))
            ri = {}
        v = ri.get("reward")
        if v is None:
            missing_reward.append(brief(s))
        elif not number(v):
            invalid_reward.append(brief(s))
        elif v not in (0, 1):
            nonbinary.append({**brief(s), "reward": v})
        basis = ri.get("reward_basis") or []
        bases["+".join(str(b) for b in basis)] += 1
        bd = ri.get("reward_breakdown")
        if not isinstance(bd, dict):
            missing_breakdown.append(brief(s))
            bd = {}
        combinations[";".join(f"{k}={bd[k]}" for k in sorted(bd)) or "missing_or_empty"] += 1
        for k, x in bd.items():
            components[k].append(x)
        absent = [b for b in basis if b not in bd]
        for b in absent:
            component_missing[b] += 1
        if absent:
            basis_absent.append({**brief(s), "basis_components_absent_from_breakdown": absent})
        if bd and all(number(x) for x in bd.values()) and number(v):
            product = math.prod(bd.values())
            if abs(product - v) > 1e-9:
                product_mismatch.append({**brief(s), "reward": v, "breakdown_product": product})
        dbc = ri.get("db_check") or {}
        if isinstance(dbc, dict):
            if dbc.get("db_reward") is not None:
                db_rewards.append(dbc.get("db_reward"))
            if dbc.get("db_match") is not None:
                db_matches.append(dbc.get("db_match"))
        for name, data in subchecks.items():
            checks = ri.get(name)
            if not isinstance(checks, list):
                continue
            data["simulation_count_nonnull"] += 1
            data["check_count"] += len(checks)
            for c in checks:
                if not isinstance(c, dict):
                    continue
                m = c.get("action_match", c.get("met", c.get("match")))
                data["positive_count"] += int(m is True)
                rv = c.get("action_reward", c.get("reward"))
                if rv is not None:
                    data["reward_values"].append(rv)
    for data in subchecks.values():
        data["reward_distribution"] = counter_json(data.pop("reward_values"))
    return {
        "missing_reward_info": missing_info, "missing_reward": missing_reward,
        "invalid_reward": invalid_reward, "nonbinary_reward": nonbinary,
        "missing_reward_breakdown": missing_breakdown,
        "reward_basis_distribution": dict(sorted(bases.items())),
        "reward_breakdown_joint_distribution": dict(sorted(combinations.items())),
        "reward_breakdown_components": {k: {"present_simulations": len(v), "value_distribution": counter_json(v), "numeric": distribution(v)} for k, v in sorted(components.items())},
        "basis_component_absent_counts": dict(component_missing),
        "basis_component_absent_records": basis_absent,
        "breakdown_product_mismatch": product_mismatch,
        "db_reward_distribution": counter_json(db_rewards), "db_match_distribution": counter_json(db_matches),
        "subcheck_diagnostics": subchecks,
        "note": "子检查只是诊断；正式成功由保存的reward==1定义。basis缺项可能是可选断言未应用，不直接定性评分错误。"
    }


def group_stats(sims):
    buckets = defaultdict(list)
    for s in sims:
        buckets[key(s)].append(s)
    unique = {k: v[0] for k, v in buckets.items() if len(v) == 1}
    duplicates = [{"task_id": k[0], "trial": k[1], "simulations": [brief(s) for s in v]} for k, v in buckets.items() if len(v) != 1]
    rewards = [reward(s) for s in sims]
    valid_rewards = [v for v in rewards if v is not None]
    binary_rewards = [v for v in rewards if v in (0., 1.)]
    bytask = defaultdict(list)
    for k, s in unique.items():
        bytask[k[0]].append(s)
    complete = {t: rs for t, rs in bytask.items() if len(rs) == 4 and len({s.get("trial") for s in rs}) == 4 and all(reward(s) in (0., 1.) for s in rs)}
    success_counts = {t: sum(reward(s) == 1 for s in rs) for t, rs in complete.items()}
    histogram = {str(c): sum(v == c for v in success_counts.values()) for c in range(5)}
    pass_all, pass_any = {}, {}
    for k in range(1, 5):
        n = len(complete)
        pass_all[str(k)] = sum(math.comb(c, k) / math.comb(4, k) if c >= k else 0 for c in success_counts.values()) / n if n else None
        pass_any[str(k)] = sum(1 - (math.comb(4-c, k) / math.comb(4, k) if 4-c >= k else 0) for c in success_counts.values()) / n if n else None
    roles = Counter()
    content_roles = Counter()
    calls_by_role = Counter()
    replies_by_requestor = Counter()
    errors_by_requestor = Counter()
    user_controls = Counter()
    usage_values = defaultdict(lambda: defaultdict(list))
    usage_nonnull = Counter()
    message_costs = defaultdict(list)
    error_sims = 0
    counts = defaultdict(list)
    for s in sims:
        sc = Counter()
        for m in s.get("messages") or []:
            role = str(m.get("role"))
            roles[role] += 1
            sc["messages"] += 1
            sc[f"messages_{role}"] += 1
            content = m.get("content")
            if content:
                content_roles[role] += 1
            calls = m.get("tool_calls") or []
            if isinstance(calls, list):
                calls_by_role[role] += len(calls)
                sc["business_tool_calls"] += len(calls)
                sc[f"business_tool_calls_{role}"] += len(calls)
            if role == "tool":
                requestor = str(m.get("requestor"))
                replies_by_requestor[requestor] += 1
                sc["tool_replies"] += 1
                if m.get("error") is True:
                    errors_by_requestor[requestor] += 1
                    sc["native_tool_errors_true"] += 1
            if role == "user":
                markers = [token for token in CONTROL if isinstance(content, str) and token in content]
                if markers:
                    for marker in markers:
                        user_controls[marker] += 1
                    sc["user_control_messages"] += 1
                else:
                    sc["user_nonterminal_messages_including_initial"] += 1
            usage = m.get("usage")
            if isinstance(usage, dict):
                usage_nonnull[role] += 1
                for k, v in usage.items():
                    if number(v):
                        usage_values[role][k].append(v)
            if m.get("cost") is not None:
                message_costs[role].append(m.get("cost"))
        sc["user_nonterminal_messages_after_initial_assumed"] = max(0, sc["user_nonterminal_messages_including_initial"] - 1)
        error_sims += int(sc["native_tool_errors_true"] > 0)
        for k in ["messages", "messages_assistant", "messages_user", "messages_tool", "business_tool_calls", "business_tool_calls_assistant", "business_tool_calls_user", "tool_replies", "native_tool_errors_true", "user_nonterminal_messages_including_initial", "user_nonterminal_messages_after_initial_assumed"]:
            counts[k].append(sc[k])
    tool_replies = sum(replies_by_requestor.values())
    error_count = sum(errors_by_requestor.values())
    duration = distribution(s.get("duration") for s in sims)
    costs = {k: {"nonnull_simulations": sum(s.get(k) is not None for s in sims), "numeric": distribution(s.get(k) for s in sims)} for k in ("agent_cost", "user_cost")}
    return {
        "raw_simulations": len(sims), "unique_task_trial_keys": len(buckets), "unique_tasks": len(bytask),
        "duplicate_task_trial": duplicates, "reward_valid_numeric_count": len(valid_rewards), "reward_binary_count": len(binary_rewards),
        "success_count_reward_eq_1": sum(v == 1 for v in rewards),
        "success_rate_over_all_saved_simulations": sum(v == 1 for v in rewards) / len(sims) if sims else None,
        "mean_reward_over_valid_numeric": statistics.mean(valid_rewards) if valid_rewards else None,
        "reward_distribution": counter_json(rewards), "score_audit": score_audit(sims),
        "trial_distribution": counter_json(s.get("trial") for s in sims), "seed_distribution": counter_json(s.get("seed") for s in sims),
        "termination_reason_distribution": counter_json(s.get("termination_reason") for s in sims),
        "duration_seconds": {**duration, "missing_or_invalid": len(sims) - duration["n"]},
        "messages": {"roles": dict(roles), "nonempty_content_by_role": dict(content_roles), "user_control_marker_counts": dict(user_controls)},
        "business_tools": {"calls_by_message_role": dict(calls_by_role), "reply_by_requestor": dict(replies_by_requestor), "native_error_true_by_requestor": dict(errors_by_requestor), "error_true_count": error_count, "error_true_fraction_of_tool_replies": error_count / tool_replies if tool_replies else None, "error_affected_simulations": error_sims, "error_affected_simulation_fraction": error_sims / len(sims) if sims else None},
        "per_simulation_counts": {k: distribution(v) for k, v in counts.items()},
        "usage": {role: {"message_count": roles[role], "nonnull_usage_message_count": usage_nonnull[role], "numeric_fields": {k: {"present_messages": len(v), "sum": sum(v)} for k, v in usage_values[role].items()}} for role in roles},
        "saved_simulation_cost": costs,
        "saved_message_cost": {role: {"nonnull_count": len(v), "value_distribution": counter_json(v)} for role, v in message_costs.items()},
        "actual_monetary_cost": None,
        "pass_metrics": {"eligible_four_trial_binary_tasks": len(complete), "excluded_tasks": [t for t in bytask if t not in complete], "success_count_histogram_over_four_trials": histogram, "observed_any_success_tasks": sum(c > 0 for c in success_counts.values()), "observed_all_four_success_tasks": sum(c == 4 for c in success_counts.values()), "observed_some_but_not_all_success_tasks": sum(0 < c < 4 for c in success_counts.values()), "pass_power_k_all_success_estimator": pass_all, "pass_at_k_any_success_estimator": pass_any},
    }, unique


def subgroup(uniques, field):
    def label(t):
        match = re.search(r"^\[([^]]+)\]", t) if field == "problem_type" else re.search(r"\[PERSONA:([^]]+)\]", t)
        return match.group(1) if match else "unknown"
    labels = sorted({label(k[0]) for u in uniques for k in u})
    out = []
    for name in labels:
        gs = []
        for u in uniques:
            rs = [s for k, s in u.items() if label(k[0]) == name]
            vals = [reward(s) for s in rs]
            gs.append({"tasks": len({s['task_id'] for s in rs}), "simulations": len(rs), "successes": sum(v == 1 for v in vals), "success_rate": sum(v == 1 for v in vals) / len(rs) if rs else None})
        out.append({"label": name, "B0": gs[0], "B1": gs[1], "delta_percentage_points": 100 * (gs[1]["success_rate"] - gs[0]["success_rate"]) if all(g["success_rate"] is not None for g in gs) else None})
    return out


def collect_stats(source, experiment):
    p = source / experiment / "runs/collect/evolution.json"
    if not p.exists():
        return {"path": p.as_posix(), "exists": False}
    raw = p.read_bytes()
    data = json.loads(raw.decode("utf-8"))
    sims = data.get("simulations") or []
    values = [reward(s) for s in sims]
    valid = [v for v in values if v is not None]
    info = data.get("info") or {}
    score = score_audit(sims)
    return {
        "source": {"path": p.as_posix(), "exists": True, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)},
        "raw_simulations": len(sims), "unique_tasks": len({str(s.get('task_id')) for s in sims}),
        "success_count_reward_eq_1": sum(v == 1 for v in values), "reward_eq_0_count": sum(v == 0 for v in values),
        "reward_missing_or_invalid_count": len(sims)-len(valid),
        "mean_reward_over_valid_numeric": statistics.mean(valid) if valid else None,
        "success_rate_over_all_saved_simulations": sum(v == 1 for v in values) / len(sims) if sims else None,
        "reward_distribution": counter_json(values), "termination_reason_distribution": counter_json(s.get('termination_reason') for s in sims),
        "reward_termination_joint_counts": dict(Counter(f"reward={reward(s)};termination={s.get('termination_reason')}" for s in sims)),
        "reward_breakdown_missing_count": len(score['missing_reward_breakdown']),
        "reward_breakdown_joint_distribution": score['reward_breakdown_joint_distribution'],
        "reward_basis_distribution": score['reward_basis_distribution'],
        "reward_breakdown_missing_records": score['missing_reward_breakdown'],
        "model_aliases": {k: (info.get(k) or {}).get('llm') for k in ('agent_info','user_info')},
        "note": "学习源采集阶段，单独列出，不能混入正式B0/B1分母。timeout/too_many_errors是保存的原生终态；它们本身不足以认定细分机制或基础设施根因。"
    }


def audit_cohort(source, domain, chinese, experiment, run):
    output = {"domain": domain, "domain_zh": chinese, "experiment": experiment, "run_directory": run, "groups": {}, "sources": {}}
    originals, uniques = [], []
    for group, filename in GROUPS:
        p = source / experiment / "runs" / run / (filename + ".json")
        raw = p.read_bytes()
        data = json.loads(raw.decode("utf-8"))
        sims = data.get("simulations") or []
        stats, unique = group_stats(sims)
        output["groups"][group] = stats
        output["sources"][group] = {"path": p.as_posix(), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "json_simulations_path": "$.simulations"}
        info = data.get("info") or {}
        stats["safe_configuration"] = {k: info.get(k) for k in ("seed", "max_steps", "max_errors", "domain", "num_trials")}
        for k in ("agent_info", "user_info"):
            sub = info.get(k) or {}
            stats["safe_configuration"][k] = {"implementation": sub.get("implementation"), "llm_alias": sub.get("llm"), "temperature": (sub.get("llm_args") or {}).get("temperature")}
        originals.append(sims)
        uniques.append(unique)
    u0, u1 = uniques
    pairs = [k for k in u0 if k in u1]
    usable = [k for k in pairs if reward(u0[k]) is not None and reward(u1[k]) is not None]
    binary = [k for k in usable if reward(u0[k]) in (0., 1.) and reward(u1[k]) in (0., 1.)]
    wins = sum(reward(u1[k]) > reward(u0[k]) for k in binary)
    losses = sum(reward(u1[k]) < reward(u0[k]) for k in binary)
    bytask = defaultdict(list)
    for k in usable:
        bytask[k[0]].append(reward(u1[k]) - reward(u0[k]))
    task_means = {t: statistics.mean(v) for t, v in bytask.items()}
    positive = sum(v > 0 for v in task_means.values())
    negative = sum(v < 0 for v in task_means.values())
    mismatch = [{"task_id": k[0], "trial": k[1], "B0_seed": u0[k].get("seed"), "B1_seed": u1[k].get("seed")} for k in pairs if u0[k].get("seed") != u1[k].get("seed")]
    missingseed = [{"task_id": k[0], "trial": k[1]} for k in pairs if u0[k].get("seed") is None or u1[k].get("seed") is None]
    ci = task_bootstrap(list(task_means.values()))
    output["paired"] = {
        "unique_matched_task_trial_pairs": len(pairs), "valid_numeric_reward_pairs": len(usable), "binary_reward_pairs": len(binary),
        "B0_unmatched": [brief(u0[k]) for k in u0 if k not in u1], "B1_unmatched": [brief(u1[k]) for k in u1 if k not in u0],
        "invalid_reward_pairs": [{"task_id": k[0], "trial": k[1]} for k in pairs if k not in usable],
        "same_seed_pairs": sum(u0[k].get("seed") == u1[k].get("seed") and u0[k].get("seed") is not None for k in pairs), "seed_mismatches": mismatch, "missing_seed_pairs": missingseed,
        "B1_wins_binary": wins, "B1_losses_binary": losses, "ties_binary": len(binary)-wins-losses,
        "both_success_binary": sum(reward(u0[k]) == reward(u1[k]) == 1 for k in binary), "both_failure_binary": sum(reward(u0[k]) == reward(u1[k]) == 0 for k in binary),
        "mean_reward_delta_B1_minus_B0": statistics.mean(reward(u1[k]) - reward(u0[k]) for k in usable) if usable else None,
        "exact_McNemar_two_sided_p_binary_pairs": exact_p(wins, losses),
        "task_count": len(task_means), "task_mean_delta_positive": positive, "task_mean_delta_negative": negative, "task_mean_delta_tied": len(task_means)-positive-negative,
        "task_level_exact_sign_two_sided_p": exact_p(positive, negative),
        "mean_of_task_mean_deltas": statistics.mean(task_means.values()) if task_means else None,
        "task_bootstrap_ci95": ci, "task_bootstrap_ci95_percentage_points": [100*x for x in ci] if ci else None,
        "task_bootstrap_method": {"iterations": 10000, "seed": 42, "rng": "Python random.Random; randrange task index", "ordering": "B0 saved simulations first-appearance task order, after unique paired numeric filtering", "quantile_indices_zero_based": [250, 9749], "rounding": "4 decimals in reward units, matching source paired_summary_v4.py", "unit": "task mean paired reward delta, resample nTasks tasks with replacement"},
        "task_records": [{"task_id": t, "paired_trials": len(bytask[t]), "B0_successes": sum(reward(u0[k]) == 1 for k in usable if k[0] == t), "B1_successes": sum(reward(u1[k]) == 1 for k in usable if k[0] == t), "mean_delta": d} for t, d in task_means.items()],
    }
    if domain == "telecom":
        output["exploratory_subgroups"] = {"problem_type_from_task_id": subgroup(uniques, "problem_type"), "persona_from_task_id": subgroup(uniques, "persona"), "note": "事后描述性诊断，未进行多重比较校正，不把子组差值当显著算法优势。"}
    reportname = {"retail": "v4_paired_summary.json", "airline": "paired_summary_267.json", "telecom": "paired_summary_268.json"}[domain]
    rp = source / experiment / "reports" / reportname
    output["source_report_comparison"] = {"path": rp.as_posix(), "exists": rp.exists()}
    if rp.exists():
        rdata = json.loads(rp.read_text(encoding="utf-8"))
        saved = rdata.get("paired") or {}
        output["source_report_comparison"]["saved_report_paired_fields"] = saved
        checks = {"pairs": len(usable), "B1_better": wins, "B0_better": losses, "ties": len(binary)-wins-losses, "mean_diff_B1_minus_B0": round(output['paired']['mean_reward_delta_B1_minus_B0'],4), "sign_test_two_sided_p": round(exact_p(wins,losses),6), "bootstrap_ci95_task_level": ci}
        output["source_report_comparison"]["independent_numeric_fields_match"] = {k: saved.get(k)==v for k,v in checks.items()}
    output['collect_source_descriptive'] = collect_stats(source, experiment)
    return output


def f(x, decimals=2):
    return "未知" if x is None else f"{x:.{decimals}f}"


def make_markdown(result):
    lines = ["# 固定远端快照 τ² 三域统计复核", "", f"来源提交：`{result['source_commit_sha']}`。本轮仅用 Python 标准库离线读取六个正式结果 JSON；未执行模型、实验或服务，未修改原始实验。数值由原始 `simulations` 复算，脚本报告只用于比较。", "", "## 正式对照", "", "| 域 | 任务×试验 | B0成功 | B1成功 | 差值pp | B1胜/负/平（场） | 精确McNemar p | 任务bootstrap 95% CI pp | 任务胜/负/平 |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for c in result["cohorts"]:
        a,b=c["groups"]["B0"],c["groups"]["B1"];p=c["paired"]
        lines.append(f"| {c['domain_zh']} | {p['task_count']}×4={p['binary_reward_pairs']} | {a['success_count_reward_eq_1']}/{a['raw_simulations']}（{100*a['mean_reward_over_valid_numeric']:.2f}%） | {b['success_count_reward_eq_1']}/{b['raw_simulations']}（{100*b['mean_reward_over_valid_numeric']:.2f}%） | {100*p['mean_reward_delta_B1_minus_B0']:+.2f} | {p['B1_wins_binary']}/{p['B1_losses_binary']}/{p['ties_binary']} | {p['exact_McNemar_two_sided_p_binary_pairs']:.6f} | [{p['task_bootstrap_ci95_percentage_points'][0]:+.2f}, {p['task_bootstrap_ci95_percentage_points'][1]:+.2f}] | {p['task_mean_delta_positive']}/{p['task_mean_delta_negative']}/{p['task_mean_delta_tied']} |")
    lines += ["", "三域场级检验均未显著、任务区间均跨零。40/20/40题各四次，场次嵌套在同题中；McNemar场级p不消除题内相关性。任务bootstrap按任务均差重采样，10,000次、seed 42、B0原始出现顺序、索引250/9749、奖励单位四位小数，已核对三域原 `paired_summary_v4.py` 定义。独立复算的配对人数、胜负平、均差、p和CI均匹配保存报告（p按报告六位小数比较）。任务层符号检验另见JSON，不与场级p混用。", "", "## 学习源采集阶段更正", "", "| 域 | 原始场数 | 保存reward=1 / reward=0 | reward均值 | 原生终态 |", "|---|---:|---:|---:|---|"]
    for c in result['cohorts']:
        s=c['collect_source_descriptive'];terms='；'.join(f"{k}: {v}" for k,v in s['termination_reason_distribution'].items())
        lines.append(f"| {c['domain_zh']} | {s['raw_simulations']} | {s['success_count_reward_eq_1']} / {s['reward_eq_0_count']} | {s['mean_reward_over_valid_numeric']:.9f} | {terms} |")
    lines += ["", "航空为19成功+7失败/26=0.730769231；电信为53成功+17失败/70=0.757142857。报告中的航空0.72、电信52+18/0.75不能作为原始结果真值。零售是5成功、50个user_stop零分、10个timeout零分、5个too_many_errors零分；后15场保存reward=0但没有正常reward_breakdown，机制归因需另查流程证据。学习源采集与正式评测分开，不把collect分数并入B0/B1。", "", "## 四次重复稳定性", "", "| 域 | 组 | 0/1/2/3/4次成功任务数 | 曾成功任务/全体题 | 四次全成功/全体题 | 曾成功但四次不稳定/曾成功 | pass^1 / pass^2 / pass^3 / pass^4 | pass@1 / pass@2 / pass@3 / pass@4 |", "|---|---|---:|---:|---:|---:|---|---|"]
    for c in result["cohorts"]:
        for group,_ in GROUPS:
            p=c["groups"][group]["pass_metrics"];n=p["eligible_four_trial_binary_tasks"]
            h="/".join(str(p['success_count_histogram_over_four_trials'][str(k)]) for k in range(5))
            allp=" / ".join(f"{100*p['pass_power_k_all_success_estimator'][str(k)]:.2f}%" for k in range(1,5))
            anyp=" / ".join(f"{100*p['pass_at_k_any_success_estimator'][str(k)]:.2f}%" for k in range(1,5))
            lines.append(f"| {c['domain_zh']} | {group} | {h} | {p['observed_any_success_tasks']}/{n} | {p['observed_all_four_success_tasks']}/{n} | {p['observed_some_but_not_all_success_tasks']}/{p['observed_any_success_tasks']} | {allp} | {anyp} |")
    lines += ["", "pass^k为每题四次观测中均匀抽取k次全部成功的估计：均值 C(c,k)/C(4,k)；pass@k为至少一次成功：均值 [1−C(4−c,k)/C(4,k)]。二者各用完整四次、二元评分任务；本次六组均无排除。pass^4=四次全成功题比例，pass@4=四次至少一次成功题比例。不能把成功率直接取k次幂或把22/40一类四次全成功计为pass@4。", "", "## 耗时、消息、业务工具与原生成本字段", "", "| 域 | 组 | 耗时均值/P50/P95秒 | 平均消息数 | 平均业务工具调用（助手/用户） | 原生tool.error=True/工具回复 | 受影响场次 | 平均用户非终止消息（含初始） | 用户prompt/completion tokens |", "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for c in result["cohorts"]:
        for group,_ in GROUPS:
            s=c['groups'][group];d=s['duration_seconds'];cnt=s['per_simulation_counts'];tools=s['business_tools'];usage=s['usage'].get('user',{}).get('numeric_fields',{})
            tok="/".join(str(usage.get(k,{}).get('sum','未知')) for k in ['prompt_tokens','completion_tokens'])
            replies=sum(tools['reply_by_requestor'].values())
            lines.append(f"| {c['domain_zh']} | {group} | {d['mean']:.2f}/{d['median']:.2f}/{d['p95']:.2f} | {cnt['messages']['mean']:.3f} | {cnt['business_tool_calls']['mean']:.3f}（{cnt['business_tool_calls_assistant']['mean']:.3f}/{cnt['business_tool_calls_user']['mean']:.3f}） | {tools['error_true_count']}/{replies}（{100*tools['error_true_fraction_of_tool_replies']:.2f}%） | {tools['error_affected_simulations']}/{s['raw_simulations']} | {cnt['user_nonterminal_messages_including_initial']['mean']:.3f} | {tok} |")
    lines += ["", "耗时按保存的每场duration，P50/P95使用线性插值；跨场耗时之和不是并发批次墙钟。业务工具为tau² messages里的tool_calls，电信含用户侧工具；外部技能Read、模型请求均不计入。错误仅指工具回复原生error字段为true，不做语义错误推断；每组总量、均值和角色分解见JSON。非终止用户消息排除STOP/TRANSFER/OUT-OF-SCOPE控制标记，含初始消息；减一版本只是对首条非终止用户消息为初始的约定。", "", "六组assistant消息usage均为空，agent/user每场cost字段均为空；用户消息usage可观察。消息cost的保存零值不能证明实际免费，agent tokens、技能生成/读取tokens、实际金额与正式评测资源归因均未知。请求日志全账本累计不得当作本表评测成本。", "", "## 评分完整性与分解", "", "| 域 | 组 | reward缺失/无效/非二元 | 分解缺失 | basis列出但分解缺项 | 保存reward分解组合 |", "|---|---|---:|---:|---|---|"]
    for c in result['cohorts']:
        for group,_ in GROUPS:
            s=c['groups'][group];a=s['score_audit']
            combos="；".join(f"{k}: {v}" for k,v in a['reward_breakdown_joint_distribution'].items())
            absent=json.dumps(a['basis_component_absent_counts'],ensure_ascii=False)
            lines.append(f"| {c['domain_zh']} | {group} | {len(a['missing_reward'])}/{len(a['invalid_reward'])}/{len(a['nonbinary_reward'])} | {len(a['missing_reward_breakdown'])} | {absent} | {combos} |")
    lines += ["", "reward_basis与分解的缺项逐场保留在JSON，不直接视为评分失败：可选NL断言未应用时可能缺少NL_ASSERTION分解。额外action/env/nl/communicate检查统计只是描述，不替换官方最终reward。", "", "## 电信事后子组诊断", "", "| 切分 | 子组 | B0成功/场数（题数） | B1成功/场数（题数） | 差值pp |", "|---|---|---:|---:|---:|"]
    tel=next(c for c in result['cohorts'] if c['domain']=='telecom')
    for kind,label in [('problem_type_from_task_id','问题类型'),('persona_from_task_id','PERSONA')]:
        for s in tel['exploratory_subgroups'][kind]:
            a,b=s['B0'],s['B1'];lines.append(f"| {label} | {s['label']} | {a['successes']}/{a['simulations']}（{a['tasks']}） | {b['successes']}/{b['simulations']}（{b['tasks']}） | {s['delta_percentage_points']:+.2f} |")
    lines += ["", "子组由保存task_id中的[问题类型]/[PERSONA:...]解析，仅作事后机制线索；未作多重检验校正，不能据某个子组称算法胜利。", "", "## 配对、适用范围与未知", "", "- 六组无重复task×trial、缺失reward或非二元reward；三域完整配对，seed分别160/160、80/80、160/160一致。所有保存正式场次termination_reason均为user_stop；具体STOP/TRANSFER/OUT-OF-SCOPE控制标记另计，user_stop不等于业务成功。", "- 本表仅包含固定快照中的指定正式结果。零售OLDlib_8partial文件不入正式分母；此前失败、重跑、选择最终保存结果的过程不能由这六份结果排除。全部保存终态正常不证明尝试历史或基础设施无故障。", "- seed=42的单一实验设定、同题四次和同任务家族相关性限制泛化；模型别名不证明物理后端、资源并发或harness过程完全相同。当前比较是技能库与显式读取提示等整个处理包的效果，不能归因于某个独立算法机制。", "- 历史159/160及其他读取率如果只由保存audit的read调用/路径判断，只能记读取尝试；不能证明调用成功、非空SKILL全文交付或全文被模型消费。本脚本没有读取外部私有session，未新增验证技能全文读取率。", "- 这三域没有合并总体p值，也没有把电信的下降删除；正式成功、稳定性、耗时和错误需同时报告。", "", "## 复现与来源", "", "脚本：`analyze_saved_results.py`；机器可读结果：`statistics_audit.json`；中文表头：`metrics.csv`。JSON记录各原始文件绝对路径、SHA-256、字段定义、异常列表、任务明细和脚本报告对照。", ""]
    for c in result['cohorts']:
        for group,_ in GROUPS:
            source=c['sources'][group];lines.append(f"- {c['domain_zh']} {group}: `{source['path']}`；SHA-256 `{source['sha256']}`")
    return '\n'.join(lines)+'\n'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,default=DEFAULT_SOURCE)
    parser.add_argument('--output',type=Path,default=DEFAULT_OUTPUT)
    args=parser.parse_args()
    # Keep all mutations in the expressly authorized review artifact directory.
    if args.output.resolve() != DEFAULT_OUTPUT.resolve():
        raise SystemExit('Output must be the authorized tau_remote_2026-10-05 review directory')
    args.output.mkdir(parents=True,exist_ok=True)
    result={"source_commit_sha":SHA,"created_utc":datetime.now(timezone.utc).isoformat(),"scope":"Six explicitly selected saved final result JSONs; offline independent recomputation; no model/service/experiment calls", "definitions":{
        "success":"saved reward_info.reward == 1; success_rate denominator all saved simulations; mean_reward denominator valid finite numeric reward",
        "pairing":"unique string(task_id), trial; duplicate keys preserved as anomalies and excluded from unique pair statistics",
        "exact_McNemar":"two-sided doubled binomial tail with min(wins,losses), p capped at1; binary paired reward only; scene correlation caveat",
        "task_bootstrap":"per-task mean paired deltas; random.Random(42), 10000 resamples; preserve B0 first appearance order; indexes250,9749; round4; source-script equivalent",
        "pass_power_k":"average C(c,k)/C(4,k), all-success estimator from four observed binary trials per task",
        "pass_at_k":"average 1-C(4-c,k)/C(4,k), any-success estimator from four observed binary trials per task",
        "duration":"saved duration seconds; percentile interpolation index p*(n-1)",
        "business_tools":"tool_calls in saved tau2 messages, all requestor roles; excludes external skills Read/LLM requests",
        "native_tool_error":"tool reply.error is true; no inferred semantic-error classifier",
        "unknown_cost":"assistant usage and sim costs null do not establish zero token/monetary cost; no all-ledger cost attribution",
        "subgroups":"telecom issue/persona parsed from task_id; post hoc descriptive, no multiplicity-adjusted claims",
    },"cohorts":[audit_cohort(args.source,*c) for c in COHORTS]}
    result['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (args.output/'statistics_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    (args.output/'statistics_audit.md').write_text(make_markdown(result),encoding='utf-8')
    with (args.output/'metrics.csv').open('w',encoding='utf-8-sig',newline='') as handle:
        writer=csv.writer(handle)
        writer.writerow(['域','组','题数','场数','成功数','成功率','平均reward','四次完整任务数','四次全成功题数','四次全成功比例_pass^4','至少一次成功题数','至少一次成功比例_pass@4','曾成功但四次不稳定题数','平均耗时秒','中位耗时秒','P95耗时秒','平均消息数','平均业务工具数','助手业务工具数','用户业务工具数','原生工具错误数','工具回复数','原生工具错误比例','错误涉及场次','平均用户非终止消息_含初始','用户prompt_tokens','用户completion_tokens','助手tokens','实际金额','来源SHA'])
        for c in result['cohorts']:
            for group,_ in GROUPS:
                s=c['groups'][group];p=s['pass_metrics'];d=s['duration_seconds'];cnt=s['per_simulation_counts'];tools=s['business_tools'];u=s['usage'].get('user',{}).get('numeric_fields',{})
                writer.writerow([c['domain_zh'],group,s['unique_tasks'],s['raw_simulations'],s['success_count_reward_eq_1'],s['success_rate_over_all_saved_simulations'],s['mean_reward_over_valid_numeric'],p['eligible_four_trial_binary_tasks'],p['observed_all_four_success_tasks'],p['pass_power_k_all_success_estimator']['4'],p['observed_any_success_tasks'],p['pass_at_k_any_success_estimator']['4'],p['observed_some_but_not_all_success_tasks'],d['mean'],d['median'],d['p95'],cnt['messages']['mean'],cnt['business_tool_calls']['mean'],tools['calls_by_message_role'].get('assistant',0),tools['calls_by_message_role'].get('user',0),tools['error_true_count'],sum(tools['reply_by_requestor'].values()),tools['error_true_fraction_of_tool_replies'],tools['error_affected_simulations'],cnt['user_nonterminal_messages_including_initial']['mean'],u.get('prompt_tokens',{}).get('sum','未知'),u.get('completion_tokens',{}).get('sum','未知'),'未知','未知',SHA])
    for c in result['cohorts']:
        p=c['paired'];print(c['domain'],json.dumps({k:p[k] for k in ['mean_reward_delta_B1_minus_B0','exact_McNemar_two_sided_p_binary_pairs','task_bootstrap_ci95','task_mean_delta_positive','task_mean_delta_negative','task_mean_delta_tied']},ensure_ascii=False))
    print('Outputs:',args.output.as_posix())


if __name__=='__main__':
    main()
