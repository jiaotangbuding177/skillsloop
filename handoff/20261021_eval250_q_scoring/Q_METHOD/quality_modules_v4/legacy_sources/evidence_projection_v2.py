"""Transparent, reversible evidence projection. No truncation or opaque codec.

Only exact duplicate text representations and repeated record keys/constants
are factored. Every unique string, XML byte string, cell and value is retained.
"""
from __future__ import annotations
import copy
import hashlib
import json

SCHEMA = "eval250-lossless-evidence-projection-v2"
MARKER = "__ev2__"
KEEP_RECORD_LISTS = {"sources", "artifacts", "outputs", "functional_observations",
    "evidence_index", "visual_pages", "render_images", "artifact_correspondence"}
EXPLANATION = """证据采用透明无损紧凑表示，不删内容：__ev2__.kind=table时，all_columns保留原字段顺序，constants是每行共有值，columns与rows按列一一对应；所有行都在，missing标记表示原行无此键，和null不同，key_orders仅记录少数行的原键顺序。kind=aliases时，其他字段原样保留，aliases.text明确给出该重复text来自哪个已给字段/对象及JSON序列化格式；不用把同一内容再复制一份。kind=literal_object仅转义原数据恰有__ev2__字段的情况。所有唯一正文、XML、公式、原缓存、样式值和图片均保留；不得把紧凑表示误判为产物缺内容。"""


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


RECIPES = {
    "canonical": {"ensure_ascii": False, "sort_keys": True, "separators": (",", ":")},
    "compact": {"ensure_ascii": False, "separators": (",", ":")},
    "default": {"ensure_ascii": False},
    "pretty2": {"ensure_ascii": False, "indent": 2},
    "pretty2_sorted": {"ensure_ascii": False, "sort_keys": True, "indent": 2},
    "ascii_canonical": {"ensure_ascii": True, "sort_keys": True, "separators": (",", ":")},
    "ascii_default": {"ensure_ascii": True},
}


def _json_render(value, recipe, newline=False):
    return json.dumps(value, allow_nan=False, **RECIPES[recipe]) + ("\n" if newline else "")


def _json_recipe(text, target):
    try:
        parsed = json.loads(text)
        if canonical(parsed) != canonical(target):
            return None
    except (ValueError, TypeError):
        return None
    for recipe in RECIPES:
        rendered = _json_render(target, recipe)
        if text == rendered:
            return {"recipe": recipe, "newline": False}
        if text == rendered + "\n":
            return {"recipe": recipe, "newline": True}
    # Unknown whitespace/order is retained verbatim, rather than guessed.
    return None


def _text_alias(record):
    text = record.get("text")
    if not isinstance(text, str):
        return None
    extraction = record.get("extraction")
    if isinstance(extraction, dict) and isinstance(extraction.get("text"), str) and text == extraction["text"]:
        return {"kind": "same_value", "path": ["extraction", "text"]}
    for field, target in record.items():
        if field == "text" or not isinstance(target, (dict, list)):
            continue
        recipe = _json_recipe(text, target)
        if recipe:
            return dict(recipe, kind="json_field", field=field)
    base = {key: value for key, value in record.items() if key != "text"}
    recipe = _json_recipe(text, base)
    return dict(recipe, kind="json_self") if recipe else None


