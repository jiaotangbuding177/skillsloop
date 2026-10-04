"""Adapt 267/268 learning scripts: domain HINT + trajectory-path freeze script."""
from pathlib import Path

ROOT = Path("/mnt/d/skillloop/research/experiments")

AIRLINE_HINT = (
    "Airline customer-service workflows: user identity lookup, reservation inspection, "
    "policy-grounded itinerary changes (cancellation, flight change, baggage, passenger updates), "
    "confirming with the customer before any write, the write itself, and the follow-up reply. "
    "Also capture failure-avoidance lessons: never fabricate reservation ids or prices; verify "
    "with tools before answering; if identity lookup fails, ask for an alternative identifier."
)
TELECOM_HINT = (
    "Telecom customer-support troubleshooting workflows: symptom intake, checking device/line "
    "state, systematic remediation steps (airplane mode, network mode preference, APN settings, "
    "app permissions, data saver, roaming, SIM reseat, reboot), verifying the fix, and closing "
    "the interaction. Also capture failure-avoidance lessons: verify each change through the "
    "tools; never claim the issue is resolved before the tools confirm it."
)

FREEZE_TEMPLATE = '''#!/usr/bin/env python3
"""Freeze the {ns} skill library: copy, per-file sha256, manifest."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "autoskill_state" / "skillbank_trajectory" / "Users" / "{ns}"
DST = ROOT / "frozen_skills"
LOG = Path("/var/tmp/{logname}")


def main() -> None:
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST)

    files = {{}}
    for path in sorted(DST.rglob("*")):
        if path.is_file():
            rel = str(path.relative_to(DST)).replace("\\\\", "/")
            files[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    skills = sorted({{path.parent.name for path in DST.rglob("SKILL.md")}})

    result = None
    if LOG.exists():
        text = LOG.read_text(encoding="utf-8", errors="replace")
        for line in reversed(text.splitlines()):
            line = line.strip()
            if line.startswith("{{{{"):
                try:
                    result = json.loads(line)
                    break
                except ValueError:
                    continue

    manifest = {{
        "namespace": "{ns}",
        "extractor": "autoskill offline agentic trajectory",
        "skill_count": len(skills),
        "skills": skills,
        "files": files,
        "build_result": result,
        "note": "Frozen library for the B1 arm; no maintenance or edits during evaluation.",
    }}
    (ROOT / "frozen_skills_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("frozen skills:", len(skills), skills)
    print("files:", len(files))


if __name__ == "__main__":
    main()
'''

specs = {
    "267_tau2_airline_autoskill": (AIRLINE_HINT, "tau_airline_pool_v1", "skillsloop267_learn.log"),
    "268_tau2_telecom_autoskill": (TELECOM_HINT, "tau_telecom_pool_v1", "skillsloop268_learn.log"),
}

for exp, (hint, ns, logname) in specs.items():
    # 1) HINT replacement in autoskill_build_trajectory.py
    p = ROOT / exp / "scripts" / "autoskill_build_trajectory.py"
    t = p.read_text(encoding="utf-8")
    i = t.index("HINT = (")
    j = t.index(")\n", i) + 2
    t = t[:i] + "HINT = (\n    " + repr(hint) + "\n)\n" + t[j:]
    p.write_text(t, encoding="utf-8")
    print(exp, "HINT patched")

    # 2) freeze script adapted for the trajectory store
    f = ROOT / exp / "scripts" / "freeze_skills.py"
    f.write_text(FREEZE_TEMPLATE.format(ns=ns, logname=logname), encoding="utf-8")
    print(exp, "freeze_skills.py rewritten")

    import py_compile
    py_compile.compile(str(p), doraise=True)
    py_compile.compile(str(f), doraise=True)
    print(exp, "compiles ok")
print("done")
