"""Mechanical terminal-artifact extensions. Never executes submitted source or OCR.

register_extensions(base) augments a vendored scorer without changing its source.
Evidence bindings and authenticity are the runtime's responsibility. Additional
measurement records are documented in artifact_extensions_normalization.json.
"""
import csv
import hashlib
import io
import posixpath
import re
import unicodedata
import zipfile
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from pathlib import PurePosixPath
from xml.etree import ElementTree as ET

SOURCE_EXT={'.py','.js','.mjs','.cjs','.ts','.tsx','.jsx','.html','.htm','.css','.scss',
            '.vue','.svelte','.c','.h','.cpp','.hpp','.cs','.java','.go','.rs','.rb','.php','.sh','.ps1','.sql'}
SOURCE_LANG={'python','py','javascript','js','typescript','ts','tsx','jsx','html','css','scss',
             'vue','svelte','c','cpp','c++','csharp','cs','java','go','rust','rs','ruby','php','bash','sh','powershell','ps1','sql'}
TEXT_EXT=SOURCE_EXT|{'.md','.txt','.json','.yaml','.yml','.xml','.csv','.tsv'}
XDR='http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
S='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS={'xdr':XDR,'a':A,'r':R,'s':S,'w':W}


def _sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def _norm(text,mode=None):
    return unicodedata.normalize('NFKC',str(text)) if mode in ('NFKC','NFKC_whitespace') else str(text)
def _need(b,test,reason):
    if not test:raise b.UnknownEvidence(reason)
def _assert(b,test,reason):
    if not test:raise b.DeliveryFailure(reason)
def _keys(b,p,allowed):
    _need(b,isinstance(p,dict),'artifact_parameters_invalid')
    extra=set(p)-allowed-{'score_at','historical_ai_is_gold'}
    _need(b,not extra,'unsupported_artifact_parameter:'+','.join(sorted(extra)))
    if 'score_at' in p:_need(b,p['score_at']=='conversation_end_only','artifact_scoring_time_not_supported')
    if 'historical_ai_is_gold' in p:_need(b,p['historical_ai_is_gold'] is False,'artifact_historical_gold_policy_not_supported')
def _true(b,p,key):
    if key in p:_need(b,p[key] is True,'unsupported_false_or_nonboolean_policy:'+key)
def _enum(b,p,key,allowed):
    if key in p:_need(b,p[key] in allowed,'unsupported_artifact_parameter_value:'+key)
def _relative(ctx,path):return path.relative_to(ctx.workspace).as_posix()
def _initial(b,ctx):
    value=ctx.evidence.get('initial_sha256')
    _need(b,isinstance(value,dict),'initial_snapshot_missing')
    _need(b,ctx.evidence.get('schema')=='final-state-evidence-v1','initial_snapshot_schema_unverified')
    measurement=ctx.evidence.get('measurement',{})
    _need(b,not isinstance(measurement,dict) or measurement.get('initial_snapshot_complete') is not False,'initial_snapshot_incomplete')
    return value
def _verified_input(b,ctx,path,expected_sha):
    _need(b,isinstance(expected_sha,str) and bool(expected_sha),'source_input_sha_missing')
    _need(b,path.is_file(),'source_input_file_missing')
    actual=_sha(path)
    _need(b,actual==expected_sha,'source_input_sha_mismatch')
    key=_relative(ctx,path)
    declared=ctx.evidence.get('declared_input_sha256')
    initial=ctx.evidence.get('initial_sha256')
    known=(isinstance(declared,dict) and declared.get(key)==actual) or (isinstance(initial,dict) and initial.get(key)==actual)
    _need(b,known,'source_input_not_bound_to_attempt_snapshot')
    return actual
def _fresh_source(b,ctx,path):
    _assert(b,path.is_file() and path.stat().st_size>0,'source_delivery_missing_or_empty')
    h=_sha(path);key=_relative(ctx,path)
    values=ctx.evidence.get('declared_input_sha256',{})
    if isinstance(values,dict):_assert(b,h not in values.values(),'unchanged_input_used_as_generated_source')
    initial=ctx.evidence.get('initial_sha256',{})
    if isinstance(initial,dict):_assert(b,h not in initial.values(),'unchanged_initial_source_used_as_new_delivery')
    try:return path.read_text('utf-8-sig')
    except UnicodeError as exc:raise b.UnknownEvidence('source_text_encoding_not_readable') from exc


