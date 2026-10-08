"""Versioned research build recovery; preserve v1 source, log and failed status."""
import ast,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
old=ROOT/'reports/prepare_vite_reference.py';text=old.read_text()
for before,after in (("'admission/vite_docs'","'admission/vite_docs_v2'"),
 ("vite_reference_build_entry.py","vite_reference_build_entry_v2.py"),
 ("rw293-vite-reference-build-","rw293-vite-reference-build-v2-"),
 ("rw293-vite-reference-","rw293-vite-reference-v2-")):
 assert before in text;text=text.replace(before,after)
ast.parse(text)
report=ROOT/'reports/vite_reference_v2_preparation_manifest.json'
assert not report.exists(),'Preserve previous preparation'
report.write_text(json.dumps({'version':'vite_reference_build_v2','prior_failure':'corepack prepare cached pnpm but no executable shim; FileNotFoundError',
 'original_preparation_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),
 'derived_preparation_sha256':hashlib.sha256(text.encode()).hexdigest(),
 'only_build_entry_and_versioned_paths_changed':True,'old_failure_preserved':True,
 'same_fixed_reference_archive':True,'agent_rounds_allocated':0,'model_calls':0},indent=2))
exec(compile(text,str(old),'exec'),{'__name__':'__main__','__file__':str(old)})
