#!/usr/bin/env python3
"""Freeze the tau_telecom_pool_v1 skill library: copy, per-file sha256, manifest."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "autoskill_state" / "skillbank_trajectory" / "Users" / "tau_telecom_pool_v1"
DST = ROOT / "frozen_skills"
LOG = Path("/var/tmp/skillsloop268_learn.log")


def main() -> None:
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST)

    files = {}
    for path in sorted(DST.rglob("*")):
        if path.is_file():
            rel = str(path.relative_to(DST)).replace("\\", "/")
            files[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    skills = sorted({path.parent.name for path in DST.rglob("SKILL.md")})

    result = None
    if LOG.exists():
        text = LOG.read_text(encoding="utf-8", errors="replace")
        for line in reversed(text.splitlines()):
            line = line.strip()
            if line.startswith("{{"):
                try:
                    result = json.loads(line)
                    break
                except ValueError:
                    continue

    manifest = {
        "namespace": "tau_telecom_pool_v1",
        "extractor": "autoskill offline agentic trajectory",
        "skill_count": len(skills),
        "skills": skills,
        "files": files,
        "build_result": result,
        "note": "Frozen library for the B1 arm; no maintenance or edits during evaluation.",
    }
    (ROOT / "frozen_skills_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("frozen skills:", len(skills), skills)
    print("files:", len(files))


if __name__ == "__main__":
    main()
