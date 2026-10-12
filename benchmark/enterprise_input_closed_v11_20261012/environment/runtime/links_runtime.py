"""Source scoped, turn delivered attachment bytes and historical path aliases.

This module never changes original human text, authenticates a historical SaaS,
or redirects unmatched public URLs. HTTP downloads expose actual admitted bytes.
"""
from __future__ import annotations
import argparse
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path, PurePosixPath
import re
import shutil
import threading
from urllib.parse import quote, unquote, urlsplit

PORT = 8765
SCHEMA = 'source-scoped-links-v1'


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def mapping_id(session, reference, mount, index):
    return 'link-' + hashlib.sha256(json.dumps([session, reference, mount, index], ensure_ascii=False).encode()).hexdigest()[:24]


def local_url(row, port=PORT):
    return f'http://127.0.0.1:{port}/resources/{row["mapping_id"]}/' + quote(PurePosixPath(row['mount']).name, safe='')


def validate_row(row, workspace):
    mount = row.get('mount')
    if not isinstance(mount, str) or not mount or mount.startswith('/') or '\\' in mount or ':' in mount or any(p in ('', '.', '..') for p in mount.split('/')):
        raise ValueError('Invalid link target mount')
    target = (workspace / mount).resolve()
    if not target.is_relative_to(workspace):
        raise ValueError('Link target escapes workspace')
    index = row.get('available_from_dispatch_index', 0)
    if type(index) is not int or index < 0:
        raise ValueError('Invalid link delivery index')
    if not re.fullmatch(r'link-[0-9a-f]{24}', row.get('mapping_id', '')):
        raise ValueError('Invalid link mapping identity')
    if row.get('sha256') is not None and not re.fullmatch(r'[0-9a-f]{64}', row['sha256']):
        raise ValueError('Invalid input SHA')
    if not isinstance(row.get('original_reference'), str) or not row['original_reference']:
        raise ValueError('Missing original reference')
    return target


def historical_path(value):
    if value.startswith('file:'):
        parsed = urlsplit(value)
        if parsed.netloc not in ('', 'localhost'):
            return None
        value = unquote(parsed.path)
    # Windows paths remain explicit mapping entries; a Linux alias is impossible.
    if not value.startswith('/') or '\\' in value or '\x00' in value:
        return None
    parts = PurePosixPath(value)
    if '..' in parts.parts or value in ('/', '/workspace'):
        return None
    if value.startswith(('/workspace/', '/mnt/data/', '/data/', '/root/.openclaw/workspace')):
        return Path(value)
    return None


