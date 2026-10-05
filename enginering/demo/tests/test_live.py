import json
import os
from pathlib import Path
import sqlite3
import hashlib
import tempfile
import unittest
from unittest.mock import patch
from skilldemo.live import creator_read_evidence, file_read_evidence, load_env, read_evidence, skill_manifest
from skilldemo.core import Loop
from skilldemo.runtime import ReplayAgent

class LiveTests(unittest.TestCase):
    def creator_files(self, root, text='official instructions\n'):
        workspace=root/'workspace';entry=workspace/'.foundation/skill-creator/SKILL.md'
        official=root/'pinned-install/skill-creator/SKILL.md'
        for p in [entry,official]:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(text.encode('utf-8'))
        return workspace,entry,official,hashlib.sha256(entry.read_bytes()).hexdigest()

    def test_creator_alias_requires_exact_pinned_official_path_and_preserves_provenance(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);workspace,entry,official,pin=self.creator_files(root)
            tool=self.read_tool(workspace,'','official instructions\n',name='read',arguments={'path':str(official)})
            with patch('skilldemo.live.CREATOR',official.parent):
                self.assertIsNone(file_read_evidence(tool,workspace,official))
                receipt=creator_read_evidence(tool,workspace,pin)
                self.assertEqual(receipt['readRange']['status'],'FULL_FILE')
                self.assertEqual(receipt['actualPath'],str(official.resolve()))
                self.assertEqual(receipt['expectedEntry'],'.foundation/skill-creator/SKILL.md')
                self.assertEqual(receipt['sourceAlias'],'PINNED_OFFICIAL_INSTALL')
                self.assertEqual(receipt['aliasBasis'],'EXACT_PINNED_PATH_AND_INITIALIZED_TWO_FILE_SHA256')
                other=root/'unapproved/SKILL.md';other.parent.mkdir();other.write_bytes(entry.read_bytes())
                self.assertIsNone(creator_read_evidence({**tool,'arguments':{'path':str(other)}},workspace,pin))

    def test_creator_alias_rejects_missing_pin_hash_mismatch_and_simultaneous_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);workspace,entry,official,pin=self.creator_files(root)
            tool=self.read_tool(workspace,'','official instructions\n',name='read',arguments={'file_path':str(official)})
            with patch('skilldemo.live.CREATOR',official.parent):
                self.assertIsNone(creator_read_evidence(tool,workspace))
                self.assertIsNone(creator_read_evidence(tool,workspace,'0'*64))
                official.write_text('mutated',encoding='utf-8')
                self.assertIsNone(creator_read_evidence(tool,workspace,pin))
                entry.write_text('mutated',encoding='utf-8')
                self.assertIsNone(creator_read_evidence(tool,workspace,pin))

    def test_creator_workspace_read_remains_compatible_without_alias_pin(self):
        with tempfile.TemporaryDirectory() as d:
            workspace,entry,official,pin=self.creator_files(Path(d))
            tool=self.read_tool(workspace,'','official instructions\n',name='read',arguments={'path':str(entry)})
            receipt=creator_read_evidence(tool,workspace)
            self.assertEqual(receipt['sourceAlias'],'WORKSPACE_FOUNDATION')
            self.assertEqual(receipt['actualPath'],str(entry.resolve()))
            self.assertIsNone(creator_read_evidence(tool,workspace,'0'*64))

    def test_creator_alias_exec_still_requires_exact_command_output_and_workdir(self):
        with tempfile.TemporaryDirectory() as d:
            workspace,entry,official,pin=self.creator_files(Path(d))
            command=f'Get-Content -Path "{official}" -Encoding utf8 -TotalCount 300'
            tool=self.read_tool(workspace,command,'official instructions')
            with patch('skilldemo.live.CREATOR',official.parent):
                self.assertEqual(creator_read_evidence(tool,workspace,pin)['readRange']['status'],'FULL_FILE')
                self.assertIsNone(creator_read_evidence({**tool,'result':json.dumps([{'type':'text','text':'read error'}])},workspace,pin))
                self.assertIsNone(creator_read_evidence({**tool,'arguments':{**tool['arguments'],'workdir':str(workspace.parent)}},workspace,pin))

    def test_creator_receipts_are_verified_before_public_result_storage_truncation(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);text=('complete instructions\n'*600)
            workspace,entry,official,pin=self.creator_files(root,text)
            state=root/'state';dbpath=state/'agents/main/agent/openclaw-agent.sqlite';dbpath.parent.mkdir(parents=True)
            events=[{'message':{'role':'assistant','content':[{'type':'toolCall','id':'c','name':'read','arguments':{'path':str(official)}}]}},
                    {'message':{'role':'toolResult','toolCallId':'c','isError':False,'content':[{'type':'text','text':text}]}}]
            with sqlite3.connect(dbpath) as db:
                db.execute('CREATE TABLE transcript_events(session_id TEXT,seq INTEGER,event_json TEXT)')
                db.executemany('INSERT INTO transcript_events VALUES(?,?,?)',[('run',i,json.dumps(e)) for i,e in enumerate(events)])
            db.close()
            with patch('skilldemo.live.CREATOR',official.parent):
                result=read_evidence(state,'run',workspace,[],creator=True,creator_sha256=pin)
            self.assertTrue(result['tools'][0]['resultTruncated'])
            self.assertEqual(result['creatorReads'][0]['readRange']['status'],'FULL_FILE')
            self.assertEqual(result['creatorReads'][0]['readRange']['fileBytes'],len(text.encode('utf-8')))

    def read_tool(self, workspace, command, text, **overrides):
        tool={'id':'read-call','name':'exec','status':'SUCCEEDED',
              'arguments':{'command':command,'workdir':str(workspace)},
              'result':json.dumps([{'type':'text','text':text}]),'resultTruncated':False,
              'recordBasis':'OPENCLAW_TRANSCRIPT_CALL_RESULT',
              'callSourceOrder':3,'resultSourceOrder':4}
        tool.update(overrides)
        return tool

    def test_get_content_matches_exact_entry_and_verifies_full_line_output(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);entry=root/'.foundation/skill-creator/SKILL.md'
            entry.parent.mkdir(parents=True);entry.write_bytes(b'first\n\nlast\n')
            tool=self.read_tool(root,'Get-Content -Path ".foundation\\skill-creator\\SKILL.md" -TotalCount 300',
                                'first\r\n\r\nlast')
            receipt=file_read_evidence(tool,root,entry)
            self.assertEqual(receipt['readMethod'],'POWERSHELL_GET_CONTENT')
            self.assertEqual(receipt['readRange']['status'],'FULL_FILE')
            self.assertEqual(receipt['readRange']['fileLineCount'],3)
            self.assertEqual(receipt['recordBasis'],tool['recordBasis'])
            self.assertEqual(receipt['toolCallId'],'read-call')

    def test_get_content_raw_and_literal_path_are_supported(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);entry=root/'SKILL.md';entry.write_bytes(b' first \n\nlast\n')
            tool=self.read_tool(root,"get-content -LiteralPath 'SKILL.md' -Encoding utf8 -Raw",' first \n\nlast\n')
            self.assertEqual(file_read_evidence(tool,root,entry)['readRange']['status'],'FULL_FILE')

    def test_get_content_allowlisted_options_can_precede_or_follow_one_quoted_path(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);entry=root/'SKILL.md';entry.write_bytes(b'one\ntwo\n')
            commands=[
                'Get-Content -Encoding UTF8 -Path "SKILL.md" -TotalCount 300',
                "Get-Content -TotalCount 300 -LiteralPath 'SKILL.md' -Encoding utf8",
                'Get-Content -Raw -Encoding utf8 -Path "SKILL.md"',
                "Get-Content -Encoding utf8 'SKILL.md' -TotalCount 300",
                'Get-Content "SKILL.md" -Raw -Encoding UTF8',
            ]
            for command in commands:
                with self.subTest(command=command):
                    output='one\ntwo\n' if '-Raw' in command else 'one\ntwo'
                    receipt=file_read_evidence(self.read_tool(root,command,output),root,entry)
                    self.assertEqual(receipt['readRange']['status'],'FULL_FILE')

    def test_absolute_exact_path_can_prove_exec_read_without_workdir(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);entry=root/'SKILL.md';entry.write_bytes(b'one\ntwo\n')
            command=f'Get-Content -Encoding UTF8 -Path "{entry}"'
            tool=self.read_tool(root,command,'one\ntwo',arguments={'command':command})
            self.assertEqual(file_read_evidence(tool,root,entry)['readRange']['status'],'FULL_FILE')
            self.assertIsNone(file_read_evidence({**tool,'result':json.dumps([{'type':'text','text':'read error'}])},root,entry))
            tool['arguments']['command']='Get-Content -Encoding UTF8 -Path "SKILL.md"'
            self.assertIsNone(file_read_evidence(tool,root,entry))

    def test_bounded_output_is_partial_and_never_full_from_count_alone(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);entry=root/'SKILL.md';entry.write_text('one\ntwo\nthree\n',encoding='utf-8')
            tool=self.read_tool(root,'Get-Content -Path "SKILL.md" -TotalCount 2','one\ntwo')
            receipt=file_read_evidence(tool,root,entry)
            self.assertEqual(receipt['readRange']['status'],'PARTIAL')
            tool['arguments']['command']='Get-Content -Path "SKILL.md" -TotalCount 300'
            self.assertIsNone(file_read_evidence(tool,root,entry))

    def test_full_verification_does_not_strip_content_or_accept_truncated_output(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);entry=root/'SKILL.md';entry.write_text(' first \n\nlast\n',encoding='utf-8')
            for body,truncated in [('first\nlast',False),(' first \n\nlast',True)]:
                with self.subTest(body=body,truncated=truncated):
                    tool=self.read_tool(root,'Get-Content -Path "SKILL.md"',body,resultTruncated=truncated)
                    self.assertIsNone(file_read_evidence(tool,root,entry))

    def test_exec_success_without_verified_file_output_does_not_prove_read(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);entry=root/'SKILL.md';entry.write_text('required content',encoding='utf-8')
            for body in ['Get-Content: Cannot find path SKILL.md because it does not exist.',
                         'required content\nCommand exited with code 0','required']:
                with self.subTest(body=body):
                    self.assertIsNone(file_read_evidence(self.read_tool(root,'Get-Content -Path "SKILL.md"',body),root,entry))

    def test_exec_grammar_rejects_chains_expansions_wildcards_and_multiple_paths(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);entry=root/'SKILL.md';entry.write_text('ok',encoding='utf-8')
            commands=[
                'Get-Content -Path "SKILL.md"; Write-Output ok',
                'Get-Content -Path "SKILL.md" | Out-String',
                'Get-Content -Path "SKILL.md" > output.txt',
                'Get-Content -Path "SKILL.md"\nWrite-Output ok',
                'Get-Content -Path "$file"',
                'Get-Content -Path "$(Get-Location)/SKILL.md"',
                'Get-Content -Path "`SKILL.md"',
                'Get-Content -LiteralPath "S*.md"',
                'Get-Content -Path "SKILL.md", "other.md"',
                'Get-Content -Path "SKILL.md" -Tail 1',
                'Get-Content -Path "SKILL.md" -Raw -TotalCount 2',
                'Get-Content -Path "SKILL.md" -Encoding utf16',
                'Get-Content -Path "SKILL.md" -TotalCount 0',
                'Get-Content -Path "SKILL.md" -TotalCount 2 -TotalCount 3',
                'Get-Content -Path "SKILL.md" -LiteralPath "SKILL.md"',
                'Get-Content "SKILL.md" "other.md"',
                'Get-Content -Encoding UTF8 -Path "SKILL.md" -Encoding UTF8',
                'Get-Content -Raw -Path "SKILL.md" -Raw',
                'gc -Path "SKILL.md"',
            ]
            for command in commands:
                with self.subTest(command=command):
                    self.assertIsNone(file_read_evidence(self.read_tool(root,command,'ok'),root,entry))

    def test_exec_requires_explicit_matching_workdir_success_and_native_basis(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);entry=root/'SKILL.md';entry.write_text('ok',encoding='utf-8')
            base=self.read_tool(root,'Get-Content -Path "SKILL.md"','ok')
            for change in [{'arguments':{'command':base['arguments']['command']}},
                           {'arguments':{**base['arguments'],'workdir':str(root/'other')}},
                           {'status':'FAILED'},{'status':'UNKNOWN'},{'recordBasis':'ASSISTANT_CLAIM'},
                           {'arguments':{**base['arguments'],'command':'Get-Content -Path "other.md"'}}]:
                with self.subTest(change=change):
                    self.assertIsNone(file_read_evidence({**base,**change},root,entry))

    def test_read_tool_compatibility_preserves_unknown_and_bounded_ranges(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);entry=root/'SKILL.md';entry.write_text('one\ntwo',encoding='utf-8')
            tool=self.read_tool(root,'','',name='read',arguments={'file_path':'SKILL.md'})
            self.assertEqual(file_read_evidence(tool,root,entry)['readMethod'],'READ_TOOL')
            self.assertEqual(file_read_evidence(tool,root,entry)['readRange']['status'],'UNKNOWN')
            tool['arguments']['limit']=1
            self.assertEqual(file_read_evidence(tool,root,entry)['readRange']['status'],'PARTIAL')

    def test_selected_skill_audit_accepts_native_get_content_and_records_range(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);entry=root/'skills/s/SKILL.md';entry.parent.mkdir(parents=True);entry.write_text('line1\nline2\n',encoding='utf-8')
            state=root/'state';dbpath=state/'agents/main/agent/openclaw-agent.sqlite';dbpath.parent.mkdir(parents=True)
            events=[{'message':{'role':'assistant','content':[{'type':'toolCall','id':'c','name':'exec',
                     'arguments':{'command':'Get-Content -Path "skills/s/SKILL.md" -TotalCount 300','workdir':str(root)}}]}},
                    {'message':{'role':'toolResult','toolCallId':'c','isError':False,'content':[{'type':'text','text':'line1\r\nline2'}]}}]
            with sqlite3.connect(dbpath) as db:
                db.execute('CREATE TABLE transcript_events(session_id TEXT,seq INTEGER,event_json TEXT)')
                db.executemany('INSERT INTO transcript_events VALUES(?,?,?)',[('run',i,json.dumps(e)) for i,e in enumerate(events)])
            db.close()
            result=read_evidence(state,'run',root,[{'id':'s','version':1,'hash':'h'}])
            self.assertEqual(result['skills'][0]['status'],'FILE_READ')
            self.assertEqual(result['skills'][0]['receipts'][0]['readRange']['status'],'FULL_FILE')
            self.assertEqual(result['tools'][0]['recordBasis'],'OPENCLAW_TRANSCRIPT_CALL_RESULT')

    def test_selected_skill_version_identity_compares_expected_entry_text(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);entry=root/'skills/s/SKILL.md';entry.parent.mkdir(parents=True)
            entry.write_bytes(b'expected\r\ncontent\r\n')
            state=root/'state';dbpath=state/'agents/main/agent/openclaw-agent.sqlite';dbpath.parent.mkdir(parents=True)
            events=[{'message':{'role':'assistant','content':[{'type':'toolCall','id':'c','name':'read','arguments':{'path':str(entry)}}]}},
                    {'message':{'role':'toolResult','toolCallId':'c','isError':False,'content':[{'type':'text','text':'expected\r\ncontent\r\n'}]}}]
            with sqlite3.connect(dbpath) as db:
                db.execute('CREATE TABLE transcript_events(session_id TEXT,seq INTEGER,event_json TEXT)')
                db.executemany('INSERT INTO transcript_events VALUES(?,?,?)',[('run',i,json.dumps(e)) for i,e in enumerate(events)])
            db.close()
            skill={'id':'s','version':1,'hash':'bundle-hash','files':[{'path':'SKILL.md','content':'expected\ncontent\n'}]}
            receipt=read_evidence(state,'run',root,[skill])['skills'][0]
            self.assertEqual(receipt['status'],'FILE_READ')
            self.assertEqual(receipt['identity']['status'],'VERIFIED')
            self.assertEqual(receipt['receipts'][0]['expectedEntrySha256'],hashlib.sha256(skill['files'][0]['content'].encode('utf-8')).hexdigest())
            entry.write_text('mutated file',encoding='utf-8')
            changed=read_evidence(state,'run',root,[skill])['skills'][0]
            self.assertEqual(changed['status'],'READ_NOT_OBSERVED')
            self.assertEqual(changed['identity']['status'],'MISMATCH')
            compatibility=read_evidence(state,'run',root,[{k:v for k,v in skill.items() if k!='files'}])['skills'][0]
            self.assertEqual(compatibility['status'],'FILE_READ')
            self.assertEqual(compatibility['identity']['status'],'NOT_CHECKED')

    def test_config_does_not_override_environment_or_execute_values(self):
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ, {'DEMO_MODEL':'existing'}):
            p=Path(d)/'.env';p.write_text('DEMO_MODEL=other\nDEMO_TEST="$(not-executed)"',encoding='utf-8')
            load_env(p);self.assertEqual(os.environ['DEMO_MODEL'],'existing')
            self.assertEqual(os.environ['DEMO_TEST'],'$(not-executed)')

    def test_manifest_contains_no_skill_content_or_history(self):
        s={'id':'s','title':'S','version':1,'hash':'h','files':[{'path':'SKILL.md','content':'SECRET-CONTROL'}]}
        self.assertNotIn('SECRET-CONTROL',json.dumps(skill_manifest([s])))

    def test_read_evidence_requires_matching_session_path_and_success(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);state=root/'state';dbpath=state/'agents/main/agent/openclaw-agent.sqlite'
            dbpath.parent.mkdir(parents=True)
            events=[{'message':{'role':'assistant','content':[{'type':'toolCall','id':'c','name':'read','arguments':{'path':'skills/s/SKILL.md'}}]}},
                    {'message':{'role':'toolResult','toolCallId':'c','isError':False}}]
            with sqlite3.connect(dbpath) as db:
                db.execute('CREATE TABLE transcript_events(session_id TEXT,seq INTEGER,event_json TEXT)')
                db.executemany('INSERT INTO transcript_events VALUES(?,?,?)',[('run',i,json.dumps(e)) for i,e in enumerate(events)])
            db.close()
            skills=[{'id':'s','version':1,'hash':'h'}]
            evidence=read_evidence(state,'run',root,skills)
            self.assertEqual(evidence['skills'][0]['status'],'FILE_READ')
            self.assertEqual(evidence['tools'][0]['callSourceOrder'],0)
            self.assertEqual(evidence['tools'][0]['resultSourceOrder'],1)
            self.assertEqual(read_evidence(state,'other',root,skills)['skills'][0]['status'],'READ_NOT_OBSERVED')

    def test_absent_transcript_is_unknown(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(read_evidence(Path(d),'run',Path(d),[])['status'],'UNKNOWN')

    def test_real_mode_cannot_attribute_update_without_read_receipt(self):
        class NoReadAgent(ReplayAgent):
            mode='openclaw'
        with tempfile.TemporaryDirectory() as d:
            loop=Loop(Path(d),NoReadAgent(),settle_seconds=0)
            loop.chat('alice','a','整理报告，必须核对退款')
            loop.tick();c=loop.discover('alice')[0];loop.generate('alice',c['id']);s=loop.accept('alice',c['id'])
            loop.chat('alice','a','新任务：整理报告',[s['id']])
            loop.chat('alice','a','不对，必须单独列出跨期退款')
            loop.tick();self.assertEqual(loop.discover('alice'),[])
            self.assertEqual(loop.snapshot('alice')['traces'][-1]['decision']['reason'],'SKILL_ATTRIBUTION_UNCLEAR')
