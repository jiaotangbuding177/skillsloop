"""Host-side checks for a stage-5 public skill package."""
import hashlib
import json
import posixpath
import re
import zipfile
from urllib.parse import unquote, urlsplit
from .runtime import validate_bundle, digest, HEADINGS

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


def assemble_step_scoped_files(files, workflow, methods):
    """Compile the new frozen step contract; keep the provider draft outside the package."""
    from .relational_workflow import with_step_scope_contract, lesson_type, LESSON_POLICY, LESSON_HEADINGS
    if workflow.get('stepScopeContract') is None:
        upgraded = with_step_scope_contract(workflow, methods)
        if upgraded.get('stepScopeContract') is None:
            return files, None
        workflow = upgraded  # A legacy FAILURE_GUARD also requires safe host rendering.
    expected = with_step_scope_contract(workflow, methods)
    if workflow != expected:
        raise ValueError('步骤范围契约与冻结workflow不一致')
    raw = validate_bundle(files)
    by_id = {m['id']: m for m in methods}
    roles = {lesson_type(m) for m in methods}
    if roles - {'PROCEDURE'} and any(f['path'] != 'SKILL.md' for f in raw):
        raise ValueError('警示／假设技能的附属资源未经用途核验，需单独验证')
    description = ('复用已归纳的任务流程时，先确认本次有效要求；目标、输入及交付形式按本次参数重新绑定，'
                   '历史取值不是长期默认，未评价效果仍待验证。')
    name = 'workflow-method-' + digest(workflow)[:12]
    lines = ['---', 'name: ' + name, 'description: ' + json.dumps(description, ensure_ascii=False),
             '---', '# 可复用任务流程', '', '## 使用前绑定',
             '先确认本次目标、有效要求、输入材料、可用工具和交付形式。'
             '仅执行“执行步骤”章节中的流程动作，并先确认本次要求仍适用；否则先重新绑定实例取值。'
             '未知结果不构成效果保证。失败警示中的历史动作不执行；待验证假设需要另行核验。']
    if 'PROCEDURE' not in roles:
        lines.append('本技能仅提供警示或待验证经验，不包含可执行的推荐步骤；来源输出约定不构成本次交付承诺。')

    def section(title, value):
        values = [value] if isinstance(value, str) else value or []
        if not isinstance(values, list) or any(not isinstance(v, str) for v in values):
            raise ValueError('冻结workflow公开正文必须为文本')
        lines.extend(['', '## ' + title])
        lines.extend(values or ['未列明；使用前按本次任务确认。'])

    for title, key in (('来源目标与触发（具体取值按本次要求绑定）', 'title'), ('触发条件', 'trigger'),
                       ('输入约定', 'inputs'), ('输出约定（交付形式按本次要求绑定）', 'outputs'),
                       ('全局适用条件', 'conditions'), ('前置依赖', 'dependencies'),
                       ('本次参数', 'parameters'), ('限制与未验证项', 'limitations')):
        section(title, workflow.get(key))
    lines.append('整体业务结果：' + str(workflow.get('businessOutcome', 'UNKNOWN')) + '；未评价步骤仍待验证。')
    method_rows = []
    lines.extend(['', '## 方法依据'])
    for mid in workflow['includedMethodIds']:
        method = by_id[mid]
        role = lesson_type(method)
        action = _lesson_action(method['action'], role)
        conditions = ['来源适用条件：' + text for text in method.get('conditions', [])]
        completion = '来源完成检查（按本次有效要求核对）：' + method['completionCheck']
        lines.extend(['', '### 方法 ' + mid, '<!-- SKILLSLOOP_METHOD:' + mid + ' -->', LESSON_POLICY[role], action,
                      *conditions, completion])
        bindings = method.get('scopeContract', {}).get('bindings', [])
        lines.extend(b['text'] for b in bindings)
        constraints = method.get('supportConstraints', {})
        lines.extend(constraints.get('limitations', []))
        method_rows.append({'methodId': mid, 'file': 'SKILL.md', 'lessonType': role, 'actionQuote': action,
                            'conditionQuotes': conditions, 'completionCheckQuote': completion,
                            'scopeQuotes': [{'scopeId': b['id'], 'quote': b['text']} for b in bindings]})
    step_rows = []
    # All methods remain accounted for, but failure history and hypotheses are
    # never placed in the section that asks the consumer to execute actions.
    contracts = {row['stepId']: row for row in workflow['stepScopeContract']['steps']}
    row_by_step = {}
    for role in ('PROCEDURE', 'FAILURE_WARNING', 'HYPOTHESIS'):
        lines.extend(['', '## ' + LESSON_HEADINGS[role]])
        selected = [step for step in workflow['steps'] if step['lessonType'] == role]
        if not selected:
            lines.append('未列出此类条款。')
        for step in selected:
            sid = step['id']; contract = contracts[sid]
            action = _lesson_action(step['action'], role)
            condition = '本步骤适用条件：' + (step.get('condition') or '先确认本次有效要求与下列适用范围。')
            completion = '本步骤来源完成检查（按本次有效要求核对）：' + step['completionCheck']
            lines.extend(['', '### 条款 ' + sid, '<!-- SKILLSLOOP_STEP:' + sid + ' -->', LESSON_POLICY[role],
                          '关联方法：' + '、'.join(step['methodIds']), condition])
            lines.extend(dict.fromkeys(b['text'] for b in contract['bindings']))
            lines.extend([action, completion])
            row_by_step[sid] = {'stepId': sid, 'file': 'SKILL.md', 'lessonType': role, 'actionQuote': action,
                'conditionQuote': condition, 'completionCheckQuote': completion,
                'scopeQuotes': [{'methodId': b['methodId'], 'scopeId': b['scopeId'], 'quote': b['text']}
                                for b in contract['bindings']]}
    step_rows = [row_by_step[step['id']] for step in workflow['steps']]
    market = [
        '需要采用已归纳任务流程的使用者；采用前确认本次目标与适用条件。',
        '保留有出处的方法、逐步适用范围和完成检查；不把未评价效果当作保证。',
        '提供本次任务目标、有效要求、输入材料与可用工具；历史实例取值不是默认。',
        '请依据【本次目标】【本次有效要求】【输入材料】【可用工具】执行流程，并重新绑定本次交付形式。',
        '按本次有效要求绑定的交付物与逐步检查记录；整体效果与未评价步骤仍待验证。']
    lines.extend(['', '## 市场信息'])
    for heading, text in zip(HEADINGS, market):
        lines.extend(['### ' + heading, text])
    compiled = validate_bundle([{'path': f['path'], 'content': '\n'.join(lines) + '\n' if f['path'] == 'SKILL.md'
                                 else f['content']} for f in raw])
    return compiled, {'version': 'workflow-step-body-v1', 'status': 'HOST_ASSEMBLED',
                      'sourceWorkflowHash': digest(workflow), 'rawFilesHash': digest(raw),
                      'assembledFilesHash': digest(compiled), 'methodCoverageManifest': method_rows,
                      'stepCoverageManifest': step_rows, 'semanticValidation': 'NOT_INDEPENDENTLY_VERIFIED'}


