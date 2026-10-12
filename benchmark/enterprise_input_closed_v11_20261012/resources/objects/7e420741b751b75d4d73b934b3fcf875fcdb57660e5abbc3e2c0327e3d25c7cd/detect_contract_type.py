#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
detect_contract_type.py - 自动识别合同类型

输入：合同文本（从 docx 提取的纯文本）
输出：JSON {primary_type, confidence, score, secondary_types, evidence}

支持 9 类合同：
- OEM 代工合同
- 采购合同
- 服务合同
- 建筑工程合同
- NDA / 保密协议
- 技术开发合同
- 租赁合同
- 股权转让 / 投融资合同
- 跨境贸易合同

可独立调用：
    python detect_contract_type.py --input "D:/合同/xxx.docx"
    python detect_contract_type.py --text "OEM代工合同..."

依赖：officecli（docx 解析）
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


# ---------------------- 9 类合同识别规则 ----------------------

TYPE_RULES = {
    "oem_contract": {
        "label": "OEM 代工合同",
        "strong_keywords": [
            "OEM", "代工", "委托加工", "委托生产", "贴牌",
            "代工方式", "代为加工", "指定加工工厂", "代为生产",
            "受托生产", "贴牌生产"
        ],
        "aux_keywords": [
            "包材", "罐体", "外箱", "商标组合",
            "出厂检验报告", "产品执行标准", "品牌授权",
            "商标许可使用", "受托方", "委托方"
        ],
        "negative_keywords": [
            "提供服务", "咨询", "培训"
        ],
    },
    "purchase_contract": {
        "label": "采购合同",
        "strong_keywords": [
            "采购合同", "订购合同", "买卖合同",
            "采购", "订购", "订单确认", "订货确认",
            "交货", "交付", "验收", "货到付款"
        ],
        "aux_keywords": [
            "货物", "商品", "标的物", "产品数量",
            "运输", "运费", "装卸",
            "开具增值税专用发票", "送货"
        ],
        "negative_keywords": [
            "提供服务", "咨询", "加工",
            "技术开发", "研发"
        ],
    },
    "service_contract": {
        "label": "服务合同",
        "strong_keywords": [
            "服务合同", "服务协议", "咨询合同",
            "提供服务", "服务内容", "服务期限",
            "服务费", "服务报酬", "按月支付服务费"
        ],
        "aux_keywords": [
            "SLA", "服务等级", "响应时间",
            "服务范围", "服务标准",
            "项目经理", "服务团队", "服务报告"
        ],
        "negative_keywords": [
            "货物", "设备", "材料",
            "代工", "加工", "生产"
        ],
    },
    "construction_contract": {
        "label": "建筑工程合同",
        "strong_keywords": [
            "建设工程", "施工合同", "工程承包",
            "建设工程", "工程施工", "工程款",
            "开工日期", "竣工日期", "工程验收"
        ],
        "aux_keywords": [
            "承包人", "发包人", "监理",
            "工程量", "工程变更", "工程签证",
            "工程进度款", "竣工结算", "施工许可证"
        ],
        "negative_keywords": [
            "货物买卖", "服务"
        ],
    },
    "nda": {
        "label": "保密协议 (NDA)",
        "strong_keywords": [
            "保密协议", "NDA", "保密合同",
            "保密义务", "保密信息", "商业秘密",
            "保密期限", "保密违约金", "脱密"
        ],
        "aux_keywords": [
            "披露方", "接收方", "保密资料",
            "去标识化", "保密措施"
        ],
        "negative_keywords": [
            "货物", "服务", "工程", "股权"
        ],
    },
    "tech_development_contract": {
        "label": "技术开发合同",
        "strong_keywords": [
            "技术开发", "委托研发", "研发合同",
            "技术开发", "研发成果", "技术成果",
            "技术指标", "技术参数", "技术验收"
        ],
        "aux_keywords": [
            "背景知识产权", "前景知识产权", "IP 归属",
            "源代码", "技术文档", "算法",
            "里程碑", "阶段交付"
        ],
        "negative_keywords": [
            "货物", "服务", "工程"
        ],
    },
    "lease_contract": {
        "label": "租赁合同",
        "strong_keywords": [
            "租赁合同", "租赁协议",
            "租赁标的", "租金", "租期",
            "出租人", "承租人", "租赁物"
        ],
        "aux_keywords": [
            "押金", "保证金", "房屋", "设备",
            "维修责任", "装修", "续租"
        ],
        "negative_keywords": [
            "货物买卖", "服务", "工程"
        ],
    },
    "equity_investment": {
        "label": "股权转让 / 投融资合同",
        "strong_keywords": [
            "股权转让", "增资协议", "投资协议",
            "股权转让", "标的股权", "对价",
            "估值", "市盈率", "业绩承诺"
        ],
        "aux_keywords": [
            "交割", "先决条件", "回购",
            "优先清算权", "反稀释", "对赌",
            "股东会决议", "董事会决议"
        ],
        "negative_keywords": [
            "货物", "服务", "工程"
        ],
    },
    "cross_border_trade": {
        "label": "跨境贸易合同",
        "strong_keywords": [
            "国际贸易", "进出口合同",
            "FOB", "CIF", "DDP", "EXW", "FCA",
            "进出口", "报关", "商检", "原产地证"
        ],
        "aux_keywords": [
            "信用证", "L/C", "T/T", "D/P",
            "汇率", "外汇", "跨境支付",
            "关税", "反倾销", "出口退税"
        ],
        "negative_keywords": [
            "服务", "工程", "股权"
        ],
    },
}


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
        # 过滤掉 paraId=... 前缀
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


