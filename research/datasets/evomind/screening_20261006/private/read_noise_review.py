import ast,json,re,sys
from pathlib import Path
B=Path(__file__).parent
tree=ast.parse((B.parent/'prepare_review.py').read_text(encoding='utf-8'))
fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='redact')
exec(compile(ast.Module(body=[fn],type_ignores=[]),'<redaction_only>','exec'))
items=[]
for i in range(1,4):
    items.extend(json.loads((B/f'noise_review_{i}.json').read_text(encoding='utf-8')))
start=int(sys.argv[1])
end=int(sys.argv[2]) if len(sys.argv)>2 else min(start+70,len(items))
for n,x in enumerate(items[start:end],start):
    print(n,x['session_id'],x['assistant_id'],repr(redact(x['text'])))
