import importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
s=importlib.util.spec_from_file_location('relay',ROOT/'relay.py'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
rejected=0
for message in [{'content':''},{'content':None},{'content':'   '},{'content':'','reasoning_content':'synthetic fixture, not a final answer'}]:
 try: m.complete({'choices':[{'finish_reason':'stop','message':message}]})
 except ValueError: rejected+=1
assert rejected==4
assert m.complete({'choices':[{'finish_reason':'stop','message':{'content':'Delivered'}}]})
report={'empty_visible_outputs_rejected':rejected,'reasoning_only_not_treated_as_final_answer':True,'nonempty_completion_accepted':True}
(ROOT/'reports/empty_output_acceptance.json').write_text(json.dumps(report,indent=2)); print(json.dumps(report))
