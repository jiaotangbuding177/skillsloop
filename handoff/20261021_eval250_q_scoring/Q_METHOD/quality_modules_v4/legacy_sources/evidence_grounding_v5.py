"""Deterministic evidence anchoring, separate from semantic CHECK judgment."""
from __future__ import annotations
import copy
import json
import re

SCHEMA = "eval250-evidence-grounding-v5-wire-provenance"


def pointer(document, path):
    value = document
    if not isinstance(path, str) or not path.startswith("/"):
        raise ValueError("Invalid absolute JSON pointer")
    for part in path.split("/")[1:]:
        key = part.replace("~1", "/").replace("~0", "~")
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def scalar_text(value):
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def _normalize_pointer(pointer):
    """Accept bracket array notation and a missing leading slash deterministically."""
    if not isinstance(pointer, str):
        return pointer
    normalized = re.sub(r"\[(\d+)\]", r"/\1", pointer)
    if normalized and not normalized.startswith("/"):
        normalized = "/" + normalized
    return normalized


def _pointer_variants(pointer):
    """Deterministic variants for common omitted extraction containers."""
    variants = [pointer]
    match = re.match(r"^(/(?:artifacts|outputs|sources|input_evidence)/\d+)/(rows|parts|pages|lines)(/.*)?$", pointer)
    if match:
        variants.append(match.group(1) + "/extraction/" + match.group(2) + (match.group(3) or ""))
    return list(dict.fromkeys(variants))


def catalog(evidence):
    atoms = {}
    for record in evidence.get("evidence_atoms", []):
        atom = copy.deepcopy(record)
        aid = atom.get("atom_id")
        if not isinstance(aid, str) or aid in atoms:
            raise ValueError("Missing/duplicate evidence atom ID")
        value = pointer(evidence, atom["json_pointer"])
        if isinstance(value, (dict, list)):
            raise ValueError("Grounding atom must address a scalar")
        segments = atom["json_pointer"].split("/")
        container_roles = {"sources": "input", "input_evidence": "input", "artifacts": "output", "outputs": "output", "functional_observations": "observation", "artifact_correspondence": "observation", "evidence_failures": "observation"}
        actual_role = container_roles.get(segments[1] if len(segments) > 1 else None)
        owner = pointer(evidence, "/" + "/".join(segments[1:3]))
        relative = tuple(segment.replace("~1", "/").replace("~0", "~") for segment in segments[3:])
        trusted_fixture = (segments[1] == "functional_observations" and owner.get("kind") == "ACTUAL_TASK_SPECIFIC_LOCAL_BROWSER_SCENARIO" and
            (relative[:2] == ("scenario", "expected_from_original_requirements") or
             relative[:3] in (("scenario", "result", "sample_from_input"), ("scenario", "result", "expected_status"))))
        if trusted_fixture:
            if atom.get("role") not in ("observation", "input"):
                raise ValueError("Trusted reference fixture declared as an unrelated role")
            atom["declared_container_role"] = atom.get("role")
            atom["role"] = "input"
            atom["role_origin"] = "TRUSTED_FUNC_EXPECTED_OR_INPUT_FIXTURE_EXACT_PATH"
        elif actual_role is None or atom.get("role") != actual_role:
            raise ValueError("Atom role disagrees with actual pointer ownership")
        owner_id = owner.get("evidence_id", owner.get("artifact_id"))
        if atom.get("evidence_id") != owner_id:
            raise ValueError("Atom evidence ID disagrees with actual record ownership")
        atom["_value"] = value
        atoms[aid] = atom
    images = {}
    for image in evidence.get("visual_pages", []) + evidence.get("render_images", []):
        eid = image.get("evidence_id")
        if eid:
            images[eid] = image
    artifacts = {}
    for artifact in evidence.get("artifacts", evidence.get("outputs", [])):
        eid = artifact.get("evidence_id", artifact.get("artifact_id"))
        if eid:
            artifacts[eid] = artifact
    by_pointer = {}
    by_absolute = {}
    for atom in atoms.values():
        by_pointer.setdefault((atom["evidence_id"], atom["json_pointer"]), []).append(atom)
        by_absolute.setdefault(atom["json_pointer"], []).append(atom)
    observations = {record["evidence_id"]: record for record in evidence.get("functional_observations", []) if record.get("evidence_id")}
    bases, records, roles = {}, {}, {}
    for collection, role in (("sources", "input"), ("input_evidence", "input"), ("artifacts", "output"),
            ("outputs", "output"), ("functional_observations", "observation"),
            ("artifact_correspondence", "observation"), ("evidence_failures", "observation")):
        for index, record in enumerate(evidence.get(collection, [])):
            eid = record.get("evidence_id", record.get("artifact_id")) if isinstance(record, dict) else None
            if isinstance(eid, str):
                bases.setdefault(eid, f"/{collection}/{index}")
                records.setdefault(eid, record)
                roles.setdefault(eid, role)
    return {"atoms": atoms, "atoms_by_pointer": by_pointer, "atoms_by_absolute_pointer": by_absolute,
        "images": images, "artifacts": artifacts, "observations": observations, "bases": bases,
        "records": records, "record_roles": roles, "wire_provenance": None, "unit_catalog": None}


