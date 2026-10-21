"""Deterministic business citation units; never scores or duplicates full evidence.

The private unit map is not a new fact source. Each unit resolves to exactly one
existing canonical scalar atom. The public grouped catalogue gives short native
IDs; original complete content and images remain in the evidence payload.
"""
from __future__ import annotations
import copy,json,re,hashlib
from collections import Counter

SCHEMA='eval250-citable-business-units-v5'

def pointer(value,path):
    if not isinstance(path,str) or not path.startswith('/'):raise ValueError('Absolute canonical pointer required')
    for part in path.split('/')[1:]:
        key=part.replace('~1','/').replace('~0','~');value=value[int(key)] if isinstance(value,list) else value[key]
    return value

def canonical(value):return json.dumps(value,ensure_ascii=False,separators=(',',':'),sort_keys=True,allow_nan=False)
def esc(value):return str(value).replace('~','~0').replace('/','~1')
def scalar(value):return value is None or type(value) in (str,int,float,bool)
def scalar_text(value):return value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False)

def build_catalog(evidence,effective_atoms=None):
    """Return {public_catalog, units, stats}; only public_catalog goes to model.

    Pass the current grounder's effective atom map to preserve e.g. trusted
    expected-fixture INPUT role overrides. No quoted value is used to find an
    address. Multiple identical values at different addresses stay distinct.
    """
    original=evidence.get('evidence_atoms',[])
    if effective_atoms is None:
        # Role ownership is not guessed here. The grounder is authoritative.
        # Expected fixture domains are never selected by this module by default.
        effective_atoms={a['atom_id']:a for a in original}
    if isinstance(effective_atoms,dict) and 'atoms' in effective_atoms and isinstance(effective_atoms['atoms'],dict):effective_atoms=effective_atoms['atoms']
    if not isinstance(effective_atoms,dict):raise TypeError('effective_atoms must be atom_id -> effective atom')
    by_address={}
    for atom in original:
        key=(atom['evidence_id'],atom['json_pointer'])
        if key in by_address:raise ValueError('Ambiguous canonical atom ownership')
        effective=effective_atoms.get(atom['atom_id'])
        if not isinstance(effective,dict):raise ValueError('Effective atom map incomplete')
        if effective.get('evidence_id')!=atom['evidence_id'] or effective.get('json_pointer')!=atom['json_pointer']:raise ValueError('Effective map changed an atom address')
        by_address[key]=effective
    units={};groups=[];unindexed=[]
    def add(uid,eid,path,kind,native_locator):
        atom=by_address.get((eid,path))
        if atom is None:
            unindexed.append({'unit_id':uid,'canonical_pointer':path,'reason':'NO_EXISTING_SCALAR_ATOM'});return False
        value=pointer(evidence,path)
        if not scalar(value):raise ValueError('Unit must resolve to original scalar')
        if isinstance(value,str) and not value:return False
        record={'unit_id':uid,'evidence_id':eid,'json_pointer':path,'atom_id':atom['atom_id'],'locator':atom['locator'],'role':atom['role'],'kind':kind,'native_locator':native_locator,'value_type':type(value).__name__,'value_sha256':hashlib.sha256(canonical(value).encode('utf8')).hexdigest()}
        if uid in units and units[uid]!=record:raise ValueError('Duplicate native unit ID: '+uid)
        units[uid]=record;return True
    def walk(value,path):
        if isinstance(value,dict):
            for k,v in value.items():yield from walk(v,path+'/'+esc(k))
        elif isinstance(value,(list,tuple)):
            for i,v in enumerate(value):yield from walk(v,path+'/'+str(i))
        elif scalar(value):yield path,value
    def group(kind,eid,**data):
        groups.append(dict(kind=kind,evidence_id=eid,**data))
    def content(eid,base,record):
        ex=record.get('extraction',{});xp=base+'/extraction';filename=record.get('filename',record.get('artifact',''))
        for si,sheet in enumerate(ex.get('sheets',[])):
            prefix=f'{eid}:X{si+1}';sp=f'{xp}/sheets/{si}';cache_count=0
            for ci,cell in enumerate(sheet.get('cells',[])):
                address=str(cell.get('cell',''))
                if not re.fullmatch(r'[A-Za-z]+[1-9][0-9]*',address):continue
                address=address.upper();cp=f'{sp}/cells/{ci}'
                if 'value' in cell:add(prefix+':'+address+':V',eid,cp+'/value','XLSX_ORIGINAL_FORMULA' if isinstance(cell['value'],str) and cell['value'].startswith('=') else 'XLSX_ORIGINAL_VALUE',f'{sheet.get("sheet")}!{address}')
                if isinstance(cell.get('value'),str) and cell['value'].startswith('=') and cell.get('original_cached_value') is not None:
                    if add(prefix+':'+address+':K',eid,cp+'/original_cached_value','XLSX_ORIGINAL_CACHED_VALUE_NOT_RECALCULATED',f'{sheet.get("sheet")}!{address} original cache'):cache_count+=1
            if 'sheet' in sheet:add(prefix+':NAME',eid,sp+'/sheet','XLSX_SHEET_NAME',str(sheet['sheet']))
            group('XLSX_ORIGINAL',eid,prefix=prefix,sheet=sheet.get('sheet'),filename=filename,id_rule=prefix+':{native_cell}:V',V='Exact original cell.value; a leading = is the original formula, never its evaluated result.',K='Use '+prefix+':{native_cell}:K only where an actual non-null original formula cache exists; stale cache is not recomputation.',indexed_cell_count=sum(u['unit_id'].startswith(prefix+':') and u['unit_id']!=prefix+':NAME' for u in units.values()),original_cache_count=cache_count)
        # Derived recalculation is a separate family, never labelled original.
        derived=record.get('derived_formula_recalculation',{});rgroups={}
        for fi,cell in enumerate(derived.get('formula_cells',[])):
            match=re.fullmatch(r'sheet:(.*)!([A-Za-z]+[1-9][0-9]*)',str(cell.get('locator','')))
            if not match or 'derived_recalculated_value' not in cell:continue
            name,address=match.groups();matches=[i for i,s in enumerate(ex.get('sheets',[])) if s.get('sheet')==name]
            if len(matches)!=1:continue
            prefix=f'{eid}:RX{matches[0]+1}';rgroups[prefix]=name
            add(prefix+':'+address.upper(),eid,f'{base}/derived_formula_recalculation/formula_cells/{fi}/derived_recalculated_value','XLSX_DERIVED_RECALCULATED_VALUE',str(cell['locator'])+' derived recalculation')
        for prefix,name in rgroups.items():group('XLSX_DERIVED_RECALCULATION',eid,prefix=prefix,sheet=name,id_rule=prefix+':{native_cell}',meaning='Actual derived recomputation result; separate from original formula and original cached values.')
        if isinstance(ex.get('rows'),list):
            rows=ex['rows'];count=0
            for ri,row in enumerate(rows):
                if isinstance(row,list):
                    for ci,v in enumerate(row):
                        if scalar(v):count+=add(f'{eid}:CSV:R{ri+1}:C{ci+1}',eid,f'{xp}/rows/{ri}/{ci}','CSV_ORIGINAL_CELL',f'CSV row {ri+1}, column {ci+1}')
                elif isinstance(row,dict):
                    for key,v in row.items():
                        if scalar(v):count+=add(f'{eid}:CSV:R{ri+1}:K{esc(key)}',eid,f'{xp}/rows/{ri}/{esc(key)}','CSV_ORIGINAL_FIELD',f'CSV row {ri+1}, field {key}')
            group('CSV',eid,prefix=eid+':CSV',id_rule=eid+':CSV:R{one_based_row_including_header}:C{one_based_column}',rows=len(rows),columns=copy.deepcopy(rows[0]) if rows and isinstance(rows[0],list) else None,indexed_cells=count)
        if 'parsed_json' in ex:
            count=0
            for path,v in walk(ex['parsed_json'],''):
                # JSON input business keys named expected/method remain business.
                count+=add(eid+':J'+(path or '/'),eid,xp+'/parsed_json'+path,'JSON_ORIGINAL_SCALAR','JSON '+(path or '/'))
            group('JSON',eid,prefix=eid+':J',id_rule=eid+':J{JSON_pointer_relative_to_parsed_business_root}',indexed_scalars=count,root_meaning='Original parsed JSON business root; JSON pointer escaping ~0 and ~1 applies. No outer extraction/payload wrapper in the ID.')
        if isinstance(ex.get('pages'),list):
            for pi,page in enumerate(ex['pages']):
                if isinstance(page,dict) and isinstance(page.get('text'),str):add(f'{eid}:PG{pi+1}',eid,f'{xp}/pages/{pi}/text','PDF_PAGE_TEXT',f'PDF page {page.get("page",pi+1)}')
            group('PDF',eid,id_rule=eid+':PG{one_based_page}',pages=len(ex['pages']))
        for pi,part in enumerate(ex.get('parts',[])):
            name=str(part.get('part',''))
            business=bool(re.fullmatch(r'word/(document|header[0-9]+|footer[0-9]+|footnotes|endnotes|comments)\.xml',name) or re.fullmatch(r'ppt/(slides/slide[0-9]+|notesSlides/notesSlide[0-9]+)\.xml',name))
            if not business:continue
            for ti,paragraph in enumerate(part.get('paragraphs',[])):
                if isinstance(paragraph,dict) and isinstance(paragraph.get('text'),str):add(f'{eid}:P{pi+1}:T{ti+1}',eid,f'{xp}/parts/{pi}/paragraphs/{ti}/text','OFFICE_PART_PARAGRAPH',str(paragraph.get('locator',name)))
            group('OFFICE_PARAGRAPHS',eid,prefix=f'{eid}:P{pi+1}',part=name,id_rule=f'{eid}:P{pi+1}:T'+'{one_based_paragraph}',paragraphs=len(part.get('paragraphs',[])))
        # Raw text is a single unit, not a second copy of its full value.
        if isinstance(ex.get('text'),str):
            add(eid+':TXT',eid,xp+'/text','ORIGINAL_TEXT','Original full text '+filename)
            if not ('parsed_json' in ex or 'rows' in ex):
                for li,line in enumerate(ex.get('lines',[])):
                    if isinstance(line,dict) and isinstance(line.get('text'),str):add(f'{eid}:L{li+1}',eid,f'{xp}/lines/{li}/text','ORIGINAL_TEXT_LINE',str(line.get('locator','line:'+str(li+1))))
                group('TEXT_LINES',eid,full_text_unit=eid+':TXT',id_rule=eid+':L{one_based_line}',lines=len(ex.get('lines',[])),filename=filename)
            else:group('RAW_TEXT_ALTERNATIVE',eid,unit_id=eid+':TXT',meaning='Complete original raw CSV/JSON text, not a new or reparsed business result.')
    for collection in ('sources','input_evidence','artifacts','outputs'):
        # Exact duplicate representation aliases must not mint a second ID.
        if collection in ('input_evidence','outputs') and evidence.get(collection)==evidence.get('sources' if collection=='input_evidence' else 'artifacts'):continue
        for ai,record in enumerate(evidence.get(collection,[])):
            if isinstance(record,dict):content(record.get('evidence_id',record.get('artifact_id')),f'/{collection}/{ai}',record)
    # Actual observation units: native body text / tool feedback, not UI style
    # metadata. Complex remaining facts can still use exact canonical/wire refs.
    excluded={'screenshots','image_refs','image_sha256','images','viewport','viewports','bounds','page_runtime_errors','effective_background','menu_item_styles','expanded','dialogs','font_family','font_size','color','background','parent_background','contrast_policy','limitations','schema_version','browser_version','state_ids','state_id','locator','kind','scope','interpretation','source_line','evidence_id','artifact','filename','path','sha256','original_cached_value','expected_from_original_requirements','sample_from_input','expected_status','storage_files','parser','server'}
    actual_keys={'body_text','text','public_text','decoded_text','stdout','stderr','command','code','status','executed','observed_change','failure','observed_final_sha256','csv_calendar_intervals_match','summary','dtstart','dtend','duration_minutes','query','hit_count','entry_count','company','contact','quote_date','sku','quantity','amount','unit_price','total_ex_tax','tax_9_percent','total_incl_tax'}
    for oi,ob in enumerate(evidence.get('functional_observations',[])):
        eid=ob.get('evidence_id');base=f'/functional_observations/{oi}'
        if not isinstance(eid,str):continue
        structured_observation=isinstance(ob.get('observations'),dict) and bool(ob['observations'].get('state_catalog'))
        redundant_serialized_text=structured_observation and isinstance(ob.get('text'),str)
        group_count_before=len(units)
        if isinstance(ob.get('arguments'),dict):
            for key in ('command','code'):
                if isinstance(ob['arguments'].get(key),str):add(eid+':'+key.upper(),eid,base+'/arguments/'+key,'ACTUAL_TOOL_ACTION_TEXT',str(ob.get('locator',''))+' '+key)
        for fi,feedback in enumerate(ob.get('feedback',[])):
            if isinstance(feedback,dict) and isinstance(feedback.get('public_text'),str):add(f'{eid}:FB{fi+1}',eid,f'{base}/feedback/{fi}/public_text','ACTUAL_RECORDED_TOOL_FEEDBACK',str(ob.get('locator',''))+f' feedback {fi+1}')
        obs=ob.get('observations',{});states=obs.get('state_catalog',[]) if isinstance(obs,dict) else []
        state_ids=[]
        for si,state in enumerate(states):
            if not isinstance(state,dict):continue
            sid=state.get('state_id');body=(state.get('observation') or {}).get('body_text')
            if isinstance(sid,str) and isinstance(body,str):
                if add(eid+':ST:'+sid+':BODY',eid,f'{base}/observations/state_catalog/{si}/observation/body_text','ACTUAL_BROWSER_STATE_BODY',str(ob.get('artifact',''))+' state '+sid):state_ids.append(sid)
        if state_ids:group('ACTUAL_BROWSER_STATE_TEXT',eid,id_rule=eid+':ST:{state_id}:BODY',available_state_ids=state_ids,meaning='Actual visible body_text of this recorded state; not expected fixture text and not proof of pixel contrast.')
        # Specialized browser actual_states (before/after) use their true IDs.
        for si,state in enumerate(ob.get('actual_states',[])):
            sid=state.get('state_id');body=(state.get('observation') or {}).get('body_text')
            if isinstance(sid,str) and isinstance(body,str):add(eid+':ST:'+sid+':BODY',eid,f'{base}/actual_states/{si}/observation/body_text','ACTUAL_BROWSER_STATE_BODY','Actual specialized state '+sid)
        for di,download in enumerate(ob.get('actual_downloads',[])):
            if isinstance(download.get('decoded_text'),str):add(f'{eid}:DL{di+1}',eid,f'{base}/actual_downloads/{di}/decoded_text','ACTUAL_NATIVE_DOWNLOADED_TEXT','Actual downloaded bytes decoded without replacement')
        # Select bounded business leaf kinds; no font/style/metadata scalar walk.
        def observed_walk(value,path,relative):
            if isinstance(value,dict):
                for key,child in value.items():
                    if key in excluded or (not relative and key in {'text','arguments','feedback','actual_states','actual_downloads'}):continue
                    if not relative and key=='text' and redundant_serialized_text:continue
                    if key=='state_catalog':continue
                    # The specialized capture's result.actual_page is another
                    # full DOM snapshot. Indexing every mirrored table/button
                    # label makes hundreds of duplicate navigation units; the
                    # original snapshot remains untouched and exact-pointer
                    # citable, while each actual state has its BODY unit.
                    if relative=='/scenario/result' and key=='actual_page':continue
                    new=relative+'/'+esc(key)
                    if key in actual_keys and scalar(child):yield path+'/'+esc(key),new,child
                    elif isinstance(child,(dict,list)):yield from observed_walk(child,path+'/'+esc(key),new)
            elif isinstance(value,list):
                for i,child in enumerate(value):yield from observed_walk(child,path+'/'+str(i),relative+'/'+str(i))
        for path,relative,value in observed_walk(ob,base,''):
            add(eid+':OBS'+relative,eid,path,'ACTUAL_OBSERVATION_BUSINESS_SCALAR','Actual observation '+relative)
        # Short parser-only observations without structured content retain one
        # honest text unit; complex serialized aliases are not indexed as proof.
        if not redundant_serialized_text and not any(k in ob for k in ('observations','feedback','actual_states','actual_downloads','protected_inputs')) and isinstance(ob.get('text'),str):add(eid+':TXT',eid,base+'/text','ACTUAL_OBSERVATION_TEXT',str(ob.get('locator','')))
        if len(units)>group_count_before:
            group('ACTUAL_OBSERVATION',eid,command_ids=[eid+':'+key.upper() for key in ('command','code') if eid+':'+key.upper() in units],feedback_rule=eid+':FB{one_based_feedback}',state_rule=eid+':ST:{actual_state_id}:BODY',download_rule=eid+':DL{one_based_actual_download}',business_scalar_rule=eid+':OBS{JSON_pointer_relative_to_this_actual_observation_record}',meaning='Only IDs present in the local exact index resolve; actual facts only, not expected fixtures. Missing metadata may still be cited via an exact canonical or real wire pointer.')
    table=[];long_count=0;shown=Counter()
    for unit in units.values():
        value=pointer(evidence,unit['json_pointer']);long=isinstance(value,str) and len(value)>96
        long_count+=long
        if shown[unit['kind']]<3:
            table.append([unit['unit_id'],unit['native_locator'],value[:72] if long else value,'NAV_EXCERPT_ONLY' if long else 'EXACT_SCALAR'])
            shown[unit['kind']]+=1
    public={'schema_version':SCHEMA,'contract':{'reference_shape':{'kind':'text','unit_id':'construct or copy one explicit unit_id from groups.id_rule; unit_table only shows representative examples','claim_role':'OUTPUT_CONTENT or INPUT_REQUIREMENT or OBSERVED_ACTION','exact_quote':'nonempty contiguous original string, or exact full JSON spelling for a nonstring scalar'},'short_scalar_values_explicit_and_exact':True,'navigation_excerpt_is_not_truncated_original_evidence':True,'long_original_values_remain_complete_in_body':True,'units_are_navigation_not_new_evidence':True,'original_complete_evidence_and_all_pixels_retained':True,'missing_unit_never_guessed_by_quote':True,'index_fields_not_new_scoring_requirements':True,'unindexed_fields_can_use_exact_canonical_or_real_wire_pointer':True},'groups':groups,'unit_table':{'examples_only':True,'total_unit_count':len(units),'columns':['unit_id','native_locator','scalar_or_navigation_excerpt','mode'],'rows':table,'note':'Representative examples only, not a complete listing. Construct exact IDs from groups.id_rule; the host still resolves only existing original scalars and rejects unknown IDs.'},'long_value_policy':'Strings up to 96 characters are complete exact scalars. Longer strings get only a 72-character navigation prefix labelled NAV_EXCERPT_ONLY here; the complete original scalar remains in the evidence body and is used for exact-quote validation. Never infer an absent continuation.'}
    stats={'unit_count':len(units),'public_group_count':len(groups),'public_catalog_characters':len(canonical(public)),'public_catalog_utf8_bytes':len(canonical(public).encode('utf8')),'explicit_unit_table_characters':len(canonical(public['unit_table'])),'unit_examples_only_count':sum(shown.values()),'long_values_with_navigation_excerpt_only':long_count,'private_unit_map_characters_not_sent':len(canonical(units)),'by_kind':{},'unindexed_candidates':unindexed,'duplicate_values_not_deduplicated_across_native_locations':True,'evidence_complete_content_unchanged':True}
    for unit in units.values():stats['by_kind'][unit['kind']]=stats['by_kind'].get(unit['kind'],0)+1
    return {'schema_version':SCHEMA,'evidence_identity':{'task_id':evidence.get('task_id'),'blind_case_id':evidence.get('blind_case_id')},'public_catalog':public,'units':units,'stats':stats}

