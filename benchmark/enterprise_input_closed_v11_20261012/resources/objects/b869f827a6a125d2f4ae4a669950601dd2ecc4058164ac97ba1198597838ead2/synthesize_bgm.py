#!/usr/bin/env python3
"""原创程序化 BGM 合成器（纯标准库，零依赖）。

音频工程要点（v4，含 Music Sections）：
- 每个音符独立 ADSR 包络，Attack/Release 起止均为 0 → 无 click/pop
- 和弦间自然重叠（前和弦 release 延入后和弦 attack）→ 无硬切
- detune 每次发音固定（绝非逐采样随机）→ 无宽带噪声
- 每层独立 gain + Master Headroom（目标峰值 ≤ -4dBFS）+ tanh 软限幅 → 无 clipping
- 去除 DC Offset；Master Fade In 1s / Fade Out 2.5s 平滑到真 0
- 立体声宽度、滤波运动（LFO 扫频）、轻量反馈延迟混响
- **Music Sections**：Intro / A / B / Highlight / Outro，各 Section 可改变
  层组合 / 能量 / 滤波 / 和弦 Voicing / 密度，但保持同一音乐主题

Preset 系统（8 种）：ambient-tech / corporate-clean / documentary / minimal-piano /
premium-product / cinematic-soft / warm-education / future-interface

用法:
  python3 synthesize_bgm.py --preset ambient-tech --duration 36 \
      --sections "0-4:intro,4-16:a,16-25:b,25-31:highlight,31-36:outro" \
      --out audio/music/bgm_bench.wav
"""
import argparse
import math
import random
import struct
import sys
import wave
from pathlib import Path

SR = 44100

