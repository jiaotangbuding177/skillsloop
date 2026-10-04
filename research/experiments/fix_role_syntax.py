"""Fix the missing '+' before the '# Rules' literal after the ROLE_TEXT patch."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
old = '        + ROLE_TEXT.get(DOMAIN, ROLE_TEXT["retail"])\n        "# Rules\\n"\n'
new = '        + ROLE_TEXT.get(DOMAIN, ROLE_TEXT["retail"])\n        + "# Rules\\n"\n'
for exp in ["267_tau2_airline_autoskill", "268_tau2_telecom_autoskill"]:
    p = ROOT / exp / "scripts" / "openclaw_config.py"
    t = p.read_text(encoding="utf-8")
    if old in t:
        p.write_text(t.replace(old, new, 1), encoding="utf-8")
        print(exp, "fixed")
    elif '        + ROLE_TEXT.get(DOMAIN, ROLE_TEXT["retail"])\n        + "# Rules\\n"\n' in t:
        print(exp, "already fixed")
    else:
        print(exp, "PATTERN NOT FOUND - inspect manually")