def _resolve_text_pointer(ref, evidence, index):
    if "unit_id" in ref:
        from citable_units_v5 import build_catalog, resolve_unit
        if index["unit_catalog"] is None:
            index["unit_catalog"] = build_catalog(evidence, effective_atoms=index["atoms"])
        try:
            unit = resolve_unit(evidence, ref["unit_id"], catalog=index["unit_catalog"])
        except (ValueError, TypeError):
            return None, "UNKNOWN_OR_AMBIGUOUS_CITABLE_UNIT", None
        if ref.get("evidence_id") is not None and ref["evidence_id"] != unit["evidence_id"]:
            return None, "UNIT_EVIDENCE_ID_CONFLICT", None
        if ref.get("json_pointer") is not None and ref["json_pointer"] != unit["json_pointer"]:
            return None, "UNIT_CANONICAL_POINTER_CONFLICT", None
        atom = index["atoms"].get(unit["atom_id"])
        if atom is None or atom["evidence_id"] != unit["evidence_id"] or atom["json_pointer"] != unit["json_pointer"] or atom["role"] != unit["role"]:
            return None, "CITABLE_UNIT_OWNER_OR_ROLE_MISMATCH", None
        return atom, None, {"kind": "EXACT_NATIVE_CITABLE_UNIT", "unit_id": ref["unit_id"],
            "canonical_json_pointer": atom["json_pointer"], "quote_or_value_search": False}
    eid, supplied_raw = ref.get("evidence_id"), ref.get("json_pointer")
    if not isinstance(eid, str) or not isinstance(supplied_raw, str):
        return None, "MISSING_ABSOLUTE_JSON_POINTER", None
    supplied = _normalize_pointer(supplied_raw)
    syntax = {"supplied_json_pointer": supplied_raw, "normalized_json_pointer": supplied,
              "mode": "BRACKET_ARRAY_OR_MISSING_SLASH"} if supplied != supplied_raw else None
    base = index.get("bases", {}).get(eid)
    for variant in _pointer_variants(supplied):
        try:
            direct_value = pointer(evidence, variant)
        except (KeyError, IndexError, ValueError, TypeError):
            direct_value = None
        if isinstance(direct_value, (dict, list)):
            return None, "OBJECT_POINTER_NOT_A_SCALAR", None
        direct = index["atoms_by_pointer"].get((eid, variant), [])
        if len(direct) == 1:
            return direct[0], None, {"kind": "CANONICAL_POINTER", "supplied_json_pointer": supplied,
                "canonical_json_pointer": variant, "pointer_syntax_normalization": syntax}
        if len(direct) > 1:
            return None, "AMBIGUOUS_CANONICAL_EVIDENCE_POINTER", None
        if base and variant != base and not variant.startswith(base + "/"):
            scoped = base + variant
            try:
                scoped_value = pointer(evidence, scoped)
            except (KeyError, IndexError, ValueError, TypeError):
                scoped_value = None
            if isinstance(scoped_value, (dict, list)):
                return None, "OBJECT_POINTER_NOT_A_SCALAR", None
            matches = index["atoms_by_pointer"].get((eid, scoped), [])
            if len(matches) == 1:
                return matches[0], None, {"kind": "RELATIVE_POINTER_SCOPED_TO_EVIDENCE_ID",
                    "supplied_json_pointer": supplied, "canonical_json_pointer": scoped, "pointer_syntax_normalization": syntax}
            if len(matches) > 1:
                return None, "AMBIGUOUS_RELATIVE_EVIDENCE_POINTER", None
        # Models sometimes append a substring index to a string atom, e.g.
        # /feedback/0/public_text/0. The parent string is the actual scalar;
        # the quote still has to match its content.
        parts = variant.split("/")
        for cut in range(len(parts) - 1, 0, -1):
            prefix = "/".join(parts[:cut])
            options = [prefix]
            if base and not prefix.startswith(base + "/") and prefix != base:
                options.append(base + prefix)
            for candidate in options:
                matches = index["atoms_by_pointer"].get((eid, candidate), [])
                if len(matches) == 1 and isinstance(matches[0]["_value"], str):
                    atom = matches[0]
                    return atom, None, {"kind": "STRING_PARENT_OF_SUBSTRING_POINTER",
                        "supplied_json_pointer": supplied, "canonical_json_pointer": atom["json_pointer"],
                        "quote_or_value_search": False, "pointer_syntax_normalization": syntax}
                if len(matches) > 1:
                    return None, "AMBIGUOUS_STRING_PARENT_POINTER", None
    if index["wire_provenance"] is None:
        from evidence_projection_v5 import project, build_provenance
        if index.get("wire_projected_override") is not None:
            index["wire_provenance"] = build_provenance(index["wire_projected_override"])
        else:
            from judge_v5 import _evidence_view
            safe, _ = _evidence_view(evidence)
            projected, _ = project(safe)
            expected = {key: value for key, value in safe.items() if key != "evidence_atoms"}
            index["wire_provenance"] = build_provenance(projected, expected)
    provenance = index["wire_provenance"]
    candidates = []
    for variant in _pointer_variants(supplied):
        for canonical in provenance["mapping"].get(variant, set()):
            for atom in index["atoms_by_pointer"].get((eid, canonical), []):
                # Mapping is determined before inspecting quote, never by value
                # search. This check attests decoder value against the source.
                if json.dumps(atom["_value"], ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) != json.dumps(provenance["values"][canonical], ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False):
                    raise AssertionError("Wire provenance value differs from canonical source")
                candidates.append(atom)
    unique = {atom["atom_id"]: atom for atom in candidates}
    if len(unique) == 1:
        atom = next(iter(unique.values()))
        return atom, None, {"kind": "EXACT_CODEC_WIRE_PROVENANCE", "supplied_json_pointer": supplied,
            "canonical_json_pointer": atom["json_pointer"], "quote_or_value_search": False,
            "pointer_syntax_normalization": syntax, "provenance_receipt": provenance["receipt"]}
    # Dynamic wiring: a concrete pointer may uniquely address a real output or
    # observation while the model supplied a stale sibling evidence_id. Input
    # IDs are never allowed to borrow output/observation evidence.
    supplied_role = index.get("record_roles", {}).get(eid)
    if supplied_role in ("output", "observation"):
        for variant in _pointer_variants(supplied):
            matches = index.get("atoms_by_absolute_pointer", {}).get(variant, [])
            unique_matches = {atom["atom_id"]: atom for atom in matches}
            if len(unique_matches) == 1:
                atom = next(iter(unique_matches.values()))
                if index["record_roles"].get(atom["evidence_id"]) == supplied_role:
                    return atom, None, {"kind": "EVIDENCE_ID_NORMALIZED_FROM_UNIQUE_POINTER",
                        "supplied_json_pointer": supplied, "supplied_evidence_id": eid,
                        "canonical_evidence_id": atom["evidence_id"],
                        "canonical_json_pointer": atom["json_pointer"], "quote_or_value_search": False,
                        "pointer_syntax_normalization": syntax}
    return None, "UNKNOWN_OR_AMBIGUOUS_WIRE_EVIDENCE_POINTER", {"candidate_count": len(unique)}


