#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
annotate_docx.py - 批量插入 Word 原生批注

输入：原合同 docx + 审查意见 JSON
输出：带原生批注的 docx

依赖：
- officecli（add comment 能力）

支持 7 类批注类型：
1. risk_high / risk_medium / risk_low（原有）
2. amount_anomaly（金额异常 - 新增）
3. clause_conflict（条款冲突 - 新增）
4. compliance_fail（合规问题 - 新增）
5. text_quality（文本瑕疵 - v2.0 新增）

审查意见 JSON 结构：
{
  "comments": [
    {
      "paragraph_index": 3,
      "type": "risk_high",   # 7 类之一
      "level": "high",        # 兼容旧字段
      "title": "...",
      "essence": "...",
      "law": "《民法典》第 585 条",
      "loss_estimate": "...",
      "suggestion": "...",
      "modify_text": "...",
      "search_date": "2026-08-06"
    }
  ]
}
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


# ---------------------- 批注类型配置（7 类） ----------------------

COMMENT_TYPE_CONFIG = {
    # 原有 3 类风险等级
    "risk_high": {
        "prefix": "【高风险】",
        "color": "#cf222e",
        "category": "risk",
        "required_fields": ["title", "essence", "law", "loss_estimate", "suggestion", "search_date"],
    },
    "risk_medium": {
        "prefix": "【中风险】",
        "color": "#9a6700",
        "category": "risk",
        "required_fields": ["title", "essence", "suggestion"],
        "recommended_fields": ["law"],
    },
    "risk_low": {
        "prefix": "【低风险】",
        "color": "#d0d7de",
        "category": "risk",
        "required_fields": ["title", "suggestion"],
    },
    # 新增 3 类专项
    "amount_anomaly": {
        "prefix": "【金额异常】",
        "color": "#bf8700",
        "category": "amount",
        "required_fields": ["title", "anomaly_type", "value", "threshold", "suggestion"],
        "recommended_fields": ["law"],
        "extra_format": "异常类型：{anomaly_type}\n当前值：{value}\n触发阈值：{threshold}\n法条依据：{law}\n修改建议：{suggestion}\n检索时点：{search_date}",
    },
    "clause_conflict": {
        "prefix": "【条款冲突】",
        "color": "#8250df",
        "category": "conflict",
        "required_fields": ["title", "conflict_id", "other_clause_no", "conflict_type", "suggestion"],
        "recommended_fields": ["law"],
        "extra_format": "冲突ID：{conflict_id}\n冲突类型：{conflict_type}\n对方条款：第 {other_clause_no} 条\n冲突描述：{essence}\n法条依据：{law}\n修改建议：{suggestion}",
    },
    "compliance_fail": {
        "prefix": "【合规】",
        "color": "#cf222e",
        "category": "compliance",
        "required_fields": ["title", "compliance_domain", "law", "suggestion"],
        "recommended_fields": ["severity"],
        "extra_format": "合规领域：{compliance_domain}\n严重程度：{severity}\n法律依据：{law}\n问题描述：{essence}\n修改建议：{suggestion}",
    },
    # 🆕 文本瑕疵（v2.0 新增，不计入法律风险统计）
    "text_quality": {
        "prefix": "【文本瑕疵】",
        "color": "#8c959f",
        "category": "text_quality",
        "required_fields": ["title", "text_category", "sub_category", "suggestion"],
        "recommended_fields": ["original_text"],
        "extra_format": "文本类别：{text_category} / {sub_category}\n问题原文：{original_text}\n问题描述：{essence}\n修改建议：{suggestion}\n\n（注：文本瑕疵为文本质量维度，不构成法律风险等级，仅作严谨性提示）",
    },
}

# 兼容旧字段映射（向后兼容）
LEGACY_LEVEL_MAP = {
    "high": "risk_high",
    "medium": "risk_medium",
    "low": "risk_low",
}

# 保留旧 LEVEL_CONFIG 别名（向后兼容）
LEVEL_CONFIG = COMMENT_TYPE_CONFIG


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
    return "officecli"  # 兜底交给 subprocess 报错


