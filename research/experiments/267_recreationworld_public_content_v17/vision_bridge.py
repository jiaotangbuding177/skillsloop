"""Lossless recovery of image blocks serialized by official text-only proxy."""
import base64,json,re
def split_images(text):
 out=[]; position=0; count=0; decoder=json.JSONDecoder()
 for match in re.finditer(r'\{\s*"type"\s*:\s*"image"\s*,',text):
  if match.start()<position: continue
  try:
   block,size=decoder.raw_decode(text[match.start():]); source=block.get('source',{})
   if source.get('type')!='base64' or source.get('media_type') not in ('image/png','image/jpeg','image/webp','image/gif'): continue
   data=source.get('data'); base64.b64decode(data,validate=True)
   if match.start()>position: out.append({'type':'text','text':text[position:match.start()]})
   out.append({'type':'image_url','image_url':{'url':'data:'+source['media_type']+';base64,'+data}})
   count+=1; position=match.start()+size
  except (ValueError,TypeError,KeyError): continue
 if not count: return [{'type':'text','text':text}],0
 if position<len(text): out.append({'type':'text','text':text[position:]})
 return out,count
def repair_messages(messages):
 result=[]; pending=[]; count=0; image_bytes=0
 def flush():
  if pending:
   result.append({'role':'user','content':list(pending)}); pending.clear()
 for message in messages:
  role=message.get('role'); content=message.get('content'); converted=dict(message)
  if role!='tool': flush()
  if role in ('user','tool') and isinstance(content,str):
   blocks,n=split_images(content); count+=n
   if n:
    image_bytes+=sum(len(x['image_url']['url']) for x in blocks if x['type']=='image_url')
    if role=='tool':
     converted['content']=''.join(x['text'] for x in blocks if x['type']=='text')+'\n[Image observation supplied immediately after tool results.]'
     pending.append({'type':'text','text':'Image observation from tool '+str(message.get('tool_call_id'))})
     pending.extend(x for x in blocks if x['type']=='image_url')
    else: converted['content']=blocks
  result.append(converted)
 flush()
 return result,{'recovered_image_blocks':count,'image_data_url_characters':image_bytes,'lossless':True}