def _code(b,ctx,did,p,kind):
    allowed={'accepted_forms','require_nonempty_code_payload','resolve_from_current_attempt_delivery_declaration','reject_plan_only','reject_reused_input_documents'}
    _keys(b,p,allowed)
    for key in allowed-{'accepted_forms'}:_true(b,p,key)
    forms=p.get('accepted_forms',['source_file','archive_with_source','delivered_fenced_source'])
    _need(b,isinstance(forms,list) and set(forms)<={'source_file','archive_with_source','delivered_fenced_source'},'unsupported_code_delivery_form')
    payloads=[]
    for file in ctx.files(did):
        if file.suffix.lower() in SOURCE_EXT and 'source_file' in forms:
            text=_fresh_source(b,ctx,file)
            _assert(b,bool(text.strip()),'source_code_empty')
            payloads.append(_relative(ctx,file))
        elif file.suffix.lower()=='.zip' and 'archive_with_source' in forms:
            _assert(b,file.is_file() and file.stat().st_size>0,'source_archive_missing_or_empty')
            digest=_sha(file);inputs=ctx.evidence.get('declared_input_sha256',{})
            if isinstance(inputs,dict):_assert(b,digest not in inputs.values(),'unchanged_input_archive_used_as_generated_code')
            initial=ctx.evidence.get('initial_sha256',{})
            if isinstance(initial,dict):_assert(b,digest not in initial.values(),'unchanged_initial_archive_used_as_generated_code')
            try:
                with zipfile.ZipFile(file) as z:
                    _assert(b,z.testzip() is None,'source_archive_crc_error')
                    for member in z.infolist():
                        name=PurePosixPath(member.filename.replace('\\','/'))
                        if member.is_dir() or name.suffix.lower() not in SOURCE_EXT:continue
                        _assert(b,not name.is_absolute() and '..' not in name.parts,'unsafe_source_archive_member')
                        blob=z.read(member)
                        try:text=blob.decode('utf-8-sig')
                        except UnicodeError as exc:raise b.UnknownEvidence('archive_source_encoding_not_readable') from exc
                        if text.strip():payloads.append(_relative(ctx,file)+'!'+member.filename)
            except zipfile.BadZipFile as exc:raise b.DeliveryFailure('source_archive_unreadable') from exc
            except RuntimeError as exc:raise b.UnknownEvidence('source_archive_payload_not_readable') from exc
    if 'delivered_fenced_source' in forms and (not payloads or 'text' in ctx.binding(did) or 'items' in ctx.binding(did)):
        text=ctx.text(did,allow_files=False)
        for i,(lang,body) in enumerate(re.findall(r'(?m)^\s*```([^\n`]*)\n(.*?)^\s*```\s*$',text,re.S),1):
            if lang.strip().casefold() in SOURCE_LANG and body.strip():payloads.append('delivered_code_block:'+str(i))
    _assert(b,bool(payloads),'actual_source_code_delivery_missing')
    return {'code_payloads':len(payloads),'payloads':payloads,'functionality_executed':False,'semantic_quality_verified':False}


def _scoped_text(b,ctx,did,p):
    scope=p.get('scope','current_attempt_delivery')
    known={'current_attempt_delivery','generated_skill_and_examples','generated_skill_and_references','final_feedback_report'}
    _need(b,scope in known,'unsupported_literal_scope')
    if scope.startswith('generated_skill_'):
        directory=ctx.binding(did).get('directory')
        _need(b,bool(directory),'generated_skill_directory_binding_missing')
        root=ctx.path(directory);_assert(b,root.is_dir(),'generated_skill_directory_missing')
        inputs=ctx.evidence.get('declared_input_sha256',{})
        chunks=[]
        for file in root.rglob('*'):
            if file.is_file() and file.suffix.lower() in TEXT_EXT:
                if isinstance(inputs,dict) and _sha(file) in inputs.values():continue
                try:chunks.append(file.read_text('utf-8-sig'))
                except UnicodeError as exc:raise b.UnknownEvidence('generated_skill_text_encoding_unreadable') from exc
        text='\n'.join(chunks)
    else:text=ctx.text(did)
    used='full_report'
    if 'section_scope' in p:
        _enum(b,p,'section_scope',{'second_chapter_if_machine_identifiable_else_full_report'})
        match=re.search(r'(?m)^\s*(?:#{1,6}\s*)?(?:第二[章节]|二[、.]|2[、.])[^\n]*\n',text)
        if match:
            end=re.search(r'(?m)^\s*(?:#{1,6}\s*)?(?:第三[章节]|三[、.]|3[、.])',text[match.end():])
            text=text[match.start():match.end()+end.start()] if end else text[match.start():]
            used='second_chapter'
    return text,used


