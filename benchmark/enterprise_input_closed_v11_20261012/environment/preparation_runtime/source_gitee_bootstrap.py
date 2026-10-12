"""Permit native Git access to this attempt's declared mounted repositories."""
from pathlib import Path
import argparse,json,os,subprocess,sys


def main():
    p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,default=Path('/workspace'));a,chain=p.parse_known_args()
    if chain and (not chain[0].endswith('.py') or not Path(chain[0]).is_file()):p.error('Following bootstrap must be an existing Python script')
    def finish():
        if chain:
            sys.stdout.flush();os.execv(sys.executable,[sys.executable,*chain])
        return 0
    root=a.workspace.resolve();statepath=root/'services/gitee_activity.json'
    if not statepath.is_file():print(json.dumps({'gitee_initialized':False,'reason':'no declared source state'}));return finish()
    state=json.loads(statepath.read_text(encoding='utf-8'));paths=[]
    for repository in state.get('repositories',[]):
        for field in ['checkout','local_remote']:
            if repository.get(field):paths.append((root/repository[field]).resolve())
    if not paths and (root/'services/gitee_repo/.git').is_dir():paths.append((root/'services/gitee_repo').resolve())
    for path in paths:
        if not path.is_relative_to(root) or not path.is_dir():raise ValueError('Declared Git repository is absent or outside this workspace')
        subprocess.run(['git','config','--global','--add','safe.directory',str(path)],check=True,capture_output=True)
    print(json.dumps({'gitee_initialized':True,'source':state['session_id'],'declared_repository_paths':len(paths),'configuration_lifetime':'current container only','public_gitee_API_calls':0}))
    return finish()


if __name__=='__main__':raise SystemExit(main())
