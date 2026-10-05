"""The versioned parser is wired only to the frozen stage-9 contract."""
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch

from skilldemo.core import Loop
from skilldemo.learning import VERSION, freeze_approved_proposals
from skilldemo.runtime import ReplayAgent, digest
from test_prebound_evolution import selected, user_rule_payload


class FrozenSelectionCoreTests(unittest.TestCase):
    def run_candidate(self, payload, text):
        payload = {**payload, 'algorithm':VERSION}
        with tempfile.TemporaryDirectory() as directory:
            loop = Loop(directory, ReplayAgent())
            candidate = {'id':'parser-fixture', 'owner':'alice', 'status':'QUEUED',
                'mode':'replay', 'action':'UPDATE', 'title':'冻结范围测试',
                'input':payload, 'baseHash':digest(payload['initial_files'])}
            with loop.store.tx() as db:
                loop.store.put(db, 'candidate', candidate)
            reply = {'text':text, 'raw':{'providerReply':text}}
            with patch.object(loop, '_current', return_value=None), \
                    patch.object(loop, '_reserve', return_value=True), \
                    patch.object(loop, '_execute', return_value=reply):
                result = loop.generate('alice', candidate['id'])
            with loop.store.tx() as db:
                stored = loop.store.get(db, 'patchset', 'patchset-'+candidate['id'])
            return result, stored, reply

    def test_new_contract_accepts_one_json_block_and_persists_raw_format_audit(self):
        payload = freeze_approved_proposals(user_rule_payload())
        selection = selected(payload)
        text = '更新单元已选择。\n```json\n'+json.dumps(selection, ensure_ascii=False)+'\n```\n以上为冻结提议。'
        result, stored, reply = self.run_candidate(payload, text)
        self.assertEqual(result['status'], 'READY')
        audit = result['patchAudit']['formatParserAudit']
        self.assertEqual(audit['strategy'], 'UNIQUE_JSON_FENCE')
        self.assertEqual(audit['originalTextSha256'], hashlib.sha256(text.encode('utf-8')).hexdigest())
        self.assertEqual(stored['formatParserAudit'], audit)
        self.assertEqual(reply['text'], text)
        self.assertEqual(reply['raw']['providerReply'], text)

    def test_new_contract_still_rejects_selection_outside_frozen_units(self):
        payload = freeze_approved_proposals(user_rule_payload())
        selection = selected(payload)
        selection['mergedPatches'][0]['proposalIds'][0] = 'unapproved-unit'
        text = '说明\n```json\n'+json.dumps(selection)+'\n```\n结束'
        result, stored, reply = self.run_candidate(payload, text)
        self.assertEqual(result['status'], 'FAILED')
        self.assertIn('未获准', result['error'])
        self.assertIsNone(stored)
        self.assertEqual(reply['text'], text)

    def test_legacy_contract_keeps_its_existing_whole_reply_parser(self):
        payload = user_rule_payload()
        text = '说明\n```json\n{"decision":"DEFER"}\n```\n结束'
        result, stored, reply = self.run_candidate(payload, text)
        self.assertEqual(result['status'], 'FAILED')
        self.assertNotIn('patchAudit', result)
        self.assertIsNone(stored)
        self.assertEqual(reply['text'], text)


if __name__ == '__main__':
    unittest.main()