def score_text(text: str, contract_type: str) -> dict:
    """对单个合同类型打分"""
    rules = TYPE_RULES[contract_type]
    title_section = text[:500]  # 标题 + 第一条
    evidence = []

    score = 0

    # 强特征词（标题 +5，正文 +3）
    for kw in rules["strong_keywords"]:
        if kw in title_section:
            score += 5
            evidence.append({"keyword": kw, "location": "title", "weight": 5})
        elif kw in text:
            score += 3
            evidence.append({"keyword": kw, "location": "body", "weight": 3})

    # 辅助特征词（+1）
    for kw in rules["aux_keywords"]:
        if kw in text:
            score += 1
            evidence.append({"keyword": kw, "location": "body", "weight": 1})

    # 反例关键词（-2）
    for kw in rules["negative_keywords"]:
        if kw in text:
            score -= 2
            evidence.append({"keyword": kw, "location": "body", "weight": -2})

    return {"score": score, "evidence": evidence}


def detect_contract_type(text: str) -> dict:
    """主函数：识别合同类型"""
    all_scores = {}
    all_evidence = {}
    for ctype in TYPE_RULES:
        result = score_text(text, ctype)
        all_scores[ctype] = result["score"]
        all_evidence[ctype] = result["evidence"]

    # 排序
    sorted_types = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)

    if not sorted_types or sorted_types[0][1] <= 0:
        return {
            "primary_type": "unknown",
            "primary_type_label": "未知合同类型",
            "confidence": "unknown",
            "score": 0,
            "secondary_types": [],
            "evidence": [],
            "all_scores": all_scores,
        }

    best_type, best_score = sorted_types[0]
    second_score = sorted_types[1][1] if len(sorted_types) > 1 else 0

    # 置信度判定
    if best_score >= 8:
        confidence = "high"
    elif best_score >= 4:
        confidence = "medium"
    else:
        confidence = "low"

    # 第二名差距 < 3 → 标注歧义
    if best_score - second_score < 3 and second_score >= 3:
        confidence = "ambiguous"

    # 副类型（≥5 且与主类型差距 ≥ 3）
    secondary_types = []
    for ctype, s in sorted_types[1:]:
        if s >= 5 and best_score - s >= 3:
            secondary_types.append({
                "type": ctype,
                "label": TYPE_RULES[ctype]["label"],
                "score": s,
            })

    return {
        "primary_type": best_type,
        "primary_type_label": TYPE_RULES[best_type]["label"],
        "confidence": confidence,
        "score": best_score,
        "secondary_types": secondary_types,
        "evidence": all_evidence[best_type][:20],  # 截断
        "all_scores": all_scores,
    }


# ---------------------- CLI ----------------------

def main():
    parser = argparse.ArgumentParser(description="自动识别合同类型")
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

    result = detect_contract_type(text)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"合同类型识别结果：")
        print(f"  主类型：{result['primary_type_label']} ({result['primary_type']})")
        print(f"  置信度：{result['confidence']}")
        print(f"  得分：{result['score']}")
        if result['secondary_types']:
            print(f"  副类型：")
            for st in result['secondary_types']:
                print(f"    - {st['label']} (得分 {st['score']})")
        print(f"\n  证据（Top 10）：")
        for ev in result['evidence'][:10]:
            print(f"    - {ev['location']}: '{ev['keyword']}' ×{ev['weight']}")


if __name__ == "__main__":
    main()