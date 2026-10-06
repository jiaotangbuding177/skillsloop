"""Offline dependency clues; not installed-program inventory or execution proof."""
from pathlib import Path
from collections import Counter
import contextlib,io,json,re
R=Path(__file__).resolve().parent
# Reuse the audited extraction and deduplication up to its in-memory record list.
# No historical commands are executed and no prior outputs are overwritten.
code=(R/'normalize_tools.py').read_text(encoding='utf-8').split('hits=[]')[0]
namespace={'__file__':str(R/'normalize_tools.py')}
exec(compile(code,str(R/'normalize_tools.py'),'exec'),namespace)
records=namespace['records']
patterns={'Python':r'\bpython(?:3(?:\.\d+)?)?\b','Node/npm/npx':r'\b(?:node|npm|npx)\b','LibreOffice/soffice':r'\b(?:soffice|libreoffice)\b','Pandoc':r'\bpandoc\b','Poppler工具':r'\b(?:pdftoppm|pdftotext|pdfinfo|pdftocairo)\b','FFmpeg':r'\b(?:ffmpeg|ffprobe)\b','Git':r'\bgit\b','curl/wget':r'\b(?:curl|wget)\b','Bash':r'\bbash\b'}
dependencies=[]
for name,pattern in patterns.items():
 matches=[r for r in records if r['name']=='exec' and re.search(pattern,namespace['j'](r['args']),re.I)]
 if not matches:continue
 dependencies.append({'dependency_clue':name,'exec_parameter_records':len(matches),'sessions':len({r['session_id'] for r in matches}),'evidence_refs':[{'session_id':r['session_id'],'tool_call_id':r['tool_call_id'],'message_id':r['message_id'],'status':r['status']} for r in matches],'interpretation':'参数文本包含名称，可能是检查/安装/脚本内容/实际调用；不是已安装或成功使用认证'})
out={'all_deduplicated_exported_tool_records':len(records),'tool_name_counts':dict(Counter(r['name'] for r in records)),'dependencies':dependencies,'scope':'现有1466会话工具活动与范围内1373工具样本合并去重；非全部历史工具执行','not_verified':['完整覆盖','工具参数/返回正式schema','程序版本与安装','产物正确','本机可运行']}
(R/'private/environment_requirement_clues.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({**{k:v for k,v in out.items() if k!='dependencies'},'dependencies':[{k:v for k,v in x.items() if k!='evidence_refs'} for x in dependencies]},ensure_ascii=False))
