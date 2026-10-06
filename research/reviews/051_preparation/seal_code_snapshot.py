"""Archive the already frozen experiment sources without editing the running code."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

PROJECT=Path(__file__).resolve().parents[3]
DEMO=PROJECT/'enginering/demo'
sys.path.insert(0,str(DEMO))
from skilldemo.experiment import select_source
from skilldemo.runtime import digest

run=Path(sys.argv[1]).resolve()
manifest=json.loads((run/'manifest.json').read_text(encoding='utf-8'))
copied=[]
for name,expected in manifest['codeFiles'].items():
    source=DEMO/name
    assert hashlib.sha256(source.read_bytes()).hexdigest()==expected, name
    destination=run/'frozen-code'/name
    destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,destination)
    copied.append(name)
events,descriptor=select_source(PROJECT/'research/cases/038_contract_multi_review')
assert digest(events)==manifest['source']['eventHash']
(run/'selected-events.json').write_text(json.dumps(events,ensure_ascii=False,indent=2),encoding='utf-8')
report={'manifestHash':manifest['manifestHash'],'codeFileCount':len(copied),
        'files':copied,'selectedEvents':len(events),'sourceEventHash':descriptor['eventHash']}
(run/'source-snapshot.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='files'}))
