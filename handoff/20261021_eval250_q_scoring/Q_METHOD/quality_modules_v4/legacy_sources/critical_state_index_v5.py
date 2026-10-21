"""Neutral, source-addressed index of already observed HTML interaction states.

No business judgment, numerical threshold, model request, or original-file edit.
The full source states and every original image remain the primary evidence.
"""
from __future__ import annotations
from collections import Counter,defaultdict
from concurrent.futures import ThreadPoolExecutor
import argparse,copy,hashlib,json,shutil
from pathlib import Path

B=Path(__file__).resolve().parent
SCHEMA='actual-html-critical-state-difference-index-v5'
STYLE_KEYS=('color','background','parent_background','effective_background','foreground_background_contrast_ratio','font_family','font_size','outline')
STYLE_NAMES={'color':'foreground','background':'local_background','parent_background':'parent_background','effective_background':'effective_background',
 'foreground_background_contrast_ratio':'observed_ratio','font_family':'font_family','font_size':'font_size','outline':'outline'}
DISPLAY_STYLE_KEYS=('color','background','effective_background','foreground_background_contrast_ratio','outline')

def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def write(path,value):
 p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def resolve(document,pointer):
 value=document
 for part in pointer.split('/')[1:]:
  key=part.replace('~1','/').replace('~0','~');value=value[int(key)]if isinstance(value,list)else value[key]
 return value

def _identity(record,collection):
 if record.get('id'):return ('DOM_ID',str(record['id']))
 # Anonymous repeated links are matched by occurrence, never assumed unique.
 return ('ANONYMOUS',record.get('tag'),record.get('href'),record.get('text'),record.get('name'),record.get('type'),collection if collection in {'fields','notices'}else None)

def _summary(record,pointer,collection):
 value={'source_pointer':pointer,'source_collection':collection,'actual_observation':True}
 for key in ('tag','id','text','href','expanded','visible','type','name','value','disabled','readOnly','required'):
  if key in record:value[key]=copy.deepcopy(record[key])
 styles={STYLE_NAMES[k]:copy.deepcopy(record[k])for k in DISPLAY_STYLE_KEYS if k in record}
 if isinstance(styles.get('effective_background'),dict):
  styles['effective_background']={k:copy.deepcopy(styles['effective_background'][k])for k in('status','rgb','limitations')if k in styles['effective_background']}
 value['style']=styles
 value['style_measurement']='RECORDED_IN_ORIGINAL_STATE'if styles else'NOT_RECORDED_IN_ORIGINAL_STATE'
 if 'visible'not in record:value['visibility_basis']='VISIBLE_ONLY_SOURCE_COLLECTION'if collection in {'visible_controls','buttons','notices'}else'NOT_RECORDED'
 return value

def _widgets(observation,pointer):
 """Return actual control inventory; retain every anonymous occurrence."""
 visible={};styles={};occurrences=Counter()
 for collection in ('visible_controls','fields','buttons','notices'):
  for i,record in enumerate(observation.get(collection,[])):
   if not isinstance(record,dict)or record.get('visible')is False:continue
   # Hidden upload inputs are not promoted to visible merely because they exist.
   key=_identity(record,collection);ordinal=occurrences[key];occurrences[key]+=1
   full=key+(ordinal,);visible[full]=_summary(record,f'{pointer}/{collection}/{i}',collection)
 for collection in ('expanded','dialogs','menu_item_styles','selected_element','active'):
  rows=observation.get(collection,[])
  if isinstance(rows,dict):rows=[rows];single=True
  else:single=False
  for i,record in enumerate(rows or []):
   if not isinstance(record,dict)or record.get('tag')in {'BODY','HTML'}:continue
   source=f'{pointer}/{collection}'+(''if single else'/'+str(i));key=_identity(record,collection)
   entry=_summary(record,source,collection)
   entry['_complete_style']={STYLE_NAMES[k]:copy.deepcopy(record[k])for k in STYLE_KEYS if k in record}
   prior=styles.get(key)
   # Same DOM measurement may be recorded in multiple original collections.
   # Prefer the richer record, keep all exact source pointers as provenance.
   if prior is None:entry['also_measured_at']=[];styles[key]=entry
   elif len(entry['style'])>len(prior['style']):
    entry['also_measured_at']=[prior['source_pointer']]+prior.get('also_measured_at',[]);styles[key]=entry
   else:prior.setdefault('also_measured_at',[]).append(source)
 for key,record in styles.items():
  matches=[k for k in visible if k[:-1]==key]
  if matches:
   for full in matches:
    # A duplicate anonymous identity is explicitly ambiguous; do not pretend a
    # specific DOM instance was measured when the old collector cannot tell.
    visible[full]['style']=copy.deepcopy(record['style']);visible[full]['style_source_pointer']=record['source_pointer']
    visible[full]['style_measurement']=record['style_measurement']
    if len(matches)>1:visible[full]['style_identity_ambiguity']='MULTIPLE_ANONYMOUS_VISIBLE_CONTROLS_SAME_TAG_TEXT_HREF'
  elif record.get('visible')is True:
   visible[key+(0,)]={k:copy.deepcopy(v)for k,v in record.items()if not k.startswith('_')}
 return visible,styles

