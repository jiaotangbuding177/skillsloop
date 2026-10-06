"""Byte-preserving export of native directory output; no rewriting or creator."""
import argparse,json,shutil,subprocess,sys,zipfile
from pathlib import Path
from audited_runtime import HERE,BASELINE,dump,sha,bootstrap_imports

def export(source,destination):
    bootstrap_imports()
    from skill_evolver.skill_evolving_agent import QUICK_VALIDATE_SCRIPT
    source=Path(source).resolve(); destination=Path(destination).resolve()
    if destination.exists(): raise RuntimeError('Never overwrite a deliverable')
    check=subprocess.run([sys.executable,'-X','utf8',str(QUICK_VALIDATE_SCRIPT),str(source)],
                         capture_output=True,text=True,encoding='utf-8')
    if check.returncode: raise RuntimeError('Real checker rejected native output: '+check.stdout+check.stderr)
    destination.mkdir(parents=True)
    target=destination/source.name; shutil.copytree(source,target)
    source_files={str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()}
    copy_files={str(p.relative_to(target)):sha(p) for p in target.rglob('*') if p.is_file()}
    if copy_files!=source_files: raise RuntimeError('Export changed native files')
    archive=destination/(source.name+'.skill')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(target.rglob('*')):
            if p.is_file(): z.write(p,p.relative_to(destination))
    with zipfile.ZipFile(archive) as z:
        import hashlib
        zip_files={str(Path(n).relative_to(source.name)):hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist()}
    if zip_files!=source_files: raise RuntimeError('Archive changed native bytes')
    dump(destination/'manifest.json',{'format':'Original full skill directory + optional byte-equivalent ZIP archive',
        'source':str(source),'target':str(target),'archive':str(archive),'archive_sha256':sha(archive),
        'native_content_rewritten':False,'original_resources_kept':True,
        'checker':str(QUICK_VALIDATE_SCRIPT),'checker_sha256':sha(QUICK_VALIDATE_SCRIPT),
        'actual_checker_stdout':check.stdout.strip(),'source_files':source_files,'copied_files':copy_files,
        'zip_entries_sha256':zip_files,'task_benefit_established':False})
    print(json.dumps({'status':'EXPORTED_NATIVE_BYTES','target':str(target)},ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--destination',type=Path,required=True)
    a=p.parse_args();export(a.source,a.destination)
