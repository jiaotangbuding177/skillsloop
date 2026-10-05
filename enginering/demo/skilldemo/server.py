import json
import os
from pathlib import Path
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from .core import ACTORS, Conflict, Forbidden, identity
from .runtime import OpenClawAgent
from .scenario import scenario

WEB = Path(__file__).resolve().parents[1] / 'web'


def scheduled_cycle(settings, cycle):
    """The auto-learn switch pauses every learning stage, including stage 2/3."""
    if settings['autoLearn']: return cycle()

def serve(loop, port=8765, auto_learn=True):
    # OS-owned exclusive lock; no stale PID guessing or hidden concurrent recovery.
    lock = open(loop.store.root / 'server.lock', 'a+b')
    lock.seek(0); lock.write(b'1'); lock.flush(); lock.seek(0)
    try:
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        lock.close()
        raise RuntimeError('此数据目录已有demo服务，请换端口和数据目录，或先关闭原服务')
    loop.recover_interrupted()
    settings = {'autoLearn': auto_learn}
    stop = threading.Event()
    cycle_lock = threading.Lock()
    def cycle(actor=None):
        if not cycle_lock.acquire(blocking=False): return {'busy': True}
        try:
            if loop.stage_pipeline: loop.run_stages(actor)
            else: loop.tick()
            for user in ([actor] if actor else ACTORS):
                loop.discover(user)
                pending = [c for c in loop.snapshot(user)['candidates'] if c['status'] == 'QUEUED']
                for c in pending[:1]:
                    try: loop.generate(user, c['id'])
                    except Conflict: pass
            return {'ok': True}
        finally: cycle_lock.release()
    def scheduler():
        while not stop.wait(2):
            try:
                scheduled_cycle(settings,cycle)
            except Exception as exc: print('scheduler:', type(exc).__name__, str(exc), flush=True)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args): pass
        def send(self, value, status=200, content_type='application/json; charset=utf-8'):
            data = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'")
            self.end_headers(); self.wfile.write(data)
        def allowed(self):
            host = self.headers.get('Host', '')
            if host not in (f'127.0.0.1:{port}', f'localhost:{port}'): raise Forbidden('仅允许本地访问')
            origin = self.headers.get('Origin')
            if origin and origin not in (f'http://127.0.0.1:{port}', f'http://localhost:{port}'): raise Forbidden('拒绝跨站请求')
        def do_GET(self):
            try:
                self.allowed()
                url = urlparse(self.path)
                actor = parse_qs(url.query).get('actor', ['alice'])[0]
                if url.path == '/api/state':
                    self.send({**loop.snapshot(actor), 'settings': settings,
                        'runtime': {'model':os.getenv('DEMO_MODEL'), 'configured':bool(os.getenv('DEMO_MODEL') and os.getenv('DEMO_API_KEY'))}})
                elif url.path == '/api/harness/state':
                    self.send(loop.harness_state(actor))
                elif url.path == '/api/harness/candidate':
                    self.send(loop.harness_candidate(actor,parse_qs(url.query)['id'][0]))
                elif url.path == '/api/harness/skill':
                    self.send(loop.harness_skill(actor,parse_qs(url.query)['id'][0]))
                elif url.path == '/api/health':
                    self.send({'mode': loop.agent.mode, **OpenClawAgent().health()})
                elif url.path == '/api/skill-package':
                    q = parse_qs(url.query)
                    self.send(loop.export_skill(actor,q['id'][0]),content_type='application/octet-stream')
                elif url.path == '/api/artifact':
                    q = parse_qs(url.query)
                    path = loop.artifact(actor,q['run'][0],q['path'][0])
                    self.send(path.read_bytes(),content_type='application/octet-stream')
                elif url.path == '/api/export':
                    state = loop.snapshot(actor)
                    rows = [{'type': 'manifest', 'schema': 1, 'mode': loop.agent.mode, 'actor': actor, 'exportedAt': time.time()}]
                    for kind in ('turns','pairs','intakes','pairAnnotations','pairDetections','recoveries','stageStatus','traces','workflows','learningDecisions','experienceMetadata','detections','pools','patchsets','candidates','skills','submissions','runs','events'):
                        rows += [{'type': kind, 'data': row} for row in state[kind]]
                    self.send(('\n'.join(json.dumps(r, ensure_ascii=False) for r in rows)+'\n').encode(), content_type='application/x-ndjson; charset=utf-8')
                elif url.path in ('/skills','/chat','/harness.js','/harness.css'):
                    name = 'harness.html' if url.path in ('/skills','/chat') else url.path[1:]
                    file = WEB / name
                    self.send(file.read_bytes(), content_type={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8'}[file.suffix])
                elif url.path in ('/', '/app.js', '/style.css'):
                    file = WEB / ('index.html' if url.path == '/' else url.path[1:])
                    self.send(file.read_bytes(), content_type={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8'}[file.suffix])
                else: self.send({'error':'not found'}, 404)
            except Forbidden as exc: self.send({'error':str(exc)},403)
            except Exception as exc: self.send({'error':str(exc)},400)
        def do_POST(self):
            try:
                self.allowed()
                if not self.headers.get('Content-Type','').startswith('application/json'): raise ValueError('需要application/json')
                size = int(self.headers.get('Content-Length','0'))
                if not 0 < size <= 1_000_000: raise ValueError('请求体大小不合法')
                data = json.loads(self.rfile.read(size))
                actor = data.get('actor', 'alice'); identity(actor)
                path = urlparse(self.path).path
                if path == '/api/chat': result = loop.chat(actor, data['session'], data['message'], data.get('skills'), data.get('requestId'), data.get('replyTo'))
                elif path == '/api/cycle': result = cycle(actor)
                elif path == '/api/generate': result = loop.generate(actor, data['id'])
                elif path == '/api/accept': result = loop.accept(actor, data['id'])
                elif path == '/api/reject': result = loop.reject(actor, data['id'])
                elif path == '/api/submit': result = loop.submit(actor, data['id'])
                elif path == '/api/review': result = loop.review(actor, data['id'], bool(data['approve']))
                elif path == '/api/rollback': result = loop.rollback(actor, data['id'], int(data['version']))
                elif path == '/api/scenario':
                    with cycle_lock: result = scenario(loop, actor)
                elif path == '/api/settings':
                    settings['autoLearn'] = bool(data.get('autoLearn')); result = settings
                elif path == '/api/import':
                    entries = data.get('entries')
                    if not isinstance(entries, list) or len(entries)>100: raise ValueError('一次最多导入100条')
                    result = [loop.import_turn(actor, entry) for entry in entries]
                elif path == '/api/import-events':
                    result = loop.import_events(actor,data.get('entries'),data.get('purposeSplit','generation'),data.get('initialization'))
                elif path == '/api/import-experience':
                    result=loop.import_experience(actor,data.get('experience'),data.get('purposeSplit','generation'),data.get('initialization'))
                elif path == '/api/stages':
                    result = loop.run_stages(actor)
                else: self.send({'error':'not found'},404); return
                self.send(result)
            except Forbidden as exc: self.send({'error':str(exc)},403)
            except Conflict as exc: self.send({'error':str(exc)},409)
            except Exception as exc: self.send({'error':str(exc)},400)

    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    threading.Thread(target=scheduler, daemon=True).start()
    print(f'Skills Loop Demo [{loop.agent.mode}] http://127.0.0.1:{port}', flush=True)
    try: server.serve_forever()
    finally: stop.set(); server.server_close(); lock.close()
