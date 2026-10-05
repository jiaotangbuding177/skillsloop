"""Lossless, content-addressed stage-4 transport with complete private evidence.

The model sees the indexed wire; host compilers expand it before checking source
relations. Indexing saves repeated representations, never filters source facts.
"""
from collections import Counter
from copy import deepcopy
import hashlib
import json

VERSION = 'workflow-input-index-v1'
TEXT_REF = '$workflowText'
RECORD_REF = '$workflowRecord'
CONTENT_KEYS = {'text', 'quote', 'content', 'result', 'requestedText', 'delta'}
TRANSPORT_KEYS = {'indexFormat', 'contentIndex', 'expandedHash'}


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def _hash(value):
    return hashlib.sha256(_json(value).encode('utf-8')).hexdigest()


def _record_key(value):
    kind = 'tuple' if isinstance(value, tuple) else 'list' if isinstance(value, list) else 'dict'
    return kind, _json(value)


def compact(payload):
    if not isinstance(payload, dict) or TRANSPORT_KEYS & payload.keys():
        raise ValueError('工作流原始输入含非法索引保留字段')
    counts = Counter()

    def scan(value):
        if isinstance(value, (dict, list, tuple)):
            counts[_record_key(value)] += 1
            for child in value.values() if isinstance(value, dict) else value:
                scan(child)
    scan(payload)
    texts, records = {}, {}

    def encode(value, key=None, inline=False):
        if isinstance(value, str):
            if key in CONTENT_KEYS or len(value) >= 96:
                tid = 'tx_' + _hash(value)[:24]
                if tid in texts and texts[tid] != value:
                    raise ValueError('工作流正文索引ID冲突')
                texts[tid] = value
                return {TEXT_REF:tid}
            return value
        if isinstance(value, (dict, list, tuple)):
            kind, serialized = _record_key(value)
            literal_ref = isinstance(value, dict) and set(value) in ({TEXT_REF}, {RECORD_REF})
            repeated = counts[(kind, serialized)] > 1 and len(serialized) >= 160
            if not inline and (repeated or literal_ref or isinstance(value, tuple)):
                rid = 'ob_' + _hash([kind, value])[:24]
                if rid not in records:
                    records[rid] = {'kind':kind, 'value':encode(value, inline=True)}
                return {RECORD_REF:rid}
            if isinstance(value, dict):
                return {k:encode(v,k) for k,v in value.items()}
            return [encode(v) for v in value]
        return deepcopy(value)

    result = encode(payload, inline=True)
    result.update(indexFormat=VERSION, contentIndex={'texts':texts,'records':records},
                  expandedHash=_hash(payload))
    # Verify the representation at its only trusted construction boundary.
    if expand(result) != payload:
        raise ValueError('工作流无损索引往返校验失败')
    return result


def expand(payload):
    if not isinstance(payload, dict):
        raise ValueError('工作流输入必须为对象')
    if 'indexFormat' not in payload:
        return deepcopy(payload)
    if payload.get('indexFormat') != VERSION:
        raise ValueError('工作流输入索引版本非法')
    index = payload.get('contentIndex')
    if not isinstance(index, dict) or not isinstance(index.get('texts'), dict) or not isinstance(index.get('records'), dict):
        raise ValueError('工作流正文/结构索引缺失')
    texts, records = index['texts'], index['records']
    active, resolved = set(), {}

    def decode(value, literal_root=False):
        if isinstance(value, dict):
            if not literal_root and set(value) == {TEXT_REF}:
                tid = value[TEXT_REF]
                text = texts.get(tid) if isinstance(tid, str) else None
                if not isinstance(text, str) or tid != 'tx_' + _hash(text)[:24]:
                    raise ValueError('工作流正文索引引用缺失或内容改变')
                return text
            if not literal_root and set(value) == {RECORD_REF}:
                rid = value[RECORD_REF]
                if not isinstance(rid, str) or rid not in records or rid in active:
                    raise ValueError('工作流结构索引引用缺失或循环')
                if rid not in resolved:
                    row = records[rid]
                    if not isinstance(row, dict) or row.get('kind') not in ('dict','list','tuple'):
                        raise ValueError('工作流结构索引条目非法')
                    active.add(rid)
                    full = decode(row.get('value'), literal_root=True)
                    active.remove(rid)
                    if row['kind'] == 'tuple':
                        if not isinstance(full, list):raise ValueError('工作流元组索引非法')
                        full = tuple(full)
                    if ((row['kind'] == 'dict' and not isinstance(full, dict))
                            or (row['kind'] == 'list' and not isinstance(full, list))
                            or rid != 'ob_' + _hash([row['kind'],full])[:24]):
                        raise ValueError('工作流结构索引内容改变')
                    resolved[rid] = full
                return deepcopy(resolved[rid])
            return {k:decode(v) for k,v in value.items()}
        if isinstance(value, list):
            return [decode(v) for v in value]
        return deepcopy(value)

    result = decode({k:v for k,v in payload.items() if k not in TRANSPORT_KEYS}, literal_root=True)
    if payload.get('expandedHash') != _hash(result):
        raise ValueError('工作流索引展开后完整性校验失败')
    return result


def wire(payload):
    """Avoid making already-small canonical inputs larger with index overhead."""
    indexed = compact(payload)
    if len(json.dumps(indexed,ensure_ascii=False)) < len(json.dumps(payload,ensure_ascii=False)):
        return indexed
    return deepcopy(payload)


PROMPT = '''若输入存在indexFormat=workflow-input-index-v1，则使用无损索引；否则字段直接给出完整材料。
采用索引时，contentIndex.texts是完整正文目录；
{"$workflowText":"tx_..."}表示到该目录读取原文。contentIndex.records是重复结构目录；
{"$workflowRecord":"ob_..."}表示读取条目的value并递归解析，其中kind说明原结构类型。
这些引用只消除重复存放，不表示证据缺失或省略。先解析所需引用再判断要求、尝试、反馈、评价和方法关系。
contentIndex中的tx_/ob_是内部内容索引，不是可作为方法evidenceRefs的新证据ID；仍只能引用原allowedEvidenceIds。
sourceId/requirementId/attemptId/关系ID及其作用域保持原身份，不得更改目录或将索引条目当作新增事实。'''
