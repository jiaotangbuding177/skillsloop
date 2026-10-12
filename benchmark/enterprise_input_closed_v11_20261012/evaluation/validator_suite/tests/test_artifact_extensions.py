"""Mechanical positive/negative/unknown fixtures; no business functionality runs."""
import hashlib,importlib.util,io,json,zipfile
from pathlib import Path
import pytest
from PIL import Image
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject

SUITE=Path(__file__).resolve().parents[1]
ROOT=SUITE.parents[1]

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

@pytest.fixture
def engine():
    base=load(SUITE/'vendor/final_state_scorer.py','artifact_base_fixture')
    ext=load(SUITE/'_artifact_extensions.py','artifact_extension_fixture')
    ext.register_extensions(base);return base

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def ctx(b,tmp_path,files=None,text=None,extra=None):
    bound={}
    if files is not None:bound['files']=files
    if text is not None:bound['text']=text
    evidence={'schema':'final-state-evidence-v1','source_session_id':'fixture','conversation_complete':True,
              'initial_sha256':{},'declared_input_sha256':{},'deliveries':{'d':bound}}
    if extra:evidence.update(extra)
    return b.Context({'task_id':'fixture','source_session_id':'fixture','workspace':str(tmp_path),'result':{},'evidence':evidence},
                     {'session_id':'fixture','final_deliverables':[{'id':'d','kind':'text_or_file','name':'fixture','turn_indices':[0]}]})

def run(b,c,kind,p):return b.HANDLERS[kind](c,'d',p,kind)
def pdf(path,text):
    w=PdfWriter();page=w.add_blank_page(width=200,height=100)
    font=w._add_object(DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')}))
    page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):font})})
    stream=DecodedStreamObject();stream.set_data(('BT /F1 12 Tf 10 50 Td ('+text+') Tj ET' if text else 'q Q').encode('ascii'))
    page[NameObject('/Contents')]=w._add_object(stream)
    with path.open('wb') as f:w.write(f)

