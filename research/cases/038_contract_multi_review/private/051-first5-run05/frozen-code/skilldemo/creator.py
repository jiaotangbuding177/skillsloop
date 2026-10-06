"""Host-side checks for a stage-5 public skill package."""
import hashlib
import json
import posixpath
import re
import zipfile
from urllib.parse import unquote, urlsplit
from .runtime import validate_bundle

METHOD_MARK = re.compile(r'<!--\s*SKILLSLOOP_METHOD:([A-Za-z0-9_-]+)\s*-->')
LINK = re.compile(r'\]\(([^)]+)\)')


def parse_creator_result(text):
    """Read one final creator JSON block without rewriting its content.

    This presentation tolerance belongs to the interactive creator; structured
    analysis requests retain their strict parser and source/cache identities.
    """
    text = text.strip()
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        blocks = re.findall(r'^[ \t]*```(?:json)?[ \t]*\r?\n(.*?)^[ \t]*```[ \t]*\r?$',
                            text, flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)
        if len(blocks) != 1:
            raise ValueError('需要一个完整且无歧义的JSON对象或JSON代码块')
        obj = json.loads(blocks[0])
    if not isinstance(obj, dict): raise ValueError('需要JSON对象')
    return obj


def _resource_target(source, link, names):
    """Resolve Markdown links within the public package, allowing parent links."""
    raw=link.strip()
    if raw.startswith('<'):
        end=raw.find('>')
        if end<0:raise ValueError('技能资源链接格式非法')
        raw=raw[1:end]
    else:
        # Optional Markdown link title is not part of the target.
        raw=re.split(r'\s+[\"\']',raw,maxsplit=1)[0].strip()
    raw=unquote(raw)
    if '\\' in raw or any(ord(c)<32 for c in raw) or raw.startswith('//'):
        raise ValueError('技能资源链接为非法路径')
    parsed=urlsplit(raw)
    if parsed.scheme:
        if parsed.scheme.lower() not in ('http','https') or not parsed.netloc:
            raise ValueError('技能资源链接包含不允许的URI')
        return
    target=parsed.path
    if not target:return
    if target.startswith('/') or ':' in target:raise ValueError('技能资源链接必须位于包内')
    resolved=posixpath.normpath(posixpath.join(posixpath.dirname(source),target))
    if resolved=='..' or resolved.startswith('../'):raise ValueError('技能资源链接越过包根目录')
    if resolved not in names:raise ValueError('技能资源引用不存在: '+target)


def _visible(text):
    text=re.sub(r'<!--.*?-->','',text,flags=re.S)
    text=re.sub(r'^\s*#{1,6}[^\n]*$','',text,flags=re.M)
    return re.sub(r'\s+','',text)


def _content_quote(text, quote, label):
    if not isinstance(quote,str) or quote not in text or len(_visible(quote))<6:
        raise ValueError('方法覆盖'+label+'缺少实际正文落点')
    if METHOD_MARK.search(quote):raise ValueError('方法覆盖不能以marker代替正文')


def verify_files(files, method_ids, source_phrases=(), methods=None, coverageManifest=None):
    files = validate_bundle(files)
    names = {f['path'] for f in files}
    if any(p != 'SKILL.md' and not p.startswith(('references/','templates/','scripts/')) for p in names):
        raise ValueError('技能包出现未授权文件角色')
    md = next(f['content'] for f in files if f['path']=='SKILL.md')
    observed = METHOD_MARK.findall(md)
    if sorted(observed) != sorted(method_ids):
        raise ValueError('技能步骤未覆盖冻结方法，或混入未批准方法')
    if len(set(method_ids))!=len(method_ids):raise ValueError('冻结方法ID重复')
    # A marker alone is never content coverage. Consecutive markers may point
    # to one shared operation, but each must have real text before the next heading.
    for match in METHOD_MARK.finditer(md):
        tail=md[match.end():]
        boundary=re.search(r'^\s*#{1,6}\s',tail,re.M)
        segment=tail[:boundary.start()] if boundary else tail
        if len(_visible(segment))<6:raise ValueError('方法marker缺少对应步骤正文')
    coverage=[{'methodId':m,'file':'SKILL.md','status':'MARKER_AND_CONTENT_PRESENT'} for m in method_ids]
    if methods is not None:
        if not isinstance(methods,list) or any(not isinstance(m,dict) for m in methods):raise ValueError('冻结方法契约非法')
        method_map={m.get('id'):m for m in methods}
        if len(method_map)!=len(methods) or set(method_map)!=set(method_ids):raise ValueError('冻结方法正文与ID不一致')
        if not isinstance(coverageManifest,list):raise ValueError('creator缺少方法内容覆盖清单')
        rows={}
        text_by_path={f['path']:f['content'] for f in files}
        for row in coverageManifest:
            if not isinstance(row,dict) or row.get('methodId') not in method_map or row['methodId'] in rows:
                raise ValueError('方法内容覆盖清单有重复/未批准方法')
            path=row.get('file')
            if path not in text_by_path:raise ValueError('方法内容覆盖文件不存在')
            text=text_by_path[path];method=method_map[row['methodId']]
            _content_quote(text,row.get('actionQuote'),'动作')
            _content_quote(text,row.get('completionCheckQuote'),'完成检查')
            quotes=row.get('conditionQuotes')
            if not isinstance(quotes,list) or len(quotes)!=len(method.get('conditions',[])):
                raise ValueError('方法覆盖遗漏冻结适用条件')
            for quote in quotes:_content_quote(text,quote,'适用条件')
            rows[row['methodId']]={'methodId':row['methodId'],'file':path,
                'actionQuote':row['actionQuote'],'conditionQuotes':quotes,
                'completionCheckQuote':row['completionCheckQuote'],
                'status':'CONTENT_ANCHORED','semanticStatus':'DECLARED_NOT_INDEPENDENTLY_VERIFIED'}
        if set(rows)!=set(method_ids):raise ValueError('方法内容覆盖清单不完整')
        coverage=[rows[mid] for mid in method_ids]
    for f in files:
        text = f['content']
        for link in LINK.findall(text):
            _resource_target(f['path'],link,names)
        for phrase in source_phrases:
            compact = re.sub(r'\s+', '', str(phrase))
            flattened = re.sub(r'\s+', '', text)
            if len(compact)>=48 and any(compact[i:i+48] in flattened for i in range(0,len(compact)-47,24)):
                raise ValueError('技能文件疑似复制了企业会话原文')
    return {'status':'PASS','methodCoverage':coverage,
            'semanticValidation':'NOT_INDEPENDENTLY_VERIFIED',
            'fileCount':len(files),'files':[{'path':f['path'],'sha256':hashlib.sha256(f['content'].encode('utf-8')).hexdigest(),
                                           'bytes':len(f['content'].encode('utf-8'))} for f in files]}


def verify_archive(workspace, receipt, files):
    archive=(workspace/receipt['path']).resolve()
    if not archive.is_relative_to(workspace.resolve()) or archive.is_symlink() or not archive.is_file():raise ValueError('封装产物不存在')
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=receipt['sha256']:raise ValueError('封装产物hash不符')
    with zipfile.ZipFile(archive) as bundle:
        rows={p.split('/',1)[1]:bundle.read(p) for p in bundle.namelist() if '/' in p and not p.endswith('/')}
    expected={f['path']:f['content'].encode('utf-8') for f in files}
    if rows!=expected:raise ValueError('封装内容与受检草稿不一致')
    return {'status':'PASS','sha256':receipt['sha256'],'fileCount':len(rows)}