def allowed_artifacts(item, evidence, index):
    names = set(item.get("deliverables", []))
    result = {eid for eid, artifact in index["artifacts"].items() if artifact.get("filename") in names}
    for alias in evidence.get("artifact_correspondence", []):
        if alias.get("expected_filename") in names and alias.get("status") == "UNIQUE_FORMAT_CONTENT_CANDIDATE_WITH_EXPLICIT_NAMING_MISMATCH":
            result.add(alias["actual_evidence_id"])
    return result


def _base_id(eid, artifacts):
    return next((base for base in artifacts if eid == base or eid.startswith(base + ":")), None)


def _unique_artifact_for_record(record, artifacts):
    name = record.get("artifact", record.get("filename")) if isinstance(record, dict) else None
    if not isinstance(name, str):
        return None
    matches = [eid for eid, artifact in artifacts.items() if name == artifact.get("filename") or name == artifact.get("relative_path")]
    return matches[0] if len(matches) == 1 else None


def _reference_base_id(ref, index):
    if ref.get("claim_role") not in ("OUTPUT_CONTENT", "VISUAL_OBSERVATION", "OBSERVED_ACTION", "OUTPUT_ABSENCE"):
        return None
    eid = ref.get("evidence_id", "")
    base = _base_id(eid, index["artifacts"])
    if base:
        return base
    if ref.get("kind") == "visual":
        return _unique_artifact_for_record(index["images"].get(eid), index["artifacts"])
    if ref.get("claim_role") == "OBSERVED_ACTION":
        return _unique_artifact_for_record(index["observations"].get(eid), index["artifacts"])
    return None


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _quote_match(value, quoted):
    actual = scalar_text(value)
    if not isinstance(quoted, str) or not quoted:
        return False, None
    if not isinstance(value, str):
        return quoted == actual, "EXACT" if quoted == actual else None
    if quoted in actual:
        return True, "EXACT"
    if quoted.strip() and quoted.strip() in actual:
        return True, "TRIMMED"
    compact_actual = "".join(actual.split())
    compact_quote = "".join(quoted.split())
    if compact_quote and compact_quote in compact_actual:
        return True, "WHITESPACE_NORMALIZED"
    try:
        if _canonical(json.loads(actual)) == _canonical(json.loads(quoted)):
            return True, "JSON_EQUIVALENT"
    except (ValueError, TypeError):
        pass
    return False, None


def _pointer_exists(evidence, base, pointer):
    for variant in _pointer_variants(pointer):
        options = [variant]
        if base and not variant.startswith(base + "/") and variant != base:
            options.append(base + variant)
        for candidate in options:
            try:
                pointer(evidence, candidate)
                return True
            except (KeyError, IndexError, ValueError, TypeError):
                continue
    return False


def _artifact_full_texts(eid, index):
    record = index.get("records", {}).get(eid)
    if not isinstance(record, dict):
        return []
    extraction = record.get("extraction") or {}
    values = []
    if isinstance(extraction.get("text"), str):
        values.append(extraction["text"])
    parts_text = []
    for part in extraction.get("parts", []) or []:
        for paragraph in part.get("paragraphs", []) or []:
            if isinstance(paragraph, dict) and isinstance(paragraph.get("text"), str):
                parts_text.append(paragraph["text"])
    if parts_text:
        values.append("\n".join(parts_text))
    rows = extraction.get("rows")
    if isinstance(rows, list):
        cells = []
        for row in rows:
            if isinstance(row, list):
                cells.extend(str(x) for x in row)
            elif isinstance(row, dict):
                cells.extend(str(x) for x in row.values())
        if cells:
            values.append("\n".join(cells))
    return values


def _artifact_full_text_supports(eid, quoted, index):
    for text in _artifact_full_texts(eid, index):
        if _quote_match(text, quoted)[0]:
            return True
    return False


def _artifact_text_fallback(eid, quoted, index):
    base = index.get("bases", {}).get(eid)
    if not base:
        return None, None
    for path in (base + "/extraction/text", base + "/text"):
        matches = index["atoms_by_pointer"].get((eid, path), [])
        if len(matches) == 1 and isinstance(matches[0]["_value"], str):
            ok, mode = _quote_match(matches[0]["_value"], quoted)
            if ok:
                return matches[0], mode
    return None, None


