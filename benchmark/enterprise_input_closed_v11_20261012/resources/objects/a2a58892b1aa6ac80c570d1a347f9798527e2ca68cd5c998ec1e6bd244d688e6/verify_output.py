#!/usr/bin/env python3
"""最终成片 QA：校验 MP4 存在、大小、时长、分辨率、FPS。纯标准库解析 MP4 box。

用法:
  python3 verify_output.py <output.mp4> [--expect-width 1920] [--expect-height 1080] [--expect-duration 12]
退出码: 0 = 全部通过；1 = 存在失败项（会打印失败原因）
"""
import argparse
import struct
import sys
from pathlib import Path


def read_boxes(data: bytes, start: int = 0, end: int | None = None) -> list[tuple[str, int, int]]:
    """返回 [(box_type, box_start, box_end)]，支持 64 位 size。"""
    end = end if end is not None else len(data)
    boxes = []
    i = start
    while i + 8 <= end:
        size = struct.unpack(">I", data[i:i + 4])[0]
        btype = data[i + 4:i + 8].decode("latin1")
        header = 8
        if size == 1:
            size = struct.unpack(">Q", data[i + 8:i + 16])[0]
            header = 16
        elif size == 0:
            size = end - i
        if size < header:
            break
        boxes.append((btype, i, i + size))
        i += size
    return boxes


def find_box(data: bytes, path: list[str], start: int = 0, end: int | None = None):
    """按路径查找嵌套 box，返回 (box_start, box_end) 或 None。"""
    end = end if end is not None else len(data)
    for btype, bs, be in read_boxes(data, start, end):
        if btype == path[0]:
            if len(path) == 1:
                return bs, be
            return find_box(data, path[1:], bs + 8, be)
    return None


def mvhd_info(data: bytes, bs: int, be: int) -> tuple[int, int]:
    version = data[bs + 8]
    if version == 1:
        timescale = struct.unpack(">I", data[bs + 28:bs + 32])[0]
        duration = struct.unpack(">Q", data[bs + 32:bs + 40])[0]
    else:
        timescale = struct.unpack(">I", data[bs + 20:bs + 24])[0]
        duration = struct.unpack(">I", data[bs + 24:bs + 28])[0]
    return timescale, duration


def tkhd_size(data: bytes, bs: int, be: int) -> tuple[int, int]:
    version = data[bs + 8]
    off = bs + 8 + (4 if version == 1 else 0)
    # width/height 在 tkhd 末尾，16.16 定点数
    w = struct.unpack(">I", data[be - 8:be - 4])[0] >> 16
    h = struct.unpack(">I", data[be - 4:be])[0] >> 16
    return w, h


def video_track_stats(data: bytes) -> dict:
    """返回第一个视频轨道的 {width, height, duration, timescale, fps}。"""
    moov = find_box(data, ["moov"])
    if not moov:
        raise ValueError("缺少 moov box")
    moov_s, moov_e = moov
    for btype, trak_s, trak_e in read_boxes(data, moov_s + 8, moov_e):
        if btype != "trak":
            continue
        # 注意: 以下查找以 trak 内部为起点，路径不要再包含 trak 自身
        tkhd = find_box(data, ["tkhd"], trak_s + 8, trak_e)
        if not tkhd:
            continue
        w, h = tkhd_size(data, tkhd[0], tkhd[1])
        if w == 0 and h == 0:
            continue
        mdhd = find_box(data, ["mdia", "mdhd"], trak_s + 8, trak_e)
        if not mdhd:
            continue
        ts, dur = mvhd_info(data, mdhd[0], mdhd[1])
        stts = find_box(data, ["mdia", "minf", "stbl", "stts"], trak_s + 8, trak_e)
        samples = 0
        if stts:
            stts_s, stts_e = stts[0], stts[1]
            entry_count = struct.unpack(">I", data[stts_s + 12:stts_s + 16])[0]
            pos = stts_s + 16
            for _ in range(entry_count):
                count, _delta = struct.unpack(">II", data[pos:pos + 8])
                samples += count
                pos += 8
        fps = (samples / (dur / ts)) if dur else 0
        return {"width": w, "height": h, "duration": dur / ts, "timescale": ts, "fps": round(fps, 3)}
    raise ValueError("未找到视频轨道")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--expect-width", type=int)
    parser.add_argument("--expect-height", type=int)
    parser.add_argument("--expect-duration", type=float)
    args = parser.parse_args()

    path = Path(args.path)
    failures = []

    if not path.exists():
        print(f"[FAIL] 文件不存在: {path}")
        return 1
    size = path.stat().st_size
    if size == 0:
        print("[FAIL] 文件为空")
        return 1
    print(f"[OK]   文件存在，大小 {size / 1024:.1f} KB")

    data = path.read_bytes()
    try:
        stats = video_track_stats(data)
    except ValueError as exc:
        print(f"[FAIL] 解析失败: {exc}")
        return 1

    print(f"[OK]   分辨率 {stats['width']}x{stats['height']}")
    print(f"[OK]   时长 {stats['duration']:.3f}s，FPS ≈ {stats['fps']}")

    if args.expect_width and stats["width"] != args.expect_width:
        failures.append(f"分辨率宽不符: 期望 {args.expect_width}，实际 {stats['width']}")
    if args.expect_height and stats["height"] != args.expect_height:
        failures.append(f"分辨率高不符: 期望 {args.expect_height}，实际 {stats['height']}")
    if args.expect_duration and abs(stats["duration"] - args.expect_duration) > 1.5:
        failures.append(f"时长不符: 期望 ~{args.expect_duration}s，实际 {stats['duration']:.2f}s")

    if failures:
        for f in failures:
            print(f"[FAIL] {f}")
        return 1
    print("[OK]   全部检查通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
