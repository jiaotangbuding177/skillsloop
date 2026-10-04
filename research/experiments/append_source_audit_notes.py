"""Append experiment-267/268 adaptation notes to their source_audit.md copies."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent

NOTE = """

---

### 267/268 域适配差异（2026-10-04，相对 148）

1. `scripts/run_wrapper.py`：新增 `TAU2_RETAIL_DOMAIN`（默认按实验分别为 `airline`/`telecom`）；
   `get_tasks(DOMAIN)`、`build_environment(DOMAIN)`、`TextRunConfig.domain=DOMAIN` 由域决定。
2. `scripts/openclaw_config.py`：新增 `DOMAIN`/`ROLE_TEXT`；按域生成角色文本（retail/airline/telecom），
   MCP 服务名默认取域（`airline__*` / `telecom__*` 工具前缀）。
3. `scripts/audit_split.py`：按域重写分类规则（airline 按写操作主类；telecom 按任务 ID 的
   类别/子问题/PERSONA 结构），输出本目录 `split_manifest.json`。
4. relay 独立：`TAU2_RETAIL_RELAY_PORT` = 8170（267）/ 8171（268），`ledger/` 独立于 148。
5. 其余（挂起-转发 bridge、v6 `$技能` 引用、判分补丁、运行纪律）与 148 相同，未改 vendor。
"""

for exp in ["267_tau2_airline_autoskill", "268_tau2_telecom_autoskill"]:
    p = ROOT / exp / "source_audit.md"
    t = p.read_text(encoding="utf-8")
    if "267/268 域适配差异" in t:
        print(exp, "already noted")
        continue
    p.write_text(t.rstrip() + "\n" + NOTE, encoding="utf-8")
    print(exp, "note appended")
