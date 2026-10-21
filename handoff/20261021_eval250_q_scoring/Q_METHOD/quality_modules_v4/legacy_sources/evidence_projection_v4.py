"""Complete business evidence, with the redundant local atom index not sent.

Only metadata repetition is factored.  Complete values, states, XML and images
are retained.  The decoder is symmetric and type-sensitive SHA checked.
"""
from __future__ import annotations
import copy
import hashlib
import json
import re
from collections import Counter

import evidence_projection_v2 as v2

SCHEMA = "eval250-business-evidence-projection-v4-local-atom-index"
ATOM_MARKER = "__atom_catalog_v3__"
SHARED_MARKER = "__shared_text_v3__"
EXPLANATION = v2.EXPLANATION + """
本轮不投递本机冗余atom编号目录，完整业务证据仍全部给出。文字引用直接返回evidence_id、还原后完整证据内的绝对json_pointer及exact_quote，不需猜atom_id或冗余locator，host会唯一反查并验证原文/角色/产物。例如实际某值在artifacts第0项的extraction.text，pointer为/artifacts/0/extraction/text；路径键内'/'编码为~1，'~'编码为~0。引用必须具体落到原字符串/数值/布尔/null等scalar，不能指整个对象或数组。若正文采用__ev2__table/aliases/shared表示，json_pointer始终针对完整还原结构，而非紧凑表示的rows/shared_strings位置。不能用编号目录本身当业务证据。
最外层__shared_text_v3__.kind=document中data为完整证据，shared_strings是完全相同长字符串的共享原文；形如{"__shared_text_v3__":{"kind":"string_ref","id":"S00001"}}精确等于shared_strings.S00001的全文，非摘要、非缺失。shared_values给出完全相同长对象/数组的完整结构，kind=value_ref/id=V00001精确引用shared_values.V00001；其中还可引用同一字典的共享原文或对象。kind=literal_object仅转义原数据同名键。先递归展开共享值，再按__ev2__规则还原。所有状态、原值、唯一业务字符串和图片均保留；不可因共享形式判断产物缺内容。"""


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha(value):
    return hashlib.sha256(canonical(value).encode("utf8")).hexdigest()


def _atom_groups(atoms):
    """Fallback untouched if a nonstandard catalog cannot be derived exactly."""
    if not isinstance(atoms, list) or not atoms:
        return atoms, False
    groups = []
    current = None
    last_serial = -1
    for atom in atoms:
        if not isinstance(atom, dict) or set(atom) != {"atom_id", "evidence_id", "role", "locator", "json_pointer", "value_type"} or not all(isinstance(v, str) for v in atom.values()):
            return atoms, False
        match = re.fullmatch(re.escape(atom["evidence_id"]) + r":A([0-9]+)", atom["atom_id"])
        pointer = atom["json_pointer"]
        if not match or not pointer.startswith("/") or len(pointer.split("/")) < 4 or not atom["locator"].endswith(" @" + pointer):
            return atoms, False
        tokens = pointer.split("/")[1:]
        prefix = "/" + "/".join(tokens[:2])
        locator_prefix = atom["locator"][:-len(" @" + pointer)]
        key = (atom["evidence_id"], atom["role"], prefix, locator_prefix)
        serial = int(match.group(1))
        if current is None or current["_key"] != key:
            current = {"_key": key, "evidence_id": key[0], "role": key[1],
                       "pointer_prefix": prefix, "locator_prefix": locator_prefix, "paths": [], "_paths": {}}
            groups.append(current)
            last_serial = -1
        if serial <= last_serial:
            return atoms, False
        last_serial = serial
        parts, indices = [], []
        for token in tokens[2:]:
            if token.isdigit() and str(int(token)) == token:
                parts.append(None)
                indices.append(int(token))
            else:
                parts.append(token)
        pattern_key = compact(parts)
        if pattern_key not in current["_paths"]:
            record = {"parts": parts, "columns": ["atom_id", "indices", "value_type"], "rows": []}
            current["paths"].append(record)
            current["_paths"][pattern_key] = record
        current["_paths"][pattern_key]["rows"].append([atom["atom_id"], indices, atom["value_type"]])
    for group in groups:
        group.pop("_key")
        group.pop("_paths")
        for path in group["paths"]:
            types = {row[2] for row in path["rows"]}
            if len(types) == 1:
                path["value_type"] = next(iter(types))
                path["columns"] = ["atom_id", "indices"]
                path["rows"] = [row[:2] for row in path["rows"]]
    result = {ATOM_MARKER: {"schema": "pointer-patterns-v1", "order": "GROUP_THEN_NUMERIC_A_SUFFIX", "groups": groups}}
    if len(compact(result)) >= len(compact(atoms)):
        return atoms, False
    return result, True


def _expand_atoms(value):
    if not isinstance(value, dict) or set(value) != {ATOM_MARKER}:
        return value
    meta = value[ATOM_MARKER]
    if meta.get("schema") != "pointer-patterns-v1" or meta.get("order") != "GROUP_THEN_NUMERIC_A_SUFFIX":
        raise ValueError("Unknown atom projection schema")
    atoms = []
    for group in meta["groups"]:
        rows = []
        for path in group["paths"]:
            for row in path["rows"]:
                if len(row) != len(path["columns"]):
                    raise ValueError("Atom compact row width mismatch")
                data = dict(zip(path["columns"], row))
                indices = iter(data["indices"])
                parts = [str(next(indices)) if token is None else token for token in path["parts"]]
                if next(indices, None) is not None:
                    raise ValueError("Unused atom path index")
                pointer = group["pointer_prefix"] + "/" + "/".join(parts)
                atom_id = data["atom_id"]
                serial = int(re.fullmatch(re.escape(group["evidence_id"]) + r":A([0-9]+)", atom_id).group(1))
                rows.append((serial, {"atom_id": atom_id, "evidence_id": group["evidence_id"], "role": group["role"],
                    "locator": group["locator_prefix"] + " @" + pointer, "json_pointer": pointer,
                    "value_type": data.get("value_type", path.get("value_type"))}))
        atoms.extend(atom for _, atom in sorted(rows, key=lambda pair: pair[0]))
    return atoms