def _images(evidence,artifact,state,source_pointer):
 offered={im['evidence_id']:im for im in evidence.get('visual_pages',[])if im.get('artifact',im.get('filename'))==artifact and im.get('role')!='input'}
 direct=state.get('image_evidence_ids',[])
 if direct:
  assert all(eid in offered for eid in direct),('State image mapping invalid',source_pointer)
  return list(dict.fromkeys(direct))
 # Specialized raw states have local FI IDs; join their actual state IDs and
 # original SHA, rather than inventing or renaming evidence identifiers.
 refs=state.get('image_refs',[]);sid=state.get('state_id');result=[]
 for ref in refs:
  matches=[eid for eid,im in offered.items()if im.get('sha256')==ref.get('sha256')and sid in im.get('state_ids',[])]
  assert matches,('Actual specialized state image missing',source_pointer,ref)
  result.extend(matches)
 return list(dict.fromkeys(result))

def _catalogs(evidence):
 artifacts={a['filename']:a for a in evidence.get('artifacts',[])if Path(a['filename']).suffix.lower()in{'.html','.htm'}and a.get('presence')=='PRESENT'}
 for i,observation in enumerate(evidence.get('functional_observations',[])):
  artifact=observation.get('artifact')
  if artifact not in artifacts:continue
  base=f'/functional_observations/{i}'
  generic=observation.get('observations',{}).get('state_catalog',[])if isinstance(observation.get('observations'),dict)else[]
  if generic:
   yield artifact,artifacts[artifact],observation,base,'GENERIC_ACTUAL_BROWSER',[(s,f'{base}/observations/state_catalog/{j}')for j,s in enumerate(generic)]
  specialized=observation.get('actual_states',[])
  if specialized:
   yield artifact,artifacts[artifact],observation,base,'SPECIALIZED_ACTUAL_BROWSER',[(s,f'{base}/actual_states/{j}')for j,s in enumerate(specialized)]

def _intern_control_variants(record):
 """Exact repeated display facts get one readable catalog entry; origins stay per use."""
 variants={};catalog=[];change_variants={};changes=[]
 def replace(widget):
  origins={k:copy.deepcopy(widget[k])for k in('source_pointer','source_collection','style_source_pointer','also_measured_at')if k in widget}
  value={k:copy.deepcopy(v)for k,v in widget.items()if k not in origins and not k.startswith('_')}
  key=canonical(value)
  if key not in variants:
   cid='C'+str(len(catalog)+1).zfill(4);variants[key]=cid;catalog.append({'control_variant_id':cid,**value})
  return{'control_variant_id':variants[key],**origins}
 for state in record['states']:
  for key in('initial_observed_visible_controls','added_to_visible_control_inventory','no_longer_in_visible_control_inventory','new_style_measurements_before_unknown'):
   if key in state['delta']:state['delta'][key]=[replace(w)for w in state['delta'][key]]
  focus=state['delta'].get('actual_focus_observation_change')
  if focus:
   for key in('before','after'):
    if focus.get(key):focus[key]=replace(focus[key])
  rows=state['delta'].get('recorded_style_or_visibility_changes')
  if rows:
   refs=[]
   for row in rows:
    origins={k:row[k]for k in('before_source_pointer','after_source_pointer')}
    value={k:copy.deepcopy(v)for k,v in row.items()if k not in origins};key=canonical(value)
    if key not in change_variants:
     cid='D'+str(len(changes)+1).zfill(4);change_variants[key]=cid;changes.append({'change_variant_id':cid,**value})
    refs.append({'change_variant_id':change_variants[key],**origins})
   state['delta']['recorded_style_or_visibility_changes']=refs
 record['control_catalog']=catalog
 record['style_change_catalog']=changes
 record['catalog_contract']='control_variant_id is exact observed display-value reuse, not a unique DOM identity. Each state occurrence retains its exact source pointer(s); no control, state or pixel is removed.'
 return record