class ResourceLinks:
    def __init__(self, context, workspace, transport, *, port=PORT):
        self.workspace = Path(workspace).resolve()
        self.transport = Path(transport).resolve()
        self.port = port
        spec = context.get('link_adaptations', {}) if isinstance(context, dict) else {}
        if spec and spec.get('schema') != SCHEMA:
            raise ValueError('Unknown link adaptation schema')
        self.session_id = spec.get('session_id')
        self.rows = list(spec.get('mappings', []))
        self.directory_specs = list(context.get('directory_adaptations', [])) if isinstance(context, dict) else []
        self.prior_specs = list(context.get('prior_produced_resources', [])) if isinstance(context, dict) else []
        for prior in self.prior_specs:
            if type(prior.get('available_from_dispatch_index')) is not int or prior['available_from_dispatch_index'] < 0:
                raise ValueError('Invalid prior-output reference dispatch')
            if type(prior.get('generated_from_dispatch_index')) is not int or not 0 <= prior['generated_from_dispatch_index'] < prior['available_from_dispatch_index']:
                raise ValueError('Prior-output generation must precede its referencing human')
            if not prior.get('expected_basenames') or any('/' in name or '\\' in name or name in ('.', '..') for name in prior['expected_basenames']):
                raise ValueError('Prior output requires concrete file basenames')
        self.prior_rows = []
        self.observed_outputs = {}
        self.initial_files = {p.relative_to(self.workspace).as_posix(): file_sha(p) for p in self.workspace.rglob('*') if p.is_file() and not p.is_symlink()}
        self.input_hashes = {r.get('sha256') for r in self.rows if r.get('sha256')}
        self.by_id = {}
        for row in self.rows:
            validate_row(row, self.workspace)
            if row['mapping_id'] in self.by_id:
                raise ValueError('Duplicate link mapping identity')
            self.by_id[row['mapping_id']] = dict(row)
        self.active_index = -1
        self.cache = self.transport / 'admitted_link_bytes'
        self.cache.mkdir(parents=True, exist_ok=True)
        self.cached = {}
        self.events = []
        self.aliases = []
        self.lock = threading.RLock()
        self.server = None
        self.thread = None

    def active_prior_specs(self):
        return [r for r in self.prior_specs if r.get('available_from_dispatch_index', 0) <= self.active_index]

    def input_shadowed(self, row):
        for prior in self.active_prior_specs():
            if row['original_reference'] == prior['original_reference']:
                return True
            if PurePosixPath(row['mount']).name in prior.get('expected_basenames', []):
                return True
        return False

    def output_candidates(self, prior):
        names = set(prior.get('expected_basenames', []))
        blocked = set(prior.get('prohibited_historical_or_synthetic_sha256', [])) | self.input_hashes
        candidates = []
        explicit = list(prior.get('candidate_paths', []))
        excluded_roots = ('inputs/', 'reference_inputs/', 'skills/', 'learned_skills/', 'reference_support/', '.claude/', 'simulation/', 'runtime_links/')
        for file in self.workspace.rglob('*'):
            if not file.is_file() or file.is_symlink() or file.name not in names:
                continue
            relative = file.relative_to(self.workspace).as_posix()
            if relative.startswith(excluded_roots) or relative in self.initial_files:
                continue
            actual = file_sha(file)
            if actual in blocked:
                continue
            observed = self.observed_outputs.get(relative)
            if observed is None or observed['sha256'] != actual:
                observed = {'sha256': actual, 'first_observed_before_dispatch_index': self.active_index}
                self.observed_outputs[relative] = observed
            if observed['first_observed_before_dispatch_index'] <= prior.get('generated_from_dispatch_index', -1):
                continue
            rank = explicit.index(relative) if relative in explicit else len(explicit)
            candidates.append({'file': file, 'mount': relative, 'sha256': actual, 'rank': rank,
                               'observed_before_dispatch_index': observed['first_observed_before_dispatch_index']})
        candidates.sort(key=lambda r: (r['rank'], r['mount']))
        if candidates and candidates[0]['rank'] == len(explicit) and len({c['sha256'] for c in candidates}) > 1:
            return [], 'ambiguous_multiple_new_outputs'
        return candidates, 'fresh_prior_output_found' if candidates else 'prior_generated_output_missing'

    def prior_alias_path(self, reference):
        absolute = historical_path(reference)
        if absolute is not None:
            return absolute
        parts = PurePosixPath(reference)
        if not parts.is_absolute() and reference and '\\' not in reference and ':' not in reference and '..' not in parts.parts:
            return self.workspace / reference
        return None

    def configure_prior_alias(self, row, candidate):
        alias = self.prior_alias_path(row['original_reference'])
        if alias is None:
            return
        owned = any(a['path'] == str(alias) for a in self.aliases)
        if alias.is_symlink() and owned:
            if candidate is not None and alias.resolve() == candidate['file'].resolve():
                return
            alias.unlink()
        if candidate is None:
            if owned:
                self.events.append({'operation': 'prior_output_alias_invalidated_missing', 'path': str(alias), 'user_index': self.active_index})
            return
        target = candidate['file']
        if alias == target:
            return
        if alias.exists() or alias.is_symlink():
            self.events.append({'operation': 'prior_output_alias_conflict_preserved', 'path': str(alias), 'user_index': self.active_index})
            return
        alias.parent.mkdir(parents=True, exist_ok=True)
        alias.symlink_to(target)
        event = {'operation': 'fresh_prior_output_alias', 'path': str(alias), 'target': str(target), 'user_index': self.active_index, 'changes_source_bytes': False}
        self.aliases.append(event)
        self.events.append(event)

    def refresh_prior_outputs(self):
        self.prior_rows = []
        latest = {}
        for prior in self.active_prior_specs():
            ref = prior['original_reference']
            if ref not in latest or prior.get('available_from_dispatch_index', 0) >= latest[ref].get('available_from_dispatch_index', 0):
                latest[ref] = prior
        for prior in self.prior_specs:
            index = prior.get('available_from_dispatch_index', 0)
            expected = prior.get('candidate_paths', [])
            mount = expected[0] if expected else 'outputs/' + prior['expected_basenames'][0]
            identity = mapping_id(self.session_id, prior['original_reference'], mount, index)
            row = dict(prior, mapping_id=identity, mount=mount, kind='fresh_prior_generated_output',
                       redirect_original_reference=True, historical_bytes_not_preseeded=True)
            candidate = None
            # Observe expected output versions at every turn, before each actor
            # invocation, so a pre-generation file cannot masquerade as new.
            candidates, status = self.output_candidates(prior)
            if index > self.active_index:
                row.update(status='not_at_reference_turn', available=False, file_bytes_available=False)
            else:
                candidate = candidates[0] if candidates else None
                row.update(status=status, available=True, file_bytes_available=candidate is not None)
                if candidate is not None:
                    row.update(mount=candidate['mount'], sha256=candidate['sha256'], provenance='fresh_current_rollout_prior_turn_file',
                               observed_before_dispatch_index=candidate['observed_before_dispatch_index'])
                    cached = self.cache / identity
                    shutil.copyfile(candidate['file'], cached)
                    self.cached[identity] = {'path': cached, 'sha256': candidate['sha256']}
                else:
                    self.cached.pop(identity, None)
                if latest.get(prior['original_reference']) is prior:
                    self.configure_prior_alias(row, candidate)
            self.prior_rows.append(row)
            self.by_id[identity] = row
            self.events.append({'operation': 'prior_output_resolution', 'mapping_id': identity, 'status': row['status'],
                                'user_index': self.active_index, 'sha256': row.get('sha256'), 'historical_bytes_supplied': False})

    def advance(self, user_index):
        """Called only after this human turn's actual resource delivery."""
        with self.lock:
            if user_index < self.active_index:
                raise ValueError('Link delivery index cannot go backwards')
            self.active_index = user_index
            for row in self.rows:
                index = row.get('available_from_dispatch_index', 0)
                if index > user_index or row['mapping_id'] in self.cached:
                    continue
                target = validate_row(row, self.workspace)
                if not target.is_file():
                    raise FileNotFoundError('Admitted link target was not delivered: ' + row['mount'])
                actual = file_sha(target)
                if row.get('sha256') and row['sha256'] != actual:
                    raise ValueError('Delivered link target SHA mismatch')
                cached = self.cache / row['mapping_id']
                shutil.copyfile(target, cached)
                self.cached[row['mapping_id']] = {'path': cached, 'sha256': actual}
                self.events.append({'operation': 'admit_actual_bytes', 'mapping_id': row['mapping_id'], 'user_index': user_index, 'sha256': actual})
            # Latest admitted version of each historical path becomes the alias.
            latest = {}
            for row in self.rows:
                if row.get('available_from_dispatch_index', 0) <= user_index and not self.input_shadowed(row):
                    ref = row['original_reference']
                    if ref not in latest or row.get('available_from_dispatch_index', 0) >= latest[ref].get('available_from_dispatch_index', 0):
                        latest[ref] = row
            for row in latest.values():
                same_ref=[r for r in self.rows if r['original_reference']==row['original_reference'] and r.get('available_from_dispatch_index',0)==row.get('available_from_dispatch_index',0)]
                if len({r.get('sha256') for r in same_ref})>1:
                    self.events.append({'operation':'ambiguous_file_alias_not_created','original_reference':row['original_reference'],'user_index':user_index})
                    continue
                alias = historical_path(row['original_reference'])
                # Exported attachment references commonly omit /workspace/,
                # while original human text uses the absolute Linux spelling.
                # Preserve filename/path aliases for real references, including
                # a .doc reference served by a tested .docx compatibility file.
                if alias is None and row.get('kind')!='url' and (Path(row['original_reference']).suffix or '/' in row['original_reference']):
                    alias=self.prior_alias_path(row['original_reference'])
                if alias is None:
                    continue
                target = self.workspace / row['mount']
                if alias == target:
                    continue
                if alias.is_symlink():
                    if alias.resolve() != target.resolve():
                        alias.unlink()
                    else:
                        continue
                elif alias.exists():
                    # Preserve an existing user output or native environment file.
                    self.events.append({'operation': 'alias_conflict_preserved', 'path': str(alias), 'mapping_id': row['mapping_id']})
                    continue
                alias.parent.mkdir(parents=True, exist_ok=True)
                alias.symlink_to(target)
                event = {'operation': 'historical_file_alias', 'path': str(alias), 'target': str(target), 'user_index': user_index, 'changes_source_bytes': False}
                self.aliases.append(event)
                self.events.append(event)
            self.refresh_prior_outputs()
            for directory in self.directory_specs:
                if directory.get('available_from_dispatch_index',0)>user_index:continue
                for child in directory.get('child_mounts',[]):
                    target=self.workspace / child['mount']
                    if not target.is_file() or file_sha(target)!=child['sha256']:
                        raise ValueError('Directory input child not delivered: '+child['mount'])
                for entry in directory.get('directories',[]):
                    target=self.workspace / entry['target_workspace_relative_path']
                    if not target.is_dir():raise NotADirectoryError(str(target))
                    alias=self.prior_alias_path(entry['original_directory_alias'])
                    if alias is None or alias==target:continue
                    if alias.exists() or alias.is_symlink():
                        if not alias.is_dir():raise NotADirectoryError('Historical directory reference points to a file: '+str(alias))
                        continue
                    alias.parent.mkdir(parents=True,exist_ok=True);alias.symlink_to(target,target_is_directory=True)
                    event={'operation':'historical_directory_alias','path':str(alias),'target':str(target),'user_index':user_index}
                    self.aliases.append(event);self.events.append(event)
            self.write_state()

    def write_state(self):
        rows = []
        for row in self.rows:
            rows.append(dict(row, local_url=local_url(row, self.port), available=row.get('available_from_dispatch_index', 0) <= self.active_index and not self.input_shadowed(row),
                             shadowed_by_fresh_prior_output_requirement=self.input_shadowed(row)))
        for row in self.prior_rows:
            rows.append(dict(row, local_url=local_url(row, self.port) if row.get('file_bytes_available') else None))
        value = {'schema': SCHEMA, 'session_id': self.session_id, 'active_dispatch_index': self.active_index, 'mappings': rows, 'events': self.events}
        (self.transport / 'resource_link_receipt.json').write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        destination = self.workspace / 'runtime_links'
        destination.mkdir(exist_ok=True)
        (destination / 'current_mapping.json').write_text(json.dumps({k: v for k, v in value.items() if k != 'events'}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    def guide(self):
        active = [r for r in self.rows if r.get('available_from_dispatch_index', 0) <= self.active_index and not self.input_shadowed(r)]
        # A repeated "this CV" reference has its own referring-turn owner.
        # Keep all files in the workspace, but describe only the latest binding
        # for each original reference (multiple files at that same turn remain).
        latest_indices={}
        for row in active:
            ref=row['original_reference'];latest_indices[ref]=max(latest_indices.get(ref,-1),row.get('available_from_dispatch_index',0))
        active=[r for r in active if r.get('available_from_dispatch_index',0)==latest_indices[r['original_reference']]]
        active=list({(r['original_reference'],r['mount'],r.get('sha256')):r for r in active}.values())
        directories=[r for r in self.directory_specs if r.get('available_from_dispatch_index',0)<=self.active_index]
        if not active and not self.active_prior_specs() and not directories:
            return ''
        lines = ['原轨迹的附件路径／文件对象链接按当前会话、当前用户轮次适配。原文保留；请使用以下实际容器地址。',
                 '本地HTTP链接支持exec中的curl/Python及浏览器真实下载；不是历史企业服务认证。后轮附件未投递前不能访问。']
        for row in active:
            if row.get('kind') == 'url' and not row.get('redirect_original_reference', True):
                lines.append('- 原网络引用保持：' + row['original_reference'] + '\n  实验模拟配套材料（并非该原站／服务）：/workspace/' + row['mount'] + '\n  仅配套文件下载：' + local_url(row, self.port))
            else:
                lines.append('- 原引用：' + row['original_reference'] + '\n  实际文件：/workspace/' + row['mount'] + '\n  实际下载：' + local_url(row, self.port))
        for directory in directories:
            lines.append('- 原用户已有目录：'+directory.get('user_directory_description',directory['original_reference'])+'。这是已投递的真实目录，请使用ls/read遍历；目录不是单个索引文件。')
            for entry in directory.get('directories',[]):lines.append('  原目录：'+entry['original_directory_alias']+' → 实际目录：/workspace/'+entry['target_workspace_relative_path'])
        latest = {}
        for row in self.prior_rows:
            if row.get('available_from_dispatch_index', 0) <= self.active_index:
                ref = row['original_reference']
                if ref not in latest or row.get('available_from_dispatch_index', 0) >= latest[ref].get('available_from_dispatch_index', 0):latest[ref] = row
        for row in latest.values():
            if row.get('file_bytes_available'):
                lines.append('- 本次连续回放的前轮实际成果：' + row['original_reference'] + '\n  当前实际文件：/workspace/' + row['mount'] + '\n  SHA256：' + row['sha256'] + '\n  实际下载：' + local_url(row, self.port))
            else:
                lines.append('- 前轮成果缺失或有歧义：' + row['original_reference'] + '（' + row['status'] + '）。本次回放没有可确认的新成果文件；不得用历史附件或同名初始输入替代，不得声称已生成。')
        return '\n'.join(lines)

    def start(self):
        if not self.rows and not self.prior_specs and not self.directory_specs:
            return {'enabled': False, 'model_calls': 0}
        links = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass

            def do_HEAD(self):
                self.respond(False)

            def do_GET(self):
                self.respond(True)

            def respond(self, body):
                path = unquote(urlsplit(self.path).path)
                with links.lock:
                    if path == '/health':
                        payload = json.dumps({'status': 'ready', 'session_id': links.session_id, 'active_dispatch_index': links.active_index}).encode()
                        status = 200
                        headers = {'Content-Type': 'application/json'}
                    elif path.startswith('/resources/'):
                        parts = path.split('/')
                        row = links.by_id.get(parts[2]) if len(parts) >= 4 else None
                        cached = links.cached.get(parts[2]) if len(parts) >= 4 else None
                        if row is None:
                            status, payload, headers = 404, b'Unmatched source-scoped link', {}
                        elif row.get('available_from_dispatch_index', 0) > links.active_index:
                            status, payload, headers = 425, b'Attachment has not been delivered at this user turn', {}
                        elif cached is None:
                            status, payload, headers = (404, b'Fresh prior generated output is missing', {}) if row.get('kind') == 'fresh_prior_generated_output' else (409, b'Admitted bytes unavailable', {})
                        else:
                            payload = cached['path'].read_bytes()
                            status = 200
                            name = PurePosixPath(row['mount']).name
                            headers = {'Content-Type': mimetypes.guess_type(name)[0] or 'application/octet-stream',
                                       'Content-Disposition': "inline; filename*=UTF-8''" + quote(name, safe=''),
                                       'X-Input-SHA256': cached['sha256']}
                            if headers['Content-Type'].startswith('text/') or headers['Content-Type'] == 'application/json':
                                headers['Content-Type'] += '; charset=utf-8'
                        links.events.append({'operation': 'http_download', 'mapping_id': row.get('mapping_id') if row else None, 'status': status, 'user_index': links.active_index, 'byte_count': len(payload) if status == 200 else 0})
                        links.write_state()
                    else:
                        status, payload, headers = 404, b'Unknown local resource route', {}
                self.send_response(status)
                for key, value in headers.items():
                    self.send_header(key, value)
                self.send_header('Content-Length', str(len(payload)))
                self.end_headers()
                if body:
                    self.wfile.write(payload)
        self.server = ThreadingHTTPServer(('127.0.0.1', self.port), Handler)
        self.port = self.server.server_port
        self.thread = threading.Thread(target=self.server.serve_forever, name='source-resource-links', daemon=True)
        self.thread.start()
        self.write_state()
        return {'enabled': True, 'base_url': f'http://127.0.0.1:{self.port}', 'session_id': self.session_id, 'mapping_count': len(self.rows), 'model_calls': 0, 'redirect_unmatched_public_urls': False}

    def close(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        self.write_state()


def configure_skill_root_aliases(workspace, context=None):
    """Only names of actual admitted skills get aliases; SKILL bytes are untouched."""
    workspace = Path(workspace).resolve()
    skills = workspace / 'skills'
    if not skills.is_dir():
        return []
    results = []
    roots = ['/app/skills', '/root/.openclaw/skills', '/opt/openclaw/skills', '/usr/share/openclaw/skills']
    for root in roots:
        base = Path(root)
        for skill in skills.iterdir():
            if not skill.is_dir() or not (skill / 'SKILL.md').is_file():
                continue
            alias = base / skill.name
            if alias.is_symlink() and alias.resolve() == skill.resolve():
                continue
            if alias.exists() or alias.is_symlink():
                results.append({'path': str(alias), 'target': str(skill), 'status': 'existing_path_preserved'})
                continue
            base.mkdir(parents=True, exist_ok=True)
            alias.symlink_to(skill, target_is_directory=True)
            results.append({'path': str(alias), 'target': str(skill), 'status': 'actual_admitted_skill_alias', 'changes_skill_bytes': False})
    spec = context.get('link_adaptations', {}) if isinstance(context, dict) else {}
    for row in spec.get('skill_path_aliases', []):
        value = row.get('path', '')
        reconstructed_private = row.get('source_exact') is True and row.get('admission_kind') == 'v5_source_reconstruction' and __import__('re').fullmatch(r'/root/\.evomind/[A-Za-z0-9_-]+/skills/[^/]+', value) is not None
        if not reconstructed_private and not value.startswith(('/root/.openclaw/workspace', '/root/.evomind/workspace', '/home/node/.openclaw/workspace', '/home/node/.evomind/workspace', '/workspace/', '/app/skills/', '/opt/openclaw/skills/', '/usr/share/openclaw/skills/', '/opt/evomind-shared-skills/', '/opt/openclaw-shared-skills/', '/opt/evomindskills/')) or '..' in PurePosixPath(value).parts:
            raise ValueError('Historical skill alias is outside a declared skill workspace')
        target = Path(row.get('target', '')).resolve()
        if not target.is_relative_to(skills) or not (target / 'SKILL.md').is_file():
            raise ValueError('Historical skill alias requires an actual admitted skill')
        alias = Path(value)
        if alias == target or alias.is_symlink() and alias.resolve() == target:
            continue
        if alias.exists() or alias.is_symlink():
            results.append({'path': str(alias), 'target': str(target), 'status': 'existing_path_preserved'})
            continue
        alias.parent.mkdir(parents=True, exist_ok=True)
        alias.symlink_to(target, target_is_directory=True)
        results.append({'path': str(alias), 'target': str(target), 'status': 'source_exact_historical_skill_alias', 'changes_skill_bytes': False})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference')
    parser.add_argument('--mapping', default='/workspace/runtime_links/current_mapping.json')
    args = parser.parse_args()
    state = json.loads(Path(args.mapping).read_text(encoding='utf-8'))
    candidates = [r for r in state['mappings'] if r['original_reference'] == args.reference and r['available']]
    if not candidates:
        parser.error('No admitted current-turn mapping for this exact historical reference')
    current = max(candidates, key=lambda r: r.get('available_from_dispatch_index', 0))
    print(json.dumps(current, ensure_ascii=False))
    if current.get('kind') == 'fresh_prior_generated_output' and not current.get('file_bytes_available'):
        raise SystemExit(2)


if __name__ == '__main__':
    main()
