#!/usr/bin/env python3
"""BGM Preset 自动匹配评分。

根据视频属性给各 Preset 打分，选择最匹配的 BGM。
维度：Video Type / Voiceover Density / Mood / Energy / Audience / Scene Pace / Brand Tone

用法:
  python3 select_bgm.py --video-type report --voiceover-density high [--mood professional] \
      [--energy medium] [--audience tech] [--pace medium] [--brand-tone modern]

示例:
  报告解读 + 高旁白密度 → 优先 documentary，降低 premium-product/future-interface
  AI 产品宣传 + 中等旁白 → 优先 ambient-tech / future-interface
"""
import argparse
import sys

# 各 Preset 的属性画像（0~1 倾向）
PRESET_PROFILES = {
    "ambient-tech":     {"types": {"ai-demo": 1.0, "product": 0.7, "saas": 1.0, "report": 0.3},
                         "moods": {"professional": 1.0, "future": 1.0, "calm": 0.5, "warm": 0.2},
                         "energy": {"low": 0.6, "medium": 1.0, "high": 0.4},
                         "audiences": {"tech": 1.0, "enterprise": 0.6, "general": 0.5},
                         "pace": {"fast": 0.5, "medium": 1.0, "slow": 0.6},
                         "brand": {"modern": 1.0, "classic": 0.2, "premium": 0.6},
                         "voiceover_tolerance": 1.0},
    "corporate-clean":  {"types": {"corporate": 1.0, "report": 0.6, "product": 0.5, "ai-demo": 0.4},
                         "moods": {"professional": 1.0, "uplifting": 0.8, "warm": 0.5, "future": 0.4},
                         "energy": {"low": 0.5, "medium": 1.0, "high": 0.5},
                         "audiences": {"enterprise": 1.0, "general": 0.6, "tech": 0.5},
                         "pace": {"medium": 1.0, "slow": 0.6, "fast": 0.4},
                         "brand": {"classic": 0.8, "modern": 0.5, "premium": 0.6},
                         "voiceover_tolerance": 0.9},
    "documentary":      {"types": {"report": 1.0, "knowledge": 1.0, "corporate": 0.5, "ai-demo": 0.3},
                         "moods": {"calm": 1.0, "professional": 0.6, "warm": 0.5, "future": 0.3},
                         "energy": {"low": 1.0, "medium": 0.4, "high": 0.1},
                         "audiences": {"general": 0.8, "enterprise": 0.6, "tech": 0.4},
                         "pace": {"slow": 1.0, "medium": 0.5, "fast": 0.2},
                         "brand": {"classic": 0.7, "modern": 0.5, "premium": 0.5},
                         "voiceover_tolerance": 1.0},
    "minimal-piano":    {"types": {"tutorial": 1.0, "education": 1.0, "knowledge": 0.8, "product": 0.4},
                         "moods": {"calm": 1.0, "warm": 0.7, "emotional": 0.8, "professional": 0.4},
                         "energy": {"low": 1.0, "medium": 0.5, "high": 0.2},
                         "audiences": {"general": 0.8, "education": 1.0, "tech": 0.4},
                         "pace": {"slow": 0.8, "medium": 0.8, "fast": 0.3},
                         "brand": {"classic": 0.6, "premium": 0.6, "modern": 0.4},
                         "voiceover_tolerance": 1.0},
    "premium-product":  {"types": {"product": 1.0, "brand": 1.0, "ai-demo": 0.5, "corporate": 0.5},
                         "moods": {"premium": 1.0, "uplifting": 0.7, "professional": 0.6, "warm": 0.5},
                         "energy": {"medium": 1.0, "low": 0.4, "high": 0.5},
                         "audiences": {"general": 0.7, "enterprise": 0.6, "tech": 0.5},
                         "pace": {"medium": 0.9, "slow": 0.5, "fast": 0.4},
                         "brand": {"premium": 1.0, "modern": 0.6, "classic": 0.4},
                         "voiceover_tolerance": 0.6},
    "cinematic-soft":   {"types": {"story": 1.0, "brand": 0.7, "product": 0.5, "corporate": 0.4},
                         "moods": {"emotional": 1.0, "epic": 0.9, "premium": 0.7, "calm": 0.6},
                         "energy": {"low": 0.7, "medium": 0.8, "high": 0.4},
                         "audiences": {"general": 0.8, "enterprise": 0.5, "tech": 0.4},
                         "pace": {"slow": 0.9, "medium": 0.6, "fast": 0.2},
                         "brand": {"premium": 0.8, "classic": 0.5, "modern": 0.5},
                         "voiceover_tolerance": 0.6},
    "warm-education":   {"types": {"education": 1.0, "tutorial": 1.0, "knowledge": 0.9, "report": 0.4},
                         "moods": {"warm": 1.0, "calm": 0.8, "professional": 0.4},
                         "energy": {"low": 0.8, "medium": 0.7, "high": 0.3},
                         "audiences": {"education": 1.0, "general": 0.7, "tech": 0.3},
                         "pace": {"medium": 0.8, "slow": 0.7, "fast": 0.3},
                         "brand": {"modern": 0.5, "classic": 0.5, "premium": 0.4},
                         "voiceover_tolerance": 1.0},
    "future-interface": {"types": {"saas": 1.0, "ai-demo": 1.0, "product": 0.6, "report": 0.2},
                         "moods": {"future": 1.0, "professional": 0.7, "uplifting": 0.5},
                         "energy": {"medium": 0.9, "high": 0.8, "low": 0.4},
                         "audiences": {"tech": 1.0, "enterprise": 0.5, "general": 0.4},
                         "pace": {"fast": 0.8, "medium": 0.8, "slow": 0.3},
                         "brand": {"modern": 1.0, "premium": 0.5, "classic": 0.1},
                         "voiceover_tolerance": 0.7},
}

