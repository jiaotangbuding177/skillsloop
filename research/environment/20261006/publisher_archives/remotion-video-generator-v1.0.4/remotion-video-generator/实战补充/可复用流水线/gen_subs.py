#!/usr/bin/env python3
"""
1) 调用 edge-tts 生成各段句子级 SRT
2) 把长句二次切分成 ≤16 字宽的短句（按字数比例分配时间）
3) 按"音频连续时间轴"换算成帧号，输出 subs.ts
4) 顺带输出画面 TIMELINE（场景间保留 15 帧交叉溶解）
"""
import json
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, ".")
# 音色/语速/分段文案全部从 gen_audio 继承，杜绝两边配置不一致导致字幕与音频错位
from gen_audio import SEGMENTS, VOICE, RATE, OUT as AUDIO_DIR

FPS = 30
OVERLAP = 15          # 画面交叉溶解帧数
MAX_WIDTH = 15        # 字幕单行最大"字宽"（中文 1，英文/数字 0.6）
ETTS = "/workspace/tts-env/bin/edge-tts"
TMP = "tts_tmp"
MAX_TRIES = 6         # 微软接口间歇限流，重试 + 退避


def char_width(s: str) -> float:
    """估算显示宽度：中文/全角算 1，英文数字算 0.6"""
    w = 0.0
    for ch in s:
        w += 0.6 if ord(ch) < 128 else 1.0
    return w


def srt_time_to_sec(t: str) -> float:
    h, m, rest = t.split(":")
    s, ms = rest.split(",")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def parse_srt(path: str):
    blocks = open(path, encoding="utf-8").read().strip().split("\n\n")
    out = []
    for b in blocks:
        lines = [l for l in b.split("\n") if l.strip()]
        if len(lines) < 2:
            continue
        if re.match(r"^\d+$", lines[0].strip()):
            lines = lines[1:]
        m = re.match(
            r"(\d+):(\d+):(\d+),(\d+)\s*-->\s*(\d+):(\d+):(\d+),(\d+)", lines[0]
        )
        if not m:
            continue
        start = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3)) \
            + int(m.group(4)) / 1000
        end = int(m.group(5)) * 3600 + int(m.group(6)) * 60 + int(m.group(7)) \
            + int(m.group(8)) / 1000
        text = normalize_spacing(" ".join(lines[1:]))
        if text:
            out.append((start, end, text))
    return out