def _literal(b,ctx,did,p,kind):
    allowed={'scope','literals','numeric_fields','number_match','unicode_normalization','trigger_examples','trigger_examples_mode','section_scope'}
    _keys(b,p,allowed);_enum(b,p,'unicode_normalization',{'NFKC'});_enum(b,p,'number_match',{'token_after_grouping_separator_normalization'});_enum(b,p,'trigger_examples_mode',{'report_only'})
    _need(b,any(k in p for k in ('literals','numeric_fields','trigger_examples')),'literal_predicate_missing')
    raw,scope=_scoped_text(b,ctx,did,p);text=_norm(raw,p.get('unicode_normalization'))
    literals=p.get('literals',[]);numbers=p.get('numeric_fields',[])
    _need(b,isinstance(literals,list) and all(isinstance(v,str) for v in literals),'invalid_literal_list')
    _assert(b,all(_norm(v,p.get('unicode_normalization')) in text for v in literals),'explicit_literal_field_missing')
    numerictext=unicodedata.normalize('NFKC',text)
    # Remove only syntactically valid thousands groups; never match 500 inside 5000 or a SKU.
    numerictext=re.sub(r'(?<![\d.,])\d{1,3}(?:,\d{3})+(?:\.\d+)?(?![\d,])',lambda m:m.group().replace(',',''),numerictext)
    tokens=re.findall(r'(?<![0-9A-Za-z_.])[-+]?\d+(?:\.\d+)?(?![0-9A-Za-z_.])',numerictext)
    parsed={Decimal(v) for v in tokens}
    try:expected=[Decimal(unicodedata.normalize('NFKC',str(v)).replace(',','')) for v in numbers]
    except InvalidOperation as exc:raise b.UnknownEvidence('invalid_expected_numeric_field') from exc
    _assert(b,all(v in parsed for v in expected),'explicit_numeric_field_missing')
    triggers=p.get('trigger_examples',[])
    if triggers:_need(b,p.get('trigger_examples_mode')=='report_only','trigger_examples_require_observation_mode')
    _need(b,isinstance(triggers,list),'invalid_trigger_example_list')
    return {'literal_count':len(literals),'numeric_fields_matched':len(expected),'text_scope_used':scope,
            'trigger_examples_observed':{v:_norm(v,p.get('unicode_normalization')) in text for v in triggers},'trigger_behavior_verified':False}


class _HTMLTables(HTMLParser):
    def __init__(self):super().__init__();self.stack=[];self.tables=[]
    def handle_starttag(self,tag,attrs):
        if tag=='table':self.stack.append({'rows':[],'row':None,'cell':None,'header':False,'row_header':False})
        if self.stack and tag=='thead':self.stack[-1]['header']=True
        if self.stack and tag=='tr':
            self.stack[-1]['row']=[];self.stack[-1]['row_header']=self.stack[-1]['header']
        if self.stack and tag in ('td','th'):self.stack[-1]['cell']=[tag,[]]
    def handle_data(self,text):
        for frame in self.stack:
            if frame['cell'] is not None:frame['cell'][1].append(text)
    def handle_endtag(self,tag):
        if self.stack and tag in ('td','th') and self.stack[-1]['cell'] is not None:
            frame=self.stack[-1]
            if frame['row'] is not None:frame['row'].append((frame['cell'][0],''.join(frame['cell'][1]).strip()))
            frame['cell']=None
        if self.stack and tag=='tr' and self.stack[-1]['row'] is not None:
            frame=self.stack[-1]
            if not frame['row_header']:frame['rows'].append(frame['row'])
            frame['row']=None
        if self.stack and tag=='thead':self.stack[-1]['header']=False
        if tag=='table' and self.stack:self.tables.append(self.stack.pop()['rows'])


def _table_rows(text,form):
    if form=='html_table':
        parser=_HTMLTables();parser.feed(text)
        return [sum(any(tag=='td' and v for tag,v in row) for row in table) for table in parser.tables]
    if form=='markdown_table':
        lines=text.splitlines();counts=[]
        for i,line in enumerate(lines):
            cells=[v.strip() for v in line.strip().strip('|').split('|')]
            if i==0 or len(cells)<2 or not all(re.fullmatch(r':?-{3,}:?',v) for v in cells):continue
            if '|' not in lines[i-1]:continue
            n=0
            for nxt in lines[i+1:]:
                if '|' not in nxt or not nxt.strip():break
                values=[v.strip() for v in nxt.strip().strip('|').split('|')]
                if len(values)!=len(cells):break
                if any(values):n+=1
            counts.append(n)
        return counts
    if form=='plain_text_matrix':
        rows=[v for v in text.splitlines() if '\t' in v and v.strip()]
        return [max(0,len(rows)-1)] if rows else []
    return []


