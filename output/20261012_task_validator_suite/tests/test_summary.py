import importlib.util
import json
from pathlib import Path
import sys
import pytest

HERE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(HERE))
from summarize_scores import summarize


def manifest():
    return {'tasks':[{'source_session_id':'a','category':'A'},{'source_session_id':'b','category':'B'}]}


def response(tmp_path,sid,status,score):
    path=tmp_path/(sid+'.json');path.write_text(json.dumps({'source_session_id':sid,'score_at':'conversation_end_only',
        'quality_scored':False,'task_success_status':status,'score':score,'valid':status!='UNSCORED'}),'utf-8')
    return path


def test_complete_fixed_micro_macro(tmp_path):
    out=summarize([response(tmp_path,'a','PASS',1),response(tmp_path,'b','FAIL',0)],manifest())
    assert out['official_task_success_rate']==.5 and out['official_macro_success_rate']==.5


def test_unknown_never_silently_removed(tmp_path):
    out=summarize([response(tmp_path,'a','PASS',1),response(tmp_path,'b','UNSCORED',None)],manifest())
    assert out['coverage']==.5 and out['measured_task_success_rate']==1
    assert out['official_task_success_rate'] is None and out['official_macro_success_rate'] is None


def test_missing_stays_in_fixed_denominator(tmp_path):
    out=summarize([response(tmp_path,'a','PASS',1)],manifest())
    assert out['missing']==1 and out['fixed_tasks']==2 and out['coverage']==.5


def test_duplicate_attempt_not_pooled(tmp_path):
    path=response(tmp_path,'a','PASS',1)
    with pytest.raises(ValueError,match='duplicate_source'):
        summarize([path,path],manifest())


def test_boolean_score_rejected(tmp_path):
    with pytest.raises(ValueError,match='measurement_validity'):
        summarize([response(tmp_path,'a','PASS',True)],manifest())