def build_critical_state_index(evidence):
 """Pure appendable index; never reads new source files or runs a browser."""
 grouped={};initial={};last_viewport={};last_tab={};last_action={};state_count=0;missing_images=[]
 for artifact,artifact_record,observation,observation_pointer,session,states in _catalogs(evidence):
  aid=artifact_record['evidence_id'];group=grouped.setdefault(aid,{'evidence_id':aid+':CRITICAL_STATES_V5','artifact':artifact,'kind':'ACTUAL_HTML_CRITICAL_STATE_DIFFERENCE_INDEX',
   'locator':'output:'+artifact+'/actual-state-differences','text':'Neutral index of recorded before/after UI observations. All referenced original pixels and full state records remain available. No threshold, score, or business conclusion is assigned.',
   'artifact_evidence_id':aid,'control_catalog':[],'style_change_catalog':[],'states':[],'source_catalogs':[]})
  group['source_catalogs'].append({'evidence_id':observation['evidence_id'],'pointer':observation_pointer,'session_kind':session,'original_coverage':copy.deepcopy(observation.get('observations',{}).get('coverage'))})
  for state,state_pointer in states:
   state_count+=1;actual=state.get('observation',{});vp=state.get('viewport')or{'width':actual.get('viewport_width',1440),'height':actual.get('viewport_height',1000)}
   viewport=(vp.get('width'),vp.get('height'));bucket=(aid,session,viewport);action=state.get('action_id')or state.get('scenario_id')or observation.get('scenario',{}).get('scenario_id')or'NO_ACTION_ID_RECORDED'
   stage=state.get('stage','UNKNOWN');action_bucket=bucket+(action,)
   if stage=='initial':before=None
   elif stage=='keyboard-tab-focus':before=last_tab.get(bucket)or initial.get(bucket)
   elif stage in {'before-action','keyboard-focused-before-key'}:before=initial.get(bucket)
   elif stage=='before'and session=='SPECIALIZED_ACTUAL_BROWSER':before=last_viewport.get(bucket)
   else:before=last_action.get(action_bucket)or initial.get(bucket)
   images=_images(evidence,artifact,state,state_pointer)
   if not images:missing_images.append({'state_pointer':state_pointer,'artifact':artifact,'reason':'No actual image references in original captured state'})
   widgets,styles=_widgets(actual,state_pointer+'/observation');old_widgets,old_styles=(before['widgets'],before['styles'])if before else({}, {})
   delta={}
   if before is None:
    delta['initial_observed_visible_controls']=list(widgets.values())
   else:
    newly=[widgets[k]for k in widgets if k not in old_widgets]
    disappeared=[old_widgets[k]for k in old_widgets if k not in widgets]
    if newly:delta['added_to_visible_control_inventory']=newly
    if disappeared:delta['no_longer_in_visible_control_inventory']=disappeared
    changed=[]
    for key in sorted(widgets.keys()&old_widgets.keys(),key=lambda item:canonical(list(item))):
     current,previous=widgets[key],old_widgets[key];fields={}
     for name in ('text','value','disabled','readOnly','required','expanded'):
      if name in current and name in previous and current[name]!=previous[name]:fields[name]={'before':copy.deepcopy(previous[name]),'after':copy.deepcopy(current[name])}
     if fields:changed.append({'identity':list(key),'before_source_pointer':previous['source_pointer'],'after_source_pointer':current['source_pointer'],'actual_fields':fields})
    if changed:delta['control_field_changes']=changed
    style_changes=[];newly_measured=[]
    for key,current in styles.items():
     if current.get('visible')is not True:continue
     previous=old_styles.get(key)
     if previous is None:
      already_visible_addition=any(_identity(w,w.get('source_collection'))==key for w in newly)
      if current['style']and not already_visible_addition:newly_measured.append(current)
     else:
      fields={STYLE_NAMES[k]:{'before':copy.deepcopy(previous['_complete_style'][STYLE_NAMES[k]]),'after':copy.deepcopy(current['_complete_style'][STYLE_NAMES[k]])}for k in STYLE_KEYS if STYLE_NAMES[k]in previous['_complete_style']and STYLE_NAMES[k]in current['_complete_style']and previous['_complete_style'][STYLE_NAMES[k]]!=current['_complete_style'][STYLE_NAMES[k]]}
      if previous.get('visible')is False:fields['visible']={'before':False,'after':True}
      if fields:style_changes.append({'before_source_pointer':previous['source_pointer'],'after_source_pointer':current['source_pointer'],'control':{k:copy.deepcopy(current[k])for k in('tag','id','text','href')if k in current},'actual_style_changes':fields})
    if style_changes:delta['recorded_style_or_visibility_changes']=style_changes
    if newly_measured:delta['new_style_measurements_before_unknown']=newly_measured
    old_active=before['observation'].get('active');current_active=actual.get('active')
    def focus_identity(value):
     if not value:return None
     return tuple(value.get(k)for k in('tag','id','href'))+(None if value.get('tag')in{'BODY','HTML'}else value.get('text'),)
    # Body text or scroll geometry changing is not itself a focus change.
    if focus_identity(current_active)!=focus_identity(old_active):
     def active_key(x,pointer):
      if not x:return None
      if x.get('tag')in{'HTML','BODY'}:return{'tag':x.get('tag'),'id':x.get('id'),'source_pointer':pointer,'source_collection':'active','style':{},'style_measurement':'DOCUMENT_FOCUS_NOT_A_CONTROL_STYLE'}
      return _summary(x,pointer,'active')
     delta['actual_focus_observation_change']={'before':active_key(old_active,before['pointer']+'/observation/active'),'after':active_key(current_active,state_pointer+'/observation/active')}
    for key in ('body_text','tables','notices'):
     if key in actual and key in before['observation']and actual[key]!=before['observation'][key]:delta['actual_'+key+'_changed']={'before_source_pointer':before['pointer']+'/observation/'+key,'after_source_pointer':state_pointer+'/observation/'+key}
   row={'state_id':state.get('state_id'),'viewport':vp,'action_id':action,'stage':stage,'source_observation_id':observation['evidence_id'],'source_state_pointer':state_pointer,
        'before_state_id':before['state_id']if before else None,'before_source_state_pointer':before['pointer']if before else None,'image_evidence_ids':images,
        'actual_observation':True,'capture_status':'IMAGES_REFERENCED'if images and state.get('capture_complete',True)else'INCOMPLETE_OR_NO_IMAGES','delta':delta,
        'index_state':'OBSERVED_DIFFERENCE'if before and delta else'INITIAL_OBSERVATION'if before is None else'NO_INDEXED_DIFFERENCE'}
   if 'element'in state:row['actual_action_target']=copy.deepcopy(state['element'])
   if 'scenario'in observation:row['source_action_pointer']=observation_pointer+'/scenario/actions';row['action_label']=observation['scenario'].get('name')
   group['states'].append(row)
   current={'pointer':state_pointer,'state_id':state.get('state_id'),'observation':actual,'widgets':widgets,'styles':styles}
   if stage=='initial':initial[bucket]=current
   if stage=='keyboard-tab-focus':last_tab[bucket]=current
   last_action[action_bucket]=current;last_viewport[bucket]=current
 records=[_intern_control_variants(record)for record in grouped.values()]
 return{'schema_version':SCHEMA,'artifact_indices':records,'coverage':{'actual_html_artifacts_indexed':len(records),'actual_states_indexed':state_count,'missing_image_states':missing_images,
         'all_observed_states_retained':sum(len(r['states'])for r in records)==state_count,'unexecuted_original_states_are_not_invented':True},
        'semantics':{'role':'ACTUAL_OBSERVATION_INDEX_NOT_INPUT_EXPECTATION','no_business_score_or_threshold':True,'pixels_still_required_for_visual_scoring':True,
          'missing_style_measurement_remains_unknown':True,'anonymous_controls_matched_by_occurrence_not_assumed_unique':True,'only_observed_scope_not_all_possible_ui_paths':True,
          'style_projection':STYLE_NAMES,'displayed_control_style_fields':DISPLAY_STYLE_KEYS,'full_style_and_geometry_remain_at_canonical_source_pointer':True,
          'font_and_other_recorded_style_changes_still_compared':True,'unknown_before_is_not_claimed_as_actual_style_change':True,'all_original_evidence_and_images_must_be_retained':True}}