# 视频类型 → 默认属性
VIDEO_TYPE_DEFAULTS = {
    "ai-demo":     {"mood": "professional", "energy": "medium", "audience": "tech",
                    "pace": "medium", "brand": "modern", "vo_density": "medium"},
    "report":      {"mood": "professional", "energy": "low", "audience": "enterprise",
                    "pace": "slow", "brand": "classic", "vo_density": "high"},
    "corporate":   {"mood": "professional", "energy": "medium", "audience": "enterprise",
                    "pace": "medium", "brand": "classic", "vo_density": "medium"},
    "product":     {"mood": "premium", "energy": "medium", "audience": "general",
                    "pace": "medium", "brand": "premium", "vo_density": "medium"},
    "tutorial":    {"mood": "calm", "energy": "low", "audience": "general",
                    "pace": "medium", "brand": "modern", "vo_density": "high"},
    "education":   {"mood": "warm", "energy": "low", "audience": "education",
                    "pace": "slow", "brand": "modern", "vo_density": "high"},
    "brand":       {"mood": "premium", "energy": "medium", "audience": "general",
                    "pace": "medium", "brand": "premium", "vo_density": "low"},
    "saas":        {"mood": "professional", "energy": "medium", "audience": "tech",
                    "pace": "fast", "brand": "modern", "vo_density": "medium"},
}


def score_preset(name: str, profile: dict, attrs: dict) -> float:
    score = 0.0
    weights = {"types": 0.25, "moods": 0.2, "energy": 0.15, "audiences": 0.1,
               "pace": 0.1, "brand": 0.1, "vo": 0.1}
    vt = attrs["video_type"]
    score += profile["types"].get(vt, 0.2) * weights["types"]
    score += profile["moods"].get(attrs["mood"], 0.3) * weights["moods"]
    score += profile["energy"].get(attrs["energy"], 0.5) * weights["energy"]
    score += profile["audiences"].get(attrs["audience"], 0.4) * weights["audiences"]
    score += profile["pace"].get(attrs["pace"], 0.5) * weights["pace"]
    score += profile["brand"].get(attrs["brand"], 0.4) * weights["brand"]
    # 高旁白密度：偏好 voiceover_tolerance 高的 Preset
    vo_tol = profile.get("voiceover_tolerance", 0.7)
    if attrs["vo_density"] == "high":
        score += vo_tol * weights["vo"]
    elif attrs["vo_density"] == "medium":
        score += (0.5 + 0.5 * vo_tol) * weights["vo"]
    else:  # low → 音乐可以更活跃
        score += (1.0 - 0.4 * vo_tol) * weights["vo"]
    return round(score, 3)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video-type", required=True, choices=sorted(VIDEO_TYPE_DEFAULTS))
    parser.add_argument("--voiceover-density", choices=["low", "medium", "high"], default=None)
    parser.add_argument("--mood", default=None)
    parser.add_argument("--energy", choices=["low", "medium", "high"], default=None)
    parser.add_argument("--audience", default=None)
    parser.add_argument("--pace", choices=["slow", "medium", "fast"], default=None)
    parser.add_argument("--brand-tone", default=None)
    parser.add_argument("--top", type=int, default=3)
    args = parser.parse_args()

    d = VIDEO_TYPE_DEFAULTS[args.video_type]
    attrs = {
        "video_type": args.video_type,
        "vo_density": args.voiceover_density or d["vo_density"],
        "mood": args.mood or d["mood"],
        "energy": args.energy or d["energy"],
        "audience": args.audience or d["audience"],
        "pace": args.pace or d["pace"],
        "brand": args.brand_tone or d["brand"],
    }

    ranked = sorted(
        ((score_preset(n, p, attrs), n) for n, p in PRESET_PROFILES.items()),
        reverse=True,
    )
    print(f"视频属性: {attrs}")
    print("Preset 评分排序:")
    for s, n in ranked:
        mark = " ← 推荐" if s == ranked[0][0] else ""
        print(f"  {n}: {s:.3f}{mark}")
    best = ranked[0][1]
    print(f"推荐 Preset: {best}")
    print(f"Music Sections 建议: intro(开场轻) → a(主体稳定) → b(推进) → highlight(核心亮点提升) → outro(收束)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
