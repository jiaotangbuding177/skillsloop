"""Compact neutral native/source relationships, private to the quality Judge."""
from __future__ import annotations
from decimal import Decimal
import hashlib
from pathlib import Path
from neutral_reading_facts import build_reading_facts


def _sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_observations(case, inventory, evidence):
    """Read fresh SHA-bound bytes, never static audit answers or prior scores."""
    if case['task_id']!='T0003':
        return []
    rubric=case['base_rubric']
    item_ids=[i['item_id'] for i in rubric['items'] if i['dimension'] in {'D1','D4'}]
    records={record['filename']:record for record in inventory['all_output_artifacts']}
    delivered={record['filename']:record for record in evidence['artifacts'] if record.get('presence')=='PRESENT'}
    result=[]
    for filename,record in records.items():
        if Path(filename).suffix.lower() not in {'.xlsx','.xlsm'} or filename not in delivered:
            continue
        assert _sha(record['path'])==record['sha256']==delivered[filename]['sha256']
        facts=build_reading_facts(record['path'],case)
        assert facts['artifact_sha256']==record['sha256']
        result.append({'evidence_id':'MTREADING:'+case['task_id']+':'+filename,
            'artifact':filename,'item_ids':[iid for iid in item_ids if filename in next(i for i in rubric['items'] if i['item_id']==iid).get('deliverables',[])],
            'kind':'PRIVATE_SHA_BOUND_NATIVE_AND_SOURCE_TABLE_READING_FACTS',
            'locator':'private-table-reading/'+filename,'quality_only':True,'evaluation_scope':'QUALITY_ONLY',
            'scope':'Exact observed coordinates/headers/formulas/values and independent source arithmetic. No rubric score, pass/fail or forced correctness. Never provided to Actor, user simulator or basic acceptance.',
            'measured_artifacts':[{'filename':filename,'sha256':record['sha256']}],
            'observations':facts})
    return result


def public_index(observations):
    """Complete compact cell table, close to task text, pointing to full facts.

    This is neutral navigation. All 220 recognized cells remain in the actual
    observation and in this table. Unknown layouts are explicit, not failures.
    """
    artifacts=[]
    for observation in observations:
        facts=observation['observations']
        by_cell={(cell['sheet'],cell['cell']):cell for cell in facts.get('cells',[])}
        rows=[]
        for cell in facts.get('cells',[]):
            components=[]
            for value in cell.get('same_row_observed_components',[]):
                found=by_cell.get((value['sheet'],value['cell']))
                components.append([value['sheet'],value['cell'],value['column_label'],value['raw'],
                                   found.get('value') if found else None])
            dependencies=[[value['sheet'],value['cell'],value['column_label'],value['raw']]
                          for value in cell.get('formula_dependency_cells',[])]
            # Every row is retained. This is not a list of selected matching
            # cells and never calls a difference zero/nonzero a quality score.
            rows.append([cell['sheet'],cell['cell'],cell['row_label'],cell['column_label'],
                cell.get('raw'),cell.get('formula'),cell.get('value'),cell.get('independent_source_value'),
                components,dependencies])
        artifacts.append({'artifact':observation['artifact'],'artifact_sha256':facts['artifact_sha256'],
            'actual_observation_id':observation['evidence_id'],'availability':facts.get('availability'),
            'unknown_reason':facts.get('unavailable_reason'),
            'column_headers':['sheet','column','header_cell','actual_header','entity','period'],
            'columns':[[value['sheet'],value['column'],value['header_cell'],value['header'],value['entity'],value['period']]
                       for value in facts.get('column_map',[])],
            'cell_headers':['sheet','cell','row_label','actual_column_label','original_raw','original_formula',
                'evaluated_output_value','independent_sum_from_original_sources',
                'same_row_actual_components:[sheet,cell,column_label,raw,evaluated_output_value]',
                'formula_dependencies:[sheet,cell,column_label,raw]'],
            'cells':rows,'cell_count':len(rows),
            'source_records_in_actual_observation':len(facts.get('source_records',[])),
            'neutral_reading_note':'Column labels distinguish company/month, signed elimination columns and group/month. Component amounts retain their original signs. Independent sums use only SHA-bound original ledgers and explicit original matching pairs; these facts do not preassign any rubric score.'})
    return {'schema':'private-source-bound-neutral-table-reading-index-v1','artifacts':artifacts,
        'scope':'NEUTRAL_READING_NAVIGATION_NOT_REFERENCE_SCORE_OR_ACTOR_INPUT',
        'all_recognized_target_cells_included':True,'no_pass_fail_or_quality_score_supplied':True}
