"""Classify public filename hints, without equating hints with functioning coverage."""
import hashlib, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent
inv_path = pathlib.Path("D:/skillloop/research/experiments/266_recreationworld_public_inventory/reports/public_reference_inventory.json")
inv = json.loads(inv_path.read_text(encoding="utf-8"))
audit = json.loads((ROOT.parents[1]/"279_gui_acquisition/web_bench_identity_audit.json").read_text(encoding="utf-8"))
by_id = {r["task_id"]:r for r in inv["tasks"]}
patterns = {
  "documentation_content_navigation": ["docs/","documentation","guide","learn","blog","research","about"],
  "catalog_gallery_list": ["stock-photos","artists","collection","gallery","templates","directory","topics","categories","_content-type","products"],
  "search_filter_query_state": ["search","?s=","_topics=","filter","?q=","category"],
  "multi_field_form_or_step": ["register","signup","sign-up","contact","quiz","verify","login","sign-in","apply"],
  "marketing_pricing_menu": ["pricing","features","solutions","product","enterprise","how-it-works","demo"],
  "booking_checkout_or_schedule": ["booking","checkout","cart","calendar","events","schedule","reservation","tickets"],
  "dashboard_chart_data": ["dashboard","data-explorer","emissions","countries","charts","statistics"]
}
rows=[]
for r in audit["identities"]:
    paths = [p for p in by_id[r["task_id"]]["public_page_paths"] if not p.startswith("_cdn/")]
    hints = {cat:[p for p in paths if any(t in p.lower() for t in toks)][:4] for cat,toks in patterns.items()}
    rows.append({"task_id":r["task_id"],"paper_origin":"synthetic" if r["task_id"].endswith(".example") else "public_website","public_html_pages_including_cdn_paths":by_id[r["task_id"]]["public_html_pages"],"title":str(r.get("title", ""))[:130],"filename_feature_hints":{k:v for k,v in hints.items() if v},"feature_hints_are_not_observed_active_behavior":True,"private_tests_accessed":False,"runtime_coverage_proven":False})
summary={cat:sum(cat in r["filename_feature_hints"] for r in rows) for cat in patterns}
report={"benchmark_revision":audit["revision"],"public_index_inventory_sha256":hashlib.sha256(inv_path.read_bytes()).hexdigest(),"all_web_rows":len(rows),"synthetic_rows":sum(r["paper_origin"]=="synthetic" for r in rows),"public_website_rows":sum(r["paper_origin"]=="public_website" for r in rows),"scope":"public identity and normal reference filenames only; no tests/gold; capability hints, not pass rate or task coverage fraction","overlapping_hint_counts":summary,"rows":rows}
(ROOT/"web50_capability_hints.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({k:v for k,v in report.items() if k!="rows"},ensure_ascii=False,indent=2))