def normalize_spacing(s: str) -> str:
    """edge-tts 会吃掉中英之间的空格，这里补回来，避免 "MIT刚刚" / "AIAgent" 粘连"""
    # 中文 → 英文/数字 之间补空格
    s = re.sub(r"(?<=[\u4e00-\u9fff])(?=[A-Za-z0-9])", " ", s)
    # 英文/数字 → 中文 之间补空格
    s = re.sub(r"(?<=[A-Za-z0-9])(?=[\u4e00-\u9fff])", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def split_sentence(text: str, start: float, end: float):
    """按标点把长句切成短句，时间按字宽比例分配"""
    # 保留标点地切分（注意：排除集里不能含 \s，否则 "MIT 刚刚" 会被拆成 "MIT""刚刚" 再拼回 "MIT刚刚"）
    parts = re.findall(r"[^，。、；：！？]*[，。、；：！？]?", text)
    parts = [p for p in parts if p.strip()]
    if not parts:
        return [(start, end, text)]

    # 超宽片段（无标点的长句）按空格在英文词边界再切一刀，避免溢出画面
    refined = []
    for p in parts:
        if char_width(p) > MAX_WIDTH and " " in p:
            buf = ""
            for w in p.split(" "):
                piece = w if not buf else buf + " " + w
                if char_width(piece) > MAX_WIDTH and buf:
                    refined.append(buf)
                    buf = w
                else:
                    buf = piece
            if buf:
                refined.append(buf)
        else:
            refined.append(p)
    parts = [p for p in refined if p.strip()]

    PUNCT = "，。、；：！？"
    chunks, cur = [], ""
    for p in parts:
        if cur and char_width(cur) + char_width(p) > MAX_WIDTH:
            chunks.append(cur)
            cur = p.strip()
        else:
            # 标点后不再补空格（否则会出现 "社会、 分工"），英文词之间才补
            sep = "" if (cur.endswith(tuple(PUNCT)) or p.strip().startswith(tuple(PUNCT))) else " "
            cur = (cur + sep + p).strip() if cur else p.strip()
    if cur:
        chunks.append(cur)
    chunks = [normalize_spacing(c) for c in chunks]

    total = sum(char_width(c) for c in chunks) or 1
    res, t = [], start
    for c in chunks:
        d = (end - start) * char_width(c) / total
        res.append((t, t + d, c.strip()))
        t += d
    return res


def main():
    os.makedirs(TMP, exist_ok=True)
    manifest = json.load(open(f"{AUDIO_DIR}/manifest.json", encoding="utf-8"))
    seg_durs = [s["dur"] for s in manifest["segments"]]

    # ---- 音频连续时间轴（无重叠）----
    audio_from = []
    acc = 0.0
    for d in seg_durs:
        audio_from.append(acc)
        acc += d
    audio_total = acc

    # 场景帧数（取整）+ 画面时间轴（含 15 帧重叠）
    seg_frames = [int(round(d * FPS)) for d in seg_durs]
    timeline, acc_f = [], 0
    for i, nf in enumerate(seg_frames):
        dur = nf + (OVERLAP if i < len(seg_frames) - 1 else 0)
        timeline.append({"i": i + 1, "from": acc_f, "dur": dur, "audioFrom": acc_f})
        acc_f += nf
    total_frames = acc_f

    # ---- 逐段生成 SRT 并切分 ----
    all_cues = []
    for i, text in enumerate(SEGMENTS):
        idx = i + 1
        srt = f"{TMP}/s{idx}.srt"
        for attempt in range(MAX_TRIES):
            r = subprocess.run(
                [ETTS, "--voice", VOICE, "--rate", RATE,
                 "--text", text,
                 "--write-media", f"{TMP}/s{idx}.mp3",
                 "--write-subtitles", srt],
                capture_output=True, text=True,
            )
            if os.path.exists(srt) and os.path.getsize(srt) > 0:
                break
            if attempt == MAX_TRIES - 1:
                raise RuntimeError(f"S{idx} SRT 生成失败: {r.stderr[-300:]}")
            wait = 1.2 * (attempt + 1)
            print(f"  S{idx}: 第 {attempt+1} 次失败，{wait:.1f}s 后重试")
            time.sleep(wait)
        base_sec = audio_from[i]
        for (s, e, t) in parse_srt(srt):
            for (cs, ce, ct) in split_sentence(t, s, e):
                all_cues.append({
                    "start": int(round((base_sec + cs) * FPS)),
                    "end": int(round((base_sec + ce) * FPS)),
                    "text": ct,
                })
        print(f"  S{idx}: {len(parse_srt(srt))} 长句 → 已切分")

    # 修正相邻字幕空隙：让每条字幕延续到下一条开始，避免闪烁空档
    for i in range(len(all_cues) - 1):
        gap = all_cues[i + 1]["start"] - all_cues[i]["end"]
        if 0 < gap <= 8:  # 小于 8 帧的空档直接连上
            all_cues[i]["end"] = all_cues[i + 1]["start"]

    # ---- 输出 TS ----
    os.makedirs("src/compositions/stigmergy", exist_ok=True)
    ts = ["// 自动生成，请勿手改。重新生成：python3 gen_subs.py", ""]
    ts.append("export const TOTAL_FRAMES = %d;" % total_frames)
    ts.append("")
    ts.append("export const TIMELINE = {")
    for t in timeline:
        ts.append(
            "  S%d: { from: %d, dur: %d }," % (t["i"], t["from"], t["dur"])
        )
    ts.append("};")
    ts.append("")
    ts.append("export type Cue = { start: number; end: number; text: string };")
    ts.append("")
    ts.append("export const CUES: Cue[] = [")
    for c in all_cues:
        ts.append(
            "  { start: %d, end: %d, text: %s },"
            % (c["start"], c["end"], json.dumps(c["text"], ensure_ascii=False))
        )
    ts.append("];")
    ts.append("")
    open("src/compositions/stigmergy/subs.ts", "w", encoding="utf-8").write("\n".join(ts))

    print(f"\n总帧数: {total_frames} ({total_frames/FPS:.2f}s)")
    print(f"音频总长: {audio_total:.2f}s")
    print(f"字幕条数: {len(all_cues)}")
    print("已写入 src/compositions/stigmergy/subs.ts")


if __name__ == "__main__":
    main()
