#!/usr/bin/env python3
"""音乐清单与素材追溯管理：music_manifest.json + credits.txt + media-manifest.json。

用法:
  # 扫描音乐目录，构建/更新 manifest（合成音乐自动登记为 CC0 原创）
  python3 update_manifest.py --music-dir audio/music --out-dir . \
      [--add '{"id":"track1","title":"...","artist":"...","source":"user","source_url":"...","license":"CC BY","attribution":"..."}'] \
      [--media '{"images":[{"file":"public/bg1_001.png","source":"ai-generated"}],"voiceover":["audio/voiceover/vo1.mp3"]}']

许可证过滤（自动）:
  允许: CC0 / Public Domain / CC BY（CC BY 必须带 attribution）
  谨慎: CC BY-SA（默认仅个人使用，需确认再商用）
  拒绝商用: CC BY-NC / CC BY-ND / CC BY-NC-ND / Unknown / 未登记
"""
import argparse
import json
import sys
from pathlib import Path

ALLOWED = {"CC0", "CC0-1.0", "Public Domain", "CC BY", "CC BY 3.0", "CC BY 4.0"}
CAUTION = {"CC BY-SA", "CC BY-SA 3.0", "CC BY-SA 4.0"}
DENIED = {"CC BY-NC", "CC BY-ND", "CC BY-NC-ND", "CC BY-NC-SA", "Unknown", ""}

SYNTH_PREFIX = "bgm_"  # 本技能合成的原创音乐文件名前缀


def license_policy(license_name: str) -> dict:
    lic = (license_name or "Unknown").strip()
    if lic in ALLOWED:
        return {"usable": True, "commercial_use": True,
                "derivatives": lic != "CC BY" or True,  # CC BY 允许衍生（需署名）
                "attribution_required": lic == "CC BY"}
    if lic in CAUTION:
        return {"usable": True, "commercial_use": "confirm",
                "derivatives": True, "attribution_required": True}
    return {"usable": False, "commercial_use": False,
            "derivatives": False, "attribution_required": True}


def scan_music_dir(music_dir: Path) -> list[Path]:
    exts = {".wav", ".mp3", ".ogg", ".flac", ".m4a"}
    return sorted(p for p in music_dir.iterdir()
                  if p.is_file() and p.suffix.lower() in exts)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--music-dir", default="audio/music")
    parser.add_argument("--out-dir", default=".")
    parser.add_argument("--add", default="{}", help="附加 track 元数据 JSON（用户提供音乐用）")
    parser.add_argument("--media", default="{}", help="其他媒体素材 JSON（图片/配音/字体）")
    args = parser.parse_args()

    music_dir = Path(args.music_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = out_dir / "music_manifest.json"
    manifest: dict = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    extra: dict = json.loads(args.add or "{}")
    extra_by_id = {extra["id"]: extra} if extra.get("id") else {}

    files = scan_music_dir(music_dir)
    if not files:
        print("WARN: 音乐目录为空", file=sys.stderr)

    for f in files:
        entry_id = f.stem
        existing = manifest.get(entry_id)
        if existing:
            continue
        is_synth = f.name.startswith(SYNTH_PREFIX)
        entry = {
            "id": entry_id,
            "title": f.stem,
            "artist": "AI Video Production (synthesized)" if is_synth else "unknown",
            "local file": str(f),
            "source": "procedural-generator" if is_synth else "user-provided",
            "source_url": "",
            "generator": "synthesize_bgm.py" if is_synth else "",
            "external_samples": False if is_synth else True,
            "license": "CC0-1.0" if is_synth else "Unknown",
            "commercial_use": True if is_synth else False,
            "derivatives": True if is_synth else False,
            "attribution_required": False if is_synth else True,
            "attribution": "" if is_synth else "",
            "mood": "ambient calm",
            "genre": "ambient electronic",
            "energy": 0.2,
            "instrumental": True,
            "duration": 0.0,
        }
        if entry_id in extra_by_id:
            entry.update(extra_by_id[entry_id])
        # 依据许可证策略修正权限位
        policy = license_policy(entry["license"])
        entry["commercial_use"] = policy["commercial_use"]
        entry["derivatives"] = policy["derivatives"]
        entry["attribution_required"] = policy["attribution_required"]
        manifest[entry_id] = entry

    # 时长回填
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        import get_audio_duration  # noqa: E402
        for eid, entry in manifest.items():
            fp = Path(entry["local file"])
            if fp.exists() and not entry.get("duration"):
                try:
                    entry["duration"] = round(float(
                        get_audio_duration.main_quiet(str(fp))), 3)
                except Exception:  # noqa: BLE001
                    pass
    except Exception:  # noqa: BLE001
        pass

    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # credits.txt：需要署名的第三方音乐
    credits_lines = ["Video Credits", "============", ""]
    for eid, entry in manifest.items():
        if entry.get("attribution_required") and entry.get("attribution"):
            credits_lines.append(
                f"Music: {entry.get('title', eid)} by {entry.get('artist', 'unknown')} "
                f"({entry.get('license')}) — {entry['attribution']}"
            )
    if len(credits_lines) == 3:
        credits_lines.append("All music in this video is original (CC0) or license-confirmed.")
    (out_dir / "credits.txt").write_text("\n".join(credits_lines) + "\n", encoding="utf-8")

    # media-manifest.json：完整素材追溯
    media = json.loads(args.media or "{}")
    media_manifest = {
        "project": str(out_dir),
        "music": list(manifest.values()),
        "images": media.get("images", []),
        "voiceover": media.get("voiceover", []),
        "fonts": media.get("fonts", []),
        "generated_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
    }
    (out_dir / "media-manifest.json").write_text(
        json.dumps(media_manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    usable = [e for e in manifest.values() if e["commercial_use"] is True]
    print(f"manifest={manifest_path}")
    print(f"credits={out_dir / 'credits.txt'}")
    print(f"media-manifest={out_dir / 'media-manifest.json'}")
    print(f"tracks={len(manifest)} usable_for_commercial={len(usable)}")
    for e in manifest.values():
        print(f"  - {e['id']}: license={e['license']} "
              f"commercial={e['commercial_use']} attribution_required={e['attribution_required']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
