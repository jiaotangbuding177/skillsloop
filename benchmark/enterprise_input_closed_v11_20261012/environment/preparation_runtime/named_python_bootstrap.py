"""Apply source-scoped pinned Python support after the current turn's delivery.

This helper modifies the caller's subprocess env mapping, not global os.environ.
It installs no business files or model outputs, and performs no network requests.
"""
import hashlib
import json
import os
import shlex
import sys
import sysconfig
import tarfile
from pathlib import Path

SOURCE='conv_bcae4fd64969'
KEY='source_named_python_support'

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def apply(context, workspace, env):
    cfg=context.get(KEY)
    if not cfg:
        return {'schema':'source-named-python-support-receipt-v1','applied':False,'reason':'not_declared_in_current_turn'}
    sid=context.get('source_session_id',cfg.get('source_session_id'))
    if sid!=SOURCE or cfg.get('source_session_id')!=SOURCE:
        raise ValueError('Named Python support belongs only to its declared source')
    if int(cfg.get('available_from_dispatch_index',-1))!=1:
        raise ValueError('Support must be declared at the reviewed first demand')
    workspace=Path(workspace).resolve()
    archive=workspace/cfg['archive_relative_path']
    if not archive.resolve().is_relative_to(workspace) or not archive.is_file():
        raise ValueError('Current-turn runtime archive is not available inside workspace')
    if sha(archive)!=cfg['archive_sha256']:
        raise ValueError('Pinned Python support archive checksum mismatch')
    # Expand libraries in the container filesystem: thousands of small wheel
    # files should not be copied through a Windows workspace bind mount.
    runtime_root=Path('/tmp/benchmark_named_python_runtime').resolve()
    token=hashlib.sha256((str(workspace)+'|'+cfg['archive_sha256']).encode()).hexdigest()[:20]
    prefix=runtime_root/token
    if not prefix.resolve().is_relative_to(runtime_root):raise ValueError('Invalid runtime destination')
    marker=prefix/'.ready.json'
    reused=False
    if marker.exists():
        old=json.loads(marker.read_text('utf8'))
        reused=old.get('archive_sha256')==cfg['archive_sha256']
        if not reused:raise ValueError('Runtime prefix contains a different support version')
    else:
        prefix.mkdir(parents=True,exist_ok=True)
        with tarfile.open(archive,'r:gz') as tar:
            for member in tar.getmembers():
                target=(prefix/member.name).resolve()
                if not target.is_relative_to(prefix.resolve()) or not (member.isdir() or member.isfile()):
                    raise ValueError('Unsafe path or link in pinned support archive')
            # Fixed image uses CPython 3.11.2, before extractall(filter=...)
            # existed. Every member above is already checked: local regular
            # files/directories only, no links and no escape from the prefix.
            tar.extractall(prefix)
        manifest=prefix/'runtime_manifest.json'
        if sha(manifest)!=cfg['runtime_manifest_sha256']:
            raise ValueError('Support manifest checksum mismatch')
        data=json.loads(manifest.read_text('utf8'))
        for entry in data['files']:
            p=prefix/entry['path']
            if not p.resolve().is_relative_to(prefix.resolve()) or sha(p)!=entry['sha256']:
                raise ValueError('Installed support member checksum mismatch')
        marker.write_text(json.dumps({'archive_sha256':cfg['archive_sha256'],'files':len(data['files'])})+'\n','utf8')
    # Gateway already runs with its initial environment. Newly launched Python
    # exec processes read this late registration independently of that old env.
    purelib=Path(sysconfig.get_path('purelib'))
    purelib.mkdir(parents=True,exist_ok=True)
    registration=purelib/'benchmark_source_named_python_support.pth'
    content=f'import sys; sys.path.insert(0, {str(prefix)!r})\n'
    if registration.exists() and registration.read_text('utf8')!=content:
        raise ValueError('Temporary container Python site has a conflicting source registration')
    registration.write_text(content,'utf8')
    inherited_path=env.get('PATH',os.environ.get('PATH',''))
    scripts=Path(sysconfig.get_path('scripts'))
    if str(scripts) not in inherited_path.split(os.pathsep):
        raise ValueError('Python console scripts directory is not visible to the original Gateway PATH')
    shims=[]
    for entry in sorted((prefix/'bin').iterdir()):
        if not entry.is_file() or not (entry.name.startswith('jupyter') or entry.name in ['ipython','ipython3']):continue
        dest=scripts/entry.name
        body='#!/bin/sh\nexec '+shlex.quote(sys.executable)+' '+shlex.quote(str(entry))+' "$@"\n'
        if dest.exists() and dest.read_text('utf8')!=body:
            raise ValueError('Existing console command conflicts with the source-scoped runtime')
        dest.write_text(body,'utf8');dest.chmod(0o755);shims.append(str(dest))
    def prepend(key,path,default=''):
        rest=[part for part in env.get(key,default).split(os.pathsep) if part and part!=str(path)]
        env[key]=os.pathsep.join([str(path)]+rest)
    prepend('PYTHONPATH',prefix)
    prepend('PATH',prefix/'bin',os.environ.get('PATH',''))
    env['JUPYTER_PATH']=str(prefix/'share/jupyter')
    return dict(schema='source-named-python-support-receipt-v1',source_session_id=SOURCE,applied=True,
                reused=reused,archive_sha256=cfg['archive_sha256'],prefix=str(prefix),
                pythonpath_applied=True,path_applied=True,network_calls=0,model_calls=0,
                temporary_python_site_registration=str(registration),console_shims=shims,
                registration_scope='Only this disposable current-source container, registered after first explicit demand; image and host untouched',
                gateway_old_environment_supported=True)
