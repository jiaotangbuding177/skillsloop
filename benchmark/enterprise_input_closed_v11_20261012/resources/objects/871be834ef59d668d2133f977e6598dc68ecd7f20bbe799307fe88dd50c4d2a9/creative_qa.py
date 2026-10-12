#!/usr/bin/env python3
"""Creative Quality Gate（第二层 QA）：基于 Storyboard 计划检查导演质量。

用法:
  python3 creative_qa.py storyboard.json [--strict]

storyboard.json 结构:
{
  "title": "...",
  "creative_concept": "一句话视觉母题",
  "visual_motif": "贯穿元素",
  "music_brief": {"mood": "...", "energy": "Low→Medium→Low",
                  "beginning": "...", "middle": "...", "climax": "...", "ending": "..."},
  "scenes": [
    {"id": "S1", "scene_type": "hero", "duration": 4.5, "layout": "center-title",
     "motion_density": "medium", "shots": 1, "static_hold": 0.8, "has_visual_subject": true},
    ...
  ]
}

检查（Anti-PPT 规则）:
  - 连续 3 个 Scene 相同 scene_type / layout → PPT-like risk
  - 超过 70% 场景是"标题+背景"且无视觉主体 → PPT risk
  - Motion Density 全程一致 → 缺少节奏变化
  - Scene 时长过于平均（CV < 0.15）→ 节奏机械
  - 存在 >5s 完全静止场景（low density + 1 shot + 无主体运动）
  - 缺少视觉主体（has_visual_subject=false 占比过高）
  - Creative Concept / Music Brief 缺失
  - 结尾场景缺失
"""
import argparse
import json
import statistics
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("storyboard")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    sb = json.loads(Path(args.storyboard).read_text(encoding="utf-8"))
    scenes = sb.get("scenes", [])
    problems: list[str] = []
    warnings: list[str] = []
    info: list[str] = []

    if not scenes:
        print("[FAIL] 无 Scene 定义")
        return 1

    # 基础信息
    if not sb.get("creative_concept"):
        problems.append("缺少 Creative Concept（一句话视觉母题）")
    if not sb.get("visual_motif"):
        warnings.append("未声明 Visual Motif（贯穿元素）")
    mb = sb.get("music_brief") or {}
    if not mb:
        problems.append("缺少 Music Brief（mood/energy/beginning/middle/climax/ending）")

    n = len(scenes)
    total_dur = sum(s.get("duration", 0) for s in scenes)
    types = [s.get("scene_type", "") for s in scenes]
    layouts = [s.get("layout", "") for s in scenes]
    densities = [s.get("motion_density", "medium") for s in scenes]
    shot_counts = [s.get("shots", 1) for s in scenes]
    durations = [s.get("duration", 0) for s in scenes]

    # 连续重复 scene_type / layout（≥2 连续即警告，≥3 为 PPT risk）
    for field, name in ((types, "scene_type"), (layouts, "layout")):
        run = 1
        for i in range(1, len(field)):
            if field[i] == field[i - 1] and field[i]:
                run += 1
                if run == 3:
                    problems.append(f"连续 3 个 Scene 相同 {name}='{field[i]}'（PPT-like risk）")
                elif run == 2 and args.strict:
                    warnings.append(f"连续 2 个 Scene 相同 {name}='{field[i]}'")
            else:
                run = 1

    # 标题+背景无主体占比
    no_subject = sum(1 for s in scenes if not s.get("has_visual_subject", True))
    if no_subject / n > 0.3:
        problems.append(f"{no_subject}/{n} 场景缺少视觉主体（>30%）")

    # Scene Type 多样性
    uniq_types = len(set(t for t in types if t))
    info.append(f"Scene Type 种类: {uniq_types}（{sorted(set(types))}）")
    if uniq_types < 3:
        problems.append(f"Scene Type 少于 3 种（实际 {uniq_types}）")

    # Shot 数量
    total_shots = sum(shot_counts)
    info.append(f"总 Shot 数: {total_shots}")
    if total_shots < 8:
        warnings.append(f"Shot 总数偏少（{total_shots}，建议 ≥8）")

    # Motion Density 变化
    if len(set(densities)) == 1:
        warnings.append(f"Motion Density 全程一致（{densities[0]}），缺少节奏变化")

    # 时长平均度（CV）
    if len(durations) > 2 and min(durations) > 0:
        mean = statistics.mean(durations)
        cv = statistics.pstdev(durations) / mean
        info.append(f"Scene 时长 CV={cv:.2f}（<0.15 过于平均）")
        if cv < 0.15:
            warnings.append("Scene 时长过于平均，节奏机械（建议快慢交错）")

    # 静止场景 >5s
    for s in scenes:
        if (s.get("motion_density") == "low" and s.get("shots", 1) == 1
                and s.get("duration", 0) > 5 and not s.get("has_visual_subject", True)):
            problems.append(f"Scene {s.get('id')} 为 >5s 完全静止画面（无视觉主体）")

    # 结尾场景
    last_type = types[-1] if types else ""
    if last_type not in ("ending", "fullscreen-typography", "cta"):
        warnings.append(f"结尾场景类型 '{last_type}' 非收束型（ending/typography/cta）")

    # 开场
    first_type = types[0] if types else ""
    if first_type not in ("hero", "hook", "fullscreen-visual", "big-number"):
        warnings.append(f"开场场景类型 '{first_type}' 建议用 hero/hook 快速建立主题")

    # 视觉节奏信息
    info.append(f"总时长: {total_dur:.1f}s，Scene 数: {n}")
    info.append(f"Motion Density 分布: { {d: densities.count(d) for d in set(densities)} }")

    print(f"Creative QA: {sb.get('title', '未命名')}")
    for line in info:
        print(f"  [i] {line}")
    for w in warnings:
        print(f"  [!] {w}")
    if problems:
        print("[FAIL] Creative QA 未通过：")
        for p in problems:
            print(f"  - {p}")
        print("提示: 重新设计后重跑（增加 Shot 变化/布局变化/深度/运动/视觉叙事）")
        return 1
    print("[OK] Creative QA 通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