def resolve_unit(evidence,unit_id,catalog=None,effective_atoms=None):
    """Strict lookup only; returns canonical reference metadata, never a score."""
    if not isinstance(unit_id,str):raise ValueError('unit_id must be a string')
    catalog=build_catalog(evidence,effective_atoms) if catalog is None else catalog
    if catalog.get('schema_version')!=SCHEMA:raise ValueError('Unknown unit catalogue schema')
    if catalog.get('evidence_identity')!={'task_id':evidence.get('task_id'),'blind_case_id':evidence.get('blind_case_id')}:raise ValueError('Citable unit map belongs to another evidence case')
    unit=catalog['units'].get(unit_id)
    if unit is None:raise ValueError('Unknown citable unit ID')
    value=pointer(evidence,unit['json_pointer'])
    if not scalar(value):raise ValueError('Unit no longer addresses a scalar')
    if hashlib.sha256(canonical(value).encode('utf8')).hexdigest()!=unit['value_sha256']:raise ValueError('Original unit scalar changed after catalogue construction')
    # An exact original scalar is revalidated by the ordinary grounder. This
    # helper must not search for a different address using a quotation.
    return copy.deepcopy(unit)

def check_unit_quote(evidence,unit_id,exact_quote,catalog=None,effective_atoms=None):
    unit=resolve_unit(evidence,unit_id,catalog,effective_atoms);value=pointer(evidence,unit['json_pointer']);actual=scalar_text(value)
    valid=isinstance(exact_quote,str) and bool(exact_quote) and (exact_quote in actual if isinstance(value,str) else exact_quote==actual)
    if not valid:raise ValueError('Quote not supported by exact unit scalar')
    return unit