def _table(b,ctx,did,p,kind):
    allowed={'accepted_forms','minimum_table_count','require_nonempty_table_body'}
    _keys(b,p,allowed)
    forms=p.get('accepted_forms',['markdown_table','html_table','docx_table','xlsx_table','plain_text_matrix'])
    _need(b,isinstance(forms,list) and set(forms)<={'markdown_table','html_table','docx_table','xlsx_table','plain_text_matrix'},'unsupported_table_form')
    nonempty=p.get('require_nonempty_table_body',True)
    _need(b,isinstance(nonempty,bool),'invalid_nonempty_table_flag')
    try:text=ctx.text(did,allow_files=False)
    except b.UnknownEvidence:
        if not ctx.binding(did).get('files'):raise
        text=''
    counts=[]
    for form in set(forms)&{'markdown_table','html_table','plain_text_matrix'}:counts.extend(_table_rows(text,form))
    for path in ctx.files(did) if ctx.binding(did).get('files') else []:
        info=ctx.info(path)
        if info['format'] in ('md','txt','html'):
            for form in set(forms)&{'markdown_table','html_table','plain_text_matrix'}:counts.extend(_table_rows(info.get('text',''),form))
        if info['format']=='docx' and 'docx_table' in forms:
            for table in info['tree'].findall('.//w:tbl',NS):
                rows=table.findall('w:tr',NS)
                counts.append(sum(bool(''.join(row.itertext()).strip()) for row in rows if row.find('w:trPr/w:tblHeader',NS) is None))
        elif info['format']=='xlsx' and 'xlsx_table' in forms:
            strings=[]
            if 'xl/sharedStrings.xml' in info['members']:
                strings=[''.join(v.itertext()) for v in ET.fromstring(info['members']['xl/sharedStrings.xml']).findall('s:si',NS)]
            def cell_text(cell):
                value=cell.find('s:v',NS)
                if cell.get('t')=='s' and value is not None:
                    try:return strings[int(value.text)]
                    except (ValueError,IndexError) as exc:raise b.UnknownEvidence('table_shared_string_reference_unreadable') from exc
                return ''.join(cell.itertext())
            for name,blob in info['members'].items():
                if re.fullmatch(r'xl/worksheets/sheet\d+\.xml',name):
                    rows=ET.fromstring(blob).findall('.//s:row',NS)
                    counts.append(sum(any(cell_text(v).strip() for v in row.findall('s:c',NS)) for row in rows))
    usable=sum(v>0 if nonempty else True for v in counts)
    minimum=p.get('minimum_table_count',1)
    _need(b,isinstance(minimum,int) and minimum>=1,'invalid_minimum_table_count')
    _assert(b,usable>=minimum,'nonempty_parseable_table_missing')
    return {'tables':usable,'nonempty_rows':sum(counts),'semantic_table_subject_verified':False}


def _memory(b,ctx,did,p,kind,legacy):
    extra={'new_or_changed_since_attempt_start','request_user_turns','storage_scope','exact_historical_ai_wording_required'}
    old={'readable_nonempty_record','nonempty_persisted_record','current_source_record','separate_export_required'}
    _keys(b,p,old|extra)
    _enum(b,p,'storage_scope',{'current_attempt_memory_state'})
    if 'exact_historical_ai_wording_required' in p:_need(b,p['exact_historical_ai_wording_required'] is False,'historical_ai_wording_cannot_be_gold')
    if 'readable_nonempty_record' in p:_true(b,p,'readable_nonempty_record')
    if 'nonempty_persisted_record' in p:_true(b,p,'nonempty_persisted_record')
    if 'current_source_record' in p:
        _true(b,p,'current_source_record')
        sid=ctx.contract.get('session_id',ctx.contract.get('sid'))
        _need(b,ctx.evidence.get('source_session_id')==sid,'memory_current_source_record_unverified')
    if 'separate_export_required' in p:_need(b,p['separate_export_required'] is False,'memory_export_not_supported')
    initial=_initial(b,ctx) if p.get('new_or_changed_since_attempt_start') else None
    if 'new_or_changed_since_attempt_start' in p:_true(b,p,'new_or_changed_since_attempt_start')
    turns=p.get('request_user_turns')
    if turns is not None:
        _need(b,isinstance(turns,list) and all(isinstance(v,int) and v>=1 for v in turns),'invalid_memory_request_turns')
        bindings=ctx.evidence.get('memory_request_bindings',{}).get(did)
        _need(b,isinstance(bindings,list) and set(turns)<=set(bindings),'memory_request_binding_missing')
    values=ctx.binding(did).get('files',ctx.evidence.get('memory_files'))
    _need(b,isinstance(values,list),'current_attempt_memory_binding_missing')
    paths=[ctx.path(v.get('path') if isinstance(v,dict) else v) for v in values]
    changed=0
    for path in paths:
        _assert(b,path.is_file() and path.stat().st_size>0,'persisted_memory_missing_or_empty')
        try:text=path.read_text('utf-8-sig')
        except UnicodeError as exc:raise b.UnknownEvidence('memory_text_encoding_unreadable') from exc
        _assert(b,bool(text.strip()),'persisted_memory_empty')
        if initial is None or _sha(path) not in initial.values():changed+=1
    _assert(b,bool(paths),'persisted_memory_missing')
    if initial is not None:_assert(b,changed>0,'persisted_memory_not_new_or_changed')
    return {'persisted_records':len(paths),'changed_records':changed,'preference_semantics_verified':False}


