"""Direct verification: read evidence in matched session sqlites for v4-B1 sims."""
import json
import random
import re
import sqlite3
import zstandard
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sims = json.loads((ROOT / "runs" / "test_v4" / "autoskill_library.json").read_text())["simulations"]
audit = json.loads((ROOT / "reports" / "skill_read_audit_v4.json").read_text())
by_key = {(r["task"], r["session"]): r for r in audit["sessions"]}

sess_by_task = {}
for p in (ROOT / "runs" / "autoskill_library").glob("task_*/*/turn_000_prompt.txt"):
    sess_by_task.setdefault(p.parent.parent.name, []).append(p.parent)


def first_epoch(s):
    return (s / "turn_000_prompt.txt").stat().st_mtime


def load_payload(rec):
    blob = rec.get("event_json") or rec.get("event_zstd") or b""
    if isinstance(blob, (memoryview, bytes)):
        try:
            return zstandard.ZstdDecompressor().decompress(bytes(blob)).decode("utf-8", "replace")
        except Exception:
            return bytes(blob).decode("utf-8", "replace")
    return str(blob)


picks, no_read = [], []
for sim in sims:
    task = "task_" + str(sim["task_id"])
    start = datetime.fromisoformat(sim["start_time"]).timestamp()
    cands = sess_by_task.get(task, [])
    best = min(cands, key=lambda s: abs(first_epoch(s) - start)) if cands else None
    if best is None:
        continue
    rec = by_key.get((task, best.name))
    (picks if (rec and rec["triggered_skills"]) else no_read).append((sim, best, rec))

print("with-read matched sims:", len(picks), "| no-read matched sims:", len(no_read))

random.seed(7)
for sim, sess, rec in random.sample(picks, 3):
    db = sess / "openclaw_state_archive/agents/main/agent/openclaw-agent.sqlite"
    con = sqlite3.connect("file:" + str(db) + "?mode=ro", uri=True)
    cur = con.cursor()
    cols = [r[1] for r in cur.execute("PRAGMA table_info(transcript_events)")]
    hits, sample = 0, None
    for row in cur.execute("SELECT * FROM transcript_events"):
        payload = load_payload(dict(zip(cols, row)))
        compact = payload.replace(" ", "")
        if '"type":"toolCall"' in compact and "SKILL.md" in compact:
            m = re.search(r"skills/([A-Za-z0-9_\-]+)/SKILL\.md", payload)
            if m:
                hits += 1
                sample = m.group(0)[:70]
    con.close()
    print("task", sim["task_id"], "trial", sim["trial"], "reward", sim["reward_info"]["reward"],
          "| sqlite toolCall .. SKILL.md hits =", hits, "|", sample, "| scan:", rec["triggered_skills"])

for sim, sess, rec in no_read:
    print("NO-READ sim: task", sim["task_id"], "trial", sim["trial"],
          "reward", sim["reward_info"]["reward"], "| session", sess.name[:8],
          "| refs:", (rec or {}).get("prompt_skill_refs"), "| triggers:", (rec or {}).get("triggered_skills"))