def _artifact_level_reference(ref, item, evidence, index, original_error=None, allowed_fallback=True):
    eid, role = ref.get("evidence_id"), ref.get("claim_role")
    actual_role = index.get("record_roles", {}).get(eid)
    expected = {"OUTPUT_CONTENT": "output", "INPUT_REQUIREMENT": "input",
        "OBSERVED_ACTION": "observation"}.get(role)
    role_normalization = None
    if actual_role == "input" and expected != "input":
        return False, "INPUT_OR_UNRELATED_ARTIFACT_USED_AS_OUTPUT", None
    if actual_role in ("output", "observation") and expected in ("output", "observation") and actual_role != expected:
        role = "OUTPUT_CONTENT" if actual_role == "output" else "OBSERVED_ACTION"
        role_normalization = {"supplied": ref.get("claim_role"), "normalized": role,
            "basis": "EVIDENCE_RECORD_OWNS_ROLE"}
        ref = dict(ref, claim_role=role)
        expected = actual_role
    if actual_role is None or expected is None or actual_role != expected:
        return False, "DYNAMIC_REFERENCE_ROLE_OR_RECORD_MISMATCH", None
    if not allowed_fallback:
        return False, original_error or "UNKNOWN_OR_AMBIGUOUS_WIRE_EVIDENCE_POINTER", None
    # Dynamic artifact/observation-level citation is still allowed. A supplied
    # exact_quote is a factual claim, however, and must exist in this same
    # record. Do not turn an existent artifact into support for invented text.
    # This does not require a unique field mapping and never borrows another
    # record's matching value to rescue the citation.
    supplied_quote = ref.get("exact_quote")
    if supplied_quote is not None:
        supported_quote = _artifact_full_text_supports(eid, supplied_quote, index) or any(
            atom.get("evidence_id") == eid and _quote_match(atom.get("_value"), supplied_quote)[0]
            for atom in index.get("atoms", {}).values())
        if not supported_quote:
            return False, "EXACT_QUOTE_NOT_IN_CITED_ARTIFACT_OR_OBSERVATION", None
    if role == "OUTPUT_CONTENT" and _base_id(eid, index["artifacts"]) not in allowed_artifacts(item, evidence, index):
        return False, "INPUT_OR_UNRELATED_ARTIFACT_USED_AS_OUTPUT", None
    if role == "OBSERVED_ACTION" and index["observations"].get(eid, {}).get("kind") == "ACTUAL_TASK_SPECIFIC_LOCAL_BROWSER_SCENARIO" and _reference_base_id(ref, index) not in allowed_artifacts(item, evidence, index):
        return False, "ACTION_FROM_UNRELATED_ARTIFACT", None
    record = index["records"].get(eid)
    if record is None:
        return False, original_error or "UNKNOWN_EVIDENCE_RECORD", None
    return True, "ARTIFACT_LEVEL_DYNAMIC_SUPPORT", dict(ref,
        support_level="ARTIFACT_LEVEL", locator=record.get("locator", "artifact inventory"),
        quote=ref.get("exact_quote") or "artifact-level support",
        unverified_supplied_pointer=ref.get("json_pointer"),
        pointer_resolution={"kind": "ARTIFACT_LEVEL_DYNAMIC_WIRING",
            "original_error": original_error, "quote_or_value_search": False},
        role_normalization=role_normalization)


