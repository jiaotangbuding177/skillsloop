"""Role-grouped event-bag R adapter; no invented chronology or reply-to."""
from copy import deepcopy
import json
from skilldemo.relational import _score, _reason, _cycle

WIDTH = 8
MARGIN = 0.10

def compile_recovery(raw, source):
    messages = {m["id"]:m for m in source["messages"]}
    tasks = raw.get("tasks")
    if raw.get("session_id") != source["session_id"] or not isinstance(tasks,list):
        raise ValueError("Recovery session/tasks mismatch")
    task_map = {}
    for t in tasks:
        if t.get("id") in task_map or t.get("anchor_message") not in messages:
            raise ValueError("Invalid/duplicate task or missing anchor")
        if messages[t["anchor_message"]]["role"] != "user":
            raise ValueError("Task anchor must be actual user source")
        if t.get("outcome") != "UNKNOWN" or not all(t.get(k) for k in ("id","goal","object")):
            raise ValueError("Task status or goal invalid")
        task_map[t["id"]] = t
    rows = raw.get("memberships")
    if not isinstance(rows,list) or len(rows)!=len(messages):
        raise ValueError("Membership must cover all messages")
    proposals={};kinds={}
    for row in rows:
        mid=row.get("message_id")
        if mid not in messages or mid in proposals:
            raise ValueError("Missing/duplicate membership source")
        opts=row.get("options")
        if not isinstance(opts,list) or not 1<=len(opts)<=3:
            raise ValueError("Expected one to three membership candidates")
        legal=[]
        for opt in opts:
            ids=opt.get("task_ids")
            if not isinstance(ids,list) or len(set(ids))!=len(ids) or any(i not in task_map for i in ids):
                raise ValueError("Membership task IDs invalid")
            legal.append({"task_ids":ids,"score":_score(opt),"reason":_reason(opt)})
        proposals[mid]=legal;kinds[mid]=row.get("kind","OTHER")
    # Existing R ranking primitives, bounded candidate search; unknown ordering adds no temporal rule.
    beam=[(0.,{})]
    for mid,opts in proposals.items():
        expanded=[(s+o["score"],{**a,mid:o}) for s,a in beam for o in opts]
        beam=sorted(expanded,key=lambda x:x[0],reverse=True)[:WIDTH]
    best=beam[0]
    near=[a for s,a in beam if best[0]-s<=MARGIN]
    confirmed={};unresolved=[]
    for mid in proposals:
        selected=best[1][mid]
        sets={tuple(sorted(a[mid]["task_ids"])) for a in near}
        if len(sets)==1 and selected["task_ids"]:
            confirmed[mid]=selected["task_ids"]
        else:
            unresolved.append({"message_id":mid,"candidates":proposals[mid]})
    edges=[];selected_relations=[];unresolved_relations=[]
    for row in raw.get("relations",[]):
        src=row.get("source")
        if src not in messages:
            raise ValueError("Relation source missing")
        options=row.get("options",[])
        if not isinstance(options,list) or not options:
            raise ValueError("Relation candidates missing")
        legal=[]
        for opt in options:
            target=opt.get("target")
            score=_score(opt);reason=_reason(opt)
            ids=opt.get("source_ids",[])
            if target is not None and (target not in messages or target==src):
                raise ValueError("Relation target invalid")
            if any(i not in messages for i in ids):
                raise ValueError("Relation cites missing source")
            if target is None:
                legal.append({**opt,"score":score});continue
            if src not in ids or target not in ids:
                raise ValueError("Relation needs both endpoint sources")
            if row.get("kind")=="RESPONDS_TO" and not (
                messages[src]["role"]=="assistant" and messages[target]["role"]=="user"):
                raise ValueError("Response relation roles invalid")
            if not set(confirmed.get(src,[])) & set(confirmed.get(target,[])):
                continue
            if _cycle([*edges,(src,target)]):
                continue
            legal.append({**opt,"score":score})
        legal.sort(key=lambda o:o["score"],reverse=True)
        if not legal or legal[0].get("target") is None or (
                len(legal)>1 and legal[0]["score"]-legal[1]["score"]<=MARGIN):
            unresolved_relations.append(deepcopy(row));continue
        opt=legal[0];edges.append((src,opt["target"]))
        selected_relations.append({"source":src,"target":opt["target"],"kind":row["kind"],
            "reason":opt["reason"],"source_ids":opt["source_ids"],
            "status":"SOURCE_CHECKED_SEMANTIC_INFERENCE","chronology_verified":False})
    reqs=[]
    for row in raw.get("requirements",[]):
        if row.get("task_id") not in task_map or row.get("source_id") not in messages:
            raise ValueError("Requirement source/task invalid")
        if messages[row["source_id"]]["role"]!="user" or not row.get("value"):
            raise ValueError("Requirement must have visible user source")
        if row.get("scope") not in ("CURRENT_TASK","CURRENT_DELIVERY","EXPLICIT_FUTURE_PREFERENCE"):
            raise ValueError("Requirement scope invalid")
        if row["task_id"] not in confirmed.get(row["source_id"],[]):
            continue
        reqs.append(deepcopy(row))
    traces=[]
    for tid,t in task_map.items():
        traces.append({**deepcopy(t),"message_ids":[m for m in messages if tid in confirmed.get(m,[])],
            "relations":[r for r in selected_relations if tid in confirmed.get(r["source"],[]) and tid in confirmed.get(r["target"],[])],
            "requirements":[r for r in reqs if r["task_id"]==tid],
            "outcome":"UNKNOWN","chronology_verified":False})
    return {"session_id":source["session_id"],"adapter":"eventbag-relational-v1",
        "tasks":traces,"memberships":confirmed,"kinds":kinds,
        "unresolved_memberships":unresolved,"unresolved_relations":unresolved_relations,
        "uncertainties":raw.get("uncertainties",[]),"all_source_messages_preserved":True,
        "semantic_validation":"NOT_INDEPENDENTLY_VERIFIED"}

