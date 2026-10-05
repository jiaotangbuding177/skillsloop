"""Importer contract tests; authored fixtures are not benchmark evidence."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from skilldemo.experiment_input import convert_results, import_file
from skilldemo.pipeline import normalize_input, prepare_events
from skilldemo.evidence import catalog


def result_fixture():
    return {
        'tasks': [{'id': '7', 'evaluation_criteria': {'actions': ['HIDDEN_GOLD']}}],
        'info': {'environment_info': {'policy': 'NOT_AUTOMATICALLY_IMPORTED'}},
        'simulations': [
            {'id': 'source-session-7', 'task_id': '7',
             'reward_info': {'reward': 0, 'gold': 'HIDDEN_GOLD'},
             'messages': [
                 {'role': 'assistant', 'content': 'Hello', 'tool_calls': None},
                 {'role': 'user', 'content': 'Check my device', 'turn_idx': 2,
                  'raw_data': {'secret': 'NOT_VISIBLE'},
                  'tool_calls': [{'id': 'user-call', 'name': 'check_device',
                                  'arguments': {}, 'requestor': 'user'}]},
                 {'role': 'tool', 'id': 'user-call', 'content': '',
                  'requestor': 'user', 'error': False},
                 {'role': 'assistant', 'content': None,
                  'tool_calls': [{'id': 'assistant-call', 'type': 'function',
                                  'function': {'name': 'lookup', 'arguments': '{"id":"a"}'}}]},
                 {'role': 'tool', 'id': 'assistant-call', 'content': 'not found',
                  'error': True, 'requestor': 'assistant'},
                 {'id': 'explicit-reply', 'role': 'assistant', 'content': 'I cannot confirm completion.'},
             ]},
            {'id': 'source-session-8', 'task_id': '8',
             'messages': [{'role': 'user', 'content': 'Other task'}]},
        ],
    }


class ExperimentInputTests(unittest.TestCase):
    def test_visible_only_and_original_order(self):
        value, audit = convert_results(result_fixture(), ['7'])
        self.assertEqual(set(value), {'E', 'C', 'V'})
        self.assertEqual(value['C'], [])
        self.assertEqual(value['V'], [])
        self.assertEqual(len(value['E']), 6)
        self.assertEqual([e['sourceOrder'] for e in value['E']], list(range(1, 7)))
        self.assertTrue(all(e['sessionId'] == 'source-session-7' for e in value['E']))
        self.assertEqual(value['E'][-1]['id'], 'explicit-reply')
        encoded = json.dumps(value)
        for hidden in ('HIDDEN_GOLD', 'NOT_VISIBLE', 'NOT_AUTOMATICALLY_IMPORTED', 'reward_info'):
            self.assertNotIn(hidden, encoded)
        self.assertEqual(audit['selectedSimulationCount'], 1)
        self.assertEqual(audit['toolCallCounts'], {'user': 1, 'assistant': 1})

    def test_preserves_both_actors_calls_empty_receipt_and_pipeline_contract(self):
        value, _ = convert_results(result_fixture(), ['7'])
        self.assertEqual(value['E'][2]['content'], '')
        self.assertEqual(value['E'][2]['callId'], 'user-call')
        self.assertEqual(value['E'][1]['tool_calls'][0]['requestor'], 'user')
        normalized, _ = normalize_input(value)
        events, pairs, _ = prepare_events(normalized)
        self.assertEqual(len(events), 6)
        self.assertTrue(pairs)
        self.assertEqual(normalized['events'][3]['toolCalls'][0]['arguments'], {'id': 'a'})
        self.assertNotIn('runId', value['E'][0])
        calls = [r for r in catalog(pairs) if r['kind'] == 'TOOL_CALL']
        self.assertEqual(len(calls), 2)
        self.assertEqual({r['metadata']['actor'] for r in calls}, {'user', 'assistant'})

    def test_only_recorded_per_message_run_id_is_forwarded(self):
        source = result_fixture()
        source['simulations'][0]['messages'][0]['run_id'] = 'explicit-model-request'
        value, _ = convert_results(source, ['7'])
        self.assertEqual(value['E'][0]['runId'], 'explicit-model-request')
        self.assertNotIn('runId', value['E'][1])

    def test_explicit_public_context_and_evaluation_only(self):
        context = [{'id': 'policy', 'kind': 'POLICY', 'text': 'Confirm before changing.', 'source': 'public-policy'}]
        evaluations = [{'id': 'review', 'scope': 'STEP', 'targetIds': ['explicit-reply'],
                        'criterion': 'Completion must be qualified', 'result': True,
                        'source': 'separate-review', 'verified': True,
                        'verificationBasis': 'human-reviewed response'}]
        value, audit = convert_results(result_fixture(), ['7'], context=context, evaluations=evaluations)
        self.assertEqual(value['C'], context)
        self.assertEqual(value['V'][0]['scope'], 'STEP')
        self.assertEqual(audit['explicitEvaluationCount'], 1)

    def test_raw_reward_cannot_enter_as_explicit_v(self):
        with self.assertRaises(ValueError):
            convert_results(result_fixture(), ['7'], evaluations=[{'reward_info': {'reward': 1}}])

    def test_missing_selection_fails_instead_of_importing_everything(self):
        for tasks in ([], ['missing'], ['7', '7']):
            with self.subTest(tasks=tasks), self.assertRaises(ValueError):
                convert_results(result_fixture(), tasks)

    def test_multiple_trials_kept_as_distinct_sessions(self):
        source = result_fixture()
        extra = deepcopy(source['simulations'][0]); extra['id'] = 'second-trial'
        source['simulations'].append(extra)
        value, audit = convert_results(source, ['7'])
        self.assertEqual(audit['selectedSimulationCount'], 2)
        self.assertEqual(len({e['sessionId'] for e in value['E']}), 2)
        self.assertEqual(len(value['E']), 12)

    def test_message_history_alias(self):
        source = result_fixture()
        run = source['simulations'][0]
        run['message_history'] = run.pop('messages')
        value, _ = convert_results(source, ['7'])
        self.assertEqual(len(value['E']), 6)

    def test_different_message_arrays_fail_not_arbitrarily_choose(self):
        source = result_fixture()
        source['simulations'][0]['message_history'] = [{'role': 'user', 'content': 'different'}]
        with self.assertRaises(ValueError):
            convert_results(source, ['7'])

    def test_duplicate_session_or_message_id_rejected(self):
        source = result_fixture()
        source['simulations'].append(deepcopy(source['simulations'][0]))
        with self.assertRaises(ValueError):
            convert_results(source, ['7'])
        source = result_fixture()
        source['simulations'][0]['messages'][0]['id'] = 'explicit-reply'
        with self.assertRaises(ValueError):
            convert_results(source, ['7'])

    def test_system_message_omitted_and_recorded_without_importing_prompt(self):
        source = result_fixture()
        source['simulations'][0]['messages'].insert(0, {'role': 'system', 'content': 'PRIVATE_PROMPT'})
        value, audit = convert_results(source, ['7'])
        self.assertEqual(len(value['E']), 6)
        self.assertNotIn('PRIVATE_PROMPT', json.dumps(value))
        self.assertEqual(value['E'][0]['sourceOrder'], 2)
        self.assertEqual(audit['omittedRoleCounts'], {'system': 1})

    def test_null_calls_are_not_emitted_as_invalid_tool_arrays(self):
        value, _ = convert_results(result_fixture(), ['7'])
        self.assertNotIn('tool_calls', value['E'][0])

    def test_missing_tool_call_id_is_rejected_not_fabricated(self):
        source = result_fixture()
        source['simulations'][0]['messages'][1]['tool_calls'][0].pop('id')
        with self.assertRaises(ValueError):
            convert_results(source, ['7'])

    def test_generated_message_identity_does_not_claim_source_identity(self):
        value, audit = convert_results(result_fixture(), ['7'])
        first = audit['simulations'][0]['messages'][0]
        self.assertTrue(first['idGenerated'])
        self.assertEqual(first['sourcePosition'], 1)
        self.assertEqual(value['E'][0]['id'], first['outputId'])

    def test_file_import_immutable_and_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); source = root/'source.json'; output = root/'input.json'
            source.write_text(json.dumps(result_fixture()), encoding='utf-8')
            info = import_file(source, output, ['7'])
            self.assertEqual(info['eventCount'], 6)
            manifest = json.loads(output.with_suffix('.manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(len(manifest['sourceSha256']), 64)
            self.assertEqual(len(manifest['inputSha256']), 64)
            self.assertEqual(manifest['requestedTaskIds'], ['7'])
            original = output.read_bytes()
            import_file(source, output, ['7'])
            self.assertEqual(output.read_bytes(), original)
            with self.assertRaises(FileExistsError):
                import_file(source, output, ['8'])
            self.assertEqual(output.read_bytes(), original)

    def test_conflicting_manifest_prevents_partial_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); source = root/'source.json'; output = root/'input.json'
            source.write_text(json.dumps(result_fixture()), encoding='utf-8')
            output.with_suffix('.manifest.json').write_text('{}', encoding='utf-8')
            with self.assertRaises(FileExistsError):
                import_file(source, output, ['7'])
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
