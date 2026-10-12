#!/usr/bin/env python3
"""AI 配音生成（Edge TTS Python API，词级时间轴 WordBoundary）。

用法:
  python3 generate_voiceover.py --text "要配音的文本" [--voice zh-CN-XiaoxiaoNeural] \
      [--rate +0%] [--volume +0%] [--pitch +0Hz] [--out-dir audio/voiceover] [--stem vo1] \
      [--boundary WordBoundary|SentenceBoundary]

输出:
  <stem>.mp3            配音音频
  <stem>.vtt            句级字幕（兼容）
  <stem>.captions.json  统一字幕时间轴:
      {"text": "<整句>",
       "words": [{"text","start","end","duration"}...],
       "sentences": [{"text","start","end"}...],   # 句级（备用/句级模式用）
       "boundary": "WordBoundary"}

时间轴降级: WordBoundary 失败 → SentenceBoundary → 按音频时长比例估算。
不硬编码音色；不写入任何密钥/个人信息。
"""
import argparse
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

# ---- 自动定位/重启到带 edge_tts 的解释器 ----
def _find_tts_python() -> str:
    candidates: list[str] = []
    if os.environ.get("TTS_PYTHON"):
        candidates.append(os.environ["TTS_PYTHON"])
    candidates.append(sys.executable)
    for base in (Path.cwd(), Path(__file__).resolve().parent):
        for depth in range(5):
            venv = base / ("../" * depth) / ".venv-tts" / "bin" / "python"
            if venv.exists():
                candidates.append(str(venv))  # 勿 resolve：venv python 是符号链接
    candidates.append("python3")
    seen: set[str] = set()
    for cand in candidates:
        if not cand or cand in seen:
            continue
        seen.add(cand)
        try:
            subprocess.run([cand, "-c", "import edge_tts"], check=True,
                           capture_output=True, timeout=30)
            return cand
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            continue
    raise SystemExit("ERROR: 未找到可用的 edge_tts，请先运行 scripts/install_edge_tts.sh")


def _ensure_edge_tts() -> None:
    try:
        import edge_tts  # noqa: F401
    except ImportError:
        py = _find_tts_python()
        if py != sys.executable:
            os.execv(py, [py, os.path.abspath(__file__), *sys.argv[1:]])
        raise SystemExit("ERROR: 当前解释器无 edge_tts 且无法自动切换")


_ensure_edge_tts()
import edge_tts  # noqa: E402