def _public_style_value(value):
 """Omit only the compositor's ancestor provenance chain from this navigation view.

 The unchanged raw state and local index retain that chain. Actual measured
 status, RGB, limitations, before/after values and unknowns remain visible.
 """
 if isinstance(value,dict):return{k:_public_style_value(v)for k,v in value.items()if k!='sources'}
 if isinstance(value,list):return[_public_style_value(v)for v in value]
 return copy.deepcopy(value)

def build_public_inspection_index(index):
 """Single compact navigation table of every observed state and every delta.

 This is not a new functional observation or a scoring answer. C/D identifiers
 are exact display-value reuse, and K identifiers join states to the local full
 index. Quotable facts remain in the original observations and images.
 """
 artifacts=[]
 for record in index['artifact_indices']:
  keys={s['source_state_pointer']:'K'+str(i+1).zfill(4)for i,s in enumerate(record['states'])}
  controls=[]
  for c in record['control_catalog']:
   controls.append([c['control_variant_id'],c.get('tag'),c.get('id'),c.get('text'),c.get('href'),
    {k:copy.deepcopy(c[k])for k in('expanded','visible','type','name','value','disabled','readOnly','required')if k in c},
    _public_style_value(c['style']),c.get('style_measurement'),c.get('visibility_basis'),c.get('style_identity_ambiguity')])
  changes=[[c['change_variant_id'],copy.deepcopy(c['control']),_public_style_value(c['actual_style_changes'])]for c in record['style_change_catalog']]
  states=[]
  list_names={'initial_observed_visible_controls':'initial','added_to_visible_control_inventory':'added','no_longer_in_visible_control_inventory':'removed',
    'new_style_measurements_before_unknown':'first_measured','recorded_style_or_visibility_changes':'style_changes'}
  for s in record['states']:
   delta={}
   for original,public in list_names.items():
    if original in s['delta']:
     idkey='change_variant_id'if original=='recorded_style_or_visibility_changes'else'control_variant_id'
     delta[public]=[v[idkey]for v in s['delta'][original]]
   if 'control_field_changes'in s['delta']:
    delta['field_changes']=[[v['identity'],copy.deepcopy(v['actual_fields'])]for v in s['delta']['control_field_changes']]
   if 'actual_focus_observation_change'in s['delta']:
    focus=s['delta']['actual_focus_observation_change'];delta['focus']=[focus[k]['control_variant_id']if focus.get(k)else None for k in('before','after')]
   content=[k for k in('body_text','tables','notices')if'actual_'+k+'_changed'in s['delta']]
   if content:delta['content_changed']=content
   action={'id':s['action_id']}
   if 'actual_action_target'in s:action['target']=copy.deepcopy(s['actual_action_target'])
   if 'action_label'in s:action['label']=s['action_label']
   states.append([keys[s['source_state_pointer']],s['state_id'],s['source_observation_id'],[s['viewport'].get('width'),s['viewport'].get('height')],
    action,s['stage'],keys.get(s.get('before_source_state_pointer')),copy.deepcopy(s['image_evidence_ids']),delta,s['capture_status']])
  artifacts.append({'artifact':record['artifact'],'artifact_evidence_id':record['artifact_evidence_id'],
   'control_columns':['catalog_id','tag','dom_id','text','href','actual_control_fields','actual_style','style_measurement','visibility_basis','identity_ambiguity'],
   'controls':controls,'style_change_columns':['catalog_id','control','actual_before_after'],'style_changes':changes,
   'state_columns':['index_key','state_id','source_observation_id','viewport_width_height','actual_action','stage','before_index_key','image_ids','observed_delta','capture_status'],
   'states':states,'coverage':[{'source_observation_id':c['evidence_id'],'session_kind':c['session_kind'],'original_coverage':copy.deepcopy(c['original_coverage'])}for c in record['source_catalogs']]})
 return{'schema_version':'compact-actual-ui-inspection-navigation-v5','artifacts':artifacts,'coverage':copy.deepcopy(index['coverage']),
  'semantics':{'navigation_only_not_new_observation':True,'all_recorded_states_and_change_facts_retained':True,'no_score_or_threshold':True,
   'visual_claims_require_referenced_actual_pixels':True,'catalog_ids_are_display_variants_not_unique_dom_identity':True,
   'unknown_before_style_is_first_measured_not_proven_style_change':True,'canonical_pointer_and_compositor_ancestor_provenance_are_in_local_index':True,
   'full_original_observations_and_all_images_remain_primary_evidence':True,'only_actual_observed_scope_not_all_possible_ui_paths':True}}

