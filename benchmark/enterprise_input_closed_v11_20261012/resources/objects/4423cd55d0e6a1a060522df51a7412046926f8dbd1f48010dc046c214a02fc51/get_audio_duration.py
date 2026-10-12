#!/usr/bin/env python3
"""读取音频时长（秒）。优先 ffprobe；无 ffprobe 时用纯标准库解析 MP3 帧头。

用法:
  python3 get_audio_duration.py <audio.mp3>
输出:
  时长（秒，浮点）
"""
import struct
import subprocess
import sys
from pathlib import Path


def via_ffprobe(path: str) -> float | None:
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=30,
        )
        if out.returncode == 0 and out.stdout.strip():
            return float(out.stdout.strip())
    except (FileNotFoundError, ValueError, subprocess.TimeoutExpired):
        pass
    return None


def mp3_duration(path: str) -> float:
    """MPEG Audio 帧扫描：累计每帧采样数 / 采样率。支持 Layer I/II/III 与 MPEG1/2/2.5。"""
    SR_MPEG1 = {0: 44100, 1: 48000, 2: 32000}
    BR_L1 = [0, 32, 64, 96, 128, 160, 192, 224, 256, 288, 320, 352, 384, 416, 448, 0]
    BR_L2L3_M1 = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0]
    BR_L2L3_M2 = [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, 0]
    data = Path(path).read_bytes()
    i, total_samples, sample_rate = 0, 0, None
    n = len(data)
    while i < n - 4:
        if data[i] != 0xFF or (data[i + 1] & 0xE0) != 0xE0:
            i += 1
            continue
        b1, b2 = data[i + 1], data[i + 2]
        version = (b1 >> 3) & 0x03          # 3=MPEG1, 2=MPEG2, 0=MPEG2.5
        layer = (b1 >> 1) & 0x03            # 1=III, 2=II, 3=I
        if version == 1 or layer == 0:
            i += 1
            continue
        br_idx = (b2 >> 4) & 0x0F
        if br_idx == 0 or br_idx == 15:      # free format / 无效
            i += 1
            continue
        sr = SR_MPEG1.get((b2 >> 2) & 0x03)
        if sr is None:
            i += 1
            continue
        if version == 2:
            sr //= 2
        elif version == 0:
            sr //= 4
        padding = (b2 >> 1) & 0x01
        mpeg1 = version == 3
        if layer == 3:                       # Layer I
            spf = 384
            frame_len = (12 * BR_L1[br_idx] * 1000 // sr + padding) * 4
        elif layer == 2:                     # Layer II
            spf = 1152
            br = (BR_L2L3_M1 if mpeg1 else BR_L2L3_M2)[br_idx] * 1000
            frame_len = 144 * br // sr + padding
        else:                                # Layer III
            spf = 1152 if mpeg1 else 576
            br = (BR_L2L3_M1 if mpeg1 else BR_L2L3_M2)[br_idx] * 1000
            frame_len = (144 if mpeg1 else 72) * br // sr + padding
        if frame_len <= 0 or i + frame_len > n:
            i += 1
            continue
        total_samples += spf
        sample_rate = sr
        i += frame_len
    if sample_rate is None or total_samples == 0:
        raise ValueError("无法解析 MP3 帧")
    return total_samples / sample_rate


def wav_duration(path: str) -> float:
    import wave
    with wave.open(path, "rb") as w:
        return w.getnframes() / w.getframerate()


def main_quiet(path: str) -> float:
    """返回音频时长（秒），供其他脚本复用。"""
    duration = via_ffprobe(path)
    if duration is None:
        suffix = Path(path).suffix.lower()
        if suffix == ".wav":
            duration = wav_duration(path)
        else:
            duration = mp3_duration(path)
    return duration


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: get_audio_duration.py <audio.mp3>", file=sys.stderr)
        return 1
    path = sys.argv[1]
    if not Path(path).exists():
        print(f"ERROR: 文件不存在: {path}", file=sys.stderr)
        return 1
    try:
        duration = main_quiet(path)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"{duration:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
