"""Package the accepted validators; exclude caches and unrelated intermediates."""
import hashlib
import json
from pathlib import Path
import zipfile

HERE=Path(__file__).resolve().parent


def main():
    manifest=json.loads((HERE/'manifest.json').read_text('utf-8'))
    assert len(manifest['tasks'])==226
    for p,expected in manifest['implementation_sha256'].items():
        assert hashlib.sha256((HERE/p).read_bytes()).hexdigest()==expected
    for t in manifest['tasks']:
        for key in ['contract','script']:
            assert hashlib.sha256((HERE/t[key]).read_bytes()).hexdigest()==t[key+'_sha256']
    files=[HERE/p for p in ['_runtime.py','_extensions.py','_artifact_extensions.py','_text_extensions.py',
        'score.py','summarize_scores.py','compile_suite.py','build_bundle.py','README.md','requirements.txt',
        'manifest.json','scorer.config.fragment.json','打开这里.html',
        'artifact_extensions_normalization.json','text_extensions_normalization.json']]
    for directory in ['scripts','contracts','vendor','tests']:
        files.extend(p for p in (HERE/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    for directory in ['audit','verification']:
        files.extend(p for p in (HERE/directory).glob('*') if p.is_file() and p.suffix.lower() in ['.json','.txt','.log'])
    target=HERE/'逐任务校验脚本包.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for path in sorted(set(files)):
            z.write(path,path.relative_to(HERE).as_posix())
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        assert len([n for n in z.namelist() if n.startswith('scripts/') and n.endswith('.py')])==226
    receipt={'artifact':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
        'bytes':target.stat().st_size,'files':len(set(files)),'task_scripts':226,'zip_crc':'passed',
        'includes_original_business_inputs':False,'includes_historical_ai':False,
        'notes':'Audit user requirement excerpts and source metadata retained; original benchmark files untouched.'}
    (HERE/'交付包核验.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps(receipt,ensure_ascii=False))


if __name__=='__main__':main()