def _share_strings(value):
    counts = Counter()
    structure_counts = Counter()
    def count(node):
        if isinstance(node, str):
            if len(node) >= 128:
                counts[node] += 1
        elif isinstance(node, list):
            signature = compact(node)
            if len(signature) >= 256:
                structure_counts[signature] += 1
            for child in node:
                count(child)
        elif isinstance(node, dict):
            signature = compact(node)
            if len(signature) >= 256:
                structure_counts[signature] += 1
            for child in node.values():
                count(child)
    count(value)
    eligible_strings = {text for text, n in counts.items() if n >= 2 and (n - 1) * len(text) > 90 * n + 30}
    eligible_values = {text for text, n in structure_counts.items() if n >= 2 and (n - 1) * len(text) > 90 * n + 30}
    ids, value_ids, shared_strings, shared_values = {}, {}, {}, {}
    references = 0
    def encode(node, skip_self=False):
        nonlocal references
        if isinstance(node, str) and node in eligible_strings:
            references += 1
            if node not in ids:
                ids[node] = f"S{len(ids) + 1:05d}"
                shared_strings[ids[node]] = node
            return {SHARED_MARKER: {"kind": "string_ref", "id": ids[node]}}
        if isinstance(node, (list, dict)) and not skip_self:
            signature = compact(node)
            if signature in eligible_values:
                references += 1
                if signature not in value_ids:
                    value_ids[signature] = f"V{len(value_ids) + 1:05d}"
                    shared_values[value_ids[signature]] = encode(node, skip_self=True)
                return {SHARED_MARKER: {"kind": "value_ref", "id": value_ids[signature]}}
        if isinstance(node, list):
            return [encode(child) for child in node]
        if isinstance(node, dict):
            if SHARED_MARKER in node:
                return {SHARED_MARKER: {"kind": "literal_object", "entries": [[key, encode(child)] for key, child in node.items()]}}
            return {key: encode(child) for key, child in node.items()}
        return node
    encoded = encode(value)
    return {SHARED_MARKER: {"kind": "document", "shared_strings": shared_strings, "shared_values": shared_values, "data": encoded}}, len(shared_strings), len(shared_values), references


def _unshare(value):
    if not isinstance(value, dict) or set(value) != {SHARED_MARKER} or value[SHARED_MARKER].get("kind") != "document":
        raise ValueError("Malformed shared evidence document")
    root = value[SHARED_MARKER]
    strings = root["shared_strings"]
    values = root.get("shared_values", {})
    cache = {}
    def decode(node):
        if isinstance(node, list):
            return [decode(child) for child in node]
        if not isinstance(node, dict):
            return node
        if set(node) == {SHARED_MARKER}:
            meta = node[SHARED_MARKER]
            if meta.get("kind") == "string_ref":
                return strings[meta["id"]]
            if meta.get("kind") == "value_ref":
                identifier = meta["id"]
                if identifier not in cache:
                    cache[identifier] = decode(values[identifier])
                return copy.deepcopy(cache[identifier])
            if meta.get("kind") == "literal_object":
                return {key: decode(child) for key, child in meta["entries"]}
            raise ValueError("Unknown shared text marker")
        return {key: decode(child) for key, child in node.items()}
    return decode(root["data"])


def project(value):
    prepared = copy.deepcopy(value)
    local_atoms = []
    if isinstance(prepared, dict) and isinstance(prepared.get("evidence_atoms"), list):
        local_atoms = prepared.pop("evidence_atoms")
    projected, v2_receipt = v2.project(prepared)
    result, shared_count, shared_value_count, reference_count = _share_strings(projected)
    restored = reconstruct(result)
    original_sha, restored_sha = _sha(prepared), _sha(restored)
    if prepared != restored or original_sha != restored_sha:
        raise AssertionError("V4 non-catalog evidence inverse or typed canonical SHA mismatch")
    old, new = compact(value), compact(result)
    return result, {"schema_version": SCHEMA, "original_canonical_sha256": original_sha,
        "reconstructed_canonical_sha256": restored_sha, "deep_equal": True,
        "equality_scope": "ALL_SAFE_FIELDS_EXCEPT_REDUNDANT_LOCAL_evidence_atoms_INDEX",
        "type_sensitive_canonical_sha_equal": True, "all_unique_business_content_retained": True,
        "truncation": False, "opaque_compression": False,
        "original_compact_characters": len(old), "projected_compact_characters": len(new),
        "text_reduction_fraction": 1 - len(new) / len(old) if old else 0,
        "local_atom_index_count": len(local_atoms), "local_atom_index_sha256": _sha(local_atoms),
        "atom_index_sent": False, "local_atom_index_available_for_exact_pointer_lookup": True,
        "shared_exact_strings": shared_count,
        "shared_exact_structures": shared_value_count, "shared_value_references": reference_count,
        "v2_structural_projection": v2_receipt}


def reconstruct(value):
    return v2.reconstruct(_unshare(value))