def project(value):
    """Return (projected_value, audit_receipt); assert exact inverse internally."""
    counts = {"text_aliases": 0, "record_tables": 0, "table_records": 0,
              "table_constant_fields": 0, "literal_marker_escapes": 0}

    def encode(node, path=()):
        if isinstance(node, list):
            children = [encode(child, path + (str(i),)) for i, child in enumerate(node)]
            if len(node) < 2 or not all(isinstance(child, dict) for child in node) or (path and path[-1] in KEEP_RECORD_LISTS) or any(MARKER in child for child in children):
                return children
            # Alias/escaped nodes remain object records with a marker; storing
            # them as ordinary table values remains lossless and unambiguous.
            all_columns = list(dict.fromkeys(key for child in children for key in child))
            constants = {}
            for key in all_columns:
                if all(key in child for child in children):
                    signature = canonical(children[0][key])
                    if all(canonical(child[key]) == signature for child in children[1:]):
                        constants[key] = children[0][key]
            columns = [key for key in all_columns if key not in constants]
            missing = {MARKER: {"kind": "missing"}}
            rows = [[child.get(key, missing) for key in columns] for child in children]
            key_orders = {str(i): list(child) for i, child in enumerate(children)
                          if list(child) != [key for key in all_columns if key in child]}
            data = {"kind": "table", "all_columns": all_columns,
                    "columns": columns, "constants": constants, "rows": rows}
            if key_orders:
                data["key_orders"] = key_orders
            candidate = {MARKER: data}
            if len(compact(candidate)) >= len(compact(children)):
                return children
            counts["record_tables"] += 1
            counts["table_records"] += len(children)
            counts["table_constant_fields"] += len(constants)
            return candidate
        if not isinstance(node, dict):
            return node
        if MARKER in node:
            counts["literal_marker_escapes"] += 1
            return {MARKER: {"kind": "literal_object", "entries": [[key, encode(val, path + (key,))] for key, val in node.items()]}}
        alias = _text_alias(node)
        result = {key: encode(val, path + (key,)) for key, val in node.items() if key != "text" or alias is None}
        if alias:
            result[MARKER] = {"kind": "aliases", "aliases": {"text": alias}, "key_order": list(node)}
            counts["text_aliases"] += 1
        return result

    projected = encode(value)
    restored = reconstruct(projected)
    original_sha = _digest(value)
    restored_sha = _digest(restored)
    if value != restored or original_sha != restored_sha:
        raise AssertionError("Lossless projection inverse mismatch")
    old_text, new_text = compact(value), compact(projected)
    receipt = {"schema_version": SCHEMA, "original_canonical_sha256": original_sha,
        "reconstructed_canonical_sha256": restored_sha, "deep_equal": True,
        "all_unique_content_retained": True, "truncation": False, "opaque_compression": False,
        "original_compact_characters": len(old_text), "projected_compact_characters": len(new_text),
        "text_reduction_fraction": 1 - len(new_text) / len(old_text) if old_text else 0,
        **counts}
    return projected, receipt


def reconstruct(value):
    """Symmetric inverse including missing-vs-null and literal marker keys."""
    missing = object()

    def decode(node):
        if isinstance(node, list):
            return [decode(child) for child in node]
        if not isinstance(node, dict):
            return node
        meta = node.get(MARKER)
        if isinstance(meta, dict):
            kind = meta.get("kind")
            if kind == "missing" and len(node) == 1:
                return missing
            if kind == "literal_object" and len(node) == 1:
                return {key: decode(val) for key, val in meta["entries"]}
            if kind == "table" and len(node) == 1:
                constants = {key: decode(val) for key, val in meta["constants"].items()}
                result = []
                for i, row in enumerate(meta["rows"]):
                    if len(row) != len(meta["columns"]):
                        raise ValueError("Malformed compact table row width")
                    values = dict(constants)
                    values.update({key: decode(val) for key, val in zip(meta["columns"], row)})
                    order = meta.get("key_orders", {}).get(str(i), meta["all_columns"])
                    result.append({key: copy.deepcopy(values[key]) for key in order if values.get(key, missing) is not missing})
                return result
            if kind == "aliases":
                base = {key: decode(val) for key, val in node.items() if key != MARKER}
                for field, alias in meta["aliases"].items():
                    if alias["kind"] == "same_value":
                        target = base
                        for key in alias["path"]:
                            target = target[key]
                        base[field] = copy.deepcopy(target)
                    elif alias["kind"] == "json_field":
                        base[field] = _json_render(base[alias["field"]], alias["recipe"], alias["newline"])
                    elif alias["kind"] == "json_self":
                        base[field] = _json_render(base, alias["recipe"], alias["newline"])
                    else:
                        raise ValueError("Unknown text alias kind")
                return {key: base[key] for key in meta["key_order"]}
            raise ValueError("Unknown or ambiguous projection marker")
        return {key: decode(val) for key, val in node.items()}
    return decode(value)
