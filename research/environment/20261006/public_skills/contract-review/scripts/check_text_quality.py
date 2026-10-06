#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
check_text_quality.py - 合同文本质量扫描

输入：合同文本
输出：文本质量问题清单（标点 / 排版 / 错别字 / 语义歧义）

可独立调用：
    python check_text_quality.py --input "D:/合同/xxx.docx"
    python check_text_quality.py --text "..." --json

依赖：officecli（docx 解析）
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


# ---------------------- 工具函数 ----------------------

def get_officecli_path() -> str:
    """获取 officecli 路径（环境变量优先，其次 Windows 常见安装位置，最后 PATH）"""
    candidates = [
        os.environ.get("OFFICECLI_PATH"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "OfficeCLI", "officecli.exe"),
        "officecli",
    ]
    for c in candidates:
        if c and Path(c).exists():
            return c
    return "officecli"


def extract_text_from_docx(docx_path: str) -> str:
    """用 officecli 提取 docx 文本"""
    cli = get_officecli_path()
    try:
        result = subprocess.run(
            [cli, "view", docx_path, "text"],
            capture_output=True, text=True, encoding="utf-8", timeout=60
        )
        lines = []
        for line in result.stdout.splitlines():
            m = re.match(r'\[\/body/p\[@paraId=[^\]]+\]\]\s*(.*)', line)
            if m:
                lines.append(m.group(1))
            elif line.strip():
                lines.append(line)
        return "\n".join(lines)
    except Exception as e:
        print(f"[ERROR] 提取 docx 文本失败：{e}", file=sys.stderr)
        return ""


def split_paragraphs(text: str) -> list:
    """按行切分段落"""
    return [line for line in text.splitlines() if line.strip()]


def find_paragraph_index(paragraphs: list, pattern: str) -> int:
    """找到第一个匹配段落的索引（0-based）"""
    for i, p in enumerate(paragraphs):
        if re.search(pattern, p):
            return i
    return -1


# ---------------------- 检测规则 ----------------------

def check_punctuation(paragraphs: list) -> list:
    """检测标点符号问题"""
    issues = []

    # 1. 全角/半角混用（中文之间出现半角逗号）
    for i, p in enumerate(paragraphs):
        # 中文字符 + 半角逗号 + 中文字符
        matches = re.finditer(r'([一-龥]),([一-龥])', p)
        for m in matches:
            issues.append({
                "category": "punctuation",
                "sub_category": "全角/半角混用",
                "level": "medium",
                "para_index": i + 1,
                "original_text": m.group(0),
                "context": p[:80] + "..." if len(p) > 80 else p,
                "problem": "中文之间使用半角逗号，应改为全角逗号",
                "suggestion": f"将 '{m.group(0)}' 改为 '{m.group(1)}，{m.group(2)}'",
            })

        # 中文字符 + 半角句号
        for m in re.finditer(r'([一-龥])\.([一-龥])', p):
            issues.append({
                "category": "punctuation",
                "sub_category": "全角/半角混用",
                "level": "medium",
                "para_index": i + 1,
                "original_text": m.group(0),
                "context": p[:80] + "..." if len(p) > 80 else p,
                "problem": "中文之间使用半角句号，应改为全角句号",
                "suggestion": f"将 '{m.group(0)}' 改为 '{m.group(1)}。{m.group(2)}'",
            })

    # 2. 顿号 vs 逗号误用（中文括号后紧跟半角逗号）
    for i, p in enumerate(paragraphs):
        for m in re.finditer(r'）,\s*([一-龥])', p):
            issues.append({
                "category": "punctuation",
                "sub_category": "顿号 vs 逗号",
                "level": "low",
                "para_index": i + 1,
                "original_text": m.group(0),
                "problem": "中文括号后并列项之间应用顿号'、'而非逗号",
                "suggestion": f"将 ',{m.group(1)}' 改为 '、{m.group(1)}'",
            })

    return issues


def check_typos(paragraphs: list) -> list:
    """检测错别字"""
    issues = []

    # 1. 主谓不一致：甲方已支付的甲方货款 / 乙方已收取的乙方货款
    for i, p in enumerate(paragraphs):
        for pattern, fixed in [
            (r'甲方已支付的甲方货款', '甲方已向乙方支付的货款'),
            (r'乙方已收取的乙方货款', '乙方已收取的甲方货款'),
            (r'以甲方已支付的货款为上限', '以甲方已向乙方支付的货款为上限'),
        ]:
            if re.search(pattern, p):
                issues.append({
                    "category": "typo",
                    "sub_category": "主谓不一致",
                    "level": "high",
                    "para_index": i + 1,
                    "original_text": pattern,
                    "context": p[:80] + "..." if len(p) > 80 else p,
                    "problem": "主语'甲方'不能向'甲方'付款，条款无效或解释争议",
                    "suggestion": f"改为 '{fixed}'",
                })

    # 2. 百分比错位：0.3%/日 与 万分之三/日 出现在同一合同
    has_pct = any("0.3%" in p or "万分之三" in p for p in paragraphs)
    if has_pct:
        # 检查两种都出现
        has_03_pct = any("0.3%/日" in p or "0.3% / 日" in p for p in paragraphs)
        has_wfz3 = any("万分之三" in p for p in paragraphs)
        if has_03_pct and has_wfz3:
            issues.append({
                "category": "typo",
                "sub_category": "百分比/千分比错位",
                "level": "high",
                "para_index": -1,  # 多段落
                "original_text": "0.3%/日 vs 万分之三/日",
                "problem": "0.3% = 0.003，万分之三 = 0.0003，差异 10 倍；同一合同混用易引发解释争议",
                "suggestion": "统一为 '万分之三/日' 或 '0.03%/日'",
            })

    return issues


