"""Frozen selection parsing accepts complete, unambiguous JSON objects only.

Synthetic local responses exercise parser boundaries and audit provenance;
they do not make provider calls or change the legacy response contract.
"""
import hashlib
import unittest

from skilldemo import learning
from skilldemo.runtime import parse_object


class FrozenSelectionParserTests(unittest.TestCase):
    def parse_selection(self, text):
        parser = getattr(learning, 'parse_frozen_selection', None)
        self.assertTrue(callable(parser), 'learning.parse_frozen_selection is required')
        return parser(text)

    def assert_audit(self, audit, text, strategy=None):
        self.assertIsInstance(audit, dict)
        self.assertEqual(audit.get('version'), 'frozen-selection-parser-v1')
        self.assertEqual(
            audit.get('originalTextSha256'),
            hashlib.sha256(text.encode('utf-8')).hexdigest(),
        )
        if strategy is None:
            self.assertIn(audit.get('strategy'), ('STRICT_PARSE_OBJECT', 'UNIQUE_JSON_FENCE'))
        else:
            self.assertEqual(audit.get('strategy'), strategy)

    def test_complete_json_object_uses_strict_parser_and_hashes_unstripped_text(self):
        text = ' \n {"decision":"UPDATE","selections":[],"说明":"原文 { } 保留"} \n\t'
        obj, audit = self.parse_selection(text)
        self.assertEqual(obj, {'decision': 'UPDATE', 'selections': [], '说明': '原文 { } 保留'})
        self.assert_audit(audit, text, 'STRICT_PARSE_OBJECT')
        self.assertNotEqual(audit['originalTextSha256'], hashlib.sha256(text.strip().encode('utf-8')).hexdigest())

    def test_complete_explicit_json_fence_is_accepted(self):
        text = '```json\n{"decision":"DEFER","reason":"无唯一位置"}\n```'
        obj, audit = self.parse_selection(text)
        self.assertEqual(obj, {'decision': 'DEFER', 'reason': '无唯一位置'})
        self.assert_audit(audit, text)

    def test_unique_json_fence_in_chinese_prose_has_complete_raw_offsets(self):
        prefix = '  说明：已核对获准单元。\n\n'
        fence = '```json\n{"decision":"UPDATE","selections":[{"id":"单元一"}]}\n```'
        suffix = '\n\n后记：采用以上选择。  \n'
        text = prefix + fence + suffix
        obj, audit = self.parse_selection(text)
        self.assertEqual(obj, {'decision': 'UPDATE', 'selections': [{'id': '单元一'}]})
        self.assert_audit(audit, text, 'UNIQUE_JSON_FENCE')
        self.assertEqual(audit.get('fenceStart'), len(prefix))
        self.assertEqual(audit.get('fenceEnd'), len(prefix) + len(fence))
        self.assertEqual(text[audit['fenceStart']:audit['fenceEnd']], fence)

    def test_braces_inside_json_strings_are_not_guessed_as_boundaries(self):
        text = '说明。\n```json\n{"reason":"字符 { 及 } 属于说明","selections":[]}\n```\n后记。'
        obj, audit = self.parse_selection(text)
        self.assertEqual(obj, {'reason': '字符 { 及 } 属于说明', 'selections': []})
        self.assert_audit(audit, text, 'UNIQUE_JSON_FENCE')

    def test_multiple_fenced_blocks_are_rejected_even_when_one_is_not_json(self):
        responses = (
            '```json\n{}\n```\n```json\n{}\n```',
            '说明。\n```json\n{}\n```\n```text\n解释\n```',
            '```\n{}\n```\n```json\n{}\n```',
        )
        for text in responses:
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.parse_selection(text)

    def test_complete_unmarked_fences_are_rejected_without_changing_legacy(self):
        bare = '```\n{"decision":"DEFER"}\n```'
        self.assertEqual(parse_object(bare), {'decision': 'DEFER'})
        for text in (bare, '说明。\n' + bare + '\n后记。'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.parse_selection(text)

    def test_truncated_json_or_fence_is_rejected(self):
        responses = (
            '{"decision":"UPDATE"',
            '说明。\n```json\n{"decision":"UPDATE"}\n',
            '```json\n{"decision":"UPDATE"\n```',
            '说明。\n```json\n{"decision":"UPDATE"}\n``',
        )
        for text in responses:
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.parse_selection(text)

    def test_unfenced_embedded_object_or_brace_substrings_are_rejected(self):
        responses = (
            '说明：{"decision":"DEFER"}，请按以上处理。',
            '说明。\n{"decision":"DEFER"}\n后记。',
            '文字 {提示} 以及 {"decision":"DEFER"}',
        )
        for text in responses:
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.parse_selection(text)

    def test_json_fence_requires_an_object(self):
        for body in ('[]', '[{}]', 'null', '"DEFER"', '1', 'true'):
            text = '说明。\n```json\n' + body + '\n```\n后记。'
            with self.subTest(body=body), self.assertRaises(ValueError):
                self.parse_selection(text)

    def test_complete_json_also_requires_an_object(self):
        for text in ('[]', '[{}]', 'null', '"DEFER"', '1', 'true'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.parse_selection(text)

    def test_fenced_non_json_and_trailing_garbage_are_rejected(self):
        for body in ("{'decision':'DEFER'}", '{"decision":"DEFER",}', '{} trailing', '{}\n{}'):
            text = '说明。\n```json\n' + body + '\n```\n后记。'
            with self.subTest(body=body), self.assertRaises(ValueError):
                self.parse_selection(text)

    def test_fence_must_have_standalone_opening_and_closing_lines(self):
        responses = (
            '说明 ```json\n{}\n```\n后记。',
            '说明。\n```json\n{}\n``` 后记。',
            '```json{}\n```',
        )
        for text in responses:
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.parse_selection(text)


if __name__ == '__main__':
    unittest.main()
