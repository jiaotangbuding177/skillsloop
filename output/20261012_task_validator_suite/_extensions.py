"""Approved offline basic-delivery extensions; no actor or service calls."""
from __future__ import annotations

import copy
import os


def register_extensions(base):
    """Register against one scorer instance so its exception classes stay shared."""
    if getattr(base, "_legal_extensions_registered", False):
        return

    def guard(parameters, accepted):
        if not isinstance(parameters, dict):
            raise base.UnknownEvidence("extension_parameters_invalid")
        unknown = sorted(set(parameters) - accepted - base.POLICY_PARAMETER_NAMES)
        if unknown:
            raise base.UnknownEvidence("extension_parameters_not_implemented:" + ",".join(unknown))
        if ("score_at" in parameters
                and parameters["score_at"] != "conversation_end_only"):
            raise base.UnknownEvidence("extension_scoring_time_not_supported")
        if ("historical_ai_is_gold" in parameters
                and parameters["historical_ai_is_gold"] is not False):
            raise base.UnknownEvidence("extension_historical_gold_policy_not_supported")

    def distinct_final_file_objects(ctx, did, p, kind):
        guard(p, {"delivery_ids", "required_distinct_object_count"})
        ids = p.get("delivery_ids")
        count = p.get("required_distinct_object_count")
        if (not isinstance(ids, list) or not ids
                or any(not isinstance(v, str) or not v for v in ids)
                or len(set(ids)) != len(ids)):
            raise base.UnknownEvidence("distinct_delivery_ids_invalid")
        if type(count) is not int or count <= 0:
            raise base.UnknownEvidence("distinct_required_count_invalid")
        groups = {}
        physical = []
        for target_id in ids:
            paths = ctx.opened(target_id, {})
            groups[target_id] = [str(path.resolve()) for path in paths]
            for path in paths:
                canonical = path.resolve()
                found = False
                for previous, owner in physical:
                    try:
                        same = canonical == previous or os.path.samefile(canonical, previous)
                    except OSError as error:
                        raise base.UnknownEvidence("distinct_file_identity_unreadable") from error
                    if same:
                        base.check_assert(owner == target_id, "independent_deliveries_share_physical_file")
                        found = True
                        break
                if not found:
                    physical.append((canonical, target_id))
        base.check_assert(len(physical) >= count, "distinct_final_object_count_below_requirement")
        return {"delivery_id_to_resolved_paths": groups, "physical_object_count": len(physical)}

    def final_file_in_resolved_directory(ctx, did, p, kind):
        guard(p, {"directory_label"})
        label = p.get("directory_label")
        if not isinstance(label, str) or not label:
            raise base.UnknownEvidence("required_directory_label_invalid")
        resolved = ctx.evidence.get("resolved_parameters", {}).get(did, {})
        mapping = resolved.get("directory_binding") if isinstance(resolved, dict) else None
        sid = ctx.contract.get("sid", ctx.contract.get("session_id"))
        if (not isinstance(mapping, dict)
                or mapping.get("label") != label
                or mapping.get("source_session_id") != sid
                or mapping.get("authoritative") is not True
                or mapping.get("origin") != "frozen_environment_directory_mapping"
                or not isinstance(mapping.get("path"), str)
                or not mapping["path"]):
            raise base.UnknownEvidence("authoritative_directory_mapping_missing_or_invalid")
        directory = ctx.path(mapping["path"])
        base.check_assert(directory.is_dir(), "mapped_delivery_directory_missing")
        paths = ctx.opened(did, {})
        for path in paths:
            base.check_assert(path.resolve().is_relative_to(directory),
                              "final_file_outside_required_directory")
        return {"mapping_label": label, "canonical_directory": str(directory),
                "canonical_final_file_paths": [str(path.resolve()) for path in paths]}

    def native_docx_body_without_tables(ctx, did, p, kind):
        guard(p, {"non_docx_policy"})
        if p.get("non_docx_policy") != "report_only":
            raise base.UnknownEvidence("non_docx_table_policy_not_supported")
        paths = ctx.opened(did, {})
        formats = []
        checked = []
        unsupported = []
        for path in paths:
            data = ctx.info(path)
            actual = data.get("format")
            formats.append(actual)
            if actual != "docx":
                unsupported.append(actual)
                continue
            tree = data.get("tree")
            body = tree.find("w:body", base.NS) if tree is not None else None
            if body is None:
                raise base.UnknownEvidence("native_docx_main_body_unresolved")
            tables = body.findall(".//w:tbl", base.NS)
            base.check_assert(not tables, "native_docx_body_contains_table")
            if body.findall(".//w:altChunk", base.NS):
                raise base.UnknownEvidence("native_docx_altchunk_body_unresolved")
            checked.append({"path": str(path), "native_body_table_count": 0})
        applicable = bool(checked)
        return {"actual_formats": formats, "docx_files_checked": checked,
                "unsupported_formats": unsupported, "scorable": applicable,
                "applicable": applicable,
                "applicable_to_AND": applicable,
                "scope": "native_docx_body_only",
                "non_docx_table_presence": "not_measured"}

    new_handlers = {
        "final_distinct_artifact_objects": (distinct_final_file_objects,
            {"delivery_ids", "required_distinct_object_count"}),
        "final_artifact_parent_directory": (final_file_in_resolved_directory,
            {"directory_label"}),
        "final_native_document_no_tables": (native_docx_body_without_tables,
            {"non_docx_policy"}),
    }
    for name, (handler, supported) in new_handlers.items():
        base.register(handler, name)
        base.PARAMETERS[handler] = supported

    original_handlers = {name: base.HANDLERS[name]
                         for name in ("final_service_state", "scheduler_record_fields")}
    original_parameters = {name: set(base.PARAMETERS.get(handler, set()))
                           for name, handler in original_handlers.items()}

    class EvidenceView:
        def __init__(self, original, evidence):
            self.original = original
            self.evidence = evidence

        def __getattr__(self, name):
            return getattr(self.original, name)

    def final_service_with_source_job_identity(ctx, did, p, kind):
        original = original_handlers[kind]
        if "source_job_id" not in p:
            return original(ctx, did, p, kind)
        supported = original_parameters[kind] | {"source_job_id"}
        guard(p, supported)
        if kind != "final_service_state" or p.get("service") != "cron_registration":
            raise base.UnknownEvidence("source_job_identity_only_supported_for_cron_final_state")
        source_job = p["source_job_id"]
        if not isinstance(source_job, str) or not source_job:
            raise base.UnknownEvidence("source_job_id_invalid")
        transitions = ctx.evidence.get("timeout_change_readbacks", [])
        if not isinstance(transitions, list):
            raise base.UnknownEvidence("source_job_identity_evidence_invalid")
        matching = [row for row in transitions if isinstance(row, dict)
                    and row.get("delivery_id") == did
                    and row.get("original_job_id") == source_job
                    and row.get("observation") == "final_readback"
                    and row.get("authoritative") is True
                    and row.get("complete") is True
                    and not row.get("error")]
        if not matching:
            raise base.UnknownEvidence("source_job_native_identity_missing")
        native_ids = {row.get("job_id") for row in matching
                      if isinstance(row.get("job_id"), str) and row["job_id"]}
        if len(native_ids) != 1 or any(row.get("job_id") not in native_ids for row in matching):
            raise base.UnknownEvidence("source_job_native_identity_ambiguous")
        snapshot_fields = ("before_dispatch_index", "initial_timeout_seconds",
                           "final_timeout_seconds", "initial_config_sha256",
                           "final_config_sha256", "initial_snapshot_sha256")
        signatures = {tuple(repr(row.get(key)) for key in snapshot_fields) for row in matching}
        if len(signatures) != 1:
            raise base.UnknownEvidence("source_job_native_timeout_snapshots_conflict")
        native_id = next(iter(native_ids))
        normalized = copy.deepcopy(p)
        normalized.pop("source_job_id")
        expected = normalized.get("expected", {})
        if not isinstance(expected, dict):
            raise base.UnknownEvidence("scheduler_expected_fields_invalid")
        guard(expected, {"name", "start", "schedule", "timezone", "payload",
                         "outputs_configured", "timeout", "created", "id",
                         "not_required", "same_task_repetition", "actual_trigger_not_evaluated"})
        if expected.get("id") not in (None, native_id):
            raise base.UnknownEvidence("scheduler_expected_id_conflicts_with_source_mapping")
        normalized["expected"] = {**expected, "id": native_id}
        evidence = copy.deepcopy(ctx.evidence)
        # Only the independently mapped source's native transition can prove
        # its increase; another source's transition must not supply a baseline.
        evidence["timeout_change_readbacks"] = copy.deepcopy(matching)
        overrides = evidence.setdefault("resolved_parameters", {}).setdefault(did, {})
        if not isinstance(overrides, dict):
            raise base.UnknownEvidence("scheduler_resolved_parameters_invalid")
        expected_overrides = overrides.setdefault("expected", {})
        if not isinstance(expected_overrides, dict):
            raise base.UnknownEvidence("scheduler_resolved_expected_fields_invalid")
        if expected_overrides.get("id") not in (None, native_id):
            raise base.UnknownEvidence("resolved_scheduler_id_conflicts_with_source_mapping")
        expected_overrides["id"] = native_id
        observed = original(EvidenceView(ctx, evidence), did, normalized, kind)
        return {**observed, "source_job_id": source_job, "native_job_id": native_id}

    for name in original_handlers:
        base.register(final_service_with_source_job_identity, name)
    base.PARAMETERS[final_service_with_source_job_identity] = (
        set().union(*original_parameters.values()) | {"source_job_id"})
    base._legal_extensions_registered = True
