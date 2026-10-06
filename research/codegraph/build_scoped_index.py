"""Build a local CodeGraphMCP snapshot for the explicitly scoped research area.

Does not execute application code, connect to databases, or modify source files.
Mixed-purpose files are blanked outside explicit ranges, preserving line numbers.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import queue
import re
import sqlite3
import subprocess
import threading

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1] / 'enginering' / 'insightweaver'
EXE = Path.home() / '.local/share/codegraph-mcp/v1.1.0/runtime/src/CodeGraphMcp/bin/Release/net10.0/CodeGraphMcp.exe'
PATTERNS = [
    'apps/api/src/skill-emergence/**/*.ts',
    'apps/api/src/skill-analytics/**/*.ts',
    'apps/api/src/skills/**/*.ts',
    'apps/api/src/enterprises/enterprise-department-group.service.ts',
    'apps/api/src/enterprises/enterprise-member-import.service.ts',
    'apps/api/src/enterprises/enterprise-departments.constants.ts',
    'apps/api/src/enterprises/dto/*member*.ts',
    'apps/api/src/enterprises/dto/*department*.ts',
    'apps/api/src/enterprises/dto/join-enterprise.dto.ts',
    'apps/api/src/auth/jwt-auth.guard.ts',
    'apps/api/src/auth/admin.guard.ts',
    'apps/api/src/zclaw/zclaw-enterprise-id.util.ts',
    'apps/api/src/zclaw/interceptors/zclaw-enterprise-context.interceptor.ts',
    'apps/web/src/api/moudles/skills.ts',
    'apps/web/src/api/moudles/skill-emergence.ts',
    'apps/web/src/components/my-emergence/*.tsx',
    'apps/web/src/components/skills/*.tsx',
    'apps/web/src/components/super-lobster/Skill*.tsx',
    'apps/web/src/components/super-lobster/skill-submission-display.ts',
    'apps/web/src/components/super-lobster/skillDisplay.ts',
    'apps/web/src/hooks/useSkillEmergenceStatus.ts',
    'apps/web/src/hooks/useSkillManagementAuth.ts',
    'apps/web/src/hooks/useEnterpriseSkillDisplay.ts',
    'apps/web/src/lib/enterprise-skill-picker.ts',
    'apps/web/src/lib/skill-market-md.ts',
    'apps/web/src/lib/skill-install-prompt.ts',
    'apps/web/src/lib/resolve-active-enterprise.ts',
    'apps/web/src/lib/enterprise-context.ts',
    'apps/web/src/app/**/admin/skills/**/*.tsx',
    'apps/web/src/app/**/admin/skills/**/*.ts',
    'packages/shared/src/enterprise-kind.ts',
]
# Version-specific boundary excerpts. Refresh deliberately if the source changes.
RANGES = {
    'apps/api/src/enterprises/enterprise.controller.ts': [(33, 74), (81, 86), (102, 107), (132, 196), (206, 225), (239, 298), (308, 320), (338, 447), (462, 510)],
    'apps/api/src/zclaw/zclaw.service.ts': [(7539, 8050), (8796, 9097), (9846, 9846), (9927, 9935), (10401, 10492), (13059, 13166)],
    'apps/api/src/agent/agent-runtime.ts': [(33, 57), (565, 590), (654, 679)],
    'packages/db/prisma/schema.prisma': [(12, 16), (98, 118), (202, 277), (560, 743), (2295, 2557), (2823, 2837)],
}

def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')

def prepare():
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run = BASE / 'runs' / stamp
    view = run / 'scope'
    view.mkdir(parents=True)
    selected = {}
    for pattern in PATTERNS:
        for path in ROOT.glob(pattern):
            rel = path.relative_to(ROOT).as_posix()
            if any(word in rel for word in ('.test.', '/__tests__/', 'template', 'builtin-skill')):
                continue
            selected[rel] = None
    selected.update(RANGES)
    # Only member/department access methods from the mixed enterprise service.
    rel = 'apps/api/src/enterprises/enterprise.service.ts'
    lines = (ROOT / rel).read_text(encoding='utf-8-sig').splitlines()
    starts = [(i, re.match(r'^  (?:(?:private|public|protected) )?(?:async )?(\w+)\(', s))
              for i, s in enumerate(lines)]
    starts = [(i, m.group(1)) for i, m in starts if m]
    ranges = []
    for pos, (i, name) in enumerate(starts):
        if re.search(r'Membership|Member|Department|joinEnterprise|listMyEnterprises|assertActiveEnterprise|assertEnterpriseAdmin|assertEnterpriseOwner', name) and not re.search(r'Token|Quota|Instance|Usage|Consumer', name):
            end = starts[pos + 1][0] if pos + 1 < len(starts) else len(lines)
            ranges.append((i + 1, end))
    selected[rel] = ranges
    manifest = []
    for rel, ranges in sorted(selected.items()):
        src = ROOT / rel
        raw = src.read_bytes()
        target = view / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if ranges:
            lines = raw.decode('utf-8-sig').splitlines(keepends=True)
            class_ranges = [(i, i) for i, s in enumerate(lines, 1) if re.match(r'^export class ', s)]
            ranges = ranges + class_ranges
            content = ''.join(s if any(a <= i <= b for a, b in ranges) else '\n'
                              for i, s in enumerate(lines, 1))
            target.write_text(content, encoding='utf-8', newline='')
        else:
            target.write_bytes(raw)
        manifest.append({'path': rel, 'source': str(src), 'sha256': hashlib.sha256(raw).hexdigest(),
                         'indexed_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                         'ranges': ranges, 'mode': 'boundary_excerpt' if ranges else 'full_scoped_file'})
    # Prisma is unsupported by this MCP version. Add a clearly labeled derived
    # Markdown projection so model names can still be queried through MCP.
    schema_rel = 'packages/db/prisma/schema.prisma'
    schema_lines = (view / schema_rel).read_text(encoding='utf-8').splitlines()
    projection = ['# Scoped Prisma model projection', '',
                  'Derived from boundary excerpts. Not a complete Prisma schema; source line numbers below are authoritative.', '']
    for i, s in enumerate(schema_lines, 1):
        match = re.match(r'model (\w+) \{', s)
        if match:
            projection.extend([f'## {match.group(1)}', f'Source: {schema_rel}:{i}', ''])
        elif s.strip():
            projection.append('    ' + s)
    (view / 'SCOPED_SCHEMA.md').write_text('\n'.join(projection), encoding='utf-8')
    write_json(run / 'manifest.json', {'source_root': str(ROOT), 'scope_root': str(view),
               'generated': ['SCOPED_SCHEMA.md'], 'files': manifest})
    print(json.dumps({'run': str(run), 'files': len(manifest)}, ensure_ascii=False))
    return run, view

class Client:
    def __init__(self, view, run):
        self.run = run
        self.log = (run / 'server.stderr.log').open('w', encoding='utf-8')
        self.process = subprocess.Popen([str(EXE), str(view), str(run / 'graph.db')],
            cwd=str(view), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.log,
            text=True, encoding='utf-8')
        self.queue = queue.Queue()
        self.seq = 0
        threading.Thread(target=lambda: [self.queue.put(line) for line in self.process.stdout], daemon=True).start()
        self.request('initialize', {'protocolVersion': '2024-11-05', 'capabilities': {},
                     'clientInfo': {'name': 'scoped-research-index', 'version': '1.0'}}, 'initialize')
        self.process.stdin.write(json.dumps({'jsonrpc':'2.0','method':'notifications/initialized'}) + '\n')
        self.process.stdin.flush()

    def request(self, method, params, label):
        self.seq += 1
        self.process.stdin.write(json.dumps({'jsonrpc': '2.0', 'id': self.seq, 'method': method, 'params': params}) + '\n')
        self.process.stdin.flush()
        while True:
            reply = json.loads(self.queue.get(timeout=180))
            if reply.get('id') != self.seq:
                continue
            if 'error' in reply:
                raise RuntimeError(reply['error'])
            result = reply['result']
            out = self.run / 'queries'
            out.mkdir(exist_ok=True)
            write_json(out / (label + '.json'), {'method': method, 'params': params, 'result': result})
            if result.get('isError'):
                raise RuntimeError(result)
            for content in result.get('content', []):
                if content.get('type') == 'text':
                    try:
                        payload = json.loads(content['text'])
                    except (ValueError, KeyError):
                        continue
                    if isinstance(payload, dict) and 'error' in payload:
                        raise RuntimeError(payload['error'])
            return result

    def close(self):
        self.process.stdin.close()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        self.log.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', help='MCP tool name; reuse latest snapshot')
    parser.add_argument('--args', default='{}', help='MCP arguments as JSON')
    parser.add_argument('--label', default='custom')
    opts = parser.parse_args()
    if opts.query:
        latest = json.loads((BASE / 'latest.json').read_text(encoding='utf-8'))
        run, view = Path(latest['run']), Path(latest['scope'])
    else:
        run, view = prepare()
    client = Client(view, run)
    try:
        if opts.query:
            result = client.request('tools/call', {'name': opts.query, 'arguments': json.loads(opts.args)}, opts.label)
            print(json.dumps(result, ensure_ascii=False))
        else:
            listed = client.request('tools/list', {}, 'tools')
            print('Tools:', ', '.join(t['name'] for t in listed['tools']))
            for name, arguments, label in [
                ('GetCodeGraph', {'maxTokens': 80000}, 'graph'),
                ('GetSystemPrompt', {}, 'overview'),
                ('GetSymbol', {'symbolName': 'SkillEmergence'}, 'emergence-symbols'),
                ('GetSymbol', {'symbolName': 'SkillSubmissionService'}, 'submission-symbol'),
                ('GetSymbol', {'symbolName': 'EnterpriseService'}, 'enterprise-symbol'),
                ('GetSymbol', {'symbolName': 'PersonalSkillConfig'}, 'personal-model'),
                ('GetFileContext', {'filePath': 'apps/api/src/skill-emergence/skill-emergence.module.ts', 'hopDepth': 2}, 'emergence-module-context'),
            ]:
                client.request('tools/call', {'name': name, 'arguments': arguments}, label)
                print('Saved:', label, flush=True)
    finally:
        client.close()
    if not opts.query:
        manifest = json.loads((run / 'manifest.json').read_text(encoding='utf-8'))
        changed = [f['path'] for f in manifest['files']
                   if hashlib.sha256(Path(f['source']).read_bytes()).hexdigest() != f['sha256']]
        if changed:
            raise RuntimeError('Source changed during snapshot: ' + repr(changed))
        con = sqlite3.connect(run / 'graph.db')
        con.row_factory = sqlite3.Row
        nodes = [dict(row) for row in con.execute('select * from nodes')]
        edges = [dict(row) for row in con.execute('select * from edges')]
        if not nodes:
            raise RuntimeError('Empty MCP graph')
        paths = {f['path']: f for f in manifest['files']}
        for node in nodes:
            rel = Path(node['file_path']).relative_to(view).as_posix()
            node['indexed_path'] = node.pop('file_path')
            node['source_path'] = str(ROOT / rel) if rel in paths else None
            node['generated_projection'] = rel not in paths
        write_json(run / 'symbol-index.json', nodes)
        ids = {n['id'] for n in nodes}
        summary = {'source_files': len(manifest['files']), 'generated_files': 1,
                   'nodes': len(nodes), 'edges_raw': len(edges),
                   'edges_with_both_endpoints': sum(e['source_id'] in ids and e['target_id'] in ids for e in edges),
                   'source_hashes_unchanged': True,
                   'limitations': ['regex TS parser; method bodies and Prisma relations require source verification',
                                   'NestJS Injectable mislabeled Angular by upstream parser',
                                   'snapshot only; refresh explicitly after source changes']}
        write_json(run / 'verification.json', summary)
        write_json(BASE / 'latest.json', {'run': str(run), 'scope': str(view), 'database': str(run / 'graph.db')})
        print(json.dumps(summary, ensure_ascii=False))

if __name__ == '__main__':
    main()
