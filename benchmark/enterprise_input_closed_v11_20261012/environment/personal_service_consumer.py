"""Use the preserved personal-account layer with this benchmark's pinned image."""
import argparse, importlib.util, json
from pathlib import Path

BASE=Path(__file__).resolve().parent.parent
LAYER=Path('D:/skillloop/research/environment/20261008_personal_service_access/personal_service_consumer.py')

def main():
    p=argparse.ArgumentParser();p.add_argument('request');p.add_argument('response')
    p.add_argument('--services',default=str(LAYER.parent/'private/services_active.json'))
    p.add_argument('--credentials',required=True);p.add_argument('--timeout',type=int,default=900)
    p.add_argument('--image',default=json.loads((BASE/'environment/config.json').read_text('utf-8-sig'))['image'])
    a=p.parse_args();spec=importlib.util.spec_from_file_location('preserved_personal_layer',LAYER)
    layer=importlib.util.module_from_spec(spec);spec.loader.exec_module(layer)
    layer.ACTIVE_BENCH=BASE;layer.ORIGINAL=BASE/'environment/runtime/consumer.py'
    consumer=layer.install_layer(Path(a.services).resolve())
    original_command=consumer.build_command
    def command(*args,**kwargs):
        result=original_command(*args,**kwargs)
        index=result.index('/opt/real-services/service_bootstrap.py')
        result.insert(index,'/opt/eval-adapter/builtin_service_bootstrap.py')
        return result
    consumer.build_command=command
    consumer.run(a.request,a.response,image=a.image,timeout=a.timeout,credentials=a.credentials,backend='wsl')

if __name__=='__main__':main()