def format_comment_text(comment: dict) -> str:
    """根据批注类型格式化批注文本（支持 7 类）"""
    # 解析批注类型：优先使用 type，其次兼容旧的 level
    comment_type = comment.get("type") or comment.get("level", "medium").lower()
    # 向后兼容映射
    if comment_type in LEGACY_LEVEL_MAP:
        comment_type = LEGACY_LEVEL_MAP[comment_type]
    # 取配置
    config = COMMENT_TYPE_CONFIG.get(comment_type, COMMENT_TYPE_CONFIG["risk_medium"])

    # 如有 extra_format，使用模板填充（新增 3 类批注）
    if config.get("extra_format"):
        return _format_with_template(comment, config)

    # 否则使用默认拼接（原有 3 类风险等级）
    parts = [f'{config["prefix"]}第 {comment.get("clause_no", "?")} 条 - {comment.get("title", "未命名")}']

    # 问题本质
    if comment.get("essence"):
        parts.append(f"\n问题本质：{comment['essence']}")

    # 法条依据
    if comment.get("law"):
        parts.append(f"\n法条依据：{comment['law']}")

    # 量化损失（高风险必带）
    if comment.get("loss_estimate"):
        parts.append(f"\n损失预估：{comment['loss_estimate']}")

    # 修改建议
    if comment.get("suggestion"):
        parts.append(f"\n修改建议：{comment['suggestion']}")

    # 修改后文本（如提供）
    if comment.get("modify_text"):
        parts.append(f"\n建议修改为：\n「{comment['modify_text']}」")

    # 检索时点
    if comment.get("search_date"):
        parts.append(f"\n检索时点：{comment['search_date']}")

    return "\n".join(parts)


def _format_with_template(comment: dict, config: dict) -> str:
    """使用 extra_format 模板填充（新增 3 类批注）"""
    template = config["extra_format"]
    # 准备变量
    vars_map = {
        "title": comment.get("title", "未命名"),
        "clause_no": comment.get("clause_no", "?"),
        # 金额异常
        "anomaly_type": comment.get("anomaly_type", "未指定"),
        "value": comment.get("value", "未指定"),
        "threshold": comment.get("threshold", "未指定"),
        # 条款冲突
        "conflict_id": comment.get("conflict_id", "未指定"),
        "conflict_type": comment.get("conflict_type", "未指定"),
        "other_clause_no": comment.get("other_clause_no", "?"),
        # 合规问题
        "compliance_domain": comment.get("compliance_domain", "未指定"),
        "severity": comment.get("severity", "高"),
        # 🆕 文本瑕疵（v2.0）
        "text_category": comment.get("text_category", "未指定"),
        "sub_category": comment.get("sub_category", "未指定"),
        "original_text": comment.get("original_text", "（无）"),
        # 通用
        "essence": comment.get("essence", "未指定"),
        "law": comment.get("law", "（无）"),
        "suggestion": comment.get("suggestion", "（无）"),
        "search_date": comment.get("search_date", "2026-08-06"),
    }
    # 简单 .format() 填充（避免 KeyError 用 safe_substitute）
    import string
    body = string.Formatter().vformat(template, (), vars_map)

    # 头部添加 prefix + 第 X 条 - 标题（让 validate.py 能识别批注类型）
    header = f'{config["prefix"]}第 {vars_map["clause_no"]} 条 - {vars_map["title"]}'

    return f"{header}\n\n{body}"


def validate_comments(comments: list) -> list:
    """校验审查意见完整性，返回问题清单"""
    issues = []

    for i, c in enumerate(comments):
        # 解析批注类型
        comment_type = c.get("type") or c.get("level", "medium").lower()
        if comment_type in LEGACY_LEVEL_MAP:
            comment_type = LEGACY_LEVEL_MAP[comment_type]
        config = COMMENT_TYPE_CONFIG.get(comment_type, COMMENT_TYPE_CONFIG["risk_medium"])

        # 检查必填字段
        for field in config["required_fields"]:
            if not c.get(field):
                issues.append({
                    "index": i,
                    "type": comment_type,
                    "missing_field": field,
                    "message": f"第 {i+1} 条意见（类型 {comment_type}）缺少必填字段 '{field}'",
                })

        # 检查 paragraph_index
        if "paragraph_index" not in c or c["paragraph_index"] < 1:
            issues.append({
                "index": i,
                "type": comment_type,
                "message": f"第 {i+1} 条意见缺少或无效的 paragraph_index",
            })

    return issues


