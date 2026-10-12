#!/usr/bin/env python3
"""音频质量 QA：峰值 / RMS / DC Offset / Clipping / Click 突变 / 首尾检查。

用法:
  python3 audio_qa.py <audio.wav> [--tail-seconds 2] [--click-threshold 0.25]

检查项（纯标准库解析 WAV）:
  - 时长 / 采样率 / 声道
  - Peak（dBFS）与 RMS（dBFS）
  - DC Offset（应接近 0）
  - Clipping（abs ≥ 0.999 采样数）
  - Click/Pop 突变检测：相邻采样跳变超过阈值则报告位置（重点检查开头/结尾/Loop 点）
  - 开头 100ms 峰值、结尾 N 秒峰值（Master Fade Out 后应接近 0）
退出码: 0 = 通过；1 = 发现异常。
"""
import argparse
import array
import math
import sys
import wave
from pathlib import Path


def analyze(path: str, tail_seconds: float, click_threshold: float) -> int:
    with wave.open(path, "rb") as w:
        sr = w.getframerate()
        ch = w.getnchannels()
        sw = w.getsampwidth()
        n = w.getnframes()
        raw = w.readframes(n)
    duration = n / sr
    samples = array.array("h", raw)
    if ch == 2:
        # 取双声道合并（L+R 平均幅度用于整体判断，跳变检测用 L 声道）
        left = samples[0::2]
        mono = [ (samples[i] + samples[i+1]) / 2 for i in range(0, len(samples)-1, 2) ]
    else:
        left = samples
        mono = list(samples)
    scale = 32767.0

    problems: list[str] = []

    # Peak / RMS
    peak = max(abs(s) for s in mono) / scale
    peak_db = 20 * math.log10(peak) if peak > 0 else -120
    rms = math.sqrt(sum(s * s for s in mono) / len(mono)) / scale
    rms_db = 20 * math.log10(rms) if rms > 0 else -120

    # DC Offset
    dc = sum(mono) / len(mono) / scale

    # Clipping
    clip_count = sum(1 for s in mono if abs(s) >= 0.999 * scale)

    # Click 检测（相邻采样跳变）
    max_jump = 0.0
    max_jump_pos = 0
    clicks: list[tuple[float, float]] = []
    prev = left[0]
    for i in range(1, len(left)):
        j = abs(left[i] - prev) / scale
        if j > max_jump:
            max_jump, max_jump_pos = j, i
        if j > click_threshold:
            clicks.append((i / sr, j))
        prev = left[i]

    # 首尾检查
    head = mono[:int(0.1 * sr)]
    head_peak = max(abs(s) for s in head) / scale if head else 0
    tail = mono[-int(tail_seconds * sr):]
    tail_peak = max(abs(s) for s in tail) / scale if tail else 0
    # 真正的"结束位置"：末尾 200ms 应接近 0（Master Fade Out 到真零）
    tail_end = mono[-int(0.2 * sr):]
    tail_end_peak = max(abs(s) for s in tail_end) / scale if tail_end else 0
    last_sample = abs(mono[-1]) / scale if mono else 1.0
    # 尾部是否平滑（最后 N 秒内无异常跳变）
    tail_jump = 0.0
    for i in range(max(1, len(left) - int(tail_seconds * sr)), len(left)):
        j = abs(left[i] - left[i - 1]) / scale
        if j > tail_jump:
            tail_jump = j

    print(f"文件: {path}")
    print(f"  时长 {duration:.2f}s | {sr}Hz | {ch}ch | {sw*8}bit")
    print(f"  Peak {peak:.4f} ({peak_db:.1f} dBFS) | RMS {rms_db:.1f} dBFS")
    print(f"  DC Offset {dc:+.6f} | Clipping 采样数 {clip_count}")
    print(f"  最大相邻跳变 {max_jump:.4f} @ {max_jump_pos/sr:.3f}s")
    print(f"  开头100ms峰值 {head_peak:.5f} | 结尾{tail_seconds}s峰值 {tail_peak:.5f} | 末尾200ms峰值 {tail_end_peak:.5f} | 末采样 {last_sample:.6f}")
    print(f"  尾部{tail_seconds}s最大跳变 {tail_jump:.4f}")

    # 判定
    if peak >= 0.999:
        problems.append(f"Clipping: peak {peak_db:.1f} dBFS 达到满幅")
    elif peak > 0.85:
        problems.append(f"Peak 过高（{peak_db:.1f} dBFS），无足够 Headroom")
    if abs(dc) > 0.005:
        problems.append(f"DC Offset 明显: {dc:+.5f}")
    if clip_count > 0:
        problems.append(f"存在 {clip_count} 个满幅采样")
    if max_jump > click_threshold:
        problems.append(f"检测到 click/pop: 跳变 {max_jump:.3f} @ {max_jump_pos/sr:.3f}s")
    if len(clicks) > 10:
        problems.append(f"click 数量过多: {len(clicks)} 处（含小跳变）")
    if tail_end_peak > 0.01:
        problems.append(f"末尾 200ms 未归零: 峰值 {tail_end_peak:.4f}（Master Fade Out 未到真 0）")
    if last_sample > 0.005:
        problems.append(f"末采样不为 0: {last_sample:.5f}（可能被硬截断）")
    if tail_jump > click_threshold:
        problems.append(f"尾部 {tail_seconds}s 存在跳变: {tail_jump:.3f}（Fade 不平滑）")
    if head_peak > 0.5:
        problems.append(f"开头 100ms 峰值过高 {head_peak:.3f}（Attack 不足）")

    if problems:
        print("[FAIL]")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("[OK] 音频质量检查通过")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--tail-seconds", type=float, default=2.0)
    parser.add_argument("--click-threshold", type=float, default=0.25)
    args = parser.parse_args()
    if not Path(args.path).exists():
        print(f"ERROR: 文件不存在: {args.path}", file=sys.stderr)
        return 1
    return analyze(args.path, args.tail_seconds, args.click_threshold)


if __name__ == "__main__":
    sys.exit(main())