def append_critical_state_index(evidence):
 """Append local provenance and one public navigation index; preserve primary facts.

 The local key must never enter HTTP. The public key is projected once near the
 task. Neither key is appended as a functional observation or scalar atom.
 """
 result=copy.deepcopy(evidence);index=build_critical_state_index(evidence)
 result['critical_ui_state_index_local']=index
 result['public_inspection_index']=build_public_inspection_index(index)
 return result

def validate_public_inspection_index(index,public):
 """Require every state and indexed difference to survive the compact view."""
 assert canonical(public)==canonical(build_public_inspection_index(index))
 assert len(public['artifacts'])==len(index['artifact_indices'])
 counts=Counter()
 for original,view in zip(index['artifact_indices'],public['artifacts']):
  assert len(original['states'])==len(view['states'])and len(original['control_catalog'])==len(view['controls'])and len(original['style_change_catalog'])==len(view['style_changes'])
  ids={row[0]for row in view['controls']};dids={row[0]for row in view['style_changes']}
  for source,row in zip(original['states'],view['states']):
   assert source['state_id']==row[1]and source['image_evidence_ids']==row[7]
   delta=row[8]
   for k in('initial','added','removed','first_measured'):assert set(delta.get(k,[]))<=ids
   assert set(delta.get('style_changes',[]))<=dids
   assert set(v for v in delta.get('focus',[])if v)<=ids
   counts['states']+=1;counts['indexed_delta_categories']+=len(delta)
  counts['control_variants']+=len(view['controls']);counts['style_change_variants']+=len(view['style_changes'])
 return{'all_states_and_change_facts_retained':True,'canonical_provenance_local_only':True,'counts':dict(counts)}

