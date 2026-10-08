import pathlib,json,urllib.request,re,concurrent.futures,datetime
ROOT=pathlib.Path(__file__).resolve().parent
catalog=json.loads((ROOT.parent/'bench_source_catalog.json').read_text(encoding='utf-8'))
fixed=json.loads((ROOT/'desktop_public_fixed_evidence.json').read_text(encoding='utf-8'))['repositories']
norm=lambda s:s.rstrip('/').removesuffix('.git').lower()
refs={norm(x['repo']):x for x in catalog['tasks'] if x.get('repo')}
def audit(r):
    repo,sha=r['repo'],r['commit'];dest=ROOT/repo.replace('/','__')
    d={'repo':repo,'commit':sha,'exact_source_matches':[x['instance_id'] for x in catalog['tasks'] if x.get('repo') and norm(x['repo'])==norm(r['url'])],'cross_platform_native_rows_checked':200,'web_rows_have_no_source_repo':50,'fork_graph_api_verified':False,'fork_graph_limitation':'GitHub API rate limit; public repo page and declared attribution checked, not full fork-graph proof'}
    try:
        url=r['url']+'/commit/'+sha+'.patch'
        req=urllib.request.Request(url,headers={'User-Agent':'skillloop-public-research'})
        with urllib.request.urlopen(req,timeout=20) as f:
            lines=[]
            for _ in range(30):
                ln=f.readline().decode('utf-8','replace');lines.append(ln)
                if ln.startswith('---'):break
        headers=''.join(lines)
        (dest/'fixed_commit_patch_header.txt').write_text(headers,encoding='utf-8')
        dm=re.search(r'^Date: (.+)$',headers,re.M);sm=re.search(r'^Subject: (.+)$',headers,re.M)
        d.update({'commit_date':dm.group(1) if dm else None,'commit_subject':sm.group(1) if sm else None,'commit_date_evidence':url})
    except Exception as e:d['commit_header_error']=type(e).__name__
    return d
with concurrent.futures.ThreadPoolExecutor(max_workers=9) as ex:out=list(ex.map(audit,fixed))
(ROOT/'cross_platform_source_audit.json').write_text(json.dumps({'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'evidence_catalog':str(ROOT.parent/'bench_source_catalog.json'),'results':out},ensure_ascii=False,indent=2),encoding='utf-8')
for d in out:print(d['repo'],d.get('commit_date'),d['exact_source_matches'])
