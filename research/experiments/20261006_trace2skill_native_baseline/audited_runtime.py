"""External transport and Windows shell adapters; no Trace2Skill source changes."""
from __future__ import annotations
import contextlib, hashlib, json, os, re, shutil, subprocess, sys, threading, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
BASELINE = PROJECT / 'research/baselines/Trace2Skill'

def bootstrap_imports():
    for p in (BASELINE, BASELINE/'src', BASELINE/'.runtime/deps'):
        if str(p) not in sys.path: sys.path.insert(0, str(p))
    paths = [str(BASELINE/'.runtime/deps'), str(BASELINE), str(BASELINE/'src')]
    old = os.environ.get('PYTHONPATH', '')
    os.environ['PYTHONPATH'] = os.pathsep.join(paths + ([old] if old else []))
    os.environ['PYTHONUTF8'] = '1'

def dump(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str)+'\n', encoding='utf-8')

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

class RunBudgetExceeded(RuntimeError): pass

class RequestAudit:
    """Records actual HTTP attempts, including SDK retries. Never records headers."""
    def __init__(self, root, max_requests=40, max_reported_tokens=1000000):
        self.root=Path(root); self.lock=threading.RLock(); self.rows=[]
        self.max_requests=max_requests; self.max_reported_tokens=max_reported_tokens
        self.phase='unassigned'; self.known_tokens=0
        self.secret=os.environ.get('ECNU_API_KEY') or os.environ.get('OPENAI_API_KEY') or ''
    def save(self):
        dump(self.root/'requests_ledger.json', {
            'actual_http_attempts':len(self.rows), 'reported_tokens':self.known_tokens,
            'requests_without_usage':sum(r.get('usage') is None for r in self.rows),
            'max_requests':self.max_requests, 'max_reported_tokens':self.max_reported_tokens,
            'reported_limit_is_not_an_upper_bound_on_unknown_usage':True, 'requests':self.rows})
    def begin(self, request):
        with self.lock:
            if len(self.rows)>=self.max_requests or self.known_tokens>=self.max_reported_tokens:
                raise RunBudgetExceeded('Frozen run budget exhausted; no further HTTP allowed')
            raw=request.read(); body=json.loads(raw.decode('utf-8')) if raw else {}
            seq=len(self.rows)+1
            row={'number':seq,'phase':self.phase,'method':request.method,
                 'url':str(request.url),'payload_sha256':hashlib.sha256(raw).hexdigest(),
                 'requested_model':body.get('model'),'status':'STARTED',
                 'effective_parameters':{k:v for k,v in body.items() if k!='messages'}}
            self.rows.append(row); dump(self.root/'requests'/f'{seq:03d}_request.json',body)
            self.save(); return row,time.monotonic()
    def end(self, row, start, response=None, error=None):
        with self.lock:
            row['elapsed_seconds']=round(time.monotonic()-start,3)
            if error:
                msg=str(error)
                if self.secret: msg=msg.replace(self.secret,'[REDACTED]')
                row.update(status='TRANSPORT_FAILED',error_type=type(error).__name__,error=msg)
            else:
                raw=response.read(); path=self.root/'requests'/f"{row['number']:03d}_response.json"
                try: obj=json.loads(raw); dump(path,obj)
                except Exception: obj={}; dump(path,{'raw_text':raw.decode('utf-8',errors='replace')})
                usage=obj.get('usage'); row.update(status='RETURNED',http_status=response.status_code,
                    served_model=obj.get('model'),usage=usage)
                if isinstance(usage,dict) and isinstance(usage.get('total_tokens'),int):
                    self.known_tokens+=usage['total_tokens']
                choices=obj.get('choices') or []
                if choices:
                    row['finish_reason']=choices[0].get('finish_reason')
                    msg=choices[0].get('message') or {}
                    row['has_reasoning_content']=bool(msg.get('reasoning_content') or msg.get('reasoning'))
                    row['content_characters']=len(msg.get('content') or '')
            self.save()
            print(json.dumps({'http':row['number'],'phase':row['phase'],'status':row['status'],
                              'tokens':(row.get('usage') or {}).get('total_tokens')},ensure_ascii=False),flush=True)

