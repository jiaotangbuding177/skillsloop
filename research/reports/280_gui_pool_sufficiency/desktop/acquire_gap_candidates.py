"""Additional public docs and fixed refs only, no download/build/run of apps."""
import concurrent.futures,datetime,json
import acquire_public_evidence as pub
pub.DOCS += ['INSTALL.md','requirements.txt','setup.py','pyproject.toml','src-tauri/Cargo.toml','src-tauri/tauri.conf.json','CONTRIBUTING.md','org.gnome.Calculator.json','README.adoc']
items=[('GNOME/gnome-calculator','gnome-46','46.3'),('veusz/veusz','master'),('Splode/pomotroid','main'),('geigi/cozy','master')]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:out=list(ex.map(pub.candidate,items))
(pub.ROOT/'additional_gap_candidate_evidence.json').write_text(json.dumps({'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'read public docs only; application builds and runtime admission not performed','repositories':out},ensure_ascii=False,indent=2),encoding='utf-8')