def _lesson_action(action, role):
    prefix = {'PROCEDURE': '来源实例动作（本次要求仍适用时采用，否则先重新绑定实例取值）：',
              'FAILURE_WARNING': '警示内容（风险行为或防范规则）：',
              'HYPOTHESIS': '待验证的候选办法（未经验证，不作为执行指令）：'}
    return prefix[role] + action


def verify_files(files, method_ids, source_phrases=(), methods=None, coverageManifest=None,
                 workflow=None, stepCoverageManifest=None):
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
        from .relational_workflow import lesson_type
        if any(lesson_type(m) != 'PROCEDURE' for m in methods) and names != {'SKILL.md'}:
            raise ValueError('警示／假设技能的附属资源未经用途核验，需单独验证')
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
            if method.get('scopeContract') is not None:
                from .relational_workflow import validate_frozen_method_content
                validate_frozen_method_content(md,method,row)
            from .relational_workflow import validate_scope_coverage
            from .relational_workflow import validate_lesson_content
            validate_lesson_content(md, method, row)
            scope_coverage = validate_scope_coverage(md,method,row.get('scopeQuotes'))
            rows[row['methodId']]={'methodId':row['methodId'],'file':path,
                'actionQuote':row['actionQuote'],'conditionQuotes':quotes,
                'completionCheckQuote':row['completionCheckQuote'],
                'status':'CONTENT_ANCHORED','semanticStatus':'DECLARED_NOT_INDEPENDENTLY_VERIFIED'}
            if scope_coverage:
                rows[row['methodId']]['scopeCoverage'] = scope_coverage
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
    step_coverage = []
    if workflow and workflow.get('stepScopeContract') is not None:
        from .relational_workflow import validate_step_scope_coverage
        step_coverage = validate_step_scope_coverage(md, workflow, methods, stepCoverageManifest)
    result = {'status':'PASS','methodCoverage':coverage,
            'semanticValidation':'NOT_INDEPENDENTLY_VERIFIED',
            'fileCount':len(files),'files':[{'path':f['path'],'sha256':hashlib.sha256(f['content'].encode('utf-8')).hexdigest(),
                                           'bytes':len(f['content'].encode('utf-8'))} for f in files]}
    if step_coverage:
        result['stepScopeCoverage'] = step_coverage
    return result


def verify_archive(workspace, receipt, files):
    archive=(workspace/receipt['path']).resolve()
    if not archive.is_relative_to(workspace.resolve()) or archive.is_symlink() or not archive.is_file():raise ValueError('封装产物不存在')
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=receipt['sha256']:raise ValueError('封装产物hash不符')
    with zipfile.ZipFile(archive) as bundle:
        rows={p.split('/',1)[1]:bundle.read(p) for p in bundle.namelist() if '/' in p and not p.endswith('/')}
    expected={f['path']:f['content'].encode('utf-8') for f in files}
    if rows!=expected:raise ValueError('封装内容与受检草稿不一致')
    return {'status':'PASS','sha256':receipt['sha256'],'fileCount':len(rows)}