# ---------- 音高 ----------
_NOTE_IDX = {n: i for i, n in enumerate(
    ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}


def note_freq(name: str) -> float:
    name = name.strip()
    acc = 0
    if name[1:2] == "#":
        acc, name = 1, name[0] + name[2:]
    elif name[1:2] == "b":
        acc, name = -1, name[0] + name[2:]
    midi = _NOTE_IDX[name[0]] + acc + (int(name[1:]) + 1) * 12
    return 440.0 * 2 ** ((midi - 69) / 12)


CHORDS = {
    "Am":  ["A3", "C4", "E4"], "F":  ["F3", "A3", "C4"],
    "C":   ["C3", "E3", "G3"], "G":  ["G2", "B3", "D4"],
    "Dm":  ["D3", "F3", "A3"], "Em": ["E3", "G3", "B3"],
    "Bb":  ["Bb2", "D3", "F3"], "Eb": ["Eb3", "G3", "Bb3"],
    "Cm":  ["C3", "Eb3", "G3"], "Ab": ["Ab2", "C3", "Eb3"],
    "E":   ["E2", "G#3", "B3"], "A":  ["A2", "C#3", "E3"],
    "D":   ["D3", "F#3", "A3"], "F#m":["F#2", "A3", "C#4"],
    "Gm":  ["G2", "Bb3", "D4"], "Cadd9": ["C3", "E3", "G3", "D4"],
}

PRESETS = {
    "ambient-tech": {
        "bpm": 84, "chords": ["Am", "F", "C", "G"],
        "energy": 0.35, "stereo_width": 0.7, "filter": 0.45, "reverb": 0.18,
        "fade_out": 2.5, "master_gain": 0.60,
        "layers": [
            {"type": "pad",   "gain": 0.34, "attack": 1.4, "release": 2.2, "octave": 0},
            {"type": "pulse", "gain": 0.10, "attack": 0.02, "release": 0.14, "octave": -1},
            {"type": "arp",   "gain": 0.09, "attack": 0.01, "release": 0.22, "octave": 1,
             "density": 0.5},
            {"type": "bass",  "gain": 0.16, "attack": 0.05, "release": 0.9, "octave": -1},
        ],
    },
    "corporate-clean": {
        "bpm": 96, "chords": ["C", "Am", "F", "G"],
        "energy": 0.45, "stereo_width": 0.5, "filter": 0.5, "reverb": 0.12,
        "fade_out": 2.5, "master_gain": 0.60,
        "layers": [
            {"type": "pluck", "gain": 0.20, "attack": 0.005, "release": 0.45, "octave": 1,
             "density": 0.5},
            {"type": "pad",   "gain": 0.22, "attack": 0.6, "release": 1.6, "octave": 0},
            {"type": "pulse", "gain": 0.08, "attack": 0.02, "release": 0.12, "octave": -1},
        ],
    },
    "documentary": {
        "bpm": 72, "chords": ["Dm", "Bb", "F", "C"],
        "energy": 0.2, "stereo_width": 0.6, "filter": 0.35, "reverb": 0.22,
        "fade_out": 3.0, "master_gain": 0.58,
        "layers": [
            {"type": "pad",   "gain": 0.36, "attack": 2.0, "release": 3.0, "octave": 0},
            {"type": "pluck", "gain": 0.08, "attack": 0.01, "release": 1.2, "octave": 1,
             "density": 0.25},
        ],
    },
    "minimal-piano": {
        "bpm": 80, "chords": ["Cadd9", "Am", "F", "G"],
        "energy": 0.25, "stereo_width": 0.5, "filter": 0.4, "reverb": 0.2,
        "fade_out": 2.5, "master_gain": 0.58,
        "layers": [
            {"type": "pluck", "gain": 0.24, "attack": 0.004, "release": 1.6, "octave": 1,
             "density": 0.4, "piano": True},
            {"type": "pad",   "gain": 0.18, "attack": 1.0, "release": 2.4, "octave": 0},
        ],
    },
    "premium-product": {
        "bpm": 90, "chords": ["F", "Dm", "Bb", "C"],
        "energy": 0.4, "stereo_width": 0.8, "filter": 0.55, "reverb": 0.25,
        "fade_out": 3.0, "master_gain": 0.60,
        "layers": [
            {"type": "pad",   "gain": 0.28, "attack": 0.8, "release": 2.0, "octave": 0},
            {"type": "pluck", "gain": 0.14, "attack": 0.005, "release": 0.5, "octave": 1,
             "density": 0.5},
            {"type": "arp",   "gain": 0.07, "attack": 0.01, "release": 0.3, "octave": 2,
             "density": 0.35},
            {"type": "pulse", "gain": 0.07, "attack": 0.02, "release": 0.16, "octave": -1},
        ],
    },
    "cinematic-soft": {
        "bpm": 70, "chords": ["Am", "F", "C", "G"],
        "energy": 0.3, "stereo_width": 0.9, "filter": 0.4, "reverb": 0.3,
        "fade_out": 3.0, "master_gain": 0.60,
        "layers": [
            {"type": "pad",   "gain": 0.38, "attack": 2.5, "release": 3.5, "octave": 0},
            {"type": "pluck", "gain": 0.06, "attack": 0.01, "release": 1.5, "octave": 2,
             "density": 0.15},
            {"type": "bass",  "gain": 0.14, "attack": 0.1, "release": 1.5, "octave": -2},
        ],
    },
    "warm-education": {
        "bpm": 78, "chords": ["C", "G", "Am", "F"],
        "energy": 0.3, "stereo_width": 0.55, "filter": 0.42, "reverb": 0.16,
        "fade_out": 2.5, "master_gain": 0.60,
        "layers": [
            {"type": "pad",   "gain": 0.32, "attack": 1.2, "release": 2.2, "octave": 0},
            {"type": "pluck", "gain": 0.12, "attack": 0.006, "release": 0.9, "octave": 1,
             "density": 0.35},
            {"type": "pulse", "gain": 0.07, "attack": 0.02, "release": 0.15, "octave": -1},
        ],
    },
    "future-interface": {
        "bpm": 100, "chords": ["Dm", "Bb", "F", "C"],
        "energy": 0.5, "stereo_width": 0.75, "filter": 0.5, "reverb": 0.2,
        "fade_out": 2.5, "master_gain": 0.58,
        "layers": [
            {"type": "pad",   "gain": 0.26, "attack": 0.5, "release": 1.8, "octave": 0},
            {"type": "arp",   "gain": 0.12, "attack": 0.008, "release": 0.18, "octave": 1,
             "density": 0.75},
            {"type": "pulse", "gain": 0.10, "attack": 0.02, "release": 0.14, "octave": -1},
            {"type": "bass",  "gain": 0.14, "attack": 0.04, "release": 0.8, "octave": -1},
        ],
    },
}

# ---------- Music Sections ----------
# 各 Section 的层增益倍率 / 滤波中心 / 密度倍率 / voicing 提升
SECTION_DEFS = {
    "intro":     {"layers": {"pad": 1.0},                       "filter": 0.35, "density": 0.6, "lift": 0},
    "a":         {"layers": {"pad": 1.0, "pulse": 1.0, "bass": 1.0},
                  "filter": 0.5,  "density": 0.8, "lift": 0},
    "b":         {"layers": {"pad": 1.0, "pulse": 1.0, "bass": 1.0, "arp": 1.0},
                  "filter": 0.65, "density": 1.0, "lift": 0},
    "highlight": {"layers": {"pad": 1.0, "pulse": 1.0, "bass": 1.0, "arp": 1.0, "pluck": 1.0},
                  "filter": 0.85, "density": 1.1, "lift": 1},
    "outro":     {"layers": {"pad": 0.8},                       "filter": 0.4,  "density": 0.5, "lift": 0},
}


def parse_sections(spec: str, total: float) -> list[tuple[float, float, str]]:
    """'0-4:intro,4-16:a,...' → [(start, end, name)]。'auto' 按比例划分。"""
    if not spec or spec == "auto":
        cuts = [0.0, 0.12, 0.42, 0.62, 0.78, 1.0]
        names = ["intro", "a", "b", "highlight", "outro"]
        return [(total * cuts[i], total * cuts[i + 1], names[i]) for i in range(len(names))]
    out = []
    for part in spec.split(","):
        rng, name = part.split(":")
        s, e = rng.split("-")
        out.append((float(s), float(e), name.strip()))
    return out


def section_at(sections: list[tuple[float, float, str]], t: float) -> tuple[str, dict]:
    for s, e, name in sections:
        if s <= t < e:
            return name, SECTION_DEFS[name]
    # 超出范围取最后一段
    return sections[-1][2], SECTION_DEFS[sections[-1][2]]


def smooth_env(t: float, attack: float, sustain_until: float, release: float) -> float:
    if t <= 0:
        return 0.0
    if t < attack:
        x = t / attack
        return 0.5 - 0.5 * math.cos(math.pi * min(1.0, x))
    if t <= sustain_until:
        return 1.0
    r = t - sustain_until
    if r >= release:
        return 0.0
    x = r / release
    return 0.5 + 0.5 * math.cos(math.pi * min(1.0, x))


def render_note(buf_l, buf_r, start, dur, freq, gain, attack, release,
                width, seed, piano=False, octave_lift=0) -> None:
    rng = random.Random(seed)
    freq *= 2 ** octave_lift
    n_start = int(start * SR)
    n_end = min(len(buf_l), int((start + dur + release + 0.05) * SR))
    det_l = freq * (1 - 0.0015)
    det_r = freq * (1 + 0.0015)
    h_gains = [1.0, 0.5, 0.25]
    if piano:
        h_gains = [1.0, rng.uniform(0.3, 0.5), rng.uniform(0.08, 0.2)]
    for i in range(n_start, n_end):
        t = i / SR
        local = t - start
        env = smooth_env(local, attack, dur, release)
        if env <= 0.0:
            continue
        vl = vr = 0.0
        for hi, hg in enumerate(h_gains):
            f = freq * (hi + 1)
            vl += math.sin(2 * math.pi * f * det_l / freq * t) * hg
            vr += math.sin(2 * math.pi * f * det_r / freq * t) * hg
        gl = gain * (1.0 if width >= 0 else 0.5)
        gr = gain * (0.5 if width >= 0 else 1.0)
        buf_l[i] += vl * env * gl
        buf_r[i] += vr * env * gr


def note_events(preset, total, sections) -> list[dict]:
    bpm = preset["bpm"]
    beat = 60.0 / bpm
    bar = beat * 4
    chord_len = bar * 2
    events = []
    n_chords = max(1, math.ceil(total / chord_len))
    for ci in range(n_chords):
        chord_name = preset["chords"][ci % len(preset["chords"])]
        freqs = [note_freq(n) for n in CHORDS[chord_name]]
        c_start = ci * chord_len
        for layer in preset["layers"]:
            ltype = layer["type"]
            if ltype == "pad":
                for f in freqs:
                    events.append({"start": c_start, "dur": chord_len * 1.2,
                                   "freq": f * 2 ** layer.get("octave", 0),
                                   "layer": layer})
            elif ltype == "bass":
                events.append({"start": c_start, "dur": chord_len * 1.1,
                               "freq": freqs[0] / 2 * 2 ** layer.get("octave", 0),
                               "layer": layer})
            elif ltype == "pulse":
                for b in range(int(chord_len / beat)):
                    events.append({"start": c_start + b * beat, "dur": beat * 0.9,
                                   "freq": freqs[0] / 2 * 2 ** layer.get("octave", 0),
                                   "layer": layer})
            elif ltype == "arp":
                step = beat / 2
                density = layer.get("density", 0.6)
                idx = 0
                t = c_start
                while t < c_start + chord_len:
                    if random.Random(int(t * 1000)).random() < density:
                        f = freqs[idx % len(freqs)] * 2 ** layer.get("octave", 0)
                        events.append({"start": t, "dur": step * 0.9, "freq": f,
                                       "layer": layer})
                    idx += 1
                    t += step
            elif ltype == "pluck":
                density = layer.get("density", 0.4)
                step = beat
                t = c_start + beat
                while t < c_start + chord_len - beat:
                    rng = random.Random(int(t * 1000))
                    if rng.random() < density:
                        f = freqs[rng.randrange(len(freqs))] * 2 ** layer.get("octave", 0)
                        events.append({"start": t, "dur": step * 0.8, "freq": f,
                                       "layer": layer})
                    t += step
    # 按 Section 标注：层增益倍率 / 密度过滤 / voicing 提升
    filtered = []
    for ev in events:
        name, sdef = section_at(sections, ev["start"])
        ltype = ev["layer"]["type"]
        if ltype not in sdef["layers"]:
            continue
        # 密度过滤（arp/pluck/pulse 按 density 倍率概率保留）
        if ltype in ("arp", "pluck", "pulse"):
            r = random.Random(int(ev["start"] * 7919) + int(ev["freq"]))
            if r.random() > sdef["density"]:
                continue
        ev["section"] = name
        ev["gain_mult"] = sdef["layers"][ltype]
        ev["lift"] = sdef["lift"]
        filtered.append(ev)
    return filtered


def synth(preset_name, total, only_layers, sections_spec, seed) -> tuple[list, list]:
    preset = PRESETS[preset_name]
    sections = parse_sections(sections_spec, total)
    n = int(total * SR)
    buf_l = [0.0] * n
    buf_r = [0.0] * n
    width = preset.get("stereo_width", 0.6)

    events = note_events(preset, total, sections)
    for ev in events:
        layer = ev["layer"]
        if only_layers and layer["type"] not in only_layers:
            continue
        render_note(
            buf_l, buf_r, ev["start"], ev["dur"], ev["freq"],
            gain=layer["gain"] * ev["gain_mult"],
            attack=layer["attack"], release=layer["release"],
            width=width,
            seed=seed + int(ev["start"] * 1000) + int(ev["freq"]),
            piano=layer.get("piano", False),
            octave_lift=ev["lift"],
        )

    # 滤波运动（一阶低通，按 Section 分段 + LFO）
    filt = [0.0, 0.0]
    for i in range(n):
        t = i / SR
        _, sdef = section_at(sections, t)
        fc_center = 2500 + 7500 * sdef["filter"]
        lfo = 0.5 + 0.5 * math.sin(2 * math.pi * 0.06 * t)
        fc = 1800 + (fc_center - 1800) * lfo
        a = 1.0 - math.exp(-2 * math.pi * fc / SR)
        filt[0] += a * (buf_l[i] - filt[0])
        filt[1] += a * (buf_r[i] - filt[1])
        buf_l[i], buf_r[i] = filt[0], filt[1]

    # 轻量反馈延迟混响
    wet = preset.get("reverb", 0.15)
    if wet > 0:
        dl, dr = int(0.037 * SR), int(0.043 * SR)
        dly_l, dly_r = [0.0] * dl, [0.0] * dr
        il = ir = 0
        for i in range(n):
            out_l, out_r = dly_l[il], dly_r[ir]
            dly_l[il] = buf_l[i] + out_l * 0.42
            dly_r[ir] = buf_r[i] + out_r * 0.42
            buf_l[i] += out_l * wet
            buf_r[i] += out_r * wet
            il = (il + 1) % dl
            ir = (ir + 1) % dr

    # DC 去除
    mean_l, mean_r = sum(buf_l) / n, sum(buf_r) / n
    for i in range(n):
        buf_l[i] -= mean_l
        buf_r[i] -= mean_r

    # 软限幅 + 归一化（Headroom）
    peak = 0.0
    for i in range(n):
        for b in (buf_l, buf_r):
            a = abs(b[i])
            if a > peak:
                peak = a
    target = 0.60
    scale = target / peak if peak > 0 else 1.0
    for i in range(n):
        buf_l[i] = math.tanh(buf_l[i] * scale * 1.35) / math.tanh(1.35) * target
        buf_r[i] = math.tanh(buf_r[i] * scale * 1.35) / math.tanh(1.35) * target

    # Master Fade In / Out
    fade_in = int(1.0 * SR)
    fade_out = int(preset.get("fade_out", 2.5) * SR)
    for i in range(min(fade_in, n)):
        env = 0.5 - 0.5 * math.cos(math.pi * i / fade_in)
        buf_l[i] *= env
        buf_r[i] *= env
    for i in range(min(fade_out, n)):
        k = n - 1 - i
        env = 0.5 - 0.5 * math.cos(math.pi * i / fade_out)
        buf_l[k] *= env
        buf_r[k] *= env
    return buf_l, buf_r


def write_wav(path, buf_l, buf_r) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        frames = bytearray()
        for i in range(len(buf_l)):
            l = max(-1.0, min(1.0, buf_l[i]))
            r = max(-1.0, min(1.0, buf_r[i]))
            frames += struct.pack("<hh", int(l * 32767), int(r * 32767))
        w.writeframes(bytes(frames))


def main() -> int:
    parser = argparse.ArgumentParser(description="Procedural BGM synthesizer (presets + music sections)")
    parser.add_argument("--preset", default="ambient-tech", choices=sorted(PRESETS))
    parser.add_argument("--duration", type=float, default=20.0)
    parser.add_argument("--sections", default="auto",
                        help="'0-4:intro,4-16:a,16-25:b,25-31:highlight,31-40:outro' 或 auto")
    parser.add_argument("--out", default=None)
    parser.add_argument("--layers", default=None, help="仅渲染指定层（测试用）")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    out = Path(args.out or f"audio/music/bgm_{args.preset}.wav")
    only = args.layers.split(",") if args.layers else None
    buf_l, buf_r = synth(args.preset, args.duration, only, args.sections, args.seed)
    write_wav(out, buf_l, buf_r)
    layers = ",".join(only) if only else "all"
    print(f"bgm={out}")
    print(f"preset={args.preset} layers={layers} duration={args.duration:.1f}s sections={args.sections}")
    print("license=CC0(原创合成) commercial_use=true derivatives=true attribution_required=false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
