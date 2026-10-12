"""Offline controls for final-only basic-delivery measurement; no actors/APIs."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SUITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SUITE))
import _runtime as runtime


def contract(checks=None, deliveries=None):
    return {'sid': 'offline_task', 'session_id': 'offline_task',
            'title': 'Offline control task', 'category_name': 'control',
            'score_at': 'conversation_end_only', 'actor_can_see_historical_ai': False,
            'quality_scored': False, 'intermediate_steps_scored': False,
            'manual_judgement_scored': False,
            'final_deliverables': deliveries or [{'id': 'delivery_01', 'name': 'Body', 'kind': 'text'}],
            'checks': checks or [{'delivery_id': 'delivery_01', 'kind': 'text_body_nonempty', 'parameters': {}, 'mandatory': True}]}


class RuntimeControls(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def request(self, bindings=None, **extra):
        req = {'task_id': 'offline_task', 'source_session_id': 'offline_task',
               'workspace': str(self.root), 'result': {'answer': 'Actual body'},
               'evidence': {'schema': 'final-state-evidence-v1',
                   'source_session_id': 'offline_task', 'workspace': str(self.root),
                   'conversation_complete': True, 'initial_sha256': {},
                   'declared_input_sha256': {}, 'deliveries': bindings or {},
                   'measurement': {'namespace': 'final_state_measurement', 'status': 'collected'}}}
        req.update(extra)
        return req

    def score(self, req, c=None):
        return runtime.score_task_request(req, c or contract())

    def test_nonempty_actual_final_body_passes(self):
        out = self.score(self.request({'delivery_01': {'text': 'Delivered text'}}))
        self.assertEqual(out['score'], 1)
        self.assertEqual(out['task_success_status'], 'PASS')
        self.assertFalse(out['quality_scored'])

    def skill_control(self):
        folder = self.root / 'skill'; folder.mkdir()
        (folder / 'SKILL.md').write_text('---\nname: actual-skill\ndescription: Test skill\n---\nRead the user input and deliver a file.\n', 'utf-8')
        req = self.request({'delivery_01': {'directory': 'skill'}})
        c = contract([{'delivery_id':'delivery_01','kind':'skill_final_state',
                       'parameters':{'must_be_changed':True},'mandatory':True}],
                     [{'id':'delivery_01','name':'Skill','kind':'skill'}])
        return req, c, folder

    def test_whole_skill_incomplete_initial_inventory_is_unknown(self):
        req, c, folder = self.skill_control()
        req['evidence']['measurement']['initial_snapshot_complete'] = False
        self.assertIsNone(self.score(req,c)['score'])

    def test_whole_skill_invalid_inventory_digest_is_unknown(self):
        req, c, folder = self.skill_control()
        req['evidence']['initial_sha256'] = {'old/SKILL.md':'invalid_digest'}
        self.assertIsNone(self.score(req,c)['score'])

    def test_whole_skill_renamed_copy_is_not_new_package(self):
        req, c, folder = self.skill_control()
        req['evidence']['initial_sha256'] = {'old/SKILL.md':runtime.digest(folder/'SKILL.md')}
        self.assertEqual(self.score(req,c)['score'],0)

    def test_whole_skill_resource_update_counts_without_instruction_change(self):
        req, c, folder = self.skill_control()
        req['evidence']['initial_sha256'] = {'skill/SKILL.md':runtime.digest(folder/'SKILL.md')}
        (folder/'helper.py').write_text('print("Actual helper resource")\n','utf-8')
        self.assertEqual(self.score(req,c)['score'],1)

    def test_final_only_intermediate_errors_not_scored(self):
        req = self.request({'delivery_01': {'text': 'Delivered text'}})
        req['result']['tool_error_count'] = 9
        self.assertEqual(self.score(req)['score'], 1)

    def test_blank_delivered_body_fails(self):
        out = self.score(self.request({'delivery_01': {'text': ' \n\t'}}))
        self.assertEqual(out['score'], 0)

    def test_all_mandatory_checks_are_AND(self):
        c = contract([{'delivery_id': 'delivery_01', 'kind': 'text_body_nonempty', 'mandatory': True},
                      {'delivery_id': 'delivery_01', 'kind': 'literal_fields_presence', 'parameters': {'literals': ['Required label']}, 'mandatory': True}])
        self.assertEqual(self.score(self.request({'delivery_01': {'text': 'Other text'}}), c)['score'], 0)

    def test_missing_measurement_is_unknown_not_zero(self):
        req = self.request()
        req['evidence'] = {}
        out = self.score(req)
        self.assertFalse(out['valid'])
        self.assertIsNone(out['score'])
        self.assertEqual(out['task_success_status'], 'UNSCORED')

    def test_unfinished_conversation_is_not_scored(self):
        req = self.request()
        req['evidence']['conversation_complete'] = False
        self.assertIsNone(self.score(req)['score'])

    def test_wrong_source_is_not_scored(self):
        req = self.request()
        req['evidence']['source_session_id'] = 'other_task'
        self.assertIsNone(self.score(req)['score'])

    def test_missing_evidence_source_is_not_scored(self):
        req = self.request()
        del req['evidence']['source_session_id']
        self.assertIsNone(self.score(req)['score'])

    def test_unknown_mandatory_kind_not_silently_dropped(self):
        c = contract([{'delivery_id': 'delivery_01', 'kind': 'unsupported_control', 'mandatory': True}])
        self.assertIsNone(self.score(self.request(), c)['score'])

    def test_unknown_observation_does_not_enter_success_AND(self):
        c = contract([{'delivery_id': 'delivery_01', 'kind': 'text_body_nonempty', 'mandatory': True},
                      {'delivery_id': 'delivery_01', 'kind': 'unsupported_observation', 'mandatory': False}])
        out = self.score(self.request({'delivery_01': {'text': 'Body'}}), c)
        self.assertEqual(out['score'], 1)
        self.assertFalse(out['checks'][1]['scorable'])

    def test_approximate_word_count_has_no_invented_tolerance(self):
        c = contract([{'delivery_id': 'delivery_01', 'kind': 'text_body_nonempty', 'mandatory': True},
                      {'delivery_id': 'delivery_01', 'kind': 'text_character_count_report_only', 'parameters': {'requested_approximate_count': 2500}, 'mandatory': False}])
        out = self.score(self.request({'delivery_01': {'text': 'Brief body'}}), c)
        self.assertEqual(out['score'], 1)
        self.assertFalse(out['checks'][1]['scorable'])

    def file_contract(self, kind='final_file_native_open'):
        return contract([{'delivery_id': 'delivery_01', 'kind': kind,
                          'parameters': {'allowed_formats': ['txt']} if kind != 'existing_named_file_reference_resolves' else {'basename': 'source.txt'}, 'mandatory': True}],
                        [{'id': 'delivery_01', 'name': 'New file', 'kind': 'file', 'format': 'txt'}])

    def test_real_new_readable_file_passes(self):
        (self.root / 'result.txt').write_text('Actual output', 'utf-8')
        out = self.score(self.request({'delivery_01': {'files': ['result.txt']}}), self.file_contract())
        self.assertEqual(out['score'], 1)

    def test_unchanged_input_file_is_not_new_output(self):
        f = self.root / 'source.txt'; f.write_text('Input only', 'utf-8')
        digest = hashlib.sha256(f.read_bytes()).hexdigest()
        req = self.request({'delivery_01': {'files': ['source.txt']}})
        req['evidence']['declared_input_sha256'] = {'source.txt': digest}
        self.assertEqual(self.score(req, self.file_contract())['score'], 0)

    def test_copy_of_input_is_not_new_output(self):
        f = self.root / 'copy.txt'; f.write_text('Input only', 'utf-8')
        req = self.request({'delivery_01': {'files': ['copy.txt']}})
        req['evidence']['declared_input_sha256'] = {'source.txt': hashlib.sha256(f.read_bytes()).hexdigest()}
        self.assertEqual(self.score(req, self.file_contract())['score'], 0)

    def test_unchanged_old_attempt_file_is_not_new_output(self):
        f = self.root / 'old.txt'; f.write_text('Old output', 'utf-8')
        req = self.request({'delivery_01': {'files': ['old.txt']}})
        req['evidence']['initial_sha256'] = {'old.txt': hashlib.sha256(f.read_bytes()).hexdigest()}
        self.assertEqual(self.score(req, self.file_contract())['score'], 0)

    def test_explicit_existing_reference_can_use_unchanged_input(self):
        f = self.root / 'source.txt'; f.write_text('Original document', 'utf-8')
        req = self.request({'delivery_01': {'files': ['source.txt']}})
        req['evidence']['declared_input_sha256'] = {'source.txt': hashlib.sha256(f.read_bytes()).hexdigest()}
        c = self.file_contract('existing_named_file_reference_resolves')
        c['final_deliverables'][0]['allow_existing_file_reference'] = True
        self.assertEqual(self.score(req, c)['score'], 1)

    def test_missing_initial_inventory_cannot_prove_new_file(self):
        (self.root / 'output.txt').write_text('Body', 'utf-8')
        req = self.request({'delivery_01': {'files': ['output.txt']}})
        del req['evidence']['initial_sha256']
        self.assertIsNone(self.score(req, self.file_contract())['score'])

    def test_foreign_workspace_file_is_unknown(self):
        req = self.request({'delivery_01': {'files': [str(self.root.parent / 'foreign.txt')]}})
        self.assertIsNone(self.score(req, self.file_contract())['score'])

    def test_measurement_cannot_override_fixed_service_expected_value(self):
        c = contract([{'delivery_id': 'delivery_01', 'kind': 'final_service_state',
                      'parameters': {'service': 'smtp', 'expected': {'recipient': 'alice'}}, 'mandatory': True}],
                     [{'id': 'delivery_01', 'name': 'Mail', 'kind': 'service', 'service': 'smtp'}])
        req = self.request()
        req['evidence']['service_readbacks'] = [{'delivery_id': 'delivery_01', 'service': 'smtp',
            'observation': 'final_readback', 'authoritative': True, 'complete': True,
            'records': [{'recipient': 'bob'}]}]
        req['evidence']['resolved_parameters'] = {'delivery_01': {'expected': {'recipient': 'bob'}}}
        self.assertIsNone(self.score(req, c)['score'])

    def test_payload_does_not_change_contract_policy(self):
        c = contract(); c['quality_scored'] = True
        self.assertIsNone(self.score(self.request(), c)['score'])

    def test_external_evidence_json_is_supported(self):
        req = self.request({'delivery_01': {'text': 'Body'}})
        f = self.root / 'evidence.json'
        f.write_text(json.dumps(req.pop('evidence')), 'utf-8')
        req['evidence_path'] = str(f)
        self.assertEqual(self.score(req)['score'], 1)

    def test_required_selected_skill_not_downgraded_to_observation(self):
        root = self.root / 'skills/foo'; root.mkdir(parents=True)
        (root / 'README.md').write_text('Installed entry', 'utf-8')
        c = contract([{'delivery_id': 'delivery_01', 'kind': 'skill_final_state',
                      'parameters': {'marker': 'README.md', 'skill_frontmatter_name_description': False}, 'mandatory': True}],
                     [{'id': 'delivery_01', 'name': 'Selected skill', 'kind': 'state',
                       'requires_current_reference_resolution': True, 'selection_request_turn_index': 1}])
        req = self.request({'delivery_01': {'directory': 'skills/foo'}})
        self.assertIsNone(self.score(req, c)['score'])

    def test_selected_skill_binding_is_bound_to_actual_prior_answer(self):
        root = self.root / 'skills/foo'; root.mkdir(parents=True)
        (root / 'README.md').write_text('Installed entry', 'utf-8')
        c = contract([{'delivery_id': 'delivery_01', 'kind': 'skill_final_state',
                      'parameters': {'marker': 'README.md', 'skill_frontmatter_name_description': False}, 'mandatory': True}],
                     [{'id': 'delivery_01', 'name': 'Selected skill', 'kind': 'state',
                       'requires_current_reference_resolution': True, 'selection_request_turn_index': 1}])
        req = self.request({'delivery_01': {'directory': 'skills/foo'}})
        body = 'You can use the foo skill'
        req['result']['turn_answers'] = [body, 'Installed']
        req['evidence']['resolved_parameters'] = {'delivery_01': {'selection_binding': {
            'source_session_id': 'offline_task', 'authoritative': True,
            'origin': 'before_user_request_reference_resolution',
            'before_dispatch_index': 1, 'source_reply_index': 0,
            'source_reply_sha256': hashlib.sha256(body.encode('utf-8')).hexdigest(),
            'skill_name': 'foo', 'path': 'skills/foo'}}}
        self.assertEqual(self.score(req, c)['score'], 1)
        req['evidence']['resolved_parameters']['delivery_01']['selection_binding']['source_reply_sha256'] = '0' * 64
        self.assertIsNone(self.score(req, c)['score'])

    def test_copy_of_unchanged_old_file_under_new_name_is_rejected(self):
        f = self.root / 'renamed.txt'; f.write_text('Old output', 'utf-8')
        req = self.request({'delivery_01': {'files': ['renamed.txt']}})
        req['evidence']['initial_sha256'] = {'old.txt': hashlib.sha256(f.read_bytes()).hexdigest()}
        self.assertEqual(self.score(req, self.file_contract())['score'], 0)

    def test_invalid_input_inventory_digest_is_measurement_fault(self):
        (self.root / 'new.txt').write_text('Body', 'utf-8')
        req = self.request({'delivery_01': {'files': ['new.txt']}})
        req['evidence']['declared_input_sha256'] = {'input.txt': 'invalid_digest'}
        self.assertIsNone(self.score(req, self.file_contract())['score'])

    def test_fixed_daily_schedule_cannot_be_changed_by_resolution(self):
        c = contract([{'delivery_id': 'delivery_01', 'kind': 'final_service_state',
                      'parameters': {'service': 'cron_registration', 'expected': {'schedule': 'daily 08:00'}}, 'mandatory': True}],
                     [{'id': 'delivery_01', 'name': 'Job', 'kind': 'service'}])
        req = self.request()
        req['evidence']['service_readbacks'] = [{'delivery_id': 'delivery_01', 'service': 'cron_registration',
            'observation': 'final_readback', 'authoritative': True, 'complete': True,
            'records': [{'schedule': 'daily 09:00'}]}]
        req['evidence']['resolved_parameters'] = {'delivery_01': {'expected': {'schedule': 'daily 09:00'}}}
        self.assertIsNone(self.score(req, c)['score'])

    def test_fixed_daily_schedule_does_not_need_output_as_gold(self):
        c = contract([{'delivery_id': 'delivery_01', 'kind': 'final_service_state',
                      'parameters': {'service': 'cron_registration', 'expected': {'schedule': 'daily 08:00'}}, 'mandatory': True}],
                     [{'id': 'delivery_01', 'name': 'Job', 'kind': 'service'}])
        req = self.request()
        req['evidence']['service_readbacks'] = [{'delivery_id': 'delivery_01', 'service': 'cron_registration',
            'observation': 'final_readback', 'authoritative': True, 'complete': True,
            'records': [{'schedule': 'daily 08:00'}]}]
        self.assertEqual(self.score(req, c)['score'], 1)

    def test_engine_dependency_fault_returns_unscored(self):
        with patch.object(runtime, 'load_engine', side_effect=ImportError('missing runtime dependency')):
            out = self.score(self.request())
        self.assertEqual(out['task_success_status'], 'UNSCORED')
        self.assertIsNone(out['score'])

    def test_prefilled_job_identity_without_real_initial_snapshot_not_trusted(self):
        req = self.request()
        req['evidence']['timeout_change_readbacks'] = [{'original_job_id': 'old_job', 'job_id': 'new_job'}]
        enriched = runtime.enrich_same_job_identity(req)
        self.assertNotIn('original_job_id', enriched['evidence']['timeout_change_readbacks'][0])


if __name__ == '__main__':
    unittest.main()
