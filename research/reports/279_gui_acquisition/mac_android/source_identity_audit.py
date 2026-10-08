"""Audit public source identities; no model, app, task or scoring calls."""
from pathlib import Path
import json, hashlib
from datetime import datetime, timezone
BASE=Path(__file__).resolve().parent
catalog_path=BASE.parent/"bench_source_catalog.json"
catalog=json.loads(catalog_path.read_text(encoding="utf-8"))
selected=json.loads((BASE/"selected_candidates.json").read_text(encoding="utf-8"))["selected_candidates"]
def normalize(url):
    return (url or "").lower().rstrip("/").removesuffix(".git").replace("http://", "https://")
tasks=catalog["tasks"]
audit=[]
for row in selected:
    identities=[row["repo"]]+row["source_isolation"]["aliases"]+row["source_isolation"]["known_upstream"]
    hits=[{"instance_id":t["instance_id"],"repo":t["repo"]} for t in tasks if t.get("repo") and normalize(t["repo"]) in {normalize(u) for u in identities}]
    known={t["instance_id"] for t in tasks}
    unmatched=[c["task_id"] for c in row["bench_correspondence"] if c["task_id"] not in known]
    row["source_isolation"]["exact_repo_matches"]=hits
    row["source_isolation"]["identity_audit_file"]="source_identity_audit.json"
    audit.append({"candidate_id":row["id"],"repo":row["repo"],"commit":row["commit"],"identities_checked":identities,"exact_matches":hits,"bench_correspondence_ids_not_in_catalog":unmatched,"conclusion":"No exact identity match" if not hits else "Exact source conflict; exclude","limitation":"Not a clone/fork/full dependency provenance audit; web50 public metadata has no source repo. No claim of absolute non-contamination."})
output={"date_utc":datetime.now(timezone.utc).isoformat(),"catalog":str(catalog_path),"catalog_sha256":hashlib.sha256(catalog_path.read_bytes()).hexdigest(),"dataset_revision":catalog.get("revision"),"total_tasks":len(tasks),"with_public_repo":sum(bool(t.get("repo")) for t in tasks),"without_public_repo":sum(not t.get("repo") for t in tasks),"candidates":audit,"all_exact_identity_nonmatch":all(not a["exact_matches"] for a in audit)}
(BASE/"source_identity_audit.json").write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
data=json.loads((BASE/"selected_candidates.json").read_text(encoding="utf-8"))
data["selected_candidates"]=selected
(BASE/"selected_candidates.json").write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"tasks":len(tasks),"native":output["with_public_repo"],"web":output["without_public_repo"],"candidates":len(audit),"exact_conflicts":sum(bool(a["exact_matches"]) for a in audit),"unknown_correspondence_ids":[x for a in audit for x in a["bench_correspondence_ids_not_in_catalog"]]},ensure_ascii=False))