def insert_comments_atomic(input_file: str, output_file: str, comments: list) -> dict:
    """使用 officecli batch 原子插入批注"""
    cli = get_officecli_path()

    # 1. 复制原文件到目标
    import shutil
    shutil.copy(input_file, output_file)

    # 2. 构建 batch 命令
    now = datetime.now().strftime("%Y-%m-%dT%H:%M")
    commands = []

    for c in comments:
        para_idx = c.get("paragraph_index")
        if not para_idx:
            continue

        text = format_comment_text(c)
        path = f"/body/p[{para_idx}]"

        commands.append({
            "command": "add",
            "path": path,
            "type": "comment",
            "props": {
                "text": text,
                "author": "admin",
                "initials": "AD",
                "date": now,
            }
        })

    if not commands:
        return {"success": False, "error": "无有效批注可插入"}

    # 3. 写入临时 batch JSON
    batch_file = output_file + ".batch.json"
    with open(batch_file, "w", encoding="utf-8") as f:
        json.dump(commands, f, ensure_ascii=False, indent=2)

    # 4. 调用 officecli batch
    try:
        # officecli batch 正确语法：
        # --input <json_file> 用于 JSON 文件
        # --commands <json> 用于内联 JSON 字符串
        result = subprocess.run(
            [cli, "batch", output_file, "--input", batch_file, "--json"],
            capture_output=True, text=True, timeout=120
        )

        success = result.returncode == 0
        return {
            "success": success,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "commands_count": len(commands),
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "officecli batch 执行超时"}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        # 清理临时文件（best effort，沙箱可能拒绝）
        try:
            os.remove(batch_file)
        except OSError:
            pass  # 沙箱保护，忽略


# ---------------------- 主函数 ----------------------

def main():
    parser = argparse.ArgumentParser(
        description="批量插入 Word 原生批注（基于 officecli）"
    )
    parser.add_argument("--input", required=True, help="原合同 docx 路径")
    parser.add_argument("--output", required=True, help="输出 docx 路径")
    parser.add_argument("--comments-json", required=True, help="审查意见 JSON 文件路径")

    args = parser.parse_args()

    # 1. 读取审查意见
    comments_file = Path(args.comments_json)
    if not comments_file.exists():
        print(f"错误：审查意见文件不存在 {args.comments_json}", file=sys.stderr)
        sys.exit(1)

    with open(comments_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    comments = data.get("comments", [])
    if not comments:
        print("警告：审查意见为空，输出文档将不含批注", file=sys.stderr)

    # 2. 校验审查意见
    print(f"[1/3] 校验审查意见（{len(comments)} 条）...")
    issues = validate_comments(comments)
    if issues:
        print(f"校验发现问题：{len(issues)} 处", file=sys.stderr)
        for issue in issues:
            print(f"  - {issue['message']}", file=sys.stderr)
        # 校验失败不强制退出，由用户决定
        print("继续执行（用户可中断 Ctrl+C）...", file=sys.stderr)

    # 3. 插入批注
    print(f"[2/3] 插入批注到 {args.output}...")
    result = insert_comments_atomic(args.input, args.output, comments)
    if not result["success"]:
        print(f"插入失败：{result.get('error', '未知错误')}", file=sys.stderr)
        if "stderr" in result:
            print(result["stderr"], file=sys.stderr)
        sys.exit(1)
    print(f"  成功插入 {result.get('commands_count', 0)} 条批注")

    # 4. 完成
    print(f"[3/3] 完成！输出文件：{args.output}")
    print(f"\n下一步：运行 validate.py 自检")
    print(f"  python {Path(__file__).parent / 'validate.py'} --file {args.output}")


if __name__ == "__main__":
    main()