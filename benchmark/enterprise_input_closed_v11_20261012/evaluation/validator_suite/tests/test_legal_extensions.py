"""Offline positive/negative/unknown controls for the approved basic extensions."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
import zipfile

SUITE = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
SOURCE = SUITE / "vendor/final_state_scorer.py"
EXTENSIONS = SUITE / "_extensions.py"
SID = "legal_extension_fixture"
SOURCE_JOB_ID = "fd4a7d47-dcb1-42a2-981e-95b2a91aea92"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_engine():
    source = SUITE / "vendor/final_state_scorer.py"
    base = load_module("legal_fixture_base", source if source.is_file() else SOURCE)
    if EXTENSIONS.is_file():
        load_module("legal_fixture_extensions", EXTENSIONS).register_extensions(base)
    return base


def contract(kind, parameters, deliveries=None, did="d1"):
    return {
        "sid": SID,
        "score_at": "conversation_end_only",
        "actor_can_see_historical_ai": False,
        "quality_scored": False,
        "intermediate_steps_scored": False,
        "manual_judgement_scored": False,
        "final_deliverables": deliveries or [{"id": did, "kind": "file"}],
        "checks": [{"delivery_id": did, "kind": kind, "parameters": parameters}],
    }


class LegalExtensionTests(unittest.TestCase):
    def setUp(self):
        self.base = load_engine()
        self.temp = tempfile.TemporaryDirectory(prefix="legal-extension-fixture-")
        self.root = Path(self.temp.name)
        initial_bytes = json.dumps({"source": SID, "workspace_empty": True}).encode()
        self.evidence = {
            "schema": "final-state-evidence-v1",
            "source_session_id": SID,
            "conversation_complete": True,
            "workspace": str(self.root),
            "initial_sha256": {},
            "declared_input_sha256": {},
            "fixture_initial_snapshot_sha256": hashlib.sha256(initial_bytes).hexdigest(),
            "deliveries": {},
        }

    def tearDown(self):
        self.temp.cleanup()

    def write(self, name, payload="本次实际交付正文"):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")
        return path

    def bind(self, did, *paths):
        self.evidence["deliveries"][did] = {"files": [str(p) for p in paths]}

    def score(self, c):
        return self.base.score_request({
            "task_id": SID,
            "workspace": str(self.root),
            "final_contract": c,
            "evidence": self.evidence,
            "result": {"evidence_collection_required": True},
        })

    def assert_status(self, c, expected):
        result = self.score(c)
        self.assertEqual(result["checks"][0]["status"], expected, result)
        if expected == "unknown":
            self.assertFalse(result["valid"])
            self.assertIsNone(result["score"])
        else:
            self.assertTrue(result["valid"], result)
            self.assertEqual(result["score"], 1.0 if expected == "pass" else 0.0)
        return result

    def invoke(self, c):
        ctx = self.base.Context({
            "task_id": SID, "workspace": str(self.root), "evidence": self.evidence
        }, c)
        check = c["checks"][0]
        handler = self.base.HANDLERS.get(check["kind"])
        if handler is None:
            raise self.base.UnknownEvidence("validator_not_implemented")
        return handler(ctx, check["delivery_id"], check["parameters"], check["kind"])

    def two_files_contract(self, count=2, ids=None):
        return contract("final_distinct_artifact_objects", {
            "delivery_ids": ["d1", "d2"] if ids is None else ids,
            "required_distinct_object_count": count,
        }, [{"id": "d1", "kind": "file", "format": "md"},
            {"id": "d2", "kind": "file", "format": "md"}])

    def test_distinct_same_content_different_files_pass(self):
        self.bind("d1", self.write("one.md", "相同内容"))
        self.bind("d2", self.write("two.md", "相同内容"))
        self.assert_status(self.two_files_contract(), "pass")

    def test_distinct_same_path_fails(self):
        path = self.write("one.md")
        self.bind("d1", path)
        self.bind("d2", path)
        self.assert_status(self.two_files_contract(), "fail")

    def test_distinct_dot_path_alias_fails(self):
        path = self.write("one.md")
        (self.root / "alias").mkdir()
        self.bind("d1", path)
        self.bind("d2", self.root / "alias/../one.md")
        self.assert_status(self.two_files_contract(), "fail")

    def test_distinct_hard_link_is_same_object(self):
        path = self.write("one.md")
        alias = self.root / "linked.md"
        os.link(path, alias)
        self.bind("d1", path)
        self.bind("d2", alias)
        self.assert_status(self.two_files_contract(), "fail")

    def test_distinct_count_is_really_checked(self):
        self.bind("d1", self.write("one.md"))
        self.bind("d2", self.write("two.md"))
        self.assert_status(self.two_files_contract(count=3), "fail")

    def test_distinct_unbound_targets_unknown(self):
        self.evidence.pop("deliveries")
        c = self.two_files_contract()
        result = self.base.score_request({
            "task_id": SID, "workspace": str(self.root), "final_contract": c,
            "evidence": self.evidence,
            "result": {"artifacts": [str(self.write("one.md"))]},
        })
        self.assertEqual(result["checks"][0]["status"], "unknown", result)

    def test_distinct_outside_attempt_unknown(self):
        path = self.write("one.md")
        self.bind("d1", path)
        self.bind("d2", self.root.parent / "outside.md")
        self.assert_status(self.two_files_contract(), "unknown")

    def test_distinct_invalid_ids_unknown(self):
        self.bind("d1", self.write("one.md"))
        self.bind("d2", self.write("two.md"))
        self.assert_status(self.two_files_contract(ids=["d1", "d1"]), "unknown")

    def test_distinct_unknown_hard_parameter_not_ignored(self):
        self.bind("d1", self.write("one.md"))
        self.bind("d2", self.write("two.md"))
        c = self.two_files_contract()
        c["checks"][0]["parameters"]["pretend_policy"] = True
        self.assert_status(c, "unknown")

    def test_distinct_bool_count_is_invalid_contract(self):
        self.bind("d1", self.write("one.md"))
        self.bind("d2", self.write("two.md"))
        self.assert_status(self.two_files_contract(count=True), "unknown")

    def test_declared_policy_metadata_is_compatible(self):
        self.bind("d1", self.write("one.md"))
        self.bind("d2", self.write("two.md"))
        c = self.two_files_contract()
        c["checks"][0]["parameters"].update(
            score_at="conversation_end_only", historical_ai_is_gold=False)
        self.assert_status(c, "pass")

    def directory_contract(self):
        return contract("final_artifact_parent_directory", {"directory_label": "学生资料"})

    def mapping(self, path, **updates):
        value = {
            "label": "学生资料", "path": str(path), "source_session_id": SID,
            "authoritative": True, "origin": "frozen_environment_directory_mapping",
        }
        value.update(updates)
        self.evidence.setdefault("resolved_parameters", {})["d1"] = {
            "directory_binding": value
        }

    def test_directory_verified_mapping_nested_file_passes(self):
        root = self.root / "knowledge/学生资料"
        self.bind("d1", self.write("knowledge/学生资料/sub/final.md"))
        self.mapping(root)
        self.assert_status(self.directory_contract(), "pass")

    def test_directory_other_same_basename_fails(self):
        mapped = self.root / "knowledge/学生资料"
        mapped.mkdir(parents=True)
        self.bind("d1", self.write("other/学生资料/final.md"))
        self.mapping(mapped)
        self.assert_status(self.directory_contract(), "fail")

    def test_directory_missing_physical_root_fails(self):
        self.bind("d1", self.write("elsewhere.md"))
        self.mapping(self.root / "missing")
        self.assert_status(self.directory_contract(), "fail")

    def test_directory_missing_mapping_unknown(self):
        self.bind("d1", self.write("学生资料/final.md"))
        self.assert_status(self.directory_contract(), "unknown")

    def test_directory_actor_inferred_mapping_unknown(self):
        root = self.root / "学生资料"
        self.bind("d1", self.write("学生资料/final.md"))
        self.mapping(root, origin="actor_delivery_claim")
        self.assert_status(self.directory_contract(), "unknown")

    def test_directory_wrong_source_unknown(self):
        self.bind("d1", self.write("学生资料/final.md"))
        self.mapping(self.root / "学生资料", source_session_id="another_source")
        self.assert_status(self.directory_contract(), "unknown")

    def test_directory_mapping_outside_workspace_unknown(self):
        self.bind("d1", self.write("student.md"))
        self.mapping(self.root.parent)
        self.assert_status(self.directory_contract(), "unknown")

    def docx(self, name, table=False, alt_chunk=False, revision=False):
        body = '<w:p><w:r><w:t>实际文档正文</w:t></w:r></w:p>'
        if table:
            body += '<w:tbl><w:tr><w:tc><w:p><w:r><w:t>表格</w:t></w:r></w:p></w:tc></w:tr></w:tbl>'
        if alt_chunk:
            body += '<w:altChunk r:id="external-body"/>'
        if revision:
            body += '<w:ins w:id="1"><w:r><w:t>修改</w:t></w:r></w:ins>'
        path = self.root / name
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("[Content_Types].xml",
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
            archive.writestr("word/document.xml",
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                '<w:body>' + body + '</w:body></w:document>')
        return path

    def no_tables_contract(self):
        return contract("final_native_document_no_tables", {"non_docx_policy": "report_only"})

    def test_no_table_native_docx_passes(self):
        self.bind("d1", self.docx("plain.docx"))
        self.assert_status(self.no_tables_contract(), "pass")

    def test_no_table_native_docx_table_fails(self):
        self.bind("d1", self.docx("table.docx", table=True))
        self.assert_status(self.no_tables_contract(), "fail")

    def test_no_table_unparsed_altchunk_unknown(self):
        self.bind("d1", self.docx("chunk.docx", alt_chunk=True))
        self.assert_status(self.no_tables_contract(), "unknown")

    def test_no_table_pdf_is_report_only(self):
        from reportlab.pdfgen import canvas
        path = self.root / "final.pdf"
        document = canvas.Canvas(str(path))
        document.drawString(36, 700, "actual nonempty PDF")
        document.save()
        self.bind("d1", path)
        observed = self.invoke(self.no_tables_contract())
        self.assertIs(observed["scorable"], False)
        self.assertIs(observed["applicable_to_AND"], False)
        self.assertIs(observed["applicable"], False)
        self.assertEqual(observed["actual_formats"], ["pdf"])

    def test_pdf_observation_runtime_not_reported_as_pass(self):
        from reportlab.pdfgen import canvas
        path = self.root / "observed.pdf"
        document = canvas.Canvas(str(path))
        document.drawString(36, 700, "actual PDF delivery")
        document.save()
        self.bind("d1", path)
        c = self.no_tables_contract()
        c["checks"].insert(0, {"delivery_id": "d1", "kind": "final_file_native_open",
                               "parameters": {"allowed_formats": ["pdf"]}})
        runtime = load_module("legal_runtime_integration", SUITE / "_runtime.py")
        result = runtime.score_task_request({
            "task_id": SID, "source_session_id": SID, "workspace": str(self.root),
            "evidence": self.evidence, "result": {}
        }, c)
        self.assertEqual(result["score"], 1, result)
        self.assertFalse(result["checks"][1]["scorable"])
        self.assertEqual(result["checks"][1]["status"], "not_applicable")
        self.assertIsNone(result["checks"][1]["passed"])

    def test_adding_non_docx_cannot_hide_native_table(self):
        self.bind("d1", self.docx("table.docx", table=True), self.write("extra.md"))
        self.assert_status(self.no_tables_contract(), "fail")

    def test_no_table_other_policy_unknown(self):
        self.bind("d1", self.docx("plain.docx"))
        c = self.no_tables_contract()
        c["checks"][0]["parameters"]["non_docx_policy"] = "guess_tables"
        self.assert_status(c, "unknown")

    def test_existing_revisions_checked_in_every_bound_docx(self):
        self.bind("d1", self.docx("first.docx", revision=True),
                  self.docx("second.docx", revision=False))
        c = contract("docx_track_change_elements_exist", {
            "elements": ["w:ins", "w:del"], "any_of": True
        }, [{"id": "d1", "kind": "file", "format": "docx"}])
        self.assert_status(c, "fail")

    def scheduler_contract(self, source_id=True):
        p = {
            "service": "cron_registration",
            "expected": {
                "name": "每日任务",
                "payload": "user_turn_4_full_task_text",
                "schedule": "daily 08:00",
                "timeout": "raised_value_recorded_but_no_exact_target_user_value",
                "created": True,
                "actual_trigger_not_evaluated": True,
            },
        }
        if source_id:
            p["source_job_id"] = SOURCE_JOB_ID
        return contract("final_service_state", p,
            [{"id": "d1", "kind": "service", "service": "cron_registration"}])

    def scheduler_evidence(self, final=600, initial=300):
        self.evidence["resolved_parameters"] = {
            "d1": {"expected": {"payload": "canonical task payload", "schedule": "daily 08:00"}}
        }
        self.evidence["service_readbacks"] = [{
            "delivery_id": "d1", "service": "cron_registration",
            "observation": "final_readback", "authoritative": True, "complete": True,
            "records": [{"id": "native-job", "name": "每日任务",
                         "payload": "canonical task payload", "schedule": "daily 08:00",
                         "timeoutSeconds": final}],
        }]
        self.evidence["timeout_change_readbacks"] = [{
            "delivery_id": "d1", "job_id": "native-job", "original_job_id": SOURCE_JOB_ID,
            "observation": "final_readback", "authoritative": True, "complete": True,
            "before_dispatch_index": 1,
            "initial_timeout_seconds": initial, "final_timeout_seconds": final,
            "initial_config_sha256": "a" * 64, "final_config_sha256": "b" * 64,
        }]

    def test_scheduler_current_source_same_job_and_increase_passes(self):
        self.scheduler_evidence()
        self.assert_status(self.scheduler_contract(), "pass")

    def test_scheduler_unchanged_timeout_fails(self):
        self.scheduler_evidence(final=300)
        self.assert_status(self.scheduler_contract(), "fail")

    def test_scheduler_different_job_cannot_supply_correct_fields(self):
        self.scheduler_evidence()
        rows = self.evidence["service_readbacks"][0]["records"]
        other = copy.deepcopy(rows[0])
        other["id"] = "other-job"
        rows[0]["name"] = "wrong task"
        rows.append(other)
        self.assert_status(self.scheduler_contract(), "fail")

    def test_scheduler_actual_source_missing_final_job_fails(self):
        self.scheduler_evidence()
        self.evidence["service_readbacks"][0]["records"][0]["id"] = "other-job"
        self.assert_status(self.scheduler_contract(), "fail")

    def test_scheduler_missing_original_identity_unknown(self):
        self.scheduler_evidence()
        self.evidence["timeout_change_readbacks"][0].pop("original_job_id")
        self.assert_status(self.scheduler_contract(), "unknown")

    def test_scheduler_conflicting_resolved_id_unknown(self):
        self.scheduler_evidence()
        self.evidence["resolved_parameters"]["d1"]["expected"]["id"] = "other-job"
        self.assert_status(self.scheduler_contract(), "unknown")

    def test_scheduler_ambiguous_native_identity_unknown(self):
        self.scheduler_evidence()
        other = copy.deepcopy(self.evidence["timeout_change_readbacks"][0])
        other["job_id"] = "second-alias"
        self.evidence["timeout_change_readbacks"].append(other)
        self.assert_status(self.scheduler_contract(), "unknown")

    def test_scheduler_context_evidence_not_mutated(self):
        self.scheduler_evidence()
        before = copy.deepcopy(self.evidence)
        self.assert_status(self.scheduler_contract(), "pass")
        self.assertEqual(self.evidence, before)

    def test_scheduler_design_metadata_not_silently_accepted(self):
        self.scheduler_evidence()
        c = self.scheduler_contract()
        c["checks"][0]["parameters"]["payload_ref"] = "canonical_task"
        self.assert_status(c, "unknown")

    def test_scheduler_wrong_source_transition_cannot_supply_increase(self):
        self.scheduler_evidence(final=600, initial=600)
        other = copy.deepcopy(self.evidence["timeout_change_readbacks"][0])
        other["original_job_id"] = "another-source-job"
        other["initial_timeout_seconds"] = 300
        self.evidence["timeout_change_readbacks"].append(other)
        self.assert_status(self.scheduler_contract(), "fail")

    def test_scheduler_conflicting_source_initial_snapshots_unknown(self):
        self.scheduler_evidence(final=600, initial=600)
        other = copy.deepcopy(self.evidence["timeout_change_readbacks"][0])
        other["initial_timeout_seconds"] = 300
        self.evidence["timeout_change_readbacks"].append(other)
        self.assert_status(self.scheduler_contract(), "unknown")

    def test_scheduler_nested_design_metadata_unknown(self):
        self.scheduler_evidence()
        c = self.scheduler_contract()
        c["checks"][0]["parameters"]["expected"]["payload_ref"] = "canonical_task"
        self.assert_status(c, "unknown")

    def test_original_service_policy_metadata_compatible(self):
        self.scheduler_evidence()
        c = self.scheduler_contract(source_id=False)
        c["checks"][0]["parameters"].update(
            score_at="conversation_end_only", historical_ai_is_gold=False)
        self.assert_status(c, "pass")

    def test_existing_service_without_source_id_still_works(self):
        self.scheduler_evidence()
        self.assert_status(self.scheduler_contract(source_id=False), "pass")

    def test_repeated_registration_is_idempotent(self):
        if not EXTENSIONS.is_file():
            self.fail("extensions not yet implemented")
        extension = load_module("legal_fixture_extensions_again", EXTENSIONS)
        previous = self.base.HANDLERS["final_service_state"]
        extension.register_extensions(self.base)
        self.assertIs(previous, self.base.HANDLERS["final_service_state"])


if __name__ == "__main__":
    unittest.main()
