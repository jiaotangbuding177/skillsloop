#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
validate.py - 输出前自检脚本

校验项：
1. 批注作者是否为 "admin"
2. 批注分布合理性（高风险 < 5 条，高+中 < 15 条）
3. 高风险条款是否都带法条引用
4. 是否有空批注 / 重复批注

输入：带批注的 docx 文件
输出：校验报告（通过/失败 + 问题清单）
"""

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path


# ---------------------- 工具函数 ----------------------

def get_officecli_path() -> str:
    """获取 officecli 可执行文件路径（环境变量优先，其次 Windows 常见安装位置，最后 PATH）"""
    candidates = [
        os.environ.get("OFFICECLI_PATH"),
        # Windows 常见安装位置（%LOCALAPPDATA%\OfficeCLI）
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "OfficeCLI", "officecli.exe"),
        # 兜底 PATH
        "officecli.exe",
        "officecli",
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return "officecli"  # 兜底


def extract_comments(docx_file: str) -> list:
    """从 docx 中提取所有批注"""
    cli = get_officecli_path()

    # 尝试用 officecli 提取
    try:
        result = subprocess.run(
            [cli, "view", docx_file, "annotated", "--json"],
            capture_output=True, text=True, timeout=60
        )

        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                # 适配不同 officecli 版本的输出结构
                if isinstance(data, dict) and "comments" in data:
                    return data["comments"]
                elif isinstance(data, list):
                    return data
            except json.JSONDecodeError:
                pass

        # 回退：用 marks
        result = subprocess.run(
            [cli, "get-marks", docx_file, "--json"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                pass
    except Exception as e:
        print(f"提取批注失败：{e}", file=sys.stderr)

    # 兜底：用 zipfile + xml 解析
    return extract_comments_xml(docx_file)


def extract_comments_xml(docx_file: str) -> list:
    """直接解析 docx 内部的 comments.xml"""
    import zipfile
    import xml.etree.ElementTree as ET

    comments = []
    try:
        with zipfile.ZipFile(docx_file, "r") as z:
            if "word/comments.xml" not in z.namelist():
                return []

            with z.open("word/comments.xml") as f:
                tree = ET.parse(f)
                root = tree.getroot()

                ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

                for i, comment_elem in enumerate(root.findall("w:comment", ns)):
                    author = comment_elem.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}author", "")
                    initials = comment_elem.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}initials", "")
                    date = comment_elem.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}date", "")

                    # 提取批注文本
                    text_parts = []
                    for t in comment_elem.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"):
                        if t.text:
                            text_parts.append(t.text)
                    text = "".join(text_parts)

                    # 识别风险等级
                    level = "medium"
                    if "【高风险】" in text:
                        level = "high"
                    elif "【低风险】" in text:
                        level = "low"
                    # 风险等级 → 批注类型映射（与 annotate_docx.py COMMENT_TYPE_CONFIG 键一致）
                    LEVEL_TYPE_MAP = {"high": "risk_high", "medium": "risk_medium", "low": "risk_low"}
                    comment_type = LEVEL_TYPE_MAP.get(level, level)  # 默认兼容
                    if "【金额异常】" in text:
                        comment_type = "amount_anomaly"
                    elif "【条款冲突】" in text:
                        comment_type = "clause_conflict"
                    elif "【合规】" in text:
                        comment_type = "compliance_fail"
                    elif "【文本瑕疵】" in text:
                        comment_type = "text_quality"  # 🆕 v2.0
                        # 文本瑕疵不计入法律风险等级 → level 改为 text_quality
                        level = "text_quality"

                    comments.append({
                        "index": i + 1,
                        "author": author,
                        "initials": initials,
                        "date": date,
                        "level": level,
                        "type": comment_type,
                        "text": text,
                    })
    except Exception as e:
        print(f"XML 解析失败：{e}", file=sys.stderr)

    return comments


# ---------------------- 校验规则 ----------------------

def check_authors(comments: list) -> dict:
    """检查批注作者"""
    if not comments:
        return {
            "name": "批注作者",
            "passed": False,
            "details": "文档中无批注",
        }

    expected_author = "admin"
    wrong_authors = [c for c in comments if c.get("author") != expected_author]

    return {
        "name": "批注作者",
        "passed": len(wrong_authors) == 0,
        "details": f"{len(comments)} 条批注中，{len(wrong_authors)} 条作者不正确"
                  + (f"：{set(c['author'] for c in wrong_authors)}" if wrong_authors else "")
                  if wrong_authors else f"全部 {len(comments)} 条批注作者正确",
    }


def check_distribution(comments: list) -> dict:
    """检查风险等级分布合理性（🆕 v2.0：排除文本瑕疵，不计入法律风险）"""
    # 过滤文本瑕疵（不计入法律风险统计）
    risk_comments = [c for c in comments if c.get("type") != "text_quality"]
    tq_comments = [c for c in comments if c.get("type") == "text_quality"]

    levels = Counter(c.get("level", "medium") for c in risk_comments)

    high = levels.get("high", 0)
    medium = levels.get("medium", 0)
    low = levels.get("low", 0)
    total = high + medium + low
    tq_total = len(tq_comments)

    issues = []
    if high > 5:
        issues.append(f"高风险条款过多（{high} 条，建议 ≤5 条）")
    if high + medium > 15:
        issues.append(f"高+中风险条款过多（{high + medium} 条，建议 ≤15 条）")
    if total > 0 and high == total:
        issues.append("所有条款都是高风险，请复审标准")

    details = f"法律风险：{high} / {medium} / {low}（共 {total} 条）"
    if tq_total > 0:
        details += f"\n文本瑕疵：{tq_total} 条（不计入风险等级统计）"
    if issues:
        details += f"\n问题：{'; '.join(issues)}"

    return {
        "name": "风险等级分布",
        "passed": len(issues) == 0,
        "details": details,
    }


def check_high_risk_law_reference(comments: list) -> dict:
    """检查高风险条款是否带法条引用（🆕 v2.0：排除文本瑕疵）"""
    high_comments = [c for c in comments if c.get("level") == "high" and c.get("type") != "text_quality"]

    if not high_comments:
        return {
            "name": "高风险法条引用",
            "passed": True,
            "details": "无高风险条款，跳过校验",
        }

    # 检查法条引用模式
    law_patterns = [
        r"《[^》]+》第\s*\d+\s*条",  # 《XXX法》第 X 条
        r"最高人民法院",
        r"民法典",
        r"合同法",
        r"司法解释",
    ]

    missing = []
    for c in high_comments:
        text = c.get("text", "")
        has_law = any(re.search(p, text) for p in law_patterns)
        if not has_law:
            missing.append(c.get("index", "?"))

    return {
        "name": "高风险法条引用",
        "passed": len(missing) == 0,
        "details": f"{len(high_comments)} 条高风险中，{len(missing)} 条缺少法条引用"
                  + (f"（批注 #{missing}）" if missing else ""),
    }


def check_empty_duplicate(comments: list) -> dict:
    """检查空批注和重复批注"""
    empty = [c.get("index", "?") for c in comments if not c.get("text", "").strip()]

    # 重复检测（按文本前 100 字）
    seen = {}
    duplicates = []
    for c in comments:
        text = c.get("text", "").strip()[:100]
        if text in seen:
            duplicates.append(f"#{c.get('index', '?')} 与 #{seen[text]}")
        else:
            seen[text] = c.get("index", "?")

    issues = []
    if empty:
        issues.append(f"{len(empty)} 条空批注（{empty}）")
    if duplicates:
        issues.append(f"{len(duplicates)} 组重复批注（{duplicates}）")

    return {
        "name": "空批注与重复",
        "passed": len(issues) == 0,
        "details": "; ".join(issues) if issues else "未发现空批注或重复",
    }


def check_fyopen_law_source(comments: list) -> dict:
    """检查检索时点标注（建议性，不强制失败）"""
    if not comments:
        return {
            "name": "检索时点（建议）",
            "passed": True,
            "details": "无批注，跳过",
            "warning": False,
        }

    # 检索时点模式
    date_pattern = re.compile(r"检索时点[：:]\s*(\d{4}-\d{2}-\d{2})")

    # 🆕 v2.0：排除文本瑕疵
    high_comments = [c for c in comments if c.get("level") == "high" and c.get("type") != "text_quality"]
    missing_date = []

    for c in high_comments:
        if not date_pattern.search(c.get("text", "")):
            missing_date.append(c.get("index", "?"))

    return {
        "name": "检索时点标注（建议）",
        "passed": True,  # 不强制失败
        "warning": len(missing_date) > 0,
        "details": f"{len(high_comments)} 条高风险中，{len(missing_date)} 条未标检索时点"
                  + (f"（批注 #{missing_date}）" if missing_date else ""),
    }


def check_amount_anomaly_integrity(comments: list) -> dict:
    """校验金额异常批注的完整性（新增）"""
    amount_comments = [c for c in comments if "【金额异常】" in c.get("text", "")]

    if not amount_comments:
        return {
            "name": "金额异常完整性",
            "passed": True,
            "details": "无金额异常批注，跳过",
        }

    issues = []

    for c in amount_comments:
        text = c.get("text", "")
        idx = c.get("index", "?")
        # 必须含异常类型 + 当前值 + 触发阈值 + 修改建议
        if "异常类型：" not in text:
            issues.append(f"#{idx} 缺异常类型")
        if "当前值：" not in text:
            issues.append(f"#{idx} 缺当前值")
        if "触发阈值：" not in text:
            issues.append(f"#{idx} 缺触发阈值")
        if "修改建议：" not in text:
            issues.append(f"#{idx} 缺修改建议")

    return {
        "name": "金额异常完整性",
        "passed": len(issues) == 0,
        "details": f"{len(amount_comments)} 条金额异常批注中，{len(issues)} 条不完整"
                  + (f"\n问题：{'; '.join(issues)}" if issues else ""),
    }


def check_clause_conflict_bidirectional(comments: list) -> dict:
    """校验条款冲突批注是否双侧插入（新增）"""
    conflict_comments = [c for c in comments if "【条款冲突】" in c.get("text", "")]

    if not conflict_comments:
        return {
            "name": "条款冲突双向批注",
            "passed": True,
            "details": "无条款冲突批注，跳过",
        }

    # 提取所有 conflict_id
    conflict_id_pattern = re.compile(r"冲突ID[：:]\s*([A-Z]+-\d+)")
    seen_ids = set()

    for c in conflict_comments:
        text = c.get("text", "")
        m = conflict_id_pattern.search(text)
        if m:
            seen_ids.add(m.group(1))

    # 检查每个冲突是否成对（每个 conflict_id 应出现 2 次，即双侧）
    id_counts = Counter()
    for c in conflict_comments:
        text = c.get("text", "")
        m = conflict_id_pattern.search(text)
        if m:
            id_counts[m.group(1)] += 1

    # 不成对
    unpaired = [cid for cid, count in id_counts.items() if count < 2]

    return {
        "name": "条款冲突双向批注",
        "passed": len(unpaired) == 0,
        "details": f"{len(conflict_comments)} 条冲突批注涉及 {len(id_counts)} 个冲突ID；{len(unpaired)} 个未双侧插入"
                  + (f"（{unpaired}）" if unpaired else ""),
    }


def check_compliance_law_basis(comments: list) -> dict:
    """校验合规问题批注是否带法条依据（新增）"""
    compliance_comments = [c for c in comments if "【合规】" in c.get("text", "")]

    if not compliance_comments:
        return {
            "name": "合规法条依据",
            "passed": True,
            "details": "无合规问题批注，跳过",
        }

    law_patterns = [
        r"《[^》]+》",
        r"法",
        r"规定",
        r"司法解释",
    ]

    missing = []
    for c in compliance_comments:
        text = c.get("text", "")
        idx = c.get("index", "?")
        has_law = any(re.search(p, text) for p in law_patterns)
        if not has_law:
            missing.append(idx)

    return {
        "name": "合规法条依据",
        "passed": len(missing) == 0,
        "details": f"{len(compliance_comments)} 条合规批注中，{len(missing)} 条缺法条依据"
                  + (f"（批注 #{missing}）" if missing else ""),
    }


def check_text_quality_integrity(comments: list) -> dict:
    """🆕 v2.0 · 校验文本瑕疵批注的完整性（不计入法律风险统计）"""
    tq_comments = [c for c in comments if "【文本瑕疵】" in c.get("text", "")]

    if not tq_comments:
        return {
            "name": "文本瑕疵完整性",
            "passed": True,
            "details": "无文本瑕疵批注，跳过",
        }

    issues = []
    categories = Counter()

    for c in tq_comments:
        text = c.get("text", "")
        idx = c.get("index", "?")
        # 必须含文本类别 + 子类 + 问题描述 + 修改建议
        if "文本类别：" not in text:
            issues.append(f"#{idx} 缺文本类别")
        if "问题描述：" not in text:
            issues.append(f"#{idx} 缺问题描述")
        if "修改建议：" not in text:
            issues.append(f"#{idx} 缺修改建议")

        # 统计子类（XML 存储的批注文本无换行，用"问题"或"修改"作为字段分隔符）
        m = re.search(r"文本类别[：:](.+)", text)
        if m:
            segment = m.group(1)
            # 提取主类：第一个 / 之前
            cat_match = re.match(r"\s*([^/\s]+)", segment)
            cat = cat_match.group(1).strip() if cat_match else "未分类"
            # 提取子类：第一个 / 之后到"问题"或"修改"之前
            sub_match = re.search(r"/\s*(.+?)(?=问题|修改|$)", segment)
            sub = sub_match.group(1).strip() if sub_match else ""
            if sub:
                categories[f"{cat}/{sub}"] += 1
            else:
                categories[cat] += 1
        else:
            categories["未分类"] += 1

    # 输出统计（cat_summary）
    cat_summary = "\n".join([f"  · {k}: {v}" for k, v in categories.most_common()])

    return {
        "name": "文本瑕疵完整性",
        "passed": len(issues) == 0,
        "details": f"{len(tq_comments)} 条文本瑕疵中，{len(issues)} 条不完整"
                  + (f"\n问题：{'; '.join(issues)}" if issues else "")
                  + f"\n分类统计：\n{cat_summary}",
        "warning": len(issues) > 0,  # 不强制失败
    }


def check_text_quality_isolation(comments: list) -> dict:
    """🆕 v2.0 · 校验文本瑕疵不混入法律风险等级统计"""
    # 找出 level=high/medium/low 但 type=text_quality 的批注
    mixed = []
    for c in comments:
        if c.get("type") == "text_quality" and c.get("level") in ("high", "medium", "low"):
            # 这种情况可能由于 extract_comments_xml 的识别顺序导致
            # 这里做兜底校验：如果同时识别为 text_quality 且 level 是 risk 等级 → 警告
            mixed.append(f"#{c.get('index', '?')} (type={c.get('type')}, level={c.get('level')})")

    return {
        "name": "文本瑕疵与法律风险隔离",
        "passed": len(mixed) == 0,
        "details": f"{len(mixed)} 条文本瑕疵被错误归类为法律风险等级"
                  + (f"\n{mixed}" if mixed else ""),
        "warning": len(mixed) > 0,
    }


# ---------------------- 主校验流程 ----------------------

def validate(docx_file: str) -> dict:
    """执行完整校验流程"""
    if not Path(docx_file).exists():
        return {"success": False, "error": f"文件不存在 {docx_file}"}

    print(f"开始校验：{docx_file}\n")

    # 1. 提取批注
    print("[1/10] 提取批注...")
    comments = extract_comments(docx_file)
    print(f"  找到 {len(comments)} 条批注")

    # 2. 执行各项校验
    print("[2/10] 校验批注作者...")
    r_authors = check_authors(comments)

    print("[3/10] 校验风险等级分布（不含文本瑕疵）...")
    r_distribution = check_distribution(comments)

    print("[4/10] 校验高风险法条引用...")
    r_law = check_high_risk_law_reference(comments)

    print("[5/10] 校验空批注与重复...")
    r_empty = check_empty_duplicate(comments)

    # 建议性校验
    r_date = check_fyopen_law_source(comments)

    # 专项批注校验（v1.0 新增）
    print("[6/10] 校验金额异常完整性...")
    r_amount = check_amount_anomaly_integrity(comments)

    print("[7/10] 校验条款冲突双向批注...")
    r_conflict = check_clause_conflict_bidirectional(comments)

    print("[8/10] 校验合规法条依据...")
    r_compliance = check_compliance_law_basis(comments)

    # 🆕 v2.0 文本瑕疵校验
    print("[9/10] 校验文本瑕疵完整性...")
    r_tq_integrity = check_text_quality_integrity(comments)

    print("[10/10] 校验文本瑕疵与法律风险隔离...")
    r_tq_isolation = check_text_quality_isolation(comments)

    # 汇总
    results = [r_authors, r_distribution, r_law, r_empty, r_date,
               r_amount, r_conflict, r_compliance, r_tq_integrity, r_tq_isolation]
    passed = sum(1 for r in results if r["passed"] and not r.get("warning"))
    failed = sum(1 for r in results if not r["passed"])
    warnings = sum(1 for r in results if r.get("warning") and r["passed"])

    # 输出报告
    print("\n" + "=" * 60)
    print("校验报告")
    print("=" * 60)

    for r in results:
        status = "✅ PASS" if r["passed"] and not r.get("warning") else (
            "⚠️ WARN" if r.get("warning") else "❌ FAIL"
        )
        print(f"\n{status} · {r['name']}")
        print(f"  {r['details']}")

    print("\n" + "=" * 60)
    print(f"汇总：通过 {passed} / 警告 {warnings} / 失败 {failed}")
    print("=" * 60)

    return {
        "file": docx_file,
        "comments_count": len(comments),
        "passed": passed,
        "warnings": warnings,
        "failed": failed,
        "results": results,
        "overall_passed": failed == 0,
    }


def main():
    parser = argparse.ArgumentParser(
        description="合同审查输出文档自检工具"
    )
    parser.add_argument("--file", required=True, help="待校验的 docx 文件路径")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式报告")

    args = parser.parse_args()

    report = validate(args.file)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    sys.exit(0 if report.get("overall_passed") else 1)


if __name__ == "__main__":
    main()