def check_reference(ref, item, evidence, index):
    if not isinstance(ref, dict):
        return False, "REFERENCE_NOT_OBJECT", None
    if ref.get("kind") == "functional":
        if "unit_id" in ref or isinstance(ref.get("json_pointer"), str):
            ref = dict(ref, kind="text")
        else:
            f_role, f_eid = ref.get("claim_role"), ref.get("evidence_id")
            if f_role != "OBSERVED_ACTION" or f_eid not in index.get("records", {}) or index["record_roles"].get(f_eid) != "observation":
                return False, "FUNCTIONAL_REFERENCE_REQUIRES_REAL_OBSERVATION", None
            record = index["records"][f_eid]
            return True, "OBSERVATION_LEVEL_DYNAMIC_SUPPORT", dict(ref,
                support_level="OBSERVATION_LEVEL", locator=record.get("locator", "functional observation"),
                quote=ref.get("observed_claim") or ref.get("quote") or "observation-level support",
                unverified_supplied_locator=ref.get("locator"),
                pointer_resolution={"kind": "OBSERVATION_LEVEL_DYNAMIC_WIRING", "quote_or_value_search": False})
    if "unit_id" in ref:
        if ref.get("kind") not in (None, "text"):
            return False, "CITABLE_UNIT_KIND_CONFLICT", None
        ref = dict(ref, kind="text")
    kind, role = ref.get("kind"), ref.get("claim_role")
    eid = ref.get("evidence_id")
    allowed = allowed_artifacts(item, evidence, index)
    if kind == "text":
        supplied_eid = ref.get("evidence_id")
        if "unit_id" not in ref and not isinstance(ref.get("json_pointer"), str):
            return _artifact_level_reference(ref, item, evidence, index, "NO_FIELD_POINTER")
        atom, pointer_error, resolution = _resolve_text_pointer(ref, evidence, index)
        if atom is None:
            base = index.get("bases", {}).get(eid)
            pointer_text = _normalize_pointer(ref.get("json_pointer"))
            allowed_fallback = False
            if base and isinstance(pointer_text, str) and pointer_text.startswith(base + "/"):
                child = pointer_text[len(base) + 1:].split("/", 1)[0]
                try:
                    owner = evidence
                    for part in base.strip("/").split("/"):
                        owner = owner[int(part)] if isinstance(owner, list) else owner[part.replace("~1", "/").replace("~0", "~")]
                    allowed_fallback = isinstance(owner, dict) and child.replace("~1", "/").replace("~0", "~") in owner
                except (KeyError, IndexError, ValueError, TypeError):
                    allowed_fallback = False
            if allowed_fallback:
                fallback, _ = _artifact_text_fallback(eid, ref.get("exact_quote"), index)
                if fallback is not None:
                    atom = fallback
                    resolution = {"kind": "ARTIFACT_FULL_TEXT_SUPPORTS_QUOTE",
                        "supplied_json_pointer": ref.get("json_pointer"),
                        "canonical_json_pointer": atom["json_pointer"],
                        "quote_or_value_search": "WITHIN_CITED_ARTIFACT_ONLY"}
            if atom is None:
                if pointer_error == "OBJECT_POINTER_NOT_A_SCALAR":
                    pointer_text = _normalize_pointer(ref.get("json_pointer")) or ""
                    if pointer_text.count("/") >= 4 and _artifact_full_text_supports(eid, ref.get("exact_quote"), index):
                        return _artifact_level_reference(ref, item, evidence, index, pointer_error, True)
                    if pointer_text.count("/") >= 4:
                        for suffix in ("/text", "/value", "/content"):
                            child_ref = dict(ref, json_pointer=pointer_text + suffix)
                            child_atom, child_error, child_resolution = _resolve_text_pointer(child_ref, evidence, index)
                            if child_atom is not None and _quote_match(child_atom["_value"], ref.get("exact_quote"))[0]:
                                return True, "OBJECT_CHILD_TEXT_SUPPORTS_QUOTE", dict(ref,
                                    evidence_id=child_atom["evidence_id"], support_level="FIELD_CHILD",
                                    locator=child_atom["locator"], quote=ref.get("exact_quote"),
                                    json_pointer=child_atom["json_pointer"],
                                    pointer_resolution={"kind": "OBJECT_CHILD_TEXT",
                                        "supplied_json_pointer": ref.get("json_pointer")})
                        if index.get("record_roles", {}).get(eid) == "observation":
                            return _artifact_level_reference(ref, item, evidence, index, pointer_error, True)
                    return False, pointer_error, None
                hard = pointer_error in {"MISSING_ABSOLUTE_JSON_POINTER"} or str(pointer_error).startswith("AMBIGUOUS_")
                if pointer_error == "UNKNOWN_OR_AMBIGUOUS_WIRE_EVIDENCE_POINTER" and isinstance(resolution, dict) and resolution.get("candidate_count", 0) > 0:
                    hard = True
                if hard:
                    return False, pointer_error, None
                if allowed_fallback and _artifact_full_text_supports(eid, ref.get("exact_quote"), index):
                    return _artifact_level_reference(ref, item, evidence, index, pointer_error, True)
                return _artifact_level_reference(ref, item, evidence, index, pointer_error, allowed_fallback)
        eid = atom["evidence_id"]
        role_normalization = None
        if role is None and "unit_id" in ref:
            role = {"input": "INPUT_REQUIREMENT", "output": "OUTPUT_CONTENT", "observation": "OBSERVED_ACTION"}[atom["role"]]
        if role == "OUTPUT_CONTENT" and atom.get("role") == "observation":
            role = "OBSERVED_ACTION"
            role_normalization = {"supplied": "OUTPUT_CONTENT", "normalized": role, "basis": "ATOM_RECORD_IS_OBSERVATION"}
        elif role == "OBSERVED_ACTION" and atom.get("role") == "output":
            role = "OUTPUT_CONTENT"
            role_normalization = {"supplied": "OBSERVED_ACTION", "normalized": role, "basis": "ATOM_RECORD_IS_OUTPUT"}
        ref = dict(ref, evidence_id=eid, claim_role=role)
        if ("atom_id" in ref and ref["atom_id"] != atom["atom_id"]) or ("locator" in ref and ref["locator"] != atom["locator"]):
            return False, "SUPPLIED_DERIVED_ATOM_OR_LOCATOR_MISMATCH", None
        if role == "OUTPUT_CONTENT":
            if atom.get("role") != "output" or _base_id(eid, index["artifacts"]) not in allowed:
                return False, "INPUT_OR_UNRELATED_ARTIFACT_USED_AS_OUTPUT", None
        elif role == "INPUT_REQUIREMENT":
            if atom.get("role") != "input":
                return False, "INPUT_ROLE_MISMATCH", None
        elif role == "OBSERVED_ACTION":
            if atom.get("role") != "observation":
                return False, "ACTION_ROLE_MISMATCH", None
            offered = evidence.get("item_availability", {}).get(item["item_id"], {}).get("evidence_ids", [])
            if offered and eid not in offered:
                # The item's offered list is advisory; a real observation of
                # one of this item's own deliverables remains usable.
                base = _reference_base_id(ref, index)
                if base not in allowed:
                    return False, "ACTION_NOT_RELATED_TO_THIS_ITEM", None
            if index["observations"].get(eid, {}).get("kind") == "ACTUAL_TASK_SPECIFIC_LOCAL_BROWSER_SCENARIO" and _reference_base_id(ref, index) not in allowed:
                return False, "ACTION_FROM_UNRELATED_ARTIFACT", None
        else:
            return False, "UNKNOWN_TEXT_CLAIM_ROLE", None
        quoted = ref.get("exact_quote")
        matched, quote_mode = _quote_match(atom["_value"], quoted)
        if not matched:
            for candidate_eid in dict.fromkeys(x for x in (eid, supplied_eid) if isinstance(x, str)):
                if _artifact_full_text_supports(candidate_eid, quoted, index):
                    return _artifact_level_reference(dict(ref, evidence_id=candidate_eid), item, evidence, index,
                        "ARTIFACT_FULL_TEXT_QUOTE_MISMATCH", True)
                fallback, fallback_mode = _artifact_text_fallback(candidate_eid, quoted, index)
                if fallback is not None:
                    atom = fallback
                    matched, quote_mode = True, (fallback_mode or "ARTIFACT_TEXT")
                    resolution = {"kind": "ARTIFACT_FULL_TEXT_SUPPORTS_QUOTE_AFTER_POINTER_MISMATCH",
                        "supplied_json_pointer": ref.get("json_pointer"),
                        "supplied_evidence_id": supplied_eid,
                        "canonical_evidence_id": candidate_eid,
                        "canonical_json_pointer": atom["json_pointer"],
                        "quote_or_value_search": "WITHIN_CITED_ARTIFACT_ONLY"}
                    break
        if not matched:
            return False, "EXACT_QUOTE_NOT_IN_ORIGINAL_ATOM", None
        normalized = dict(ref, evidence_id=eid, atom_id=atom["atom_id"], locator=atom["locator"], quote=quoted,
            json_pointer=atom["json_pointer"], supplied_json_pointer=ref.get("json_pointer"), pointer_resolution=resolution,
            quote_comparison=quote_mode, role_normalization=role_normalization,
            atom_id_origin="HOST_UNIQUE_EVIDENCE_ID_AND_JSON_POINTER_LOOKUP")
        return True, "EXACT_ATOM_QUOTE_SUPPORTED", normalized
    if kind == "visual":
        image = index["images"].get(eid)
        if role != "VISUAL_OBSERVATION" or not image or image.get("role") == "input":
            return False, "VISUAL_REQUIRES_ACTUAL_OUTPUT_IMAGE", None
        # A unique actually sent image ID is sufficient; SHA is optional. An
        # explicitly supplied pixel SHA must nevertheless describe those exact
        # pixels, rather than being silently ignored as an extra model field.
        for supplied_sha_key in ("image_sha256", "pixel_sha256", "sha256"):
            if ref.get(supplied_sha_key) is not None and ref[supplied_sha_key] != image.get("sha256"):
                return False, "EXPLICIT_IMAGE_SHA_DIFFERS_FROM_ACTUAL_SENT_PIXELS", None
        supplied_locator = ref.get("locator")
        locator_normalization = None
        if supplied_locator != image.get("locator"):
            # evidence_id uniquely selects the actual image; a mis-copied or
            # omitted locator does not change which pixels were supplied.
            locator_normalization = {"supplied": supplied_locator, "actual": image.get("locator"),
                "mode": "NORMALIZED_FROM_UNIQUE_EVIDENCE_ID"}
            ref = dict(ref, locator=image.get("locator"))
        base = _reference_base_id(ref, index)
        if base not in allowed:
            return False, "IMAGE_FROM_UNRELATED_ARTIFACT", None
        if str(image.get("view_semantics", "")).startswith("ORIGINAL_PRINT_DIAGNOSTIC_ONLY") and not item.get("visual_evidence_policy", {}).get("explicit_print_requirement", False):
            return False, "PRINT_DIAGNOSTIC_NOT_NATIVE_SHEET_VIEW", None
        claim = ref.get("observed_claim")
        if not isinstance(claim, str) or not claim.strip():
            return False, "VISUAL_OBSERVATION_DESCRIPTION_MISSING", None
        return True, "PIXEL_REFERENCE_VALID_SEMANTICS_REQUIRES_CHECK", dict(ref, quote=claim,
            locator_normalization=locator_normalization)
    if kind == "inventory":
        artifact = index["artifacts"].get(eid)
        availability = evidence.get("item_availability", {}).get(item["item_id"], {})
        if role != "OUTPUT_ABSENCE" or not artifact or eid not in allowed or availability.get("status") not in ("ABSENT_REQUIRED_CONTENT", "MISSING_REQUIRED"):
            return False, "ABSENCE_NOT_ESTABLISHED_FOR_THIS_ITEM", None
        if artifact.get("presence") == "PRESENT":
            return False, "PRESENT_ARTIFACT_FALSELY_CALLED_ABSENT", None
        return True, "ACTUAL_REQUIRED_ARTIFACT_ABSENCE", dict(ref, locator=artifact.get("locator", "artifact inventory"), quote="必需产物实际缺失")
    return False, "UNSUPPORTED_REFERENCE_KIND", None


