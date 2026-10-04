"""Patch openclaw_config.py in 267/268: domain role text + MCP server name from DOMAIN."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent

for exp in ["267_tau2_airline_autoskill", "268_tau2_telecom_autoskill"]:
    p = ROOT / exp / "scripts" / "openclaw_config.py"
    t = p.read_text(encoding="utf-8")

    # 1) import os
    old = "import json\nfrom pathlib import Path\n"
    new = "import json\nimport os\nfrom pathlib import Path\n"
    assert old in t, "import block"
    t = t.replace(old, new, 1)

    # 2) DOMAIN + ROLE_TEXT after DEFAULT_MODEL_ID
    anchor = 'DEFAULT_MODEL_ID = "glm-4-flash"\n'
    addition = (
        anchor
        + 'DOMAIN = os.environ.get("TAU2_RETAIL_DOMAIN", "retail")\n\n'
        + "ROLE_TEXT = {\n"
        + '    "retail": (\n'
        + '        "You are the customer-service agent for a retail store. You talk to the\\n"\n'
        + '        "customer in plain text and you perform account/order operations through\\n"\n'
        + '        "the available retail tools (native function calls).\\n\\n"\n'
        + "    ),\n"
        + '    "airline": (\n'
        + '        "You are the customer-service agent for an airline. You talk to the\\n"\n'
        + '        "customer in plain text and you perform reservation operations through\\n"\n'
        + '        "the available airline tools (native function calls).\\n\\n"\n'
        + "    ),\n"
        + '    "telecom": (\n'
        + '        "You are the customer-support agent for a telecom provider. You talk to the\\n"\n'
        + '        "customer in plain text and you troubleshoot their device and line by\\n"\n'
        + '        "calling the available support tools (native function calls).\\n\\n"\n'
        + "    ),\n"
        + "}\n"
    )
    assert anchor in t, "model id anchor"
    t = t.replace(anchor, addition, 1)

    # 3) mcp_server_name default -> None
    old = '    mcp_server_name: str = "retail",\n'
    new = "    mcp_server_name: str | None = None,\n"
    assert old in t, "mcp default"
    t = t.replace(old, new, 1)

    # 4) resolve None at top of body
    old = '    allow = ["read"]\n    if mcp_url:\n'
    new = '    mcp_server_name = mcp_server_name or DOMAIN\n    allow = ["read"]\n    if mcp_url:\n'
    assert old in t, "allow block"
    t = t.replace(old, new, 1)

    # 5) replace the hardcoded retail role block (between '# Role' line and '# Rules' line)
    start_marker = '        + "# Role\\n"\n'
    end_marker = '        "# Rules\\n"\n'
    i = t.index(start_marker) + len(start_marker)
    j = t.index(end_marker, i)
    middle = t[i:j]
    assert "retail store" in middle, f"unexpected role block: {middle[:80]!r}"
    t = t[:i] + '        + ROLE_TEXT.get(DOMAIN, ROLE_TEXT["retail"])\n' + t[j:]

    p.write_text(t, encoding="utf-8")
    print(exp, "patched ok")

print("done")
