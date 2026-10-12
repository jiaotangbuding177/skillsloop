"""Explicit media API clients for the configured experimental ECNU account."""
import argparse
import base64
import hashlib
import json
import mimetypes
import os
from pathlib import Path
import time
import urllib.request
import urllib.error
import io


def delivered_generation_image(native_bytes, size):
    """Explicitly adapt a provider canvas mismatch without cropping content."""
    from PIL import Image, ImageOps
    expected=tuple(map(int,size.split('x')))
    original=Image.open(io.BytesIO(native_bytes));original.load()
    evidence={'native_size':list(original.size),'requested_size':list(expected),
        'native_image_sha256':hashlib.sha256(native_bytes).hexdigest(),
        'native_size_matches_requested':original.size==expected}
    if original.size==expected:return native_bytes,evidence
    source=original.convert('RGB')
    contained=ImageOps.contain(source,expected,Image.Resampling.LANCZOS)
    canvas=Image.new('RGB',expected,source.getpixel((0,0)))
    canvas.paste(contained,((expected[0]-contained.width)//2,(expected[1]-contained.height)//2))
    buffer=io.BytesIO();canvas.save(buffer,format='PNG')
    evidence.update(delivered_size=list(expected),conversion='aspect_preserving_resize_and_letterbox_all_content_kept',
        historical_resolution_or_model_restored=False)
    return buffer.getvalue(),evidence


def request(cfg,path,body):
    req=urllib.request.Request(cfg['base_url'].rstrip('/')+path,data=json.dumps(body).encode(),
        headers={'Authorization':'Bearer '+cfg['api_key'],'Content-Type':'application/json'})
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(req,timeout=180) as response:
            return response.headers.get('Content-Type',''),response.read()
    except urllib.error.HTTPError as exc:
        detail=exc.read().decode(errors='replace').replace(cfg['api_key'],'[REDACTED]')
        raise RuntimeError(f'ECNU HTTP {exc.code}: {detail[:2000]}') from None


def reference_sheet(paths, target):
    """Explicit ECNU single-upload adaptation for several actual references."""
    from PIL import Image, ImageOps, ImageDraw
    paths=[Path(p) for p in paths]
    canvas=Image.new('RGB',(768*len(paths),800),'white'); draw=ImageDraw.Draw(canvas)
    sources=[]
    for index, path in enumerate(paths):
        image=Image.open(path); image.load()
        view=ImageOps.contain(image.convert('RGB'),(748,748),Image.Resampling.LANCZOS)
        canvas.paste(view,(index*768+(768-view.width)//2,40+(748-view.height)//2))
        draw.text((index*768+12,12),f'REFERENCE {index+1}',fill='black')
        sources.append({'reference_number':index+1,'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'original_size':list(image.size)})
    canvas.save(target)
    return sources

def execute(command,text,output,credentials='/run/secrets/model.json',image_path=None,size='512x512',image_paths=None):
    cfg=json.loads(Path(credentials).read_text(encoding='utf-8-sig'));out=Path(output)
    out.parent.mkdir(parents=True,exist_ok=True);start=time.monotonic()
    if out.exists(): raise ValueError('Output already exists; choose a fresh path')
    if command=='image':
        if len(text)>1024: raise ValueError('ECNU image prompt exceeds its documented 1024 character limit; do not silently truncate')
        dimensions=size.split('x')
        if len(dimensions)!=2 or any(not x.isdigit() or not 64<=int(x)<=8192 for x in dimensions):raise ValueError('size must be WIDTHxHEIGHT, each from 64 to 8192')
        supported=('512x512','768x768','720x1280','1280x720','1024x1024')
        width,height=map(int,dimensions)
        provider_size=size if size in supported else ('1280x720' if width>height else '720x1280' if height>width else '1024x1024')
        model='ecnu-image';content_type,body=request(cfg,'/images/generations',{'model':model,'prompt':text,'size':provider_size,'response_format':'b64_json'})
        result=json.loads(body)
        if result.get('err_message'):raise RuntimeError(result['err_message'])
        rows=result.get('data',[])
        if not rows or not rows[0].get('b64_json'):raise RuntimeError('Image endpoint did not return requested b64_json')
        delivered,shape=delivered_generation_image(base64.b64decode(rows[0]['b64_json'],validate=True),size)
        out.write_bytes(delivered)
        receipt={'model':model,'content_type':content_type,'provider_created':result.get('created'),'revised_prompt':rows[0].get('revised_prompt'),'requested_size':size,'provider_requested_size':provider_size,'shape_adaptation':shape}
    elif command=='image-edit':
        if len(text)>1024: raise ValueError('ECNU edit prompt exceeds its documented 1024 character limit; do not silently truncate')
        paths=list(image_paths or ([] if not image_path else [image_path]))
        if not paths or any(not Path(p).is_file() for p in paths):raise ValueError('Image editing requires actual input image files')
        adaptation=None
        source=Path(paths[0])
        if len(paths)>1:
            source=out.with_suffix('.references.png')
            references=reference_sheet(paths,source)
            prefix='Input is a labeled reference sheet. Use REFERENCE 1 as the main image; use the other numbered references as specified. Return one final image, never the sheet. '
            if len(prefix+text)>1024:raise ValueError('ECNU edit prompt plus explicit multi-reference instruction exceeds 1024 characters')
            text=prefix+text
            adaptation={'method':'labeled_reference_sheet_single_upload','references':references,'provider_multi_file_API_used':False}
        import requests
        client=requests.Session();client.trust_env=False
        with source.open('rb') as handle:
            response=client.post(cfg['base_url'].rstrip('/')+'/images/edits',
                headers={'Authorization':'Bearer '+cfg['api_key']},
                data={'model':'ecnu-image','prompt':text,'response_format':'b64_json','n':'1'},
                files={'image':(source.name,handle,mimetypes.guess_type(source.name)[0] or 'image/png')},timeout=180)
        if response.status_code!=200:
            raise RuntimeError('ECNU edit HTTP '+str(response.status_code)+': '+response.text[:1600].replace(cfg['api_key'],'[REDACTED]'))
        result=response.json();rows=result.get('data',[])
        if result.get('err_message'):raise RuntimeError(str(result['err_message']).replace(cfg['api_key'],'[REDACTED]'))
        if not rows or not rows[0].get('b64_json'):raise RuntimeError('Image edit endpoint did not return requested b64_json')
        out.write_bytes(base64.b64decode(rows[0]['b64_json'],validate=True))
        receipt={'model':'ecnu-image','endpoint':'/images/edits','http_status':response.status_code,
            'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'provider_created':result.get('created'),'single_input_image':len(paths)==1,'reference_adaptation':adaptation,
            'multi_reference_image_array_supported':False,'historical_gpt_image_2_equivalence':False}
    elif command=='speech':
        model='ecnu-tts';fmt=out.suffix.lstrip('.') or 'wav'
        content_type,body=request(cfg,'/audio/speech',{'model':model,'input':text,'voice':'xiayu','response_format':fmt,'speed':1})
        if 'json' in content_type or len(body)<128:raise RuntimeError('TTS endpoint did not return usable audio bytes')
        out.write_bytes(body);receipt={'model':model,'content_type':content_type}
    elif command=='vision':
        image=Path(image_path);mime=mimetypes.guess_type(image.name)[0] or 'image/png'
        payload={'model':cfg['model'],'messages':[{'role':'user','content':[{'type':'text','text':text},
          {'type':'image_url','image_url':{'url':'data:'+mime+';base64,'+base64.b64encode(image.read_bytes()).decode()}}]}],
          'max_tokens':2048,'temperature':0}
        _,body=request(cfg,'/chat/completions',payload);result=json.loads(body)
        answer=result['choices'][0]['message']['content'];out.write_text(answer,encoding='utf-8')
        receipt={'model':result.get('model'),'requested_model':cfg['model'],'usage':result.get('usage')}
    else:raise ValueError('Unsupported tool command')
    receipt.update(command=command,output=str(out),bytes=out.stat().st_size,
                   sha256=hashlib.sha256(out.read_bytes()).hexdigest(),seconds=time.monotonic()-start)
    out.with_suffix(out.suffix+'.receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['image','image-edit','speech','vision']);p.add_argument('--text',required=True)
    p.add_argument('--output',required=True);p.add_argument('--credentials',default='/run/secrets/model.json');p.add_argument('--image-path')
    p.add_argument('--size',default='512x512');p.add_argument('--image-paths',nargs='+')
    a=p.parse_args();print(json.dumps(execute(a.command,a.text,a.output,a.credentials,a.image_path,a.size,a.image_paths),ensure_ascii=False))
