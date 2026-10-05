"""Only exact frozen update selections use one structured provider request.

Responses and evidence are synthetic. All HTTP and native process entry points
are mocked; these tests make no provider calls and touch no historical run.
"""
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
import urllib.error
from unittest.mock import patch

from skilldemo import runtime
from skilldemo.learning import (
    ANALYST_INSTRUCTIONS,
    FROZEN_PROPOSAL_VERSION,
    freeze_approved_proposals,
    public_update_input,
)
from test_prebound_evolution import user_rule_payload


SECRET = 'frozen-update-test-secret'
PRIVATE_MARKER = 'PRIVATE-EVIDENCE-ONLY-TEST-MARKER'
FINAL_TEXT = '说明：选择已冻结更新单元。\n```json\n{"decision":"DEFER","mergedPatches":[],"deferred":[]}\n```\n结束。'


def frozen_payload():
    payload = user_rule_payload()
    # A missing cross-scope binding defers this method; the other remains legal.
    payload['approvedMethods'][0]['requirementApplicability'][0].pop('dimension')
    payload['evidence'][0]['privateAuditToken'] = PRIVATE_MARKER
    payload = freeze_approved_proposals(payload)
    payload['algorithm'] = 'trace-patch-v1'
    return payload


def provider_response(api, text=FINAL_TEXT, stop=None):
    if api == 'anthropic-messages':
        return {'model': 'fixture-model', 'content': [{'type': 'text', 'text': text}],
                'stop_reason': stop or 'end_turn',
                'usage': {'input_tokens': 12, 'output_tokens': 8}}
    return {'model': 'fixture-model', 'choices': [
        {'message': {'content': text}, 'finish_reason': stop or 'stop'}],
        'usage': {'prompt_tokens': 12, 'completion_tokens': 8, 'total_tokens': 20}}


class Response:
    def __init__(self, raw):
        self.raw = raw

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self):
        return json.dumps(self.raw, ensure_ascii=False).encode('utf-8')


class Opener:
    def __init__(self, raw=None, error=None):
        self.raw, self.error, self.calls = raw, error, []

    def open(self, request, timeout):
        self.calls.append((request, timeout))
        if self.error is not None:
            raise self.error
        return Response(self.raw)


def environment(api='openai-completions'):
    return {'DEMO_MODEL': 'fixture-model', 'DEMO_API_KEY': SECRET,
            'DEMO_MODEL_API': api, 'DEMO_BASE_URL': 'https://fixture.invalid/v1',
            'DEMO_NETWORK_MODE': 'direct', 'DEMO_DETECT_TIMEOUT': '91',
            'DEMO_AGENT_TIMEOUT': '777'}