def xlsx(path,sizes=((100,200),(100,200)),anchor='oneCellAnchor',dimension=True,linked=True):
    pic=io.BytesIO();Image.new('RGB',(2,2),'white').save(pic,format='PNG')
    rels=[];items=[]
    for i,(w,h) in enumerate(sizes,1):
        pos=f'<xdr:from><xdr:col>0</xdr:col><xdr:colOff>0</xdr:colOff><xdr:row>{i}</xdr:row><xdr:rowOff>0</xdr:rowOff></xdr:from>' if anchor!='absoluteAnchor' else '<xdr:pos x="0" y="0"/>'
        ext=f'<xdr:ext cx="{w}" cy="{h}"/>' if dimension else ''
        internal=''
        if anchor=='twoCellAnchor':
            pos+=f'<xdr:to><xdr:col>2</xdr:col><xdr:colOff>0</xdr:colOff><xdr:row>{i+(2 if i==1 else 7)}</xdr:row><xdr:rowOff>0</xdr:rowOff></xdr:to>'
            ext=''
            internal=f'<xdr:spPr><a:xfrm><a:ext cx="{w}" cy="{h}"/></a:xfrm></xdr:spPr>' if dimension else ''
        items.append(f'<xdr:{anchor}>{pos}{ext}<xdr:pic><xdr:blipFill><a:blip r:embed="r{i}"/></xdr:blipFill>{internal}</xdr:pic><xdr:clientData/></xdr:{anchor}>')
        rels.append(f'<Relationship Id="r{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/image{i}.png"/>')
    with zipfile.ZipFile(path,'w') as z:
        z.writestr('[Content_Types].xml','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/></Types>')
        z.writestr('xl/workbook.xml','<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Photos" sheetId="1" r:id="s1"/></sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="s1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
        z.writestr('xl/worksheets/sheet1.xml','<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>name</t></is></c></row></sheetData>'+('<drawing r:id="draw1"/>' if linked else '')+'</worksheet>')
        z.writestr('xl/worksheets/_rels/sheet1.xml.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="draw1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/drawing" Target="../drawings/drawing1.xml"/></Relationships>')
        z.writestr('xl/drawings/drawing1.xml','<xdr:wsDr xmlns:xdr="http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'+''.join(items)+'</xdr:wsDr>')
        z.writestr('xl/drawings/_rels/drawing1.xml.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'+''.join(rels)+'</Relationships>')
        for i in range(1,len(sizes)+1):z.writestr(f'xl/media/image{i}.png',pic.getvalue())

@pytest.mark.parametrize('form',['source','zip','fence'])
def test_code_real_forms(engine,tmp_path,form):
    if form=='source':(tmp_path/'code.ts').write_text('const n = 1;');c=ctx(engine,tmp_path,['code.ts'])
    elif form=='zip':
        with zipfile.ZipFile(tmp_path/'code.zip','w') as z:z.writestr('src/app.js','const n=1;')
        c=ctx(engine,tmp_path,['code.zip'])
    else:c=ctx(engine,tmp_path,text='```python\nx=1\n```')
    result=run(engine,c,'code_artifact_present',{'accepted_forms':['source_file','archive_with_source','delivered_fenced_source'],'require_nonempty_code_payload':True})
    assert result['code_payloads']>=1

def test_code_plan_and_md_archive_fail(engine,tmp_path):
    c=ctx(engine,tmp_path,text='I will implement this tomorrow.')
    with pytest.raises(engine.DeliveryFailure):run(engine,c,'code_artifact_present',{})
    with zipfile.ZipFile(tmp_path/'plan.zip','w') as z:z.writestr('plan.md','future plan')
    with pytest.raises(engine.DeliveryFailure):run(engine,ctx(engine,tmp_path,['plan.zip']),'code_artifact_present',{})

def test_literal_nfkc_numeric_boundaries(engine,tmp_path):
    p={'literals':['10μF'],'numeric_fields':['5000','500'],'unicode_normalization':'NFKC','number_match':'token_after_grouping_separator_normalization'}
    assert run(engine,ctx(engine,tmp_path,text='１０µＦ 5,000个 500个'),'literal_fields_presence',p)['numeric_fields_matched']==2
    for text in ['10μF 5000个','10μF 50000个 ID500 1500个']:
        with pytest.raises(engine.DeliveryFailure):run(engine,ctx(engine,tmp_path,text=text),'literal_fields_presence',p)

def test_literal_unsupported_normalization_is_unknown(engine,tmp_path):
    with pytest.raises(engine.UnknownEvidence):run(engine,ctx(engine,tmp_path,text='x'),'literal_fields_presence',{'literals':['x'],'unicode_normalization':'invented'})

def test_literal_skill_refs_and_report_only_triggers(engine,tmp_path):
    (tmp_path/'skill').mkdir();(tmp_path/'skill'/'SKILL.md').write_text('教科书 精读',encoding='utf-8')
    c=ctx(engine,tmp_path);c.evidence['deliveries']['d']={'directory':'skill'}
    out=run(engine,c,'literal_fields_presence',{'scope':'generated_skill_and_references','literals':['教科书'],'trigger_examples':['我在读一本书'],'trigger_examples_mode':'report_only'})
    assert out['trigger_examples_observed']=={'我在读一本书':False}

@pytest.mark.parametrize('text,ok',[('| A | B |\n|---|---|\n| 1 | 2 |',True),('| A | B |\n|---|---|',False),('<table><tr><td>x</td></tr></table>',True),('<table></table>',False)])
def test_table_actual_nonempty_rows(engine,tmp_path,text,ok):
    c=ctx(engine,tmp_path,text=text);p={'accepted_forms':['markdown_table','html_table'],'minimum_table_count':1,'require_nonempty_table_body':True}
    if ok:assert run(engine,c,'delivered_table_present',p)['tables']>=1
    else:
        with pytest.raises(engine.DeliveryFailure):run(engine,c,'delivered_table_present',p)

def test_memory_changed_unchanged_and_missing_initial(engine,tmp_path):
    f=tmp_path/'memory.md';f.write_text('saved preference')
    p={'readable_nonempty_record':True,'new_or_changed_since_attempt_start':True,'request_user_turns':[5],'storage_scope':'current_attempt_memory_state'}
    c=ctx(engine,tmp_path,['memory.md'],extra={'memory_request_bindings':{'d':[5]}})
    assert run(engine,c,'persisted_memory_present',p)['changed_records']==1
    c.evidence['initial_sha256']={'memory.md':sha(f)}
    with pytest.raises(engine.DeliveryFailure):run(engine,c,'persisted_memory_present',p)
    c.evidence.pop('initial_sha256')
    with pytest.raises(engine.UnknownEvidence):run(engine,c,'persisted_memory_present',p)

def test_memory_request_binding_not_guessed(engine,tmp_path):
    (tmp_path/'memory.md').write_text('saved')
    with pytest.raises(engine.UnknownEvidence):run(engine,ctx(engine,tmp_path,['memory.md']),'persisted_memory_present',{'new_or_changed_since_attempt_start':True,'request_user_turns':[5]})

def watermark_ctx(b,tmp_path,source_text,output_text):
    pdf(tmp_path/'input.pdf',source_text);pdf(tmp_path/'output.pdf',output_text)
    source_hash=sha(tmp_path/'input.pdf')
    c=ctx(b,tmp_path,['output.pdf'],extra={'declared_input_sha256':{'input.pdf':source_hash}})
    c.evidence['deliveries']['d']['manifests']={'pdf_source_outputs':{'items':[{'input_path':'input.pdf','input_sha256':source_hash,'input_user_turn':1,'output_path':'output.pdf'}]}}
    p={'source_requirements':[{'input_path':'input.pdf','input_sha256':source_hash,'input_user_turn':1,'literals':['EvoMind']}],'text_normalization':'NFKC_whitespace'}
    return c,p

def test_watermark_native_added_literal(engine,tmp_path):
    c,p=watermark_ctx(engine,tmp_path,'hello','hello EvoMind')
    assert run(engine,c,'pdf_added_literal_text_presence',p)['source_output_pairs']==1

def test_watermark_existing_word_and_raster_unknown(engine,tmp_path):
    c,p=watermark_ctx(engine,tmp_path,'EvoMind','EvoMind')
    with pytest.raises(engine.DeliveryFailure):run(engine,c,'pdf_added_literal_text_presence',p)
    c,p=watermark_ctx(engine,tmp_path,'hello','')
    with pytest.raises(engine.UnknownEvidence):run(engine,c,'pdf_added_literal_text_presence',p)

def test_watermark_missing_or_wrong_mapping(engine,tmp_path):
    c,p=watermark_ctx(engine,tmp_path,'hello','EvoMind')
    c.evidence['deliveries']['d']['manifests']={}
    with pytest.raises(engine.UnknownEvidence):run(engine,c,'pdf_added_literal_text_presence',p)
    c,p=watermark_ctx(engine,tmp_path,'hello','EvoMind')
    p['source_requirements'][0]['input_sha256']='wrong'
    with pytest.raises(engine.UnknownEvidence):run(engine,c,'pdf_added_literal_text_presence',p)

def photo_ctx(b,tmp_path,sizes=((100,200),(100,200)),anchor='oneCellAnchor',dimension=True):
    xlsx(tmp_path/'input.xlsx',((90,180),(110,190)));xlsx(tmp_path/'output.xlsx',sizes,anchor,dimension)
    h=sha(tmp_path/'input.xlsx')
    c=ctx(b,tmp_path,['output.xlsx'],extra={'declared_input_sha256':{'input.xlsx':h}})
    c.evidence['deliveries']['d']['manifests']={'source_photos':{'source_path':'input.xlsx','source_sha256':h,'source_photo_count':2}}
    return c

PHOTO={'all_photo_objects_same_display_width_and_height':True,'equality':'exact_normalized_OOXML_display_units','require_valid_cell_anchor':True,'photo_count_from':'source_photo_manifest','preserve_original_photo_count':True,'native_cell_image_relationships_accepted':True}
def test_photo_size_and_anchors(engine,tmp_path):
    assert run(engine,photo_ctx(engine,tmp_path),'spreadsheet_image_dimensions_and_anchors',PHOTO)['photo_count']==2

@pytest.mark.parametrize('sizes,anchor',[(((100,200),(101,200)),'oneCellAnchor'),(((100,200),),'oneCellAnchor'),(((100,200),(100,200)),'absoluteAnchor')])
def test_photo_explicit_mismatch_fails(engine,tmp_path,sizes,anchor):
    with pytest.raises(engine.DeliveryFailure):run(engine,photo_ctx(engine,tmp_path,sizes,anchor),'spreadsheet_image_dimensions_and_anchors',PHOTO)

def test_photo_missing_source_count_or_dimensions_unknown(engine,tmp_path):
    c=photo_ctx(engine,tmp_path);c.evidence['deliveries']['d']['manifests']['source_photos'].pop('source_photo_count')
    with pytest.raises(engine.UnknownEvidence):run(engine,c,'spreadsheet_image_dimensions_and_anchors',PHOTO)
    with pytest.raises(engine.UnknownEvidence):run(engine,photo_ctx(engine,tmp_path,dimension=False),'spreadsheet_image_dimensions_and_anchors',PHOTO)

def manifest_ctx(b,tmp_path,ids=('p1','p2')):
    for i in (1,2):Image.new('RGB',(2,2),'white').save(tmp_path/f'p{i}.png')
    body='page p1\npage p2';digest=hashlib.sha256(body.encode()).hexdigest()
    c=ctx(b,tmp_path,['p1.png','p2.png'])
    c.targets['prompts']={'id':'prompts','kind':'text','turn_indices':[0]}
    c.evidence['deliveries']['prompts']={'text':body}
    items=[{'id':v,'path':f'p{i}.png'} for i,v in enumerate(ids,1)]
    c.evidence['deliveries']['d']['manifests']={'pages':{'source_delivery_id':'prompts','source_body_sha256':digest,'items':items}}
    c.evidence['manifest_snapshots']={'d':{'pages':{'observation':'before_image_dispatch','source_body_sha256':digest,'required_item_ids':['p1','p2']}}}
    return c

def test_prompt_manifest_frozen_source(engine,tmp_path):
    c=manifest_ctx(engine,tmp_path)
    assert run(engine,c,'manifest_corresponding_artifacts',{'manifest_source':'delivered_prompt_text','freeze_manifest_before_image_phase':True,'require_one_readable_final_image_per_page':True,'reject_terminal_self_declared_subsets':True})['manifest_items_verified']==2

def test_manifest_terminal_subset_or_sha_wrong(engine,tmp_path):
    with pytest.raises(engine.DeliveryFailure):run(engine,manifest_ctx(engine,tmp_path,('p1',)),'manifest_corresponding_artifacts',{'freeze_manifest_before_image_phase':True})
    c=manifest_ctx(engine,tmp_path);c.evidence['deliveries']['d']['manifests']['pages']['source_body_sha256']='wrong'
    with pytest.raises(engine.UnknownEvidence):run(engine,c,'manifest_corresponding_artifacts',{'freeze_manifest_before_image_phase':True})

def test_manifest_no_snapshot_unknown_and_user_frozen_ids(engine,tmp_path):
    c=manifest_ctx(engine,tmp_path);c.evidence.pop('manifest_snapshots')
    with pytest.raises(engine.UnknownEvidence):run(engine,c,'manifest_corresponding_artifacts',{'freeze_manifest_before_image_phase':True})
    assert run(engine,c,'manifest_corresponding_artifacts',{'required_item_ids':['p1','p2'],'manifest_source':'user_explicit_storyboard_items'})['manifest_items_verified']==2

def test_observation_missing_target_is_unknown(engine,tmp_path):
    with pytest.raises(engine.UnknownEvidence):run(engine,ctx(engine,tmp_path),'selected_skill_identity_report_only',{'target_hints':[]})
    with pytest.raises(engine.UnknownEvidence):run(engine,ctx(engine,tmp_path),'download_scope_report_only',{'expected_document_manifest':None})

def test_registration_does_not_accept_unhandled_parameters(engine):
    for kind in ('code_artifact_present','pdf_added_literal_text_presence','spreadsheet_image_dimensions_and_anchors','literal_fields_presence','delivered_table_present','persisted_memory_present','manifest_corresponding_artifacts'):
        assert engine.parameter_support({'kind':kind,'parameters':{'invented_ignored_key':True}})==['invented_ignored_key']

def test_orphan_drawing_does_not_count_as_visible_photo(engine,tmp_path):
    c=photo_ctx(engine,tmp_path);xlsx(tmp_path/'output.xlsx',linked=False)
    with pytest.raises(engine.DeliveryFailure):run(engine,c,'spreadsheet_image_dimensions_and_anchors',PHOTO)

def test_code_archive_input_reuse_is_not_new_delivery(engine,tmp_path):
    with zipfile.ZipFile(tmp_path/'code.zip','w') as z:z.writestr('app.js','x=1;')
    c=ctx(engine,tmp_path,['code.zip'],extra={'declared_input_sha256':{'code.zip':sha(tmp_path/'code.zip')}})
    with pytest.raises(engine.DeliveryFailure):run(engine,c,'code_artifact_present',{})

def test_nested_html_table_and_incomplete_params(engine,tmp_path):
    text='<table><tr><td><table><tr><td>x</td></tr></table></td></tr></table>'
    assert run(engine,ctx(engine,tmp_path,text=text),'delivered_table_present',{'minimum_table_count':2})['tables']==2
    with pytest.raises(engine.UnknownEvidence):run(engine,ctx(engine,tmp_path,text=text),'delivered_table_present',{'accepted_forms':['invented']})
    assert engine.parameter_support({'kind':'manifest_corresponding_artifacts','parameters':{'ignore_unwritten_declared_extra_shot':True}})==['ignore_unwritten_declared_extra_shot']

def test_manifest_user_dedup_and_missing_ids_unknown(engine,tmp_path):
    c=manifest_ctx(engine,tmp_path)
    assert run(engine,c,'manifest_corresponding_artifacts',{'manifest_source':'user_explicit_storyboard_items','required_item_ids':['p1','p2','p1'],'deduplicate_repeated_storyboard':True})['manifest_items_verified']==2
    c.evidence['deliveries']['d']['manifests']['pages']['items'][0].pop('id')
    with pytest.raises(engine.UnknownEvidence):run(engine,c,'manifest_corresponding_artifacts',{'required_item_ids':['p1','p2'],'manifest_source':'user_explicit_storyboard_items'})

def test_memory_old_current_source_flag_is_executed(engine,tmp_path):
    (tmp_path/'memory.md').write_text('record')
    c=ctx(engine,tmp_path,['memory.md'])
    assert run(engine,c,'persisted_memory_present',{'current_source_record':True})['persisted_records']==1
    c.evidence.pop('source_session_id')
    with pytest.raises(engine.UnknownEvidence):run(engine,c,'persisted_memory_present',{'current_source_record':True})

@pytest.mark.parametrize('text',[
    '<table><thead><tr><td>header</td></tr></thead></table>',
    '<table><thead><tr><th>header</th></tr></thead><tbody></tbody></table>',
])
def test_explicit_html_header_is_not_table_body(engine,tmp_path,text):
    with pytest.raises(engine.DeliveryFailure):
        run(engine,ctx(engine,tmp_path,text=text),'delivered_table_present',{'require_nonempty_table_body':True})

def test_two_cell_internal_extent_is_not_actual_display_size(engine,tmp_path):
    c=photo_ctx(engine,tmp_path)
    xlsx(tmp_path/'output.xlsx',anchor='twoCellAnchor')
    # The pair of markers, worksheet column widths and row heights determine
    # twoCellAnchor's displayed geometry. An internal picture extent cannot
    # safely substitute for that calculation.
    with pytest.raises(engine.UnknownEvidence):
        run(engine,c,'spreadsheet_image_dimensions_and_anchors',PHOTO)

@pytest.mark.parametrize('kind,params,name,body',[
    ('code_artifact_present',{},'renamed.py','x=1'),
    ('persisted_memory_present',{'new_or_changed_since_attempt_start':True},'renamed.md','saved'),
])
def test_renamed_initial_product_is_not_new(engine,tmp_path,kind,params,name,body):
    f=tmp_path/name;f.write_text(body)
    c=ctx(engine,tmp_path,[name],extra={'initial_sha256':{'old/'+name:sha(f)}})
    with pytest.raises(engine.DeliveryFailure):run(engine,c,kind,params)

@pytest.mark.parametrize('policy',[{'score_at':'during_execution'},{'historical_ai_is_gold':True}])
def test_artifact_policy_values_cannot_be_ignored(engine,tmp_path,policy):
    with pytest.raises(engine.UnknownEvidence):
        run(engine,ctx(engine,tmp_path,text='```py\nx=1\n```'),'code_artifact_present',policy)

def test_allowed_artifact_policy_values(engine,tmp_path):
    result=run(engine,ctx(engine,tmp_path,text='```py\nx=1\n```'),'code_artifact_present',{'score_at':'conversation_end_only','historical_ai_is_gold':False})
    assert result['code_payloads']==1

def test_resolved_observations_do_not_claim_success(engine,tmp_path):
    (tmp_path/'selected').mkdir()
    c=ctx(engine,tmp_path,extra={'selected_skill_targets':{'d':{'resolved':True,'path':'selected'}}})
    skill=run(engine,c,'selected_skill_identity_report_only',{'record_final_skill_paths':True})
    assert skill['scorable'] is False and skill['applicable'] is False
    (tmp_path/'download.txt').write_text('downloaded native body')
    c=ctx(engine,tmp_path,['download.txt'])
    c.evidence['deliveries']['d']['manifests']={'download_scope':{'observation':'preflight_frozen','source_url':'https://fixture.test',
        'required_urls':['https://fixture.test/a','https://fixture.test/b'],'items':[{'url':'https://fixture.test/a','path':'download.txt'}]}}
    out=run(engine,c,'download_scope_report_only',{'source_url':'https://fixture.test','expected_count':2})
    assert out['scorable'] is False and out['applicable'] is False
    assert out['missing_urls']==['https://fixture.test/b'] and out['complete_download_success_claim'] is False