def check_semantic_ambiguity(paragraphs: list) -> list:
    """检测语义歧义"""
    issues = []

    # 量词模糊词列表（出现频次过高则提示）
    ambiguous_words = [
        ("合理的", "主观判断，缺乏客观标准"),
        ("必要的", "主观判断，应列举具体情形"),
        ("适当的", "主观判断，应列举具体情形"),
        ("严重的", "标准不清，应量化阈值"),
        ("重大的", "标准不清，应量化阈值"),
        ("及时的", "时间不明，应明确具体期限"),
        ("尽快", "时间模糊，应明确'X 个工作日内'"),
    ]

    # 统计频次
    word_count = {}
    for w, _ in ambiguous_words:
        word_count[w] = sum(1 for p in paragraphs if w in p)

    # 高频歧义词（≥3 次）单独标记
    for w, reason in ambiguous_words:
        if word_count.get(w, 0) >= 3:
            idx = find_paragraph_index(paragraphs, re.escape(w))
            issues.append({
                "category": "semantic_ambiguity",
                "sub_category": "量词模糊",
                "level": "medium",
                "para_index": idx + 1 if idx >= 0 else -1,
                "original_text": w,
                "problem": f"全文出现 {word_count[w]} 次「{w}」：{reason}",
                "suggestion": f"建议替换为具体可执行的标准（如'X 个工作日内'、列举具体情形）",
            })

    # 范围模糊："等"
    if any("等" in p for p in paragraphs):
        # 检查"等"是否作为兜底使用（前面有"包括但不限于"或"如下"）
        for i, p in enumerate(paragraphs):
            if re.search(r'包括但不限于[^，。]*等', p) or re.search(r'如下[^，。]*等', p):
                idx = p.find("等")
                issues.append({
                    "category": "semantic_ambiguity",
                    "sub_category": "范围模糊",
                    "level": "low",
                    "para_index": i + 1,
                    "original_text": p[max(0, idx - 20):idx + 5] + "...",
                    "problem": "'等'的范围模糊——前面列举到什么程度算'等'的边界？",
                    "suggestion": "明确'等'的范围（如'等前述同类项'）或删除'等'",
                })

    return issues


def check_format(paragraphs: list) -> list:
    """检测排版格式问题（基于规则）"""
    issues = []

    # 1. 编号层级混乱
    patterns = {
        "1.": r"^\s*\d+\.\s",
        "(1)": r"^\s*\(\d+\)\s",
        "a)": r"^\s*[a-z]\)\s",
        "①": r"^\s*[①②③④⑤⑥⑦⑧⑨⑩]\s",
    }
    used_patterns = set()
    for p in paragraphs:
        for name, pat in patterns.items():
            if re.match(pat, p):
                used_patterns.add(name)
    if len(used_patterns) >= 3:
        issues.append({
            "category": "format",
            "sub_category": "编号层级混乱",
            "level": "low",
            "para_index": -1,
            "original_text": f"使用了 {len(used_patterns)} 套编号：{', '.join(used_patterns)}",
            "problem": "全文混用多套编号体系（如 1. / (1) / a) / ①），可读性差",
            "suggestion": "统一为一套编号体系（推荐：第一条 → （一） → 1. → （1））",
        })

    return issues


# ---------------------- 主函数 ----------------------

def check_text_quality(text: str) -> dict:
    """主扫描函数"""
    paragraphs = split_paragraphs(text)
    all_issues = []
    all_issues.extend(check_punctuation(paragraphs))
    all_issues.extend(check_typos(paragraphs))
    all_issues.extend(check_semantic_ambiguity(paragraphs))
    all_issues.extend(check_format(paragraphs))

    # 按 level 排序（高 → 中 → 低）
    level_order = {"high": 0, "medium": 1, "low": 2}
    all_issues.sort(key=lambda x: level_order.get(x["level"], 99))

    # 汇总
    summary = {
        "total_issues": len(all_issues),
        "high": sum(1 for i in all_issues if i["level"] == "high"),
        "medium": sum(1 for i in all_issues if i["level"] == "medium"),
        "low": sum(1 for i in all_issues if i["level"] == "low"),
        "by_category": {},
    }
    for issue in all_issues:
        cat = issue["category"]
        summary["by_category"][cat] = summary["by_category"].get(cat, 0) + 1

    return {
        "summary": summary,
        "issues": all_issues,
    }


# ---------------------- CLI ----------------------

def main():
    parser = argparse.ArgumentParser(description="合同文本质量扫描")
    parser.add_argument("--input", help="docx 文件路径")
    parser.add_argument("--text", help="纯文本输入")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    args = parser.parse_args()

    if args.input:
        text = extract_text_from_docx(args.input)
        if not text:
            print(f"[ERROR] 无法读取 {args.input}", file=sys.stderr)
            sys.exit(1)
    elif args.text:
        text = args.text
    else:
        parser.print_help()
        sys.exit(1)

    result = check_text_quality(text)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        s = result["summary"]
        print(f"文本质量扫描结果：")
        print(f"  总问题数：{s['total_issues']}")
        print(f"    高风险：{s['high']}")
        print(f"    中风险：{s['medium']}")
        print(f"    低风险：{s['low']}")
        print(f"  按类别：{s['by_category']}")
        print(f"\n详细问题：")
        for i, issue in enumerate(result["issues"], 1):
            print(f"\n[{i}] [{issue['level'].upper()}] {issue['category']} / {issue['sub_category']}")
            print(f"    段落 #{issue['para_index']}")
            print(f"    原文：{issue['original_text']}")
            print(f"    问题：{issue['problem']}")
            print(f"    建议：{issue['suggestion']}")


if __name__ == "__main__":
    main()