def _pdf_text(b,path):
    try:
        from pypdf import PdfReader
        reader=PdfReader(str(path),strict=True)
        _need(b,not reader.is_encrypted and len(reader.pages)>0,'pdf_text_not_extractable')
        return '\n'.join(page.extract_text() or '' for page in reader.pages)
    except b.UnknownEvidence:raise
    except Exception as exc:raise b.UnknownEvidence('pdf_native_text_measurement_failed') from exc


def _watermark(b,ctx,did,p,kind):
    allowed={'source_requirements','text_normalization'}
    _keys(b,p,allowed);_enum(b,p,'text_normalization',{'NFKC_whitespace'})
    required=p.get('source_requirements')
    _need(b,isinstance(required,list) and bool(required),'pdf_source_requirements_missing')
    manifest=ctx.manifest(did,'pdf_source_outputs')
    rows=manifest.get('items') if isinstance(manifest,dict) else manifest
    _need(b,isinstance(rows,list),'pdf_source_output_mapping_missing')
    outputs=set(ctx.files(did,['pdf']));pairs=[]
    for req in required:
        _need(b,isinstance(req,dict) and set(req)=={'input_path','input_sha256','input_user_turn','literals'},'invalid_pdf_source_requirement')
        source=ctx.path(req['input_path']);_verified_input(b,ctx,source,req['input_sha256'])
        matching=[v for v in rows if isinstance(v,dict) and v.get('input_path')==req['input_path'] and v.get('input_sha256')==req['input_sha256'] and v.get('input_user_turn')==req['input_user_turn']]
        _need(b,len(matching)==1 and bool(matching[0].get('output_path')),'unique_pdf_source_output_mapping_missing')
        output=ctx.path(matching[0]['output_path'])
        _need(b,output in outputs,'mapped_pdf_not_declared_current_delivery')
        _assert(b,output.is_file() and output.stat().st_size>0,'watermarked_output_missing')
        before=_pdf_text(b,source);after=_pdf_text(b,output)
        _need(b,bool(after.strip()),'watermark_raster_or_unextractable_no_ocr')
        if p.get('text_normalization'):
            before=re.sub(r'\s+','',_norm(before,'NFKC'));after=re.sub(r'\s+','',_norm(after,'NFKC'))
        literals=req['literals'];_need(b,isinstance(literals,list) and bool(literals) and all(isinstance(v,str) and v for v in literals),'invalid_watermark_literal_list')
        for literal in literals:
            literal=re.sub(r'\s+','',_norm(literal,'NFKC')) if p.get('text_normalization') else literal
            _assert(b,after.count(literal)>before.count(literal),'explicit_watermark_text_not_added')
        pairs.append({'source':_relative(ctx,source),'output':_relative(ctx,output),'literals':literals})
    return {'source_output_pairs':len(pairs),'pairs':pairs,'visual_watermark_quality_verified':False,'ocr_executed':False}


