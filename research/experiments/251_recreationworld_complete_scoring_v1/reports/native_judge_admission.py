"""Official visual judge interface admission, isolated synthetic fixture only."""
import json,sys,struct,zlib
from pathlib import Path
root=Path(__file__).resolve().parents[1]
scripts=root.parent/'218_recreationworld_glm_pipeline/vendor/RecreationWorld/scripts'
sys.path.insert(0,str(scripts))
from common import vlm_judge
def chunk(t,b): return struct.pack('>I',len(b))+t+b+struct.pack('>I',zlib.crc32(t+b)&0xffffffff)
rows=[]
for y in range(600):
 rows.append(b'\0'+b''.join(b'\0\0\xff' if 200<=x<600 and 100<=y<500 else b'\xff\xff\xff' for x in range(800)))
path=root/'reports/blue_square_fixture.png'
path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',800,600,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(rows)))+chunk(b'IEND',b''))
cfg=vlm_judge.resolve(model='deepseek-v4-flash-vision-exp',base_url='http://127.0.0.1:8166/251_recreationworld/judge_admission/v1',api_key='local')
verdicts=vlm_judge.judge_assertions(str(path),['The screenshot contains a large blue square on a white background.','The screenshot contains a large red circle.'],cfg=cfg,retries=0)
passed=len(verdicts)==2 and verdicts[0].get('pass') is True and verdicts[1].get('pass') is False
report={'passed':passed,'official_judge_interface':True,'synthetic_not_benchmark':True,'expected':[True,False],'verdicts':verdicts,'judge_requested_model':cfg['model'],'judge_same_provider_as_agent':True,'exact_backend_unverified':True}
(root/'reports/native_judge_admission.json').write_text(json.dumps(report,indent=2)); print(json.dumps(report))
