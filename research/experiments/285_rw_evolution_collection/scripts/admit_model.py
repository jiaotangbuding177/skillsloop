"""Tiny separately tagged infrastructure checks; never counted as app trajectories."""
import base64,json,random,struct,zlib,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def post(payload,label):
 req=urllib.request.Request('http://127.0.0.1:8190/285_admission/'+label+'/v1/chat/completions',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
 return json.load(urllib.request.urlopen(req,timeout=1800))
def main():
 colors={'red':(255,0,0),'green':(0,255,0),'blue':(0,0,255),'yellow':(255,255,0)}
 order=random.SystemRandom().sample(list(colors),4);w=400;h=100
 raw=b''.join(b'\0'+b''.join(bytes(colors[order[x//100]]) for x in range(w)) for _ in range(h))
 def chunk(k,d):return struct.pack('!I',len(d))+k+d+struct.pack('!I',zlib.crc32(k+d)&0xffffffff)
 png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
 image={'type':'image','source':{'type':'base64','media_type':'image/png','data':base64.b64encode(png).decode()}}
 result=post({'model':'deepseek-v4-flash-vision-exp','messages':[{'role':'user','content':'List the four colour blocks from left to right, only as JSON array of lowercase English colour names.\n'+json.dumps(image)}],'max_tokens':256},'vision')
 text=result['choices'][0]['message'].get('content','');import re
 parsed=json.loads(re.search(r'\[[^\]]+\]',text).group());vision=parsed==order
 tool=post({'model':'deepseek-v4-flash-vision-exp','messages':[{'role':'user','content':'Call add for a=8 and b=9.'}],'tools':[{'type':'function','function':{'name':'add','description':'Add integers','parameters':{'type':'object','properties':{'a':{'type':'integer'},'b':{'type':'integer'}},'required':['a','b']}}}],'tool_choice':{'type':'function','function':{'name':'add'}},'max_tokens':256},'tool')
 calls=tool['choices'][0]['message'].get('tool_calls') or [];tools=bool(calls) and calls[0]['function']['name']=='add' and json.loads(calls[0]['function']['arguments'])=={'a':8,'b':9}
 report={'vision_ready':vision,'tools_ready':tools,'separate_admission_not_trajectory':True,'physical_backend_checkpoint':'unknown','model_reported':result.get('model'),'vision_transport':'serialized Anthropic image restored as image_url by same frozen bridge','expected_order':order,'observed_order':parsed}
 (ROOT/'reports/model_acceptance.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));assert vision and tools
if __name__=='__main__':main()
