"""Trace scalar origins through the exact frozen lossless codecs, no search.

The returned index never enters model input.  Quoted values never select a
location: address candidates must be unique before any quote is examined.
"""
from __future__ import annotations
import copy
import hashlib
import json
from dataclasses import dataclass
import evidence_projection_v2 as v2
import evidence_projection_v4 as v4


def pointer_path(parts):
    return "".join("/" + str(part).replace("~", "~0").replace("/", "~1") for part in parts)


@dataclass
class Scalar:
    value: object
    origins: set


def plain(node):
    if isinstance(node, Scalar):
        return node.value
    if isinstance(node, list):
        return [plain(x) for x in node]
    if isinstance(node, dict):
        return {key: plain(value) for key, value in node.items()}
    return node


def _annotate(node, path=()):
    if isinstance(node, list):
        return [_annotate(value, path + (str(i),)) for i, value in enumerate(node)]
    if isinstance(node, dict):
        return {key: _annotate(value, path + (key,)) for key, value in node.items()}
    return Scalar(node, {path})


def _leaf_walk(node, path=()):
    if isinstance(node, Scalar):
        yield path, node
    elif isinstance(node, list):
        for i, child in enumerate(node):
            yield from _leaf_walk(child, path + (str(i),))
    elif isinstance(node, dict):
        for key, child in node.items():
            yield from _leaf_walk(child, path + (key,))


def _decode_shared(wire):
    marker = v4.SHARED_MARKER
    root = wire[marker]
    if plain(root["kind"]) != "document":
        raise ValueError("Unsupported exact wire document")
    strings, values = root["shared_strings"], root.get("shared_values", {})
    resolving = set()
    cache = {}
    def decode(node):
        if isinstance(node, list):
            return [decode(value) for value in node]
        if isinstance(node, Scalar):
            return copy.deepcopy(node)
        if set(node) == {marker}:
            meta = node[marker]
            kind = plain(meta["kind"])
            if kind == "string_ref":
                return copy.deepcopy(strings[plain(meta["id"])])
            if kind == "value_ref":
                key = plain(meta["id"])
                if key in resolving:
                    raise ValueError("Cyclic shared value")
                if key not in cache:
                    resolving.add(key)
                    cache[key] = decode(values[key])
                    resolving.remove(key)
                return copy.deepcopy(cache[key])
            if kind == "literal_object":
                return {plain(key): decode(value) for key, value in meta["entries"]}
            raise ValueError("Unsupported wire shared marker")
        return {key: decode(value) for key, value in node.items()}
    return decode(root["data"])


def _decode_v2(node):
    missing = object()
    marker = v2.MARKER
    def decode(value):
        if isinstance(value, Scalar):
            return copy.deepcopy(value)
        if isinstance(value, list):
            return [decode(child) for child in value]
        meta = value.get(marker)
        if isinstance(meta, dict):
            kind = plain(meta.get("kind"))
            if kind == "missing" and len(value) == 1:
                return missing
            if kind == "literal_object" and len(value) == 1:
                return {plain(key): decode(child) for key, child in meta["entries"]}
            if kind == "table" and len(value) == 1:
                constants = {key: decode(child) for key, child in meta["constants"].items()}
                columns, all_columns = plain(meta["columns"]), plain(meta["all_columns"])
                result = []
                for i, row in enumerate(meta["rows"]):
                    if len(row) != len(columns):
                        raise ValueError("Wire table width mismatch")
                    fields = copy.deepcopy(constants)
                    fields.update({key: decode(child) for key, child in zip(columns, row)})
                    order = plain(meta.get("key_orders", {}).get(str(i), meta["all_columns"]))
                    result.append({key: fields[key] for key in order if fields.get(key, missing) is not missing})
                return result
            if kind == "aliases":
                base = {key: decode(child) for key, child in value.items() if key != marker}
                for field, raw_alias in meta["aliases"].items():
                    alias = plain(raw_alias)
                    if alias["kind"] == "same_value":
                        target = base
                        for key in alias["path"]:
                            target = target[key]
                        base[field] = copy.deepcopy(target)
                    elif alias["kind"] == "json_field":
                        base[field] = Scalar(v2._json_render(plain(base[alias["field"]]), alias["recipe"], alias["newline"]), set())
                    elif alias["kind"] == "json_self":
                        base[field] = Scalar(v2._json_render(plain(base), alias["recipe"], alias["newline"]), set())
                    else:
                        raise ValueError("Unknown exact alias recipe")
                return {key: base[key] for key in plain(meta["key_order"])}
            raise ValueError("Unknown wire V2 marker")
        return {key: decode(child) for key, child in value.items()}
    return decode(node)


def _address_aliases(path):
    """Only named protocol wrappers may be transparently omitted."""
    paths = {path}
    outer = (v4.SHARED_MARKER, "data")
    if path[:2] == outer:
        paths.add(path[2:])
    if path and path[0] == v4.SHARED_MARKER:
        paths.add(path[1:])
    for candidate in list(paths):
        paths.add(tuple(part for part in candidate if part != v2.MARKER))
    return {pointer_path(candidate) for candidate in paths}


def build_provenance(projected, expected_business=None):
    annotated = _annotate(projected)
    expanded = _decode_shared(annotated)
    # Each occurrence of a shared value gains an exact expanded wire address;
    # the physical shared-dictionary leaf also remains addressable/ambiguous.
    for path, scalar in _leaf_walk(expanded):
        scalar.origins.add((v4.SHARED_MARKER, "data") + path)
    decoded = _decode_v2(expanded)
    restored = plain(decoded)
    expected = v4.reconstruct(projected) if expected_business is None else expected_business
    if v4.canonical(restored) != v4.canonical(expected):
        raise AssertionError("Provenance decoder changed business values/types")
    mapping, values = {}, {}
    for path, scalar in _leaf_walk(decoded):
        canonical = pointer_path(path)
        values[canonical] = scalar.value
        for origin in scalar.origins:
            for alias in _address_aliases(origin):
                mapping.setdefault(alias, set()).add(canonical)
    receipt = {"schema_version": "wire-scalar-provenance-v5", "business_typed_inverse_equal": True,
        "canonical_scalar_count": len(values), "wire_address_count": len(mapping),
        "mapping_sha256": hashlib.sha256(v4.canonical({k: sorted(v) for k, v in mapping.items()}).encode("utf8")).hexdigest(),
        "quote_or_value_search": False, "only_named_protocol_wrappers_may_be_omitted": True}
    return {"mapping": mapping, "values": values, "receipt": receipt}
