"""Read public README/build/license documents and git refs only. Never runs an app."""
import concurrent.futures, datetime, hashlib, json, pathlib, re, subprocess, urllib.request
ROOT=pathlib.Path(__file__).resolve().parent
ROOT.mkdir(parents=True, exist_ok=True)
CATALOG=ROOT.parents[1]/'279_gui_acquisition'/'bench_source_catalog.json'
REPOS={'GNOME/gnome-calculator':'main','antonycourtney/tad':'master','KDE/kreversi':'master'}
DOCS=['README.md','README','LICENSE','LICENSE.txt','COPYING','.gitmodules','CMakeLists.txt','meson.build','meson_options.txt','package.json','doc/building.md','packages/tad-app/package.json','LICENSES/GPL-2.0-or-later.txt','LICENSES/GPL-3.0-or-later.txt','data/org.gnome.Calculator.metainfo.xml.in','doc/index.docbook']
def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':'skillloop-public-source-research'})
    with urllib.request.urlopen(req,timeout=7) as f:return f.read(1500000)
def candidate(item):
    repo,branch=item[:2]
    override=item[2] if len(item)>2 else None
    dest=ROOT/(repo.replace('/','__')+('__'+override if override else ''));dest.mkdir(exist_ok=True)
    p=subprocess.run(['git','ls-remote','https://github.com/'+repo+'.git','refs/heads/'+branch,'refs/tags/*'],capture_output=True,text=True,timeout=90)
    (dest/'public_git_refs.txt').write_text(p.stdout,encoding='utf-8')
    (dest/'public_git_refs_error.txt').write_text(p.stderr,encoding='utf-8')
    tags=[];refs={}
    for line in p.stdout.splitlines():
        sha,ref=line.split();refs[ref]=sha
        m=re.fullmatch(r'refs/tags/((?:v|veusz-)?(\d+\.\d+(?:\.\d+)*))',ref)
        if m:tags.append((tuple(int(x) for x in m[2].split('.')),m[1],sha))
    if not tags:
        print('PUBLIC REFS UNAVAILABLE',repo,flush=True)
        return {'repo':'https://github.com/'+repo,'commit':None,'public_refs_error':p.stderr,'status':'fixed SHA pending alternate official evidence'}
    if override:
        if 'refs/tags/'+override not in refs:raise RuntimeError('Public tag not present: '+repo+' '+override)
        tag=override;obj=refs['refs/tags/'+tag]
    else:_,tag,obj=max(tags)
    sha=refs.get('refs/tags/'+tag+'^{}',obj)
    result={'repo':'https://github.com/'+repo,'tag':tag,'commit':sha,'tag_object':obj,'fixed_docs':[],'archive_url':'https://codeload.github.com/'+repo+'/zip/'+sha}
    def one(path):
        try:
            data=fetch('https://raw.githubusercontent.com/'+repo+'/'+sha+'/'+path)
            (dest/path.replace('/','__')).write_bytes(data)
            return {'path':path,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'url':'https://github.com/'+repo+'/blob/'+sha+'/'+path}
        except Exception:return None
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        result['fixed_docs']=[r for r in ex.map(one,DOCS) if r]
    try:
        req=urllib.request.Request('https://github.com/'+repo+'/commit/'+sha+'.patch',headers={'User-Agent':'skillloop-public-source-research'})
        with urllib.request.urlopen(req,timeout=15) as f:
            lines=[]
            for _ in range(30):
                line=f.readline().decode('utf-8','replace')
                if line=='---\n':break
                lines.append(line)
        header=''.join(lines);(dest/'fixed_commit_patch_header.txt').write_text(header,encoding='utf-8')
        result['commit_header']=header
    except Exception as e:result['commit_header_error']=type(e).__name__
    (dest/'public_fixed_metadata.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('CANDIDATE',repo,tag,sha,flush=True)
    return result
def bench(row):
    repo=row['repo'].rstrip('/').removesuffix('.git').split('github.com/')[-1]
    dest=ROOT/'bench_readmes'/row['instance_id'].replace('/','__');dest.parent.mkdir(exist_ok=True)
    paths=['README.md','README','README.rst','readme.md','Readme.md','README.txt']
    for path in paths:
        try:
            data=fetch('https://raw.githubusercontent.com/'+repo+'/'+row['commit']+'/'+path)
            dest.with_suffix('.txt').write_bytes(data)
            lines=data.decode('utf-8','replace').splitlines()
            excerpt='\n'.join(lines[:28])
            return {**row,'public_readme':path,'url':'https://github.com/'+repo+'/blob/'+row['commit']+'/'+path,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'intro_excerpt':excerpt}
        except Exception:pass
    return {**row,'public_readme':None,'evidence_status':'not_retrieved; classify by public source identity conservatively'}
def norm(s):return s.lower().rstrip('/').removesuffix('.git').replace('https://github.com/','').replace('http://github.com/','')
if __name__=='__main__':
    catalog=json.loads(CATALOG.read_text(encoding='utf-8'))
    native=[r for r in catalog['tasks'] if r.get('repo')]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:candidates=list(ex.map(candidate,REPOS.items()))
    for c in candidates:c['all_native_exact_matches']=[r['instance_id'] for r in native if norm(r['repo'])==norm(c['repo'])]
    (ROOT/'public_candidate_evidence.json').write_text(json.dumps({'fetched_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'native_source_rows_checked':len(native),'repositories':candidates},ensure_ascii=False,indent=2),encoding='utf-8')
    rows=[r for r in catalog['tasks'] if r['platform'] in ('ubuntu','windows')]
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:evidence=list(ex.map(bench,rows))
    (ROOT/'bench_public_domain_evidence.json').write_text(json.dumps({'scope':'100 public README/source identities; no tests or task evaluation content','records':evidence},ensure_ascii=False,indent=2),encoding='utf-8')
    print('BENCH READMES',sum(bool(r.get('public_readme')) for r in evidence),'/',len(evidence),flush=True)
