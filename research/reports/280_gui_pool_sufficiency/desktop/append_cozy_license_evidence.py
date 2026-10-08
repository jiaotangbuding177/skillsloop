"""Copy one already acquired public AppStream document and record its hash."""
import hashlib
import json
from pathlib import Path

base = Path(__file__).resolve().parent
manifest = json.loads((base.parent / "source_acquisition_manifest.json").read_text(encoding="utf-8"))
entry = next(row for row in manifest["applications"] if row["repo"] == "https://github.com/geigi/cozy")
relative = "data/com.github.geigi.cozy.appdata.xml"
payload = (Path(entry["source_directory"]) / relative).read_bytes()
assert b"<project_license>GPL-3.0+</project_license>" in payload
target = base / "geigi__cozy" / "data" / "com.github.geigi.cozy.appdata.xml"
target.parent.mkdir(parents=True, exist_ok=True)
target.write_bytes(payload)
evidence_file = base / "additional_gap_candidate_evidence.json"
evidence = json.loads(evidence_file.read_text(encoding="utf-8"))
repo = next(row for row in evidence["repositories"] if row["repo"] == entry["repo"])
repo["fixed_docs"] = [row for row in repo["fixed_docs"] if row["path"] != relative]
repo["fixed_docs"].append({
    "path": relative,
    "bytes": len(payload),
    "sha256": hashlib.sha256(payload).hexdigest(),
    "url": f"{entry['repo']}/blob/{entry['commit']}/{relative}",
    "license_evidence": "project_license explicitly GPL-3.0+; metadata_license CC0",
})
evidence_file.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Cozy fixed public AppStream license evidence recorded; no app or model executed.")