def validate_critical_state_index(evidence,index,verify_pixels=False):
 """Resolve every displayed control/style change to its actual original value."""
 image_by={im['evidence_id']:im for im in evidence.get('visual_pages',[])};checked_images=set();checks=Counter()
 for record in index['artifact_indices']:
  controls={c['control_variant_id']:c for c in record['control_catalog']};changes={c['change_variant_id']:c for c in record['style_change_catalog']}
  for state in record['states']:
   original=resolve(evidence,state['source_state_pointer']);assert original['state_id']==state['state_id'];checks['states']+=1
   for eid in state['image_evidence_ids']:
    assert eid in image_by and image_by[eid].get('artifact')==record['artifact'];checked_images.add(eid)
   for key in('initial_observed_visible_controls','added_to_visible_control_inventory','no_longer_in_visible_control_inventory','new_style_measurements_before_unknown'):
    for usage in state['delta'].get(key,[]):
     control=controls[usage['control_variant_id']];raw=resolve(evidence,usage['source_pointer'])
     for field in('tag','id','text','href','expanded','visible','type','name','value','disabled','readOnly','required'):
      if field in control:assert field in raw and canonical(control[field])==canonical(raw[field]),(field,usage)
     style_raw=resolve(evidence,usage.get('style_source_pointer',usage['source_pointer']))
     assert canonical(control['style'])==canonical(_summary(style_raw,'','')['style']),(control,usage)
     checks['control_occurrences_exact']+=1
   for usage in state['delta'].get('recorded_style_or_visibility_changes',[]):
    change=changes[usage['change_variant_id']];before=resolve(evidence,usage['before_source_pointer']);after=resolve(evidence,usage['after_source_pointer'])
    reverse={v:k for k,v in STYLE_NAMES.items()}
    for field,values in change['actual_style_changes'].items():
     key='visible'if field=='visible'else reverse[field]
     assert canonical(before[key])==canonical(values['before'])and canonical(after[key])==canonical(values['after'])
    checks['style_change_occurrences_exact']+=1
   for change in state['delta'].get('control_field_changes',[]):
    before=resolve(evidence,change['before_source_pointer']);after=resolve(evidence,change['after_source_pointer'])
    for key,values in change['actual_fields'].items():assert canonical(before[key])==canonical(values['before'])and canonical(after[key])==canonical(values['after'])
    checks['field_change_occurrences_exact']+=1
   focus=state['delta'].get('actual_focus_observation_change')
   if focus:
    for key in('before','after'):
     usage=focus.get(key)
     if not usage:continue
     control=controls[usage['control_variant_id']];raw=resolve(evidence,usage['source_pointer'])
     for field in('tag','id','text','href'):
      if field in control:assert canonical(control[field])==canonical(raw[field])
     if raw.get('tag')not in{'BODY','HTML'}:assert canonical(control['style'])==canonical(_summary(raw,'','')['style'])
     checks['focus_occurrences_exact']+=1
 if verify_pixels:
  for eid in checked_images:assert sha(image_by[eid]['path'])==image_by[eid]['sha256']
 checks['referenced_unique_images']=len(checked_images)
 return{'all_values_and_source_pointers_verified':True,'pixel_sha_verified':verify_pixels,'counts':dict(checks)}