# ---- 音频时长（纯标准库 MP3 帧扫描，兜底用） ----
def _mp3_duration_seconds(path: Path) -> float:
    SR = {0: 44100, 1: 48000, 2: 32000}
    BR_L1 = [0, 32, 64, 96, 128, 160, 192, 224, 256, 288, 320, 352, 384, 416, 448, 0]
    BR_M1 = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0]
    BR_M2 = [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, 0]
    data = path.read_bytes()
    i, total, sr_ = 0, 0, None
    n = len(data)
    while i < n - 4:
        if data[i] != 0xFF or (data[i + 1] & 0xE0) != 0xE0:
            i += 1
            continue
        b1, b2 = data[i + 1], data[i + 2]
        ver = (b1 >> 3) & 0x03
        layer = (b1 >> 1) & 0x03
        if ver == 1 or layer == 0:
            i += 1
            continue
        br_idx = (b2 >> 4) & 0x0F
        if br_idx in (0, 15):
            i += 1
            continue
        sr = SR.get((b2 >> 2) & 0x03)
        if sr is None:
            i += 1
            continue
        if ver == 2:
            sr //= 2
        elif ver == 0:
            sr //= 4
        pad = (b2 >> 1) & 0x01
        m1 = ver == 3
        if layer == 3:
            spf, fl = 384, (12 * BR_L1[br_idx] * 1000 // sr + pad) * 4
        elif layer == 2:
            spf, fl = 1152, 144 * (BR_M1 if m1 else BR_M2)[br_idx] * 1000 // sr + pad
        else:
            spf = 1152 if m1 else 576
            fl = (144 if m1 else 72) * (BR_M1 if m1 else BR_M2)[br_idx] * 1000 // sr + pad
        if fl <= 0 or i + fl > n:
            i += 1
            continue
        total += spf
        sr_ = sr
        i += fl
    if sr_ is None or total == 0:
        raise ValueError("无法解析 MP3 帧")
    return total / sr_


def _fmt_ts(sec: float) -> str:
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _estimate_words(text: str, duration: float) -> list[dict]:
    """降级方案：按字符数比例估算词时间轴。"""
    chars = [c for c in text if not c.isspace()]
    if not chars:
        return [{"text": text, "start": 0.0, "end": duration, "duration": duration}]
    per = duration / len(chars)
    words, cursor = [], 0.0
    for w in text.split():
        d = len(w) * per
        words.append({"text": w, "start": round(cursor, 3),
                      "end": round(cursor + d, 3), "duration": round(d, 3)})
        cursor += d
    return words


async def _synth(args) -> dict:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    mp3_path = out_dir / f"{args.stem}.mp3"
    vtt_path = out_dir / f"{args.stem}.vtt"
    cap_path = out_dir / f"{args.stem}.captions.json"

    boundary = args.boundary
    words: list[dict] = []
    sentences: list[dict] = []
    used_boundary = boundary

    for attempt in (boundary, "SentenceBoundary"):
        communicate = edge_tts.Communicate(
            args.text, args.voice,
            rate=args.rate, volume=args.volume, pitch=args.pitch,
            boundary=attempt,
        )
        audio_bytes = bytearray()
        try:
            async for chunk in communicate.stream():
                ctype = chunk["type"]
                if ctype == "audio":
                    audio_bytes.extend(chunk["data"])
                elif ctype == "WordBoundary":
                    offset_s = chunk["offset"] / 1e7  # 100ns 单位 → 秒
                    dur_s = chunk["duration"] / 1e7
                    words.append({"text": chunk["text"],
                                  "start": round(offset_s, 3),
                                  "end": round(offset_s + dur_s, 3),
                                  "duration": round(dur_s, 3)})
                elif ctype == "SentenceBoundary":
                    offset_s = chunk["offset"] / 1e7
                    dur_s = chunk["duration"] / 1e7
                    sentences.append({"text": chunk["text"],
                                      "start": round(offset_s, 3),
                                      "end": round(offset_s + dur_s, 3)})
        except Exception as exc:  # noqa: BLE001
            print(f"WARN: {attempt} 流式获取失败: {exc}", file=sys.stderr)
            audio_bytes = bytearray()

        if not audio_bytes:
            continue
        mp3_path.write_bytes(audio_bytes)
        if words:
            used_boundary = "WordBoundary"
            break
        if sentences:
            used_boundary = "SentenceBoundary"
            break

    if not mp3_path.exists() or mp3_path.stat().st_size == 0:
        raise SystemExit("ERROR: 配音生成失败（无音频输出）")

    # 降级：WordBoundary/SentenceBoundary 都没有 → 按音频时长估算
    if not words and not sentences:
        used_boundary = "estimate"
        try:
            duration = _mp3_duration_seconds(mp3_path)
        except ValueError:
            duration = 1.0
        words = _estimate_words(args.text, duration)

    # captions.json
    caption = {"text": args.text, "words": words, "sentences": sentences, "boundary": used_boundary}
    cap_path.write_text(json.dumps(caption, ensure_ascii=False, indent=2), encoding="utf-8")

    # VTT（句级；无句级则用整句 + 词范围）
    if sentences:
        vtt_body = "WEBVTT\n\n"
        for s in sentences:
            vtt_body += f"{_fmt_ts(s['start'])} --> {_fmt_ts(s['end'])}\n{s['text']}\n\n"
    else:
        start = words[0]["start"] if words else 0.0
        end = words[-1]["end"] if words else 1.0
        vtt_body = f"WEBVTT\n\n{_fmt_ts(start)} --> {_fmt_ts(end)}\n{args.text}\n"
    vtt_path.write_text(vtt_body, encoding="utf-8")

    duration = words[-1]["end"] if words else (sentences[-1]["end"] if sentences else 0.0)
    print(f"mp3={mp3_path}")
    print(f"vtt={vtt_path}")
    print(f"captions={cap_path}")
    print(f"boundary={used_boundary}")
    print(f"words={len(words)}")
    print(f"duration={duration:.3f}")
    return caption


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate voiceover with word-level timeline via Edge TTS")
    parser.add_argument("--text", required=True, help="配音文本（口语化，一句一次调用）")
    parser.add_argument("--voice", default="zh-CN-XiaoxiaoNeural")
    parser.add_argument("--rate", default="+0%")
    parser.add_argument("--volume", default="+0%")
    parser.add_argument("--pitch", default="+0Hz")
    parser.add_argument("--out-dir", default="audio/voiceover")
    parser.add_argument("--stem", default="vo")
    parser.add_argument("--boundary", default="WordBoundary",
                        choices=["WordBoundary", "SentenceBoundary"])
    args = parser.parse_args()

    try:
        asyncio.run(_synth(args))
    except SystemExit as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
