"""Summarize saved public metadata; no program under review is executed."""
import hashlib, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent
catalog = json.loads((ROOT.parent / "bench_source_catalog.json").read_text(encoding="utf-8"))
inventory_path = pathlib.Path("D:/skillloop/research/experiments/266_recreationworld_public_inventory/reports/public_reference_inventory.json")
inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
acquisition = json.loads((ROOT.parent / "source_acquisition_manifest.json").read_text(encoding="utf-8"))
homepage_path = ROOT.parent / "web_bench_identity_audit.json"
homepages = json.loads(homepage_path.read_text(encoding="utf-8"))
def canonical(repo):
 return str(repo).lower().removeprefix("https://github.com/").removesuffix(".git").strip("/")
candidates = json.loads((ROOT / "selected_candidates.json").read_text(encoding="utf-8"))["selected_candidates"]
records=[]
for candidate in candidates:
 label = candidate["repo"].removeprefix("https://github.com/").replace("/","__")
 tree_path = ROOT / "evidence" / (label+"__tree.json")
 tree = json.loads(tree_path.read_text(encoding="utf-8")) if tree_path.exists() else {}
 blobs=[row for row in tree.get("tree",[]) if row["type"]=="blob"]
 archive = next((row for row in acquisition["applications"] if canonical(row["repo"]) == canonical(candidate["repo"])), {})
 identities=[row for row in catalog["tasks"] if row.get("repo") and canonical(row["repo"])==canonical(candidate["repo"])]
 tokens=[candidate["name"].lower(),canonical(candidate["repo"])]
 matches=[row["task_id"] for row in inventory["tasks"] if any(token in json.dumps(row).lower() for token in tokens)]
 homepage_matches=[row["task_id"] for row in homepages["identities"] if canonical(candidate["repo"]) in json.dumps(row).lower() or candidate["name"].lower() in str(row.get("title", "")).lower()]
 records.append({"id":candidate["id"],"repo":candidate["repo"],"commit":candidate["commit"],"tree_truncated":tree.get("truncated"),"source_tree_blobs":len(blobs) if tree else None,"source_tree_bytes":sum(row.get("size",0) for row in blobs) if tree else None,"source_tree_excludes_git_history_and_uninstalled_dependencies":True,"native_200_canonical_matches":identities,"web_public_filename_name_matches":matches,"web_public_homepage_explicit_identity_matches":homepage_matches,"archive_bytes":archive.get("archive_bytes"),"archive_sha256":archive.get("archive_sha256"),"expanded_regular_files":archive.get("regular_files"),"expanded_bytes":archive.get("expanded_bytes"),"web_source_identity_complete":False,"runtime_checked":False,"skill_extracted":False})
report={"scope":"saved public repository tree, benchmark identities and acquisition manifest only; no candidate code executed","catalog_sha256":hashlib.sha256((ROOT.parent/"bench_source_catalog.json").read_bytes()).hexdigest(),"inventory_sha256":hashlib.sha256(inventory_path.read_bytes()).hexdigest(),"homepage_identity_audit_sha256":hashlib.sha256(homepage_path.read_bytes()).hexdigest(),"candidates":records,"caveat":"Canonical repo/name exclusion is not cross-project shared-code or anonymous Web origin/template de-duplication."}
(ROOT/"source_identity_audit.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(records,ensure_ascii=False,indent=2))
