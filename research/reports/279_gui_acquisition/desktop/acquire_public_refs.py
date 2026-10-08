"""Read public git refs and fixed-commit docs; GitHub API not required."""
import subprocess, pathlib, concurrent.futures, re, json, urllib.request, datetime, hashlib
ROOT=pathlib.Path(__file__).resolve().parent
REPOS={'xournalpp/xournalpp':'master','flameshot-org/flameshot':'master','qarmin/czkawka':'master','johnfactotum/foliate':'gtk4','dail8859/NotepadNext':'master','NickeManarin/ScreenToGif':'master','Lymphatus/caesium-image-compressor':'main','juzzlin/Heimer':'master','WinMerge/winmerge':'master'}
def run(item):
    repo,branch=item;dest=ROOT/repo.replace('/','__');dest.mkdir(exist_ok=True)
    p=subprocess.run(['git','ls-remote','https://github.com/'+repo+'.git','refs/heads/'+branch,'refs/tags/*'],capture_output=True,text=True,timeout=90)
    (dest/'public_git_refs.txt').write_text(p.stdout,encoding='utf-8')
    tags=[];refs={}
    for line in p.stdout.splitlines():
        sha,ref=line.split();refs[ref]=sha
        m=re.fullmatch(r'refs/tags/(v?\d+\.\d+(?:\.\d+)*)',ref)
        if m:tags.append((tuple(int(x) for x in m[1].lstrip('v').split('.')),m[1],sha))
    if not tags:raise RuntimeError('no stable version tag:'+repo)
    _,tag,obj=max(tags);sha=refs.get('refs/tags/'+tag+'^{}',obj)
    d={'repo':repo,'url':'https://github.com/'+repo,'selected_ref':tag,'commit':sha,'tag_object':obj,'ref_method':'git ls-remote public refs, annotated tags dereferenced','files':[],'head_ref':refs.get('refs/heads/'+branch),'archive_url':'https://codeload.github.com/'+repo+'/zip/'+sha}
    for filename in ['README.md','README','LICENSE','LICENSE.txt','LICENSE.md','COPYING','.gitmodules','CMakeLists.txt','meson.build','ScreenToGif/ScreenToGif.csproj','docs/COMPILATION.md','docs/compilation.md']:
        url='https://raw.githubusercontent.com/'+repo+'/'+sha+'/'+filename
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'skillloop-public-research'})
            with urllib.request.urlopen(req,timeout=20) as f:data=f.read(600000)
            (dest/filename.replace('/','__')).write_bytes(data)
            d['files'].append({'path':filename,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'url':'https://github.com/'+repo+'/blob/'+sha+'/'+filename})
        except Exception:pass
    (dest/'public_fixed_metadata.json').write_text(json.dumps(d,indent=2),encoding='utf-8')
    print(repo,tag,sha,flush=True)
    return d
with concurrent.futures.ThreadPoolExecutor(max_workers=7) as ex:
    results=list(ex.map(run,REPOS.items()))
(ROOT/'desktop_public_fixed_evidence.json').write_text(json.dumps({'fetched_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'repositories':results},ensure_ascii=False,indent=2),encoding='utf-8')
