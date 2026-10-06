#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
parse_contract.py - 提取合同文本（PDF/Word/TXT）+ 段落定位

输入：合同文件路径（.pdf / .docx / .txt）
输出：JSON 结构（段落列表 + 元数据）

依赖：
- officecli（docx 解析）
- textin-xparse MCP（PDF/扫描件）
- 纯文本直接读取
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
    """获取 officecli 可执行文件路径（环境变量优先，其次 Windows 常见安装位置，最后 PATH）"""
    candidates = [
        os.environ.get("OFFICECLI_PATH"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "OfficeCLI", "officecli.exe"),
        "/c/Program Files/OfficeCLI/officecli.exe",
        "officecli",  # PATH 中
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
        if c == "officecli":
            # 尝试 which
            try:
                r = subprocess.run(["which", "officecli"], capture_output=True, text=True)
                if r.returncode == 0:
                    return r.stdout.strip()
            except Exception:
                pass
    return None


def parse_docx(file_path: str) -> dict:
    """解析 docx 文件，返回段落列表"""
    cli = get_officecli_path()
    if not cli:
        raise RuntimeError("officecli 未安装或不在 PATH 中")

    # 1. 获取纯文本
    result = subprocess.run(
        [cli, "view", file_path, "text", "--json"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"officecli view text 失败: {result.stderr}")

    # 解析输出（officecli 返回 JSON 或文本，取决于版本）
    try:
        text_data = json.loads(result.stdout)
        # 提取段落
        if isinstance(text_data, dict) and "paragraphs" in text_data:
            paragraphs = text_data["paragraphs"]
        elif isinstance(text_data, list):
            paragraphs = text_data
        else:
            paragraphs = [str(text_data)]
    except json.JSONDecodeError:
        # 纯文本回退
        paragraphs = [{"index": i + 1, "text": line.strip()}
                      for i, line in enumerate(result.stdout.split("\n"))
                      if line.strip()]

    # 2. 提取元数据（可选）
    meta_result = subprocess.run(
        [cli, "view", file_path, "stats", "--json"],
        capture_output=True, text=True
    )
    metadata = {}
    if meta_result.returncode == 0:
        try:
            metadata = json.loads(meta_result.stdout)
        except json.JSONDecodeError:
            metadata = {"raw": meta_result.stdout.strip()}

    return {
        "file_type": "docx",
        "file_path": file_path,
        "paragraph_count": len(paragraphs),
        "paragraphs": paragraphs,
        "metadata": metadata,
    }


def parse_txt(file_path: str) -> dict:
    """解析纯文本文件"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 按段落切分（空行）
    raw_paragraphs = re.split(r"\n\s*\n", content)
    paragraphs = []
    for i, text in enumerate(raw_paragraphs):
        text = text.strip()
        if text:
            paragraphs.append({"index": i + 1, "text": text})

    return {
        "file_type": "txt",
        "file_path": file_path,
        "paragraph_count": len(paragraphs),
        "paragraphs": paragraphs,
        "metadata": {"char_count": len(content)},
    }


def parse_pdf(file_path: str) -> dict:
    """
    解析 PDF 文件（需要 textin-xparse MCP）
    如 MCP 不可用，回退到提示用户先转换
    """
    # 提示：本 Skill 默认假设 textin-xparse 已连接
    # 如未连接，建议用户先用本地工具转换 PDF→docx

    return {
        "file_type": "pdf",
        "file_path": file_path,
        "paragraph_count": 0,
        "paragraphs": [],
        "metadata": {
            "note": "PDF 解析需要 textin-xparse MCP 支持。请先将 PDF 转换为 docx 后再处理。",
            "fallback_command": f"# 方案 1：使用 textin-xparse MCP（推荐）\n# 方案 2：先转换为 docx\n  officecli create temp.docx\n  # 然后用其他 PDF 转 Word 工具填充内容"
        },
    }


def detect_clause_pattern(paragraphs: list) -> list:
    """为每个段落识别条款编号（如"第一条"、"第 X 条"、"第 X 款"等）"""
    clause_patterns = [
        re.compile(r"^第[一二三四五六七八九十百千零〇\d]+条"),
        re.compile(r"^第[一二三四五六七八九十百千零〇\d]+款"),
        re.compile(r"^\d+\."),  # 1.1 条款
        re.compile(r"^\([一二三四五六七八九十\d]+\)"),  # (一)
    ]

    for p in paragraphs:
        text = p.get("text", "").strip()
        matched = None
        for pattern in clause_patterns:
            m = pattern.match(text)
            if m:
                matched = m.group(0)
                break
        p["clause_pattern"] = matched
        p["is_clause_header"] = bool(matched)
    return paragraphs


# ---------------------- 主函数 ----------------------

def main():
    parser = argparse.ArgumentParser(
        description="合同文本提取工具（PDF/Word/TXT → JSON 结构）"
    )
    parser.add_argument("--input", required=True, help="合同文件路径")
    parser.add_argument("--output", help="输出 JSON 文件路径（默认打印到 stdout）")
    parser.add_argument("--detect-clauses", action="store_true",
                        help="自动识别条款编号")

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"错误：文件不存在 {args.input}", file=sys.stderr)
        sys.exit(1)

    suffix = input_path.suffix.lower()

    # 根据扩展名分发
    if suffix == ".docx":
        result = parse_docx(str(input_path))
    elif suffix == ".txt":
        result = parse_txt(str(input_path))
    elif suffix == ".pdf":
        result = parse_pdf(str(input_path))
    else:
        print(f"错误：不支持的文件类型 {suffix}（仅支持 .docx / .pdf / .txt）",
              file=sys.stderr)
        sys.exit(1)

    # 条款编号识别
    if args.detect_clauses and result["paragraphs"]:
        result["paragraphs"] = detect_clause_pattern(result["paragraphs"])

    # 输出
    output_json = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"已保存到 {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()