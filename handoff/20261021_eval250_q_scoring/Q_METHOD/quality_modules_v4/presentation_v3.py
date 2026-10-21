"""Original-modality-applicable Judge view, with a complete native archive.

No scoring, page-quality selection, new rubric or Actor instructions. All
sheet-wide pages are kept; only a view expressly marked print-diagnostic-only
is withheld when the original task does not ask for printed XLSX output.
"""
from __future__ import annotations
import copy
from pathlib import Path

SCHEMA='original-modality-applicable-quality-view-v3'
XLSX={'.xlsx','.xlsm'}


def _print_required(rubric, filename):
    return any(filename in item.get('deliverables',[]) and
        item.get('visual_evidence_policy',{}).get('explicit_print_requirement') is True
        for item in rubric['items'])


def select_judge_view(evidence, rubric):
    """Return full content + every applicable image, and private archive facts."""
    original_images={}
    for image in evidence.get('visual_pages',[])+evidence.get('render_images',[]):
        eid=image['evidence_id']
        if eid in original_images:
            assert original_images[eid]==image,'Conflicting original image identities'
        original_images[eid]=image
    omitted=[];included=[]
    for image in original_images.values():
        filename=image.get('artifact','')
        diagnostic=str(image.get('view_semantics','')).startswith('ORIGINAL_PRINT_DIAGNOSTIC_ONLY')
        if image.get('role')!='input' and Path(filename).suffix.lower() in XLSX and diagnostic and not _print_required(rubric,filename):
            omitted.append(copy.deepcopy(image))
        else:
            included.append(copy.deepcopy(image))
    view=copy.deepcopy(evidence)
    excluded_ids={image['evidence_id'] for image in omitted}
    included_ids={image['evidence_id'] for image in included}
    view['visual_pages']=included
    view['render_images']=view['visual_pages']
    # Navigation is derived metadata, not business facts. Remove references to
    # withheld pixels everywhere so a stale critical-state index cannot invite
    # a citation to a picture absent from the actual Judge request.
    def clean_navigation(value):
        if isinstance(value,dict):
            result={}
            for key,child in value.items():
                if key in {'visual_pages','render_images'}:
                    result[key]=child
                elif isinstance(child,str) and child in excluded_ids:
                    continue
                else:
                    result[key]=clean_navigation(child)
            return result
        if isinstance(value,list):
            result=[]
            for child in value:
                if isinstance(child,str) and child in excluded_ids:continue
                if isinstance(child,dict) and child.get('evidence_id') in excluded_ids:continue
                result.append(clean_navigation(child))
            return result
        return value
    # Only metadata navigation is eligible for pruning; native extraction,
    # literal source text, functional facts and real business values stay exact.
    for key in ('critical_state_index','critical_ui_state_index_local','public_inspection_index','evidence_atoms','item_availability'):
        if key in view:view[key]=clean_navigation(view[key])
    for key in ['artifacts','outputs','sources','input_evidence']:
        for record in view.get(key,[]):
            if isinstance(record.get('evidence_ids'),list):
                record['evidence_ids']=[eid for eid in record['evidence_ids'] if eid not in excluded_ids]
    for item_id,slot in view.get('item_availability',{}).items():
        slot['evidence_ids']=[eid for eid in slot.get('evidence_ids',[]) if eid not in excluded_ids]
        if 'visual' in slot.get('required_evidence_modes',[]) and slot.get('status')=='AVAILABLE':
            current=next(item for item in rubric['items'] if item['item_id']==item_id)
            relevant=[im for im in included if im.get('role')=='output' and im.get('artifact') in current.get('deliverables',[])]
            if not relevant:
                slot.update(status='UNSCORED',reason='Original item requires actual applicable visual evidence; only unrequested print-diagnostic views exist. Complete native diagnostic archive retained; no business zero assigned.')
    view['schema_version']=SCHEMA
    view['view_semantics_contract']=str(view.get('view_semantics_contract',''))+(
        ' Judge receives every original-modality-applicable image. For XLSX without an original print requirement, '
        'all sheet-wide actual pages are supplied; print-diagnostic-only pages remain solely in the complete local native archive. '
        'Withheld images are not in the Judge image registry and cannot support a citation. No best-page selection, '
        'no native values/style/width changes and no new print requirement. PDF/PPTX/DOCX image coverage is unchanged.')
    archive={'schema':SCHEMA,'original_images':len(original_images),'judge_images':len(included),
        'withheld_print_diagnostic_images':len(omitted),'withheld_image_records_private':omitted,
        'all_applicable_original_image_ids_kept':list(included_ids),
        'selection_basis':'ORIGINAL_MODALITY_APPLICABILITY_NOT_PIXEL_CONTENT_OR_EXPECTED_SCORE',
        'original_rubric_items_modified':False,'native_archive_complete':True,
        'no_pages_selected_by_quality':True}
    assert not excluded_ids.intersection(included_ids)
    return view,archive