def _native_control(row,directory):
 """Only local frozen rendering; used to validate the other official HTMLs."""
 import evidence_v3 as base
 directory=Path(directory);target=directory/'evidence.json'
 if target.is_file():return read(target)
 directory.mkdir(parents=True,exist_ok=True);bundle=directory/'bundle';originals=[]
 packet=base._packet(row['task_id'])
 for s in packet['inputs']:
  p=Path(s['path']);assert sha(p)==s['sha256'];dest=bundle/s['name'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);originals.append((p,s['sha256']))
 artifacts=[];observations=[];images=[]
 for i,a in enumerate(row['all_output_artifacts'],1):
  p=Path(a['path']);assert sha(p)==a['sha256'];dest=bundle/a['relative_path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);originals.append((p,a['sha256']))
  if p.suffix.lower()not in{'.html','.htm'}:continue
  eid='O'+str(i).zfill(3);artifacts.append({'evidence_id':eid,'filename':p.name,'presence':'PRESENT','sha256':a['sha256']})
  pages,runtime=base._render_html(dest,directory/'renders'/eid,bundle)
  observations.append({'evidence_id':eid+':browser','artifact':p.name,'kind':'REAL_LOCAL_BROWSER_OBSERVATIONS','locator':'output:'+p.name+'/browser','observations':runtime})
  for j,page in enumerate(pages,1):
   image={'evidence_id':eid+':V'+str(j).zfill(3),'artifact':p.name,'role':'output',**page};images.append(image)
  # The same frozen adapter normally adds image IDs to state records.
  byname={Path(im['path']).name:im for im in images if im['artifact']==p.name}
  for state in runtime['state_catalog']:
   state['image_evidence_ids']=list(dict.fromkeys(byname[ref['filename']]['evidence_id']for ref in state['image_refs']))
 evidence={'task_id':row['task_id'],'blind_case_id':row['blind_case_id'],'artifacts':artifacts,'functional_observations':observations,'visual_pages':images,'render_images':images,
  'model_calls':0,'actor_runs':0,'original_files_unchanged':all(sha(p)==s for p,s in originals),'render_source_sha256':sha(base.__file__),'purpose':'LOCAL_NATIVE_STATE_CONTROL_ONLY_NOT_QUALITY_SCORING'}
 assert evidence['original_files_unchanged'];write(target,evidence);return evidence

def validate_all_html():
 import evidence_v3 as base
 destination=B/'critical_state_validation_v5';destination.mkdir(exist_ok=True)
 inventory=[json.loads(x)for x in(B/'execution_v2/private_inventory.frozen.jsonl').read_text(encoding='utf-8').splitlines()]
 rows=[r for r in inventory if any(Path(a['path']).suffix.lower()in{'.html','.htm'}for a in r['all_output_artifacts'])]
 prepared={}
 for row in rows:
  existing=B/'validation_v4/jobs'/row['blind_case_id']/'evidence/evidence.json'
  if existing.is_file():prepared[row['blind_case_id']]=(read(existing),existing)
 missing=[r for r in rows if r['blind_case_id']not in prepared]
 def prepare(row):
  folder=destination/'native_controls'/row['blind_case_id'];return row['blind_case_id'],_native_control(row,folder),folder/'evidence.json'
 with ThreadPoolExecutor(max_workers=2)as pool:
  for bid,evidence,source in pool.map(prepare,missing):prepared[bid]=(evidence,source)
 checks=[]
 for row in rows:
  e,source=prepared[row['blind_case_id']];oldsha=sha(source);index=build_critical_state_index(e)
  assert sha(source)==oldsha and index['coverage']['all_observed_states_retained']and not index['coverage']['missing_image_states']
  provenance=validate_critical_state_index(e,index,verify_pixels=True)
  imageids={i['evidence_id']for i in e['visual_pages']}
  for record in index['artifact_indices']:
   for state in record['states']:
    assert resolve(e,state['source_state_pointer'])['state_id']==state['state_id']
    assert state['image_evidence_ids']and set(state['image_evidence_ids']).issubset(imageids)
    for im in e['visual_pages']:
     if im['evidence_id']in state['image_evidence_ids']:assert sha(im['path'])==im['sha256']
    def pointers(v):
     if isinstance(v,dict):
      for k,x in v.items():
       if k.endswith('source_pointer')and x:resolve(e,x)
       else:pointers(x)
     elif isinstance(v,list):
      for x in v:pointers(x)
    pointers(state['delta'])
  folder=destination/'indices'/row['blind_case_id'];write(folder/'critical_state_index.json',index)
  public=build_public_inspection_index(index);public_control=validate_public_inspection_index(index,public);write(folder/'public_inspection_index.json',public)
  appended=append_critical_state_index(e)
  assert appended['artifacts']==e['artifacts']and appended['visual_pages']==e['visual_pages']
  assert appended['functional_observations']==e['functional_observations']
  assert set(appended)-set(e)=={'critical_ui_state_index_local','public_inspection_index'}
  line={'task_id':row['task_id'],'arm':row['arm'],'blind_case_id':row['blind_case_id'],'source_evidence':str(source),'source_sha256':oldsha,'index_path':str(folder/'critical_state_index.json'),
   'index_sha256':sha(folder/'critical_state_index.json'),'states':index['coverage']['actual_states_indexed'],'images':len(e['visual_pages']),'index_compact_bytes':len(canonical(index).encode()),
   'public_path':str(folder/'public_inspection_index.json'),'public_sha256':sha(folder/'public_inspection_index.json'),'public_compact_bytes':len(canonical(public).encode()),'public_characters':len(canonical(public)),
   'states_with_observed_differences':sum(s['index_state']=='OBSERVED_DIFFERENCE'for r in index['artifact_indices']for s in r['states']),'all_source_pointers_and_images_verified':True,'value_provenance':provenance,'public_control':public_control}
  checks.append(line);write(destination/'progress.json',checks);print(json.dumps(line,ensure_ascii=False),flush=True)
 assert len(checks)==24 and len({x['task_id']for x in checks})==8
 result={'schema_version':'critical-state-index-24html-native-controls-v5','all_passed':True,'model_calls':0,'actor_runs':0,'human_calibration':False,'source_code_sha256':sha(__file__),
  'case_count':len(checks),'task_count':8,'new_native_render_controls':len(missing),'checks':checks,'total_states':sum(x['states']for x in checks),'all_primary_evidence_retained':True,
  'semantics':'Only neutral redundancy organization of actual already-captured states. No judgment, contrast threshold, score, task-specific answer or new business requirement.'}
 write(destination/'validation_summary.json',result);print(json.dumps({k:v for k,v in result.items()if k!='checks'},ensure_ascii=False))
 write(destination/'native_manifest.json',{'source_code_sha256':sha(__file__),'case_count':len(checks),'cases':[{k:c[k]for k in('task_id','arm','blind_case_id','source_evidence','source_sha256','index_path','index_sha256','public_path','public_sha256','states','images','public_compact_bytes')}for c in checks]})

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--validate-all-html',action='store_true');args=parser.parse_args()
 if args.validate_all_html:validate_all_html()
 else:parser.error('--validate-all-html required for native offline controls')
