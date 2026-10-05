import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from skilldemo.runtime import OpenClawAgent, request_config, digest
from skilldemo.creator import parse_creator_result


class StructuredOutputTests(unittest.TestCase):
    def test_single_json_fence_with_commentary_is_losslessly_parsed(self):
        obj = {'decision': 'CREATE', 'coverageManifest': [{'methodId': 'm1'}]}
        raw = json.dumps(obj)
        for text in (raw, '```json\n'+raw+'\n```',
                     'I have verified the written file.\n\n```json\n'+raw+'\n```\nDone.'):
            self.assertEqual(parse_creator_result(text), obj)

    def test_multiple_alternatives_and_incomplete_json_are_rejected(self):
        for text in ('```json\n{}\n```\n```json\n{}\n```',
                     'Explanation.\n```json\n{"decision":\n```',
                     'Explanation.\n```json\n{}', '```json\n[]\n```'):
            with self.assertRaises(ValueError):
                parse_creator_result(text)


class RequestAuditTests(unittest.TestCase):
    def test_actual_request_and_response_are_preserved_without_credentials(self):
        raw = {'model':'audit-model','content':[{'type':'text','text':'{"sourceHash":"x"}'}],
               'stop_reason':'end_turn','usage':{'input_tokens':12,'output_tokens':6}}

        class Response:
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def read(self): return json.dumps(raw).encode()

        class Opener:
            def open(self, request, timeout):
                self.request, self.timeout = request, timeout
                return Response()

        opener = Opener()
        env = {'DEMO_MODEL':'audit-model','DEMO_API_KEY':'fixture-secret',
               'DEMO_MODEL_API':'anthropic-messages','DEMO_BASE_URL':'https://fixture.invalid/anthropic',
               'DEMO_DETECT_TIMEOUT':'180'}
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ,env), \
             patch('urllib.request.build_opener',return_value=opener):
            result = OpenClawAgent().run('detect_pairs',{'sourceHash':'x','pairs':[]},Path(directory))
            saved = json.loads((Path(directory)/'request.json').read_text(encoding='utf-8'))
            self.assertEqual(saved['body'],json.loads(opener.request.data))
            self.assertEqual(saved['config']['timeoutSeconds'],opener.timeout)
            self.assertEqual(saved['config']['maxTokens'],saved['body']['max_tokens'])
            self.assertEqual(json.loads((Path(directory)/'response.json').read_text()),raw)
            self.assertNotIn('fixture-secret',(Path(directory)/'request.json').read_text(encoding='utf-8'))
            self.assertEqual(result['usage']['total'],18)
            identity = digest(request_config('detect_pairs'))
            with patch.dict(os.environ,{'DEMO_MODEL':'different-model'}):
                self.assertNotEqual(identity,digest(request_config('detect_pairs')))


if __name__ == '__main__': unittest.main()
