"""Re-point native state roots for 267/268 adapters (away from skillsloop148)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
mapping = {
    "267_tau2_airline_autoskill": "/var/tmp/skillsloop267",
    "268_tau2_telecom_autoskill": "/var/tmp/skillsloop268",
}
for exp, newroot in mapping.items():
    p = ROOT / exp / "scripts" / "tau2_openclaw_agent.py"
    t = p.read_text(encoding="utf-8")
    old = 'Path("/var/tmp/skillsloop148")'
    assert old in t, exp
    t = t.replace(old, f'Path("{newroot}")')
    # mcp bridge import stays; also re-point any helper mention
    p.write_text(t, encoding="utf-8")
    print(exp, "native root ->", newroot)

    # cleanup script default root
    c = ROOT / exp / "scripts" / "cleanup_native_state.py"
    ct = c.read_text(encoding="utf-8")
    told = 'NATIVE_ROOT = Path("/var/tmp/skillsloop148")'
    if told in ct:
        ct = ct.replace(told, f'NATIVE_ROOT = Path("{newroot}")')
        c.write_text(ct, encoding="utf-8")
        print(exp, "cleanup script root ->", newroot)
print("done")