class DirectFrozenUpdateTests(unittest.TestCase):
    def test_exact_frozen_update_uses_one_request_with_full_public_projection(self):
        payload = frozen_payload()
        before = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        public = public_update_input(payload)
        self.assertEqual({u['status'] for u in public['updateUnits']}, {'APPROVED', 'DEFERRED'})
        for api in ('openai-completions', 'anthropic-messages'):
            with self.subTest(api=api), tempfile.TemporaryDirectory() as directory, \
                 patch.dict(os.environ, environment(api), clear=True), \
                 patch('skilldemo.runtime.urllib.request.build_opener', return_value=Opener(provider_response(api))) as build, \
                 patch('skilldemo.runtime.initialize', side_effect=AssertionError('native initialize forbidden')) as init, \
                 patch.object(runtime.OpenClawAgent, 'command', side_effect=AssertionError('native command forbidden')) as command, \
                 patch('skilldemo.runtime.subprocess.Popen', side_effect=AssertionError('native process forbidden')) as popen, \
                 patch('skilldemo.runtime.read_evidence', side_effect=AssertionError('native evidence forbidden')) as read:
                workspace = Path(directory) / 'structured'
                result = runtime.OpenClawAgent().run('learn', payload, workspace)
                opener = build.return_value
                self.assertEqual(len(opener.calls), 1)
                request, timeout = opener.calls[0]
                body = json.loads(request.data)
                prompt = body['messages'][0]['content']
                self.assertIn(json.dumps(public, ensure_ascii=False), prompt)
                self.assertTrue(prompt.startswith(runtime.FROZEN_UPDATE_SELECTION_INSTRUCTIONS))
                self.assertNotIn(PRIVATE_MARKER, prompt)
                self.assertNotIn('"evidence":', prompt)
                self.assertNotIn('"frozenAnalyses":', prompt)
                self.assertEqual(body['max_tokens'], 8192)
                self.assertEqual(body['temperature'], 0)
                self.assertEqual(timeout, 91)
                self.assertEqual(result['text'], FINAL_TEXT)
                self.assertEqual(result['runtime'], 'structured-model-request')
                self.assertEqual(result['modelRequestStarts'], 1)
                self.assertEqual(result['status'], 'ok')
                self.assertNotIn('skillEvidence', result)
                self.assertNotIn('foundationRead', result)
                self.assertNotIn('foundation', result)
                init.assert_not_called()
                command.assert_not_called()
                popen.assert_not_called()
                read.assert_not_called()
                saved = json.loads((workspace / 'request.json').read_text(encoding='utf-8'))
                self.assertEqual(saved['body'], body)
                self.assertEqual(saved['purpose'], 'frozen_update_select')
                self.assertEqual(json.loads((workspace / 'response.json').read_text(encoding='utf-8')), provider_response(api))
                self.assertNotIn(SECRET, json.dumps(saved, ensure_ascii=False))
        self.assertEqual(json.dumps(payload, ensure_ascii=False, sort_keys=True), before)

    def test_frozen_request_config_uses_one_selection_prompt_and_detect_timeout(self):
        for configured, expected in (('5', 10), ('91', 91), ('5000', 240)):
            env = {**environment(), 'DEMO_DETECT_TIMEOUT': configured}
            with self.subTest(timeout=configured), patch.dict(os.environ, env, clear=True):
                config = runtime.request_config('frozen_update_select')
                self.assertEqual(config['purpose'], 'frozen_update_select')
                self.assertEqual(config['prompt'], runtime.FROZEN_UPDATE_SELECTION_INSTRUCTIONS)
                self.assertEqual(config['maxTokens'], 8192)
                self.assertEqual(config['temperature'], 0)
                self.assertEqual(config['timeoutSeconds'], expected)
                self.assertNotIn(SECRET, json.dumps(config, ensure_ascii=False))

    def test_learn_config_records_routes_and_retains_legacy_prompt_selection(self):
        with patch.dict(os.environ, environment(), clear=True):
            config = runtime.request_config('learn')
        self.assertEqual(config['version'], 'learn-request-routing-v3')
        self.assertEqual(config['promptVariants']['legacy'], ANALYST_INSTRUCTIONS)
        self.assertEqual(config['promptVariants'][FROZEN_PROPOSAL_VERSION], runtime.FROZEN_UPDATE_SELECTION_INSTRUCTIONS)
        self.assertEqual(config['promptSelection'], {
            'payloadField': 'proposalContractVersion',
            'matchedValue': FROZEN_PROPOSAL_VERSION, 'defaultVariant': 'legacy',
        })
        self.assertIn('branchConfigurations', config)

    def test_unknown_nonempty_contract_rejects_before_http_or_native_entry(self):
        for contract in ('approved-method-proposals-v2', 'unrecognized-contract'):
            payload = frozen_payload()
            payload['proposalContractVersion'] = contract
            with self.subTest(contract=contract), tempfile.TemporaryDirectory() as directory, \
                 patch.dict(os.environ, environment(), clear=True), \
                 patch('skilldemo.runtime.urllib.request.build_opener') as build, \
                 patch('skilldemo.runtime.initialize') as init, \
                 patch.object(runtime.OpenClawAgent, 'command') as command, \
                 patch('skilldemo.runtime.subprocess.Popen') as popen:
                with self.assertRaises(ValueError):
                    runtime.OpenClawAgent().run('learn', payload, Path(directory) / 'untouched')
                build.assert_not_called()
                init.assert_not_called()
                command.assert_not_called()
                popen.assert_not_called()

    def test_legacy_learning_creator_and_chat_still_enter_native_initialization(self):
        routes = (
            ('learn', {'algorithm': 'trace-patch-v1', 'action': 'UPDATE'}),
            ('workflow_creator', {'algorithm': 'workflow-creator-v1'}),
            ('creator', {'trace': {}}),
            ('chat', {'message': '处理本次材料', 'selected_skills': []}),
        )
        for purpose, payload in routes:
            with self.subTest(purpose=purpose), tempfile.TemporaryDirectory() as directory, \
                 patch.dict(os.environ, environment(), clear=True), \
                 patch('skilldemo.runtime.urllib.request.build_opener') as build, \
                 patch('skilldemo.runtime.initialize', side_effect=RuntimeError('NATIVE_ENTRY_SENTINEL')) as init, \
                 patch('skilldemo.runtime.subprocess.Popen') as popen:
                with self.assertRaisesRegex(RuntimeError, 'NATIVE_ENTRY_SENTINEL'):
                    runtime.OpenClawAgent().run(purpose, payload, Path(directory) / 'native')
                init.assert_called_once()
                build.assert_not_called()
                popen.assert_not_called()

    def test_supported_contract_with_wrong_algorithm_rejects_before_request(self):
        payload = frozen_payload()
        payload['algorithm'] = 'future-patch-v2'
        with tempfile.TemporaryDirectory() as directory, \
             patch.dict(os.environ, environment(), clear=True), \
             patch('skilldemo.runtime.urllib.request.build_opener') as build, \
             patch('skilldemo.runtime.initialize') as init, \
             patch('skilldemo.runtime.subprocess.Popen') as popen:
            with self.assertRaises(ValueError):
                runtime.OpenClawAgent().run('learn', payload, Path(directory) / 'wrong-algorithm')
            build.assert_not_called()
            init.assert_not_called()
            popen.assert_not_called()

    def test_changed_frozen_baseline_rejects_before_request(self):
        payload = frozen_payload()
        payload['initial_files'][0]['content'] += '\n未冻结新规则。'
        with tempfile.TemporaryDirectory() as directory, \
             patch.dict(os.environ, environment(), clear=True), \
             patch('skilldemo.runtime.urllib.request.build_opener') as build, \
             patch('skilldemo.runtime.initialize') as init, \
             patch('skilldemo.runtime.subprocess.Popen') as popen:
            with self.assertRaises(ValueError):
                runtime.OpenClawAgent().run('learn', payload, Path(directory) / 'changed-baseline')
            build.assert_not_called()
            init.assert_not_called()
            popen.assert_not_called()

    def test_http_error_keeps_one_failed_request_and_never_discloses_key(self):
        error = urllib.error.HTTPError('https://fixture.invalid/v1/chat/completions', 401,
            'credential=' + SECRET, {}, io.BytesIO(('upstream body ' + SECRET).encode()))
        self.addCleanup(error.close)
        opener = Opener(error=error)
        with tempfile.TemporaryDirectory() as directory, \
             patch.dict(os.environ, environment(), clear=True), \
             patch('skilldemo.runtime.urllib.request.build_opener', return_value=opener), \
             patch('skilldemo.runtime.initialize') as init, \
             patch('skilldemo.runtime.subprocess.Popen') as popen:
            workspace = Path(directory) / 'failed'
            with self.assertRaises(runtime.RuntimeFailure) as caught:
                runtime.OpenClawAgent().run('learn', frozen_payload(), workspace)
            failure = caught.exception
            self.assertEqual(len(opener.calls), 1)
            self.assertEqual(failure.result['status'], 'FAILED')
            self.assertEqual(failure.result['modelRequestStarts'], 1)
            self.assertNotIn(SECRET, str(failure))
            self.assertNotIn(SECRET, json.dumps(failure.result, ensure_ascii=False))
            audit = (workspace / 'response-error.json').read_text(encoding='utf-8')
            self.assertNotIn(SECRET, audit)
            self.assertEqual(json.loads(audit)['modelRequestStarts'], 1)
            init.assert_not_called()
            popen.assert_not_called()

    def test_token_truncation_is_incomplete_without_retry_or_native_fallback(self):
        for api, stop in (('openai-completions', 'length'), ('anthropic-messages', 'max_tokens')):
            opener = Opener(provider_response(api, stop=stop))
            with self.subTest(api=api), tempfile.TemporaryDirectory() as directory, \
                 patch.dict(os.environ, environment(api), clear=True), \
                 patch('skilldemo.runtime.urllib.request.build_opener', return_value=opener), \
                 patch('skilldemo.runtime.initialize') as init:
                with self.assertRaises(runtime.RuntimeFailure) as caught:
                    runtime.OpenClawAgent().run('learn', frozen_payload(), Path(directory) / 'incomplete')
                self.assertEqual(caught.exception.result['status'], 'INCOMPLETE')
                self.assertEqual(caught.exception.result['modelRequestStarts'], 1)
                self.assertEqual(len(opener.calls), 1)
                init.assert_not_called()

    def test_tool_stop_with_nonempty_text_is_incomplete(self):
        for api, stop in (('openai-completions', 'tool_calls'), ('anthropic-messages', 'tool_use')):
            opener = Opener(provider_response(api, stop=stop))
            with self.subTest(api=api), tempfile.TemporaryDirectory() as directory, \
                 patch.dict(os.environ, environment(api), clear=True), \
                 patch('skilldemo.runtime.urllib.request.build_opener', return_value=opener), \
                 patch('skilldemo.runtime.initialize') as init:
                with self.assertRaises(runtime.RuntimeFailure) as caught:
                    runtime.OpenClawAgent().run('learn', frozen_payload(), Path(directory) / 'tool-stop')
                self.assertEqual(caught.exception.result['status'], 'INCOMPLETE')
                self.assertEqual(caught.exception.result['modelRequestStarts'], 1)
                self.assertEqual(len(opener.calls), 1)
                init.assert_not_called()


if __name__ == '__main__':
    unittest.main()
