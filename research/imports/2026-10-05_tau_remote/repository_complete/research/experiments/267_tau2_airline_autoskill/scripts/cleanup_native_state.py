"""Reclaim space from idle native session state in /var/tmp/skillsloop148.

Only deletes a native dir when BOTH hold:
  * no file inside modified within the last 40 minutes (no live session), and
  * the owning session dir (reverse-mapped via sha256 of session path) contains
    an openclaw_state_archive (native state already copied out and preserved
    under runs/), or a native_state_path.txt sibling mapping is archived.

Default is dry-run; pass --apply to delete.
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import time
from pathlib import Path

NATIVE_ROOT = Path("/var/tmp/skillsloop267")
RUN_ROOTS = [
    Path("/mnt/d/skillloop/research/experiments/148_tau2_retail_autoskill/runs"),
]
IDLE_SECONDS = 40 * 60


def dir_size_mb(path: Path) -> float:
    total = 0
    for f in path.rglob("*"):
        try:
            if f.is_file():
                total += f.stat().st_size
        except OSError:
            pass
    return total / 1e6


def newest_mtime(path: Path) -> float:
    newest = 0.0
    for f in path.rglob("*"):
        try:
            m = f.stat().st_mtime
        except OSError:
            continue
        newest = max(newest, m)
    return newest


def archived_session_dirs() -> set[Path]:
    """Session dirs that already hold an openclaw_state_archive."""
    archived = set()
    for run_root in RUN_ROOTS:
        for archive in run_root.glob("*/task_*/*/openclaw_state_archive"):
            archived.add(archive.parent)
    return archived


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="actually delete")
    parser.add_argument("--idle-minutes", type=int, default=40)
    args = parser.parse_args()

    archived = archived_session_dirs()
    hashes = {hashlib.sha256(str(s).encode()).hexdigest()[:24]: s for s in archived}
    print(f"archived session dirs: {len(archived)}")

    now = time.time()
    idle_candidates = []
    active = []
    for native in sorted(NATIVE_ROOT.iterdir()):
        if not native.is_dir():
            continue
        last = newest_mtime(native)
        age_min = (now - last) / 60 if last else 9999
        if age_min < args.idle_minutes:
            active.append((native.name, round(age_min, 1)))
            continue
        owner = hashes.get(native.name)
        idle_candidates.append((native, owner))

    print(f"active native dirs (<{args.idle_minutes} min): {len(active)}")
    deletable = [(n, o) for n, o in idle_candidates if o is not None]
    orphan = [(n, o) for n, o in idle_candidates if o is None]
    size = sum(dir_size_mb(n) for n, _ in deletable)
    print(f"idle dirs w/ archived session: {len(deletable)} — reclaimable ~{size:.0f} MB")
    print(f"idle dirs without archive match (kept): {len(orphan)}")

    if args.apply:
        freed = 0.0
        for native, _ in deletable:
            freed += dir_size_mb(native)
            shutil.rmtree(native, ignore_errors=True)
        print(f"deleted {len(deletable)} dirs, freed ~{freed:.0f} MB")


if __name__ == "__main__":
    main()