def ground_result(parsed, rubric, evidence, phase, draft_result=None, wire_projected=None):
    """Invalid support becomes null; never manufacture a business score of zero."""
    value = copy.deepcopy(parsed)
    index = catalog(evidence)
    index["wire_projected_override"] = wire_projected
    authored = {item["item_id"]: item for item in rubric["items"]}
    rows = value.get("items")
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError("Candidate lacks complete item objects")
    ids = [row.get("item_id") for row in rows]
    if len(ids) != len(set(ids)) or set(ids) != set(authored):
        raise ValueError("Candidate IDs differ from complete frozen rubric")
    for row in rows:
        score = row.get("score")
        if score is not None and (type(score) not in (int, float) or score not in (0, .5, 1)):
            raise ValueError("Candidate has illegal score")
        if row.get("status") not in ("SCORED", "UNSCORED") or (score is None) != (row["status"] == "UNSCORED"):
            raise ValueError("Candidate status and score disagree")
        if not isinstance(row.get("evidence"), list) or not isinstance(row.get("reason"), str) or not row["reason"].strip():
            raise ValueError("Candidate evidence/reason shape invalid")
    draft_items = {item["item_id"]: item for item in (draft_result or {}).get("items", [])}
    label_normalizations = []
    if phase == "CHECK":
        for row in rows:
            verification = row.get("verification_status")
            if verification not in ("SUPPORTED", "CORRECTED", "UNVERIFIABLE") or not isinstance(row.get("verification_reason"), str) or not row["verification_reason"].strip():
                raise ValueError("Independent CHECK response lacks required semantic verification record")
            if verification == "SUPPORTED" and row.get("score") != draft_items.get(row["item_id"], {}).get("score"):
                # The substantive evidence/reason/score are present; the label is
                # mechanically corrected rather than discarding an otherwise
                # complete independent re-check.
                row["verification_status"] = "CORRECTED"
                row["verification_reason"] = "HOST_LABEL_NORMALIZED_SUPPORTED_TO_CORRECTED（分数与初评不同，按CORRECTED处理；模型原核验理由保留）：" + row["verification_reason"]
                label_normalizations.append({"item_id": row["item_id"], "from": "SUPPORTED", "to": "CORRECTED",
                    "draft_score": draft_items.get(row["item_id"], {}).get("score"), "check_score": row.get("score")})
            if row["verification_status"] == "UNVERIFIABLE" and row.get("score") is not None:
                raise ValueError("UNVERIFIABLE requires null score")
    records, invalid_items = [], set()
    for row in value.get("items", []):
        item_id = row.get("item_id")
        if item_id not in authored:
            continue  # Exact complete ID-set validation remains in the judge.
        checks, normalized = [], []
        for ref in row.get("evidence", []):
            valid, reason, norm = check_reference(ref, authored[item_id], evidence, index)
            checks.append({"reference": ref, "supported": valid, "reason": reason})
            if valid:
                normalized.append(norm)
        numerical = row.get("score") is not None
        warnings = [c["reason"] for c in checks if not c["supported"]]
        reasons = []
        if numerical and not normalized:
            reasons.append("NUMERICAL_SCORE_WITHOUT_ARTIFACT_OR_OBSERVATION_SUPPORT")
        if numerical and not any(r.get("claim_role") in ("OUTPUT_CONTENT", "VISUAL_OBSERVATION", "OUTPUT_ABSENCE", "OBSERVED_ACTION") for r in normalized):
            reasons.append("NO_OUTPUT_OR_ACTUAL_OBSERVATION_SUPPORT")
        av = evidence.get("item_availability", {}).get(item_id, {})
        necessary = av.get("required_evidence_modes", [])
        if numerical and av.get("status") not in ("ABSENT_REQUIRED_CONTENT", "MISSING_REQUIRED"):
            deliverables = set(authored[item_id].get("deliverables", []))
            if "visual" in necessary and not any(r.get("kind") == "visual" for r in normalized):
                reasons.append("NECESSARY_VISUAL_OBSERVATION_NOT_SUPPLIED")
            if "functional" in necessary and not any(r.get("claim_role") == "OBSERVED_ACTION" for r in normalized):
                available_functional = any(
                    index.get("record_roles", {}).get(eid) == "observation" or
                    (index.get("records", {}).get(eid, {}).get("artifact") in deliverables)
                    for eid in av.get("evidence_ids", []))
                if available_functional:
                    warnings.append("FUNCTIONAL_EVIDENCE_AVAILABLE_NOT_EXPLICITLY_CITED")
                else:
                    reasons.append("NECESSARY_ACTUAL_FUNCTION_OBSERVATION_NOT_SUPPLIED")
        if row.get("score") == 1:
            binding = authored[item_id].get("evidence_binding_v3", {})
            required = set(binding.get("full_credit_requires_artifacts", []))
            comparison_required = set(binding.get("comparison_requires_deliverables", []))
            present = set()
            for ref in normalized:
                base = _reference_base_id(ref, index)
                if base:
                    present.add(index["artifacts"][base].get("filename"))
            for alias in evidence.get("artifact_correspondence", []):
                if alias.get("actual_filename") in present and alias.get("status") == "UNIQUE_FORMAT_CONTENT_CANDIDATE_WITH_EXPLICIT_NAMING_MISMATCH":
                    present.add(alias.get("expected_filename"))
            if not required.issubset(present):
                reasons.append("FULL_CREDIT_LACKS_REQUIRED_ARTIFACT_SUPPORT")
            if not comparison_required.issubset(present):
                reasons.append("FULL_CREDIT_COMPARISON_LACKS_REQUIRED_SIDE_SUPPORT")
        verification = row.get("verification_status")
        if phase == "CHECK":
            if verification == "UNVERIFIABLE":
                reasons.append("SEMANTIC_CHECK_UNVERIFIABLE")
        if reasons:
            invalid_items.add(item_id)
            row.update(score=None, status="UNSCORED", evidence=[], defect_ids=[],
                owner_cross_references=[], deduction_basis="NONE",
                reason="证据核验不足，保留缺测：" + ";".join(dict.fromkeys(reasons)))
        else:
            row["evidence"] = normalized
            if warnings:
                row["unverified_references"] = [c["reference"] for c in checks if not c["supported"]]
                row["unverified_reference_reasons"] = list(dict.fromkeys(warnings))
        records.append({"item_id": item_id, "phase": phase,
            "grounding_status": "UNVERIFIABLE" if reasons else "STRUCTURALLY_GROUNDED_WITH_UNVERIFIED_REFERENCES" if warnings else "STRUCTURALLY_GROUNDED_NOT_SEMANTICALLY_VERIFIED" if phase == "DRAFT" else verification,
            "semantic_check_status": verification if phase == "CHECK" else "NOT_YET_CHECKED",
            "reference_checks": checks, "unverifiable_reasons": list(dict.fromkeys(reasons)),
            "unverified_reference_warnings": list(dict.fromkeys(warnings)),
            "verification_reason": row.get("verification_reason"), "final_score": row.get("score")})
    removed = {d.get("defect_id") for d in value.get("defects", []) if d.get("owner_item_id") in invalid_items}
    defect_records = []
    unsupported_defect_owners = set()
    remaining_defects = []
    for defect in value.get("defects", []):
        original_defect = copy.deepcopy(defect)
        if defect.get("defect_id") in removed:
            defect_records.append({"defect_id": defect.get("defect_id"),
                "owner_item_id": defect.get("owner_item_id"), "status": "REMOVED_OWNER_ALREADY_UNVERIFIABLE",
                "raw_defect": original_defect})
            continue
        owner = authored.get(defect.get("owner_item_id"))
        if owner:
            converted, defect_checks = [], []
            for ref in defect.get("evidence", []):
                valid, why, normalized = check_reference(ref, owner, evidence, index)
                defect_checks.append({"reference": copy.deepcopy(ref), "supported": valid, "reason": why})
                if valid:
                    converted.append(normalized)
            if not converted:
                removed.add(defect.get("defect_id"))
                unsupported_defect_owners.add(owner["item_id"])
                defect_records.append({"defect_id": defect.get("defect_id"),
                    "owner_item_id": owner["item_id"], "status": "REMOVED_NO_GROUNDED_DEFECT_EVIDENCE_OWNER_NULL",
                    "raw_defect": original_defect, "reference_checks": defect_checks,
                    "no_item_reference_copied_to_defect": True})
                continue
            defect["evidence"] = converted
            defect_records.append({"defect_id": defect.get("defect_id"),
                "owner_item_id": owner["item_id"], "status": "GROUNDED_DEFECT_RETAINED",
                "raw_defect": original_defect, "reference_checks": defect_checks})
        remaining_defects.append(defect)
    value["defects"] = remaining_defects
    grounded_owners = {defect.get("owner_item_id") for defect in remaining_defects}
    removed_only_owners = invalid_items.union(unsupported_defect_owners) - grounded_owners
    for row in value.get("items", []):
        row["defect_ids"] = [did for did in row.get("defect_ids", []) if did not in removed]
        row["owner_cross_references"] = [iid for iid in row.get("owner_cross_references", []) if iid not in removed_only_owners]
        if row["item_id"] in unsupported_defect_owners:
            previous = row.get("score")
            row.update(score=None, status="UNSCORED", deduction_basis="NONE",
                reason="证据核验不足，保留缺测：DEFECT_WITHOUT_GROUNDED_EVIDENCE；原缺陷及清理理由保留审计，不补造扣分依据。")
            for record in records:
                if record["item_id"] == row["item_id"]:
                    record.update(grounding_status="UNVERIFIABLE", final_score=None,
                        score_before_defect_cleanup=previous)
                    record["unverifiable_reasons"] = list(dict.fromkeys(record.get("unverifiable_reasons", []) + ["DEFECT_WITHOUT_GROUNDED_EVIDENCE"]))
    # The model can incorrectly attach one primary defect to multiple item
    # deductions. Keep the original owner and every independent valid defect;
    # an unrelated item must not inherit that deduction or receive a made-up 1.
    # Include the original graph because V2 may already have removed a defect
    # whose owner's evidence was invalid. Its dependent duplicate still needs
    # a scoped null rather than the aggregator failing the complete job.
    original_rows = {row["item_id"]: row for row in parsed["items"]}
    original_defects = {d.get("defect_id"): d for d in parsed.get("defects", [])
                        if isinstance(d, dict)}
    valid_defects = {d.get("defect_id"): d for d in value["defects"]}
    live_owners = {d.get("owner_item_id") for d in value["defects"]}
    ownership_records, nonprimary_nulls = [], []
    for row in value["items"]:
        iid = row["item_id"]
        raw_row = original_rows[iid]
        foreign = [did for did in raw_row.get("defect_ids", [])
                   if did in original_defects and original_defects[did].get("owner_item_id") in authored
                   and original_defects[did]["owner_item_id"] != iid]
        if not foreign:
            continue
        before = copy.deepcopy(row)
        own = [did for did in row.get("defect_ids", [])
               if did in valid_defects and valid_defects[did].get("owner_item_id") == iid]
        row["defect_ids"] = [did for did in row.get("defect_ids", []) if did not in foreign]
        foreign_owners = [original_defects[did]["owner_item_id"] for did in foreign]
        row["owner_cross_references"] = list(dict.fromkeys(row.get("owner_cross_references", []) +
            [owner for owner in foreign_owners if owner in live_owners]))
        numerical_deduction = row.get("score") is not None and row["score"] < 1
        own_absence_rule = row.get("deduction_basis") in ("DEPENDENT_ARTIFACT_ABSENT", "SEMANTICALLY_EMPTY_ARTIFACT")
        nulled = numerical_deduction and not own and not own_absence_rule
        if nulled:
            previous = row["score"]
            row.update(score=None, status="UNSCORED", deduction_basis="NONE",
                reason="主责核验不足，保留缺测：NON_PRIMARY_OWNER_DEDUCTION_WITHOUT_INDEPENDENT_GROUNDED_DEFECT；同一缺陷只由原主责扣分，不自动补满分。")
            nonprimary_nulls.append(iid)
            for record in records:
                if record["item_id"] == iid:
                    record.update(grounding_status="UNVERIFIABLE", final_score=None,
                        score_before_ownership_cleanup=previous)
                    record["unverifiable_reasons"] = list(dict.fromkeys(record.get("unverifiable_reasons", []) +
                        ["NON_PRIMARY_OWNER_DEDUCTION_WITHOUT_INDEPENDENT_GROUNDED_DEFECT"]))
        ownership_records.append({"item_id": iid, "raw_item": copy.deepcopy(raw_row),
            "grounded_item_before_ownership_cleanup": before, "foreign_defect_ids": foreign,
            "original_primary_owner_item_ids": foreign_owners,
            "retained_independent_grounded_primary_defect_ids": own,
            "nonprimary_deduction_nulled": nulled, "final_score": row.get("score"),
            "action": "SCOPED_NULL_NOT_AUTOMATIC_FULL_MARK" if nulled else "REMOVE_FOREIGN_ATTRIBUTION_KEEP_INDEPENDENT_OR_UNDEDUCTED_SCORE",
            "no_automatic_score_increase": True})
    return value, {"schema_version": SCHEMA, "phase": phase,
        "deterministic_grounding_is_not_semantic_truth": True,
        "invalid_support_is_null_not_zero": True, "label_normalizations": label_normalizations,
        "item_records": records, "defect_records": defect_records,
        "deduction_ownership_cleanup": {"schema_version": "unique-primary-defect-scoped-nonowner-null-v4",
            "nulled_nonprimary_item_ids": nonprimary_nulls, "item_records": ownership_records,
            "original_primary_owners_unchanged": True, "no_automatic_full_marks": True,
            "no_semantic_correctness_claim": True, "no_prompt_or_rubric_changes": True},
        "defect_cleanup": {"schema_version": "scoped-unsupported-defect-owner-null-v1",
            "removed_defect_ids": sorted(removed),
            "nulled_owner_item_ids": sorted(unsupported_defect_owners),
            "no_original_quality_standard_changed": True,
            "no_item_evidence_automatically_copied_to_defect": True}}
