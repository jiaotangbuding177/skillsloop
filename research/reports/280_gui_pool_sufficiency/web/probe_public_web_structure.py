"""Public reference HTML structure audit only; does not run UI, source, tests or model."""
import concurrent.futures, hashlib, json, pathlib, urllib.request, urllib.parse
from collections import Counter
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent
PARENT = ROOT.parents[1] / "279_gui_acquisition"
catalog = json.loads((PARENT / "web_bench_identity_audit.json").read_text(encoding="utf-8"))
inventory = json.loads(pathlib.Path("D:/skillloop/research/experiments/266_recreationworld_public_inventory/reports/public_reference_inventory.json").read_text(encoding="utf-8"))
by_id = {row["task_id"]:row for row in inventory["tasks"]}
identities = {row["task_id"]:row for row in catalog["identities"]}

class Structure(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = Counter(); self.input_types = Counter(); self.required = 0
        self.select_names = []; self.form_actions = []; self.query_links = []; self.semantic_links = []
        self.names = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs); self.tags[tag] += 1
        if tag == "input":
            self.input_types[a.get("type", "text")] += 1
            self.required += "required" in a
            if a.get("name"): self.names.append(a["name"][:80])
        if tag == "select": self.select_names.append(a.get("name", a.get("id", ""))[:80])
        if tag == "form": self.form_actions.append(a.get("action", "")[:180])
        if tag == "a":
            href = a.get("href", "")
            if "?" in href and len(self.query_links) < 12: self.query_links.append(href[:180])
            if any(token in href.lower() for token in ("contact", "pricing", "register", "signup", "search", "filter", "catalog", "quiz")) and len(self.semantic_links) < 14: self.semantic_links.append(href[:180])

selections = [(task, "index.html") for task in ("sentorra.example", "aperlio.example", "cresvia.example", "sonelio.example", "climatewatch.org", "kartova.example", "formora.example")]
for task, needles in (("cresvia.example", ["goals-quiz/index.html"]), ("sonelio.example", ["account-register/index.html"]), ("kartova.example", ["contact/index.html"]), ("sentorra.example", ["?s=&amp;_content-type=amicus-brief&amp;_topics=border-surveillance/index.html"])):
    for candidate in needles:
        if candidate in by_id[task]["public_page_paths"]: selections.append((task,candidate))

def fetch(item):
    task, path = item
    base = identities[task]["public_source_url"].rsplit("index.html",1)[0]
    # HF filenames contain query strings literally: quote path, not runtime query.
    url = base + urllib.parse.quote(path, safe="/")
    r = {"task_id":task,"public_reference_path":path,"url":url,"scope":"public reference HTML only, static structure, no private tests","runtime_observed":False}
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent":"ResearchPublicReferenceAudit/1.0"}), timeout=45) as response:
            b = response.read(6*1024*1024+1)
        if len(b) > 6*1024*1024: raise ValueError("public file exceeds audit size bound")
        p = Structure(); p.feed(b.decode("utf-8",errors="replace"))
        r.update({"status":"public_structure_read","bytes":len(b),"sha256":hashlib.sha256(b).hexdigest(),"tags":dict(p.tags),"input_types":dict(p.input_types),"required_inputs":p.required,"input_names":p.names[:18],"select_names":p.select_names[:12],"form_actions":p.form_actions[:8],"query_links":p.query_links,"semantic_links":p.semantic_links})
    except Exception as exc: r.update({"status":"read_failed","error_type":type(exc).__name__})
    return r

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool: records = list(pool.map(fetch,selections))
report = {"benchmark_revision":catalog["revision"],"source_metadata_sha256":hashlib.sha256((PARENT/"web_bench_identity_audit.json").read_bytes()).hexdigest(),"read_scope":"normal public reference HTML structure only; no evaluate/test/gold paths, no candidate or model executed; HTML not saved", "records":records}
(ROOT/"public_web_structure_audit.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps([{k:r.get(k) for k in ("task_id","public_reference_path","status","bytes","input_types","required_inputs","select_names","form_actions")} for r in records],ensure_ascii=False,indent=2))