@contextlib.contextmanager
def instrument_sdk(audit):
    """Only adds httpx transport instrumentation; preserves SDK kwargs and retries."""
    import openai, httpx
    original_sync,original_async=openai.OpenAI,openai.AsyncOpenAI
    clients=[]
    class SyncTransport(httpx.BaseTransport):
        def __init__(self): self.inner=httpx.HTTPTransport()
        def handle_request(self, request):
            row,start=audit.begin(request)
            try:
                response=self.inner.handle_request(request)
                audit.end(row,start,response=response); return response
            except Exception as exc:
                audit.end(row,start,error=exc); raise
        def close(self): self.inner.close()
    class AsyncTransport(httpx.AsyncBaseTransport):
        def __init__(self): self.inner=httpx.AsyncHTTPTransport()
        async def handle_async_request(self, request):
            row,start=audit.begin(request)
            try:
                response=await self.inner.handle_async_request(request)
                await response.aread(); audit.end(row,start,response=response); return response
            except Exception as exc:
                audit.end(row,start,error=exc); raise
        async def aclose(self): await self.inner.aclose()
    def sync_factory(*args,**kwargs):
        if kwargs.get('http_client') is not None: raise ValueError('Uninstrumented custom HTTP client')
        kwargs['http_client']=httpx.Client(transport=SyncTransport(),timeout=kwargs.get('timeout',600))
        value=original_sync(*args,**kwargs); clients.append(value); return value
    def async_factory(*args,**kwargs):
        if kwargs.get('http_client') is not None: raise ValueError('Uninstrumented custom HTTP client')
        kwargs['http_client']=httpx.AsyncClient(transport=AsyncTransport(),timeout=kwargs.get('timeout',600))
        return original_async(*args,**kwargs)
    openai.OpenAI,openai.AsyncOpenAI=sync_factory,async_factory
    try: yield
    finally:
        openai.OpenAI,openai.AsyncOpenAI=original_sync,original_async
        for client in clients: client.close()
        audit.save()

def find_bash():
    for p in (Path('C:/Program Files/Git/bin/bash.exe'),Path('C:/Program Files/Git/usr/bin/bash.exe')):
        if p.is_file(): return str(p)
    return shutil.which('bash')

def windows_bash_factory(working_dir, timeout=120):
    """Same tool schema/observations, explicit POSIX interpreter on Windows."""
    bootstrap_imports()
    from react_agent.tools import tool
    root=Path(working_dir).resolve()
    if PROJECT.resolve() not in root.parents and root!=PROJECT.resolve():
        raise ValueError('Agent workspace must stay inside the research project')
    interpreter=find_bash()
    if not interpreter: raise RuntimeError('No POSIX Bash interpreter available')
    @tool(name='bash')
    def bash(command:str)->str:
        """
        Execute a bash command in the working directory.
        Use this to run Python scripts, install packages, navigate files,
        or perform any shell operations.

        Args:
            command: The bash command to execute
        """
        # No deletion/moving or system administration is part of the calibration.
        if re.search(r'(^|[;&|\n]\s*)(rm|rmdir|del|mv|shutdown|reboot)\b',command,re.I):
            return '[ERROR] Destructive operation is outside this frozen research run'
        env=os.environ.copy(); env['PYTHONUTF8']='1'
        env['PATH']=str(Path(sys.executable).parent)+os.pathsep+env.get('PATH','')
        # A run-local Windows profile must not hide the existing user packages.
        paths=[str(p) for p in (BASELINE/'.runtime/deps',BASELINE,BASELINE/'src')]
        paths += [p for p in sys.path if p and p.endswith('site-packages')]
        paths += env.get('PYTHONPATH','').split(os.pathsep)
        env['PYTHONPATH']=os.pathsep.join(dict.fromkeys(p for p in paths if p))
        try:
            result=subprocess.run([interpreter,'-c',command],cwd=root,env=env,capture_output=True,
                                  text=True,encoding='utf-8',errors='replace',timeout=timeout)
            output=(result.stdout or '')+(('\n[STDERR]\n'+result.stderr) if result.stderr else '')
            if result.returncode: output+=f'\n[Exit code: {result.returncode}]'
            return output.strip() or '[Command completed with no output]'
        except subprocess.TimeoutExpired: return f'[ERROR] Command timed out after {timeout} seconds'
        except Exception as exc: return f'[ERROR] Failed to execute command: {exc}'
    return bash

@contextlib.contextmanager
def platform_adapter():
    bootstrap_imports()
    import spreadsheet_agent.tools as tools_mod
    import spreadsheet_agent.tools.bash as bash_mod
    from spreadsheet_agent.agents import cli_only_agent,cli_skill_preloaded_agent
    import analysis.error_analysis_agent as error_agent
    modules=(tools_mod,bash_mod,cli_only_agent,cli_skill_preloaded_agent,error_agent)
    old=[m.create_bash_tool for m in modules]
    if os.name=='nt':
        for m in modules: m.create_bash_tool=windows_bash_factory
    try: yield
    finally:
        for m,value in zip(modules,old): m.create_bash_tool=value
