"""Public repository metadata only; never execute downloaded repository code."""
import json, urllib.request, pathlib, datetime, base64, hashlib
ROOT=pathlib.Path(__file__).resolve().parent
REPOS=['xournalpp/xournalpp','flameshot-org/flameshot','qarmin/czkawka','johnfactotum/foliate','dail8859/NotepadNext','NickeManarin/ScreenToGif','Lymphatus/caesium-image-compressor']
def get(url):
    r=urllib.request.Request(url,headers={'User-Agent':'skillloop-public-research','Accept':'application/vnd.github+json'})
    with urllib.request.urlopen(r,timeout=35) as f:return json.load(f)
out=[]
for repo in REPOS:
    dest=ROOT/repo.replace('/','__');dest.mkdir(parents=True,exist_ok=True)
    try:
        m=get('https://api.github.com/repos/'+repo)
        releases=get('https://api.github.com/repos/'+repo+'/releases?per_page=5')
        stable=next((r for r in releases if not r['draft'] and not r['prerelease']),None)
        ref=stable['tag_name'] if stable else m['default_branch']
        c=get('https://api.github.com/repos/'+repo+'/commits/'+urllib.parse.quote(ref,safe=''))
        sha=c['sha']
        d={'repo':repo,'url':m['html_url'],'canonical_full_name':m['full_name'],'archived':m['archived'],'fork':m['fork'],'parent':m.get('parent',{}).get('full_name'),'default_branch':m['default_branch'],'repository_size_kib_with_history':m['size'],'license_api':m.get('license'),'pushed_at':m['pushed_at'],'selected_ref':ref,'selected_commit':sha,'selected_commit_date':c['commit']['committer']['date'],'latest_release':({'tag':stable['tag_name'],'published_at':stable['published_at'],'url':stable['html_url'],'assets':[{'name':a['name'],'size':a['size']} for a in stable['assets']]} if stable else None),'files':[]}
        for filename in ['README.md','LICENSE','COPYING','.gitmodules','CMakeLists.txt','meson.build','README']:
            try:
                x=get('https://api.github.com/repos/'+repo+'/contents/'+filename+'?ref='+sha)
                data=base64.b64decode(x['content'])
                (dest/filename.replace('/','__')).write_bytes(data)
                d['files'].append({'path':filename,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'url':'https://github.com/'+repo+'/blob/'+sha+'/'+filename})
            except Exception as ex:
                if filename=='README.md': d.setdefault('file_errors',[]).append({'path':filename,'error':type(ex).__name__})
        (dest/'metadata.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
        out.append(d)
        print(repo,sha,ref,m['size'],(m.get('license') or {}).get('spdx_id'),m['pushed_at'],flush=True)
    except Exception as ex:
        out.append({'repo':repo,'error':type(ex).__name__+': '+str(ex)})
        print(repo,type(ex).__name__,flush=True)
(ROOT/'desktop_repository_evidence.json').write_text(json.dumps({'fetched_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'public GitHub metadata and small evidence files only; no execution','repositories':out},ensure_ascii=False,indent=2),encoding='utf-8')