def _drawing_objects(b,path):
    try:
        with zipfile.ZipFile(path) as z:
            names=z.namelist()
            if any(n.casefold()=='xl/cellimages.xml' or n.startswith('xl/richData/') for n in names):
                raise b.UnknownEvidence('native_cell_image_display_geometry_not_available')
            _need(b,'xl/workbook.xml' in names and 'xl/_rels/workbook.xml.rels' in names,'spreadsheet_workbook_relationship_graph_missing')
            book=ET.fromstring(z.read('xl/workbook.xml'))
            bookrels={v.get('Id'):v for v in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
            drawings=[]
            for sheet in book.findall('s:sheets/s:sheet',NS):
                relation=bookrels.get(sheet.get('{'+R+'}id'))
                _need(b,relation is not None,'spreadsheet_sheet_relationship_missing')
                target=relation.get('Target','');sheetname=target.lstrip('/') if target.startswith('/') else posixpath.normpath(posixpath.join('xl',target))
                _need(b,sheetname in names,'spreadsheet_sheet_part_missing')
                sheet_tree=ET.fromstring(z.read(sheetname));relname=posixpath.join(posixpath.dirname(sheetname),'_rels',posixpath.basename(sheetname)+'.rels')
                sheet_rels={v.get('Id'):v for v in ET.fromstring(z.read(relname))} if relname in names else {}
                for drawing in sheet_tree.findall('s:drawing',NS):
                    rel=sheet_rels.get(drawing.get('{'+R+'}id'))
                    _need(b,rel is not None and rel.get('TargetMode')!='External','spreadsheet_drawing_relationship_missing')
                    target=rel.get('Target','');name=target.lstrip('/') if target.startswith('/') else posixpath.normpath(posixpath.join(posixpath.dirname(sheetname),target))
                    _need(b,name in names,'spreadsheet_drawing_part_missing')
                    drawings.append(name)
            objects=[]
            for name in dict.fromkeys(drawings):
                tree=ET.fromstring(z.read(name));relname=posixpath.join(posixpath.dirname(name),'_rels',posixpath.basename(name)+'.rels')
                _need(b,relname in names,'spreadsheet_image_relationships_missing')
                rels={v.get('Id'):v for v in ET.fromstring(z.read(relname))}
                for anchor in tree:
                    pic=anchor.find('xdr:pic',NS)
                    if pic is None:continue
                    blip=pic.find('.//a:blip',NS);_need(b,blip is not None,'spreadsheet_image_blip_missing')
                    rel=rels.get(blip.get('{'+R+'}embed'))
                    _need(b,rel is not None and rel.get('TargetMode')!='External','spreadsheet_embedded_image_bytes_unavailable')
                    target=rel.get('Target','');member=target.lstrip('/') if target.startswith('/') else posixpath.normpath(posixpath.join(posixpath.dirname(name),target))
                    _need(b,member in names,'spreadsheet_image_member_missing')
                    try:
                        from PIL import Image
                        with Image.open(io.BytesIO(z.read(member))) as im:im.load()
                    except ImportError as exc:raise b.UnknownEvidence('image_parser_dependency_missing') from exc
                    except Exception as exc:raise b.DeliveryFailure('spreadsheet_embedded_image_not_decodable') from exc
                    # oneCellAnchor's explicit outer extent is authoritative.
                    # twoCellAnchor is sized by its two markers plus worksheet
                    # metrics. Its internal picture transform is not that outer
                    # extent; without a implemented measurement it stays unknown.
                    anchor_type=anchor.tag.rsplit('}',1)[-1]
                    ext=anchor.find('xdr:ext',NS) if anchor_type in ('oneCellAnchor','absoluteAnchor') else None
                    size=None
                    if ext is not None:
                        try:size=(int(ext.get('cx')),int(ext.get('cy')))
                        except (TypeError,ValueError):raise b.UnknownEvidence('spreadsheet_display_dimension_unreadable')
                    origin=anchor.find('xdr:from',NS)
                    valid=False
                    if origin is not None:
                        try:valid=0<=int(origin.find('xdr:col',NS).text)<16384 and 0<=int(origin.find('xdr:row',NS).text)<1048576
                        except (AttributeError,ValueError):pass
                    objects.append({'display_size':size,'cell_anchored':valid,'member':member})
            return objects
    except (b.UnknownEvidence,b.DeliveryFailure):raise
    except Exception as exc:raise b.UnknownEvidence('spreadsheet_geometry_measurement_failed') from exc


def _photo(b,ctx,did,p,kind):
    allowed={'all_photo_objects_same_display_width_and_height','equality','require_valid_cell_anchor','native_cell_image_relationships_accepted','photo_count_from','preserve_original_photo_count'}
    _keys(b,p,allowed);_enum(b,p,'equality',{'exact_normalized_OOXML_display_units'});_enum(b,p,'photo_count_from',{'source_photo_manifest'})
    for key in ('all_photo_objects_same_display_width_and_height','require_valid_cell_anchor','preserve_original_photo_count','native_cell_image_relationships_accepted'):_true(b,p,key)
    source=ctx.manifest(did,'source_photos')
    _need(b,isinstance(source,dict) and isinstance(source.get('source_photo_count'),int),'source_photo_count_missing')
    _need(b,bool(source.get('source_path')),'source_photo_path_missing')
    input_path=ctx.path(source['source_path']);_verified_input(b,ctx,input_path,source.get('source_sha256'))
    try:initial_objects=_drawing_objects(b,input_path)
    except b.DeliveryFailure as exc:raise b.UnknownEvidence('source_photo_bytes_unreadable') from exc
    _need(b,len(initial_objects)==source['source_photo_count'] and len(initial_objects)>0,'source_photo_count_not_bound_to_real_source')
    paths=ctx.files(did,['xlsx']);_assert(b,bool(paths),'photo_workbook_delivery_missing')
    total=0;sizes=[]
    for path in paths:
        objects=_drawing_objects(b,path);total+=len(objects)
        for obj in objects:
            _need(b,obj['display_size'] is not None,'spreadsheet_display_dimensions_missing')
            _assert(b,all(v>0 for v in obj['display_size']),'spreadsheet_display_dimension_nonpositive')
            _assert(b,obj['cell_anchored'],'spreadsheet_photo_not_cell_anchored')
            sizes.append(obj['display_size'])
    _assert(b,total>=source['source_photo_count'],'source_photos_removed_from_final_workbook')
    _assert(b,bool(sizes) and len(set(sizes))==1,'spreadsheet_photo_display_sizes_differ')
    return {'photo_count':total,'source_photo_count':source['source_photo_count'],'display_size_emu':sizes[0],'photo_name_identity_verified':False}


def _manifest(b,ctx,did,p,kind):
    allowed={'count_from','manifest_source','freeze_manifest_before_image_phase','require_one_readable_final_image_per_page','require_one_readable_final_image_per_explicit_item','final_version_per_page','reject_terminal_self_declared_subsets','reject_agent_selected_subset','required_item_ids','deduplicate_repeated_storyboard'}
    _keys(b,p,allowed)
    for key in allowed-{'count_from','manifest_source','required_item_ids'}:_true(b,p,key)
    _enum(b,p,'count_from',{'current_attempt_prompt_page_manifest','user_explicit_storyboard_items'})
    source_mode=p.get('manifest_source') or ('user_explicit_storyboard_items' if p.get('count_from')=='user_explicit_storyboard_items' else 'delivered_prompt_text')
    _need(b,source_mode is None or source_mode in {'delivered_prompt_text','user_explicit_storyboard_items','actually_delivered_prompt_text_for_turn_3','actually_delivered_prompt_text_for_turn_1'},'unsupported_manifest_source')
    manifest=ctx.manifest(did,'pages');_need(b,isinstance(manifest,dict),'artifact_manifest_requires_bound_source_metadata')
    records=manifest.get('items');_need(b,isinstance(records,list),'artifact_manifest_items_missing')
    required=p.get('required_item_ids')
    if source_mode=='user_explicit_storyboard_items':
        _need(b,isinstance(required,list) and bool(required),'compiled_user_storyboard_item_ids_missing')
        if p.get('deduplicate_repeated_storyboard'):required=list(dict.fromkeys(required))
    else:
        _need(b,'reject_agent_selected_subset' not in p and 'deduplicate_repeated_storyboard' not in p,'user_storyboard_policy_requires_user_compiled_manifest')
        ref=manifest.get('source_delivery_id');digest=manifest.get('source_body_sha256')
        _need(b,bool(ref) and isinstance(digest,str),'prompt_manifest_source_body_binding_missing')
        body=ctx.text(ref);_need(b,bool(body.strip()),'prompt_manifest_source_body_empty');actual=hashlib.sha256(body.encode('utf-8')).hexdigest()
        if source_mode.startswith('actually_delivered_prompt_text_for_turn_'):
            turn=int(source_mode.rsplit('_',1)[1])-1
            _need(b,turn in ctx.target(ref).get('turn_indices',[]),'prompt_manifest_source_turn_mismatch')
        _need(b,digest==actual,'prompt_manifest_source_body_sha_mismatch')
        snapshot=ctx.evidence.get('manifest_snapshots',{}).get(did,{}).get('pages')
        _need(b,isinstance(snapshot,dict) and snapshot.get('observation')=='before_image_dispatch','pre_image_manifest_snapshot_missing')
        _need(b,snapshot.get('source_body_sha256')==digest,'pre_image_manifest_snapshot_sha_mismatch')
        frozen=snapshot.get('required_item_ids')
        _need(b,isinstance(frozen,list) and bool(frozen),'pre_image_required_item_ids_missing')
        if required is not None:_need(b,set(required)==set(frozen),'contract_snapshot_item_ids_disagree')
        required=frozen
    _need(b,all(isinstance(v,str) and v for v in required) and len(set(required))==len(required),'invalid_frozen_required_item_ids')
    _assert(b,bool(records) and all(isinstance(v,dict) for v in records),'artifact_manifest_empty_or_invalid')
    ids=[v.get('id',v.get('page_id',v.get('item_id'))) for v in records]
    _need(b,all(isinstance(v,str) and v for v in ids),'manifest_item_id_binding_missing')
    _assert(b,len(set(ids))==len(ids) and set(required)<=set(ids),'frozen_artifact_manifest_coverage_missing')
    declared=set(ctx.files(did,['image']));paths=[]
    for row in records:
        _need(b,bool(row.get('path')),'manifest_artifact_path_missing')
        path=ctx.path(row['path']);_need(b,path in declared,'manifest_path_not_declared_current_delivery')
        info=ctx.info(path);_assert(b,info.get('family')=='image','manifest_file_is_not_readable_image')
        paths.append(path)
    _assert(b,len(set(paths))==len(paths),'manifest_reuses_one_artifact_for_multiple_items')
    return {'manifest_items_verified':len(paths),'required_item_ids':required,'semantic_image_subject_verified':False}


def _observation(b,ctx,did,p,kind):
    if kind=='selected_skill_identity_report_only':
        allowed={'selection_source','target_hints','record_final_skill_paths','do_not_accept_arbitrary_skill_as_target'};_keys(b,p,allowed)
        _enum(b,p,'selection_source',{'current_attempt_conversation_reference_resolution'})
        for key in ('record_final_skill_paths','do_not_accept_arbitrary_skill_as_target'):_true(b,p,key)
        _need(b,isinstance(p.get('target_hints',[]),list),'invalid_skill_target_hints')
        value=ctx.evidence.get('selected_skill_targets',{}).get(did)
        _need(b,isinstance(value,dict) and value.get('resolved') is True and value.get('path'),'selected_skill_target_identity_unresolved')
        path=ctx.path(value['path']);_need(b,path.is_dir(),'selected_skill_directory_unavailable')
        hints=p.get('target_hints',[])
        _need(b,not hints or any(str(h).casefold() in path.name.casefold() for h in hints),'resolved_skill_target_hints_disagree')
        return {'report_only':True,'scorable':False,'applicable':False,'applicable_to_AND':False,
                'observed_skill_path':_relative(ctx,path),'full_installation_intent_verified':False}
    allowed={'source_url','expected_document_manifest','expected_count','scope_from','unknown_scope_does_not_pass_complete_download'};_keys(b,p,allowed)
    _enum(b,p,'scope_from',{'preflight_frozen_current_site_document_manifest'});_true(b,p,'unknown_scope_does_not_pass_complete_download')
    manifest=ctx.manifest(did,'download_scope')
    _need(b,isinstance(manifest,dict) and manifest.get('observation')=='preflight_frozen','download_scope_not_frozen')
    if 'source_url' in p:_need(b,manifest.get('source_url')==p['source_url'],'download_scope_source_url_mismatch')
    required=manifest.get('required_urls');_need(b,isinstance(required,list) and bool(required),'download_required_url_manifest_missing')
    if p.get('expected_document_manifest') is not None:_need(b,p['expected_document_manifest']==required,'download_manifest_contract_disagrees')
    if p.get('expected_count') is not None:_need(b,p['expected_count']==len(required),'download_scope_count_disagrees')
    rows=manifest.get('items',[]);_need(b,isinstance(rows,list),'download_scope_items_unreadable')
    declared=set(ctx.files(did));covered=[]
    for row in rows:
        if isinstance(row,dict) and row.get('url') in required and row.get('path'):
            path=ctx.path(row['path']);_need(b,path in declared,'download_scope_path_not_declared')
            ctx.info(path);covered.append(row['url'])
    return {'report_only':True,'scorable':False,'applicable':False,'applicable_to_AND':False,
            'required_count':len(required),'covered_urls':sorted(set(covered)),'missing_urls':sorted(set(required)-set(covered)),'complete_download_success_claim':False}


def register_extensions(base):
    if getattr(base,'_artifact_extensions_registered',False):return
    old_memory=base.HANDLERS['persisted_memory_present']
    definitions=[
      ('code_artifact_present',_code,{'accepted_forms','require_nonempty_code_payload','resolve_from_current_attempt_delivery_declaration','reject_plan_only','reject_reused_input_documents'}),
      ('literal_fields_presence',_literal,{'scope','literals','numeric_fields','number_match','unicode_normalization','trigger_examples','trigger_examples_mode','section_scope'}),
      ('delivered_table_present',_table,{'accepted_forms','minimum_table_count','require_nonempty_table_body'}),
      ('persisted_memory_present',lambda b,c,d,p,k:_memory(b,c,d,p,k,old_memory),{'readable_nonempty_record','nonempty_persisted_record','current_source_record','separate_export_required','new_or_changed_since_attempt_start','request_user_turns','storage_scope','exact_historical_ai_wording_required'}),
      ('pdf_added_literal_text_presence',_watermark,{'source_requirements','text_normalization'}),
      ('spreadsheet_image_dimensions_and_anchors',_photo,{'all_photo_objects_same_display_width_and_height','equality','require_valid_cell_anchor','native_cell_image_relationships_accepted','photo_count_from','preserve_original_photo_count'}),
      ('manifest_corresponding_artifacts',_manifest,{'count_from','manifest_source','freeze_manifest_before_image_phase','require_one_readable_final_image_per_page','require_one_readable_final_image_per_explicit_item','final_version_per_page','reject_terminal_self_declared_subsets','reject_agent_selected_subset','required_item_ids','deduplicate_repeated_storyboard'}),
      ('selected_skill_identity_report_only',_observation,{'selection_source','target_hints','record_final_skill_paths','do_not_accept_arbitrary_skill_as_target'}),
      ('download_scope_report_only',_observation,{'source_url','expected_document_manifest','expected_count','scope_from','unknown_scope_does_not_pass_complete_download'})]
    for name,func,names in definitions:
        def handler(ctx,did,p,kind,func=func):return func(base,ctx,did,p,kind)
        base.HANDLERS[name]=handler;base.PARAMETERS[handler]=set(names)
    base._artifact_extensions_registered=True
