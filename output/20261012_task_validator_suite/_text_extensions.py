"""Objective terminal delivery extensions; missing evidence is never a pass.

No actors, services, model calls, source code execution or semantic quality judge.
Collector-owned snapshots and receipt pins are an external trust boundary.
"""
import base64
import hashlib
import io
import json
import os
import posixpath
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from urllib.parse import unquote
from xml.etree import ElementTree as ET


def nf(value):
    return unicodedata.normalize("NFKC", str(value))


def flat(value):
    return re.sub(r"\s+", "", nf(value))


def numbered_entries(text):
    pattern = (r"(?im)^\s*(?:#{1,6}\s*)?(?:\*\*)?"
               r"(?:第\s*(\d+)\s*[页张项]|(?:slide|page)\s*[_ -]?(\d+)"
               r"|(\d+)[.、)．]\s*)([^\n]*)")
    matches = list(re.finditer(pattern, nf(text)))
    # Explicit page/slide markers establish the unit; nested generic lists are details.
    if any(m.group(1) is not None or m.group(2) is not None for m in matches):
        matches=[m for m in matches if m.group(1) is not None or m.group(2) is not None]
    normalized = nf(text)
    result = []
    for i, m in enumerate(matches):
        number = int(next(x for x in m.groups()[:3] if x is not None))
        tail = normalized[m.end():matches[i+1].start() if i+1 < len(matches) else len(normalized)]
        body = (m.group(4) + "\n" + tail).strip().strip(":：* ")
        result.append((number, body))
    return result


class ImageTags(HTMLParser):
    def __init__(self):
        super().__init__(); self.images = []
    def handle_starttag(self, tag, attrs):
        if tag.casefold() == "img":
            a = dict(attrs); self.images.append((a.get("alt", "") + " " + a.get("title", ""), a.get("src", "")))


def table_rows(text):
    """Explicit Markdown/tab matrices; ordinary prose is not a table."""
    rows = []
    for line in nf(text).splitlines():
        if "|" in line and line.count("|") >= 2:
            cells = [x.strip() for x in line.strip().strip("|").split("|")]
        elif "\t" in line:
            cells = [x.strip() for x in line.split("\t")]
        else:
            continue
        if cells and all(re.fullmatch(r":?-+:?", x or "-") for x in cells):
            continue
        rows.append(cells)
    return rows


def section_payloads(text):
    pattern = (r"(?m)^\s*(?:#{1,6}\s*)?(?:第\s*)?"
               r"([一二三四五六七八九十]+|\d+)\s*(?:章|[、.．）)])\s*([^\n]*)")
    found = list(re.finditer(pattern, nf(text))); result = {}
    digits = {"一":"1","二":"2","三":"3","四":"4","五":"5","六":"6","七":"7","八":"8","九":"9","十":"10"}
    for i, m in enumerate(found):
        key = digits.get(m.group(1), m.group(1))
        if key in result:
            return {}
        tail = nf(text)[m.end():found[i+1].start() if i+1 < len(found) else len(nf(text))]
        result[key] = m.group(2) + "\n" + tail
    return result


def pixels(image):
    image.load()
    normalized = image.convert("RGBA")
    return (normalized.size, hashlib.sha256(normalized.tobytes()).hexdigest())


def register_extensions(base):
    def need(test, reason):
        if not test:
            raise base.UnknownEvidence(reason)

    def require(test, reason):
        if not test:
            raise base.DeliveryFailure(reason)

    def guard(p, allowed):
        need(isinstance(p, dict), "invalid_text_extension_parameters")
        unknown = set(p) - set(allowed) - base.POLICY_PARAMETER_NAMES
        need(not unknown, "unsupported_text_extension_parameters:" + ",".join(sorted(unknown)))
        if "historical_ai_is_gold" in p:
            need(p["historical_ai_is_gold"] is False,"historical_ai_gold_policy_forbidden")
        if "score_at" in p:
            need(p["score_at"] in ("conversation_end_only","end_of_conversation","final_state_only"),"non_terminal_score_policy_forbidden")

    def text(ctx, did):
        value = ctx.text(did)
        need(isinstance(value, str) and bool(value.strip()), "actual_final_text_not_extractable")
        return nf(value)

    def actual_files(ctx, did, formats=None):
        paths = ctx.files(did, formats)
        require(bool(paths), "actual_final_files_missing")
        for path in paths:
            ctx.info(path)
        return paths

    def minimum(ctx, did, p, kind):
        guard(p, ["min_characters", "count_mode"])
        need(type(p.get("min_characters")) is int and p["min_characters"] > 0, "invalid_character_minimum")
        need(p.get("count_mode", "non_whitespace_unicode_codepoints") == "non_whitespace_unicode_codepoints", "unknown_character_count_mode")
        count = len(re.sub(r"\s", "", ctx.text(did)))
        require(count >= p["min_characters"], "explicit_character_minimum_not_met")
        return {"characters": count, "minimum": p["min_characters"]}

    def item_count(ctx, did, p, kind):
        guard(p, ["count"])
        need(type(p.get("count")) is int and p["count"] > 0, "invalid_item_count")
        items = numbered_entries(text(ctx, did))
        need(bool(items), "numbered_items_not_identifiable")
        require(len(items) == p["count"], "numbered_item_count_mismatch")
        require(all(body for _, body in items), "numbered_item_body_empty")
        require(len({n for n, _ in items}) == len(items), "numbered_item_ordinals_duplicate")
        return {"item_count": len(items), "ordinals": [n for n, _ in items]}

    def status_only(ctx, did, p, kind):
        guard(p, ["phrases"])
        need(isinstance(p.get("phrases"), list) and all(isinstance(x, str) for x in p["phrases"]), "invalid_status_phrases")
        value = nf(ctx.text(did)).strip().rstrip("。.!！… ")
        exact = value in [nf(x).strip().rstrip("。.!！… ") for x in p["phrases"]]
        return {"exact_status_only": exact, "scorable": False, "applicable": False}

    def formats(ctx, did, p, kind):
        guard(p, ["formats", "aliases"])
        need(isinstance(p.get("formats"), list) and p["formats"], "input_format_requirements_missing")
        aliases = {"latex": ["latex", ".tex"], "markdown": ["markdown", ".md"],
                   "word": ["word", ".doc", ".docx"], "pdf": ["pdf"]}
        supplied = p.get("aliases", {})
        need(isinstance(supplied, dict), "invalid_format_aliases")
        aliases.update(supplied)
        bound = ctx.binding(did)
        need(bound.get("directory") or bound.get("files"), "final_skill_file_binding_missing")
        candidates = ctx.files(did)
        docs = []
        for path in candidates:
            if path.is_file() and path.name.casefold() == "skill.md":
                docs.append(path.read_text("utf-8-sig"))
        if not docs:
            for path in candidates:
                if path.is_file() and path.suffix.casefold() in (".md", ".txt"):
                    docs.append(path.read_text("utf-8-sig"))
        need(bool(docs), "actual_skill_input_contract_missing")
        regions = []
        for doc in docs:
            lines = nf(doc).splitlines()
            for i, line in enumerate(lines):
                if re.search(r"输入格式|支持.{0,6}格式|input\s+formats?|supported\s+(?:input\s+)?formats?", line, re.I):
                    tail = []
                    for following in lines[i+1:]:
                        if re.match(r"^\s*#{1,6}\s", following): break
                        tail.append(following)
                    regions.append(line + "\n" + "\n".join(tail))
        need(bool(regions), "input_format_declaration_not_identifiable")
        declared = "\n".join(regions).casefold()
        for form in p["formats"]:
            candidates = aliases.get(form, [form])
            need(isinstance(candidates, list) and candidates, "invalid_input_format_alias")
            positive=False; negative=False
            for line in declared.splitlines():
                if any(re.search(r"(?<![A-Za-z])" + re.escape(nf(a).casefold()) + r"(?![A-Za-z])",line) for a in candidates):
                    if re.search(r"不支持|不接受|unsupported|not\s+supported|not\s+accepted",line,re.I):
                        negative=True
                    else: positive=True
            need(not (positive and negative),"contradictory_input_format_declaration:"+form)
            require(positive and not negative,"declared_input_format_missing:"+form)
        return {"format_count": len(p["formats"]), "declaration_only": True}

    def numeric_reference(ctx, did, p, kind):
        guard(p, ["require_numeric_token"])
        need(type(p.get("require_numeric_token", True)) is bool, "invalid_require_numeric_token")
        value = text(ctx, did)
        numeric = re.findall(r"(?<![A-Za-z])\d+(?:\.\d+)?", value)
        if p.get("require_numeric_token", True):
            require(bool(numeric), "numeric_marker_missing")
        refs = re.findall(r"https?://[^\s)]+|(?:数据)?来源\s*[:：]|参考文献|参考资料|Source\s*:|References\b|\[\d+\]", value, re.I)
        for path in ctx.files(did) if ctx.binding(did).get("files") else []:
            info = ctx.info(path)
            if info["format"] == "docx":
                refs.extend(["docx_reference"] * len(info["tree"].findall(".//w:hyperlink", base.NS)))
                if any(x in info["members"] for x in ("word/footnotes.xml", "word/endnotes.xml")):
                    refs.append("docx_note")
        need(bool(refs), "reference_structure_not_reliably_identifiable")
        return {"numeric_count": len(numeric), "reference_count": len(refs), "truth_verified": False}

    def literals(ctx, did, p, kind):
        guard(p, ["fields"])
        need(isinstance(p.get("fields"), list) and p["fields"] and all(isinstance(v, str) for v in p["fields"]), "literal_fields_invalid")
        paths = actual_files(ctx, did, ["pdf"])
        value = "\n".join(ctx.info(f).get("text", "") for f in paths)
        need(bool(value.strip()), "pdf_native_text_unavailable_no_ocr_judge")
        require(all(flat(v) in flat(value) for v in p["fields"]), "explicit_pdf_literal_missing")
        return {"fields_present": p["fields"], "author_role_correctness_verified": False}

    def sections_unchanged(ctx, did, p, kind):
        guard(p, ["frozen_baseline_text", "section_heading_keys"])
        need(isinstance(p.get("frozen_baseline_text"), str) and p["frozen_baseline_text"], "frozen_user_baseline_missing")
        need(isinstance(p.get("section_heading_keys"), list) and p["section_heading_keys"], "protected_section_keys_missing")
        before = section_payloads(p["frozen_baseline_text"]); after = section_payloads(text(ctx, did))
        digits = {"一":"1","二":"2","三":"3","四":"4","五":"5","六":"6","七":"7","八":"8","九":"9","十":"10"}
        keys = [digits.get(nf(k), nf(k)) for k in p["section_heading_keys"]]
        need(all(k in before and k in after for k in keys), "protected_sections_not_identifiable")
        normalize = lambda value: re.sub(r"[\s#*_]", "", nf(value)).replace(chr(96), "")
        for key in keys:
            require(normalize(before[key]) == normalize(after[key]), "protected_user_section_changed:" + key)
        return {"sections_compared": len(keys), "semantic_quality_verified": False}

    def parse_number(value, unit):
        normalized = nf(value).casefold()
        token = re.search(r"(?<![\d.])([+-]?\d+(?:,\d{3})*(?:\.\d+)?)\s*([万w千k亿]?)\s*([^\s|;,，；]*)", normalized)
        if not token: return None
        try: number = Decimal(token.group(1).replace(",", ""))
        except InvalidOperation: return None
        number *= {"万":Decimal(10000),"w":Decimal(10000),"千":Decimal(1000),"k":Decimal(1000),"亿":Decimal(100000000),"":Decimal(1)}[token.group(2)]
        suffix = token.group(3)
        expected = nf(unit).casefold().replace(" ", "")
        if expected:
            aliases = {"元":["元","rmb","cny","人民币"],"人":["人","席位","席"],"月":["月","个月"],
                       "token":["token","tokens"],"元/人日":["元/人日","元/人天","元/天"],"人日":["人日","人天"],"天":["天","日"]}
            accepted = aliases.get(expected, [expected])
            if not any(suffix.startswith(x) for x in accepted): return None
        return number

    def field_value(value, field):
        """Field association is local to an explicit label or matrix column."""
        names = [field["name"]] + field.get("aliases", [])
        rows = table_rows(value)
        if len(rows) > 1:
            for row in rows[1:]:
                if row and any(flat(name) in flat(row[0]) for name in names):
                    for cell in row[1:]:
                        parsed = parse_number(cell, field.get("unit", ""))
                        if parsed is not None: return parsed
            header = rows[0]
            for i, cell in enumerate(header):
                if any(flat(name) == flat(cell) for name in names):
                    for row in rows[1:]:
                        if len(row) > i:
                            parsed = parse_number(row[i], field.get("unit",""))
                            if parsed is not None: return parsed
        for line in value.splitlines():
            for name in sorted(names, key=len, reverse=True):
                match = re.search(re.escape(nf(name)) + r"\s*(?:[:：=]|为|是)\s*([^;\n；]+)", line, re.I)
                if match:
                    parsed = parse_number(match.group(1), field.get("unit",""))
                    if parsed is not None: return parsed
        return None

    def quote_fields(ctx, did, p, kind):
        guard(p, ["fields","groups","field","value","unit"])
        value = text(ctx, did); fields = p.get("fields")
        if fields is not None:
            need(not (set(p)&{"groups","field","value","unit"}),"mixed_quotation_field_rule_modes")
            need(isinstance(fields, list) and fields, "quotation_fields_invalid")
            checked = 0
            for field in fields:
                need(isinstance(field, dict) and "name" in field and "value" in field, "quotation_field_invalid")
                need(not (set(field) - {"name","aliases","value","unit","equivalents"}), "quotation_field_unknown_keys")
                actual = field_value(value, field)
                if actual is None:
                    equivalents = field.get("equivalents", [])
                    for eq in equivalents:
                        alternate = {**field,"unit":eq.get("unit","")}
                        candidate = field_value(value,alternate)
                        if candidate is not None and candidate == Decimal(str(eq["value"])):
                            actual = Decimal(str(field["value"])); break
                need(actual is not None, "quotation_field_not_identifiable:" + field["name"])
                require(actual == Decimal(str(field["value"])), "quotation_named_value_mismatch:" + field["name"])
                checked += 1
            return {"fields_checked": checked}
        need(isinstance(p.get("groups"),list) and p["groups"] and "field" in p and "value" in p, "quotation_group_fields_invalid")
        rows = table_rows(value); need(len(rows)>1, "quotation_group_matrix_not_identifiable")
        header = rows[0]; indices = [i for i,h in enumerate(header) if flat(p["field"]) in flat(h)]
        need(len(indices)==1, "quotation_unit_price_column_not_identifiable")
        checked = 0
        for group in p["groups"]:
            selected = [r for r in rows[1:] if r and flat(group).casefold() in flat(r[0]).casefold()]
            need(bool(selected), "quotation_group_not_identifiable:" + group)
            for row in selected:
                need(len(row)>indices[0], "quotation_group_field_missing")
                cell = row[indices[0]]
                actual = parse_number(cell, p.get("unit",""))
                if actual is None: actual = parse_number(cell + p.get("unit",""), p.get("unit",""))
                need(actual is not None, "quotation_group_value_not_parseable")
                require(actual == Decimal(str(p["value"])), "quotation_group_value_mismatch")
                checked += 1
        return {"fields_checked":checked}

    def quote_bounds(ctx, did, p, kind):
        guard(p, ["bounds"])
        need(isinstance(p.get("bounds"),list) and p["bounds"],"quotation_bounds_missing")
        rows = table_rows(text(ctx,did)); need(len(rows)>1,"quotation_bounds_matrix_not_identifiable")
        header = rows[0]; checked = 0
        for bound in p["bounds"]:
            need(isinstance(bound,dict) and set(bound)<= {"scope","field","min","max"} and "scope" in bound and "field" in bound, "quotation_bound_invalid")
            indices = [i for i,h in enumerate(header) if flat(bound["field"]) in flat(h)]
            need(len(indices)==1,"quotation_bound_field_not_identifiable")
            scope = nf(bound["scope"]).casefold()
            selected = [r for r in rows[1:] if r and scope in nf(r[0]).casefold()]
            need(bool(selected),"quotation_bound_scope_not_identifiable")
            for row in selected:
                need(len(row)>indices[0],"quotation_bound_cell_missing")
                cell=nf(row[indices[0]])
                if re.search(r"天数|日数|calendar",bound["field"],re.I):
                    need(not re.search(r"人[日天]|person.{0,2}days?",cell,re.I),"calendar_bound_person_day_unit_unacceptable")
                    number=parse_number(cell,"天")
                    if number is None and re.fullmatch(r"\s*\d+(?:\.\d+)?\s*",cell): number=Decimal(cell.strip())
                elif re.search(r"人日|人天|person.{0,2}days?",bound["field"],re.I):
                    number=parse_number(cell,"人日")
                    if number is None and re.fullmatch(r"\s*\d+(?:\.\d+)?\s*",cell): number=Decimal(cell.strip())
                else: number = parse_number(cell,"")
                need(number is not None,"quotation_bound_value_not_parseable")
                if "min" in bound: require(number>=Decimal(str(bound["min"])),"quotation_value_below_explicit_min")
                if "max" in bound: require(number<=Decimal(str(bound["max"])),"quotation_value_above_explicit_max")
                checked += 1
        return {"bound_rows_checked":checked}

    def clause_observation(ctx,did,p,kind):
        guard(p,["clauses"])
        need(isinstance(p.get("clauses"),list), "clause_observation_invalid")
        value = text(ctx,did)
        return {"literal_clues_present":[clause for clause in p["clauses"] if flat(clause) in flat(value)],
                "scorable":False,"applicable":False,"semantic_clause_coverage_verified":False}

    def inquiry_observation(ctx,did,p,kind):
        guard(p,[])
        value = text(ctx,did)
        return {"reference_marker_present":bool(re.search(r"问询|函|reference|inquiry|https?://",value,re.I)),
                "scorable":False,"applicable":False,"pairing_verified":False}

    def downloads(ctx,did,p,kind):
        guard(p,["query_group_hints"])
        snapshot = ctx.evidence.get("manifest_snapshots",{}).get(did,{}).get("download_results")
        need(isinstance(snapshot,dict) and snapshot.get("observation")=="before_download", "frozen_pre_download_scope_missing")
        ids = snapshot.get("required_item_ids")
        need(isinstance(ids,list) and ids and len(set(ids))==len(ids), "frozen_download_ids_invalid")
        hints = p.get("query_group_hints",[])
        need(isinstance(hints,list), "download_query_hints_invalid")
        groups = snapshot.get("query_groups",[])
        need(all(x in groups for x in hints), "download_query_scope_not_frozen")
        manifest = ctx.manifest(did,"download_results"); items = manifest.get("items")
        need(isinstance(items,list), "download_manifest_items_missing")
        mapping = {}
        for item in items:
            need(isinstance(item,dict) and item.get("id") not in mapping, "download_manifest_item_ambiguous")
            mapping[item.get("id")] = item
        require(all(x in mapping for x in ids),"selected_downloadable_result_missing")
        finals = {f.resolve() for f in actual_files(ctx,did)}
        for item_id in ids:
            item = mapping[item_id]; need(item.get("path") and item.get("sha256"),"download_output_binding_missing")
            path = ctx.path(item["path"])
            require(path.resolve() in finals,"download_output_not_in_final_delivery")
            ctx.info(path)
            require(base.sha(path)==item["sha256"],"download_actual_file_hash_mismatch")
        return {"covered_items":len(ids),"frozen_query_groups":groups}

    def painted_pdf(ctx,path):
        from pypdf.generic import ContentStream
        reader = ctx.info(path)["reader"]; pages = []
        for page in reader.pages:
            images = []; visible = []
            def payload(operands):
                return any(bool(x.strip()) if isinstance(x,(str,bytes)) else payload(x)
                           if isinstance(x,(list,tuple)) else False for x in operands)
            def compose(a,b):
                return (a[0]*b[0]+a[2]*b[1],a[1]*b[0]+a[3]*b[1],a[0]*b[2]+a[2]*b[3],a[1]*b[2]+a[3]*b[3],a[0]*b[4]+a[2]*b[5]+a[4],a[1]*b[4]+a[3]*b[5]+a[5])
            def walk(stream, resources, mode=0, prefix=(), ancestors=(), matrix=(1,0,0,1,0,0)):
                resources = resources.get_object() if hasattr(resources,"get_object") else resources
                objects = resources.get("/XObject",{}) if resources else {}
                objects = objects.get_object() if hasattr(objects,"get_object") else objects
                stack = []
                for operands, op in ContentStream(stream,reader).operations:
                    if op==b"q": stack.append((mode,matrix))
                    elif op==b"Q":
                        need(bool(stack),"pdf_graphics_stack_unbalanced"); mode,matrix=stack.pop()
                    elif op==b"cm":
                        need(len(operands)==6,"pdf_image_transform_unparseable")
                        matrix=compose(matrix,tuple(float(v) for v in operands))
                    elif op==b"Tr":
                        need(len(operands)==1 and int(operands[0]) in range(8),"pdf_text_render_mode_invalid")
                        mode=int(operands[0])
                    elif op in (b"Tj",b"TJ",b"'",b'"'):
                        if mode not in (3,7) and payload(operands): visible.append(True)
                    elif op==b"Do":
                        need(len(operands)==1 and operands[0] in objects,"pdf_painted_xobject_unresolved")
                        key=operands[0]; obj=objects[key].get_object()
                        name=prefix+(str(key),)
                        if obj.get("/Subtype")=="/Image":
                            # A zero-area CTM paints no image, despite a Do token.
                            if matrix[0]*matrix[3]-matrix[1]*matrix[2]==0: continue
                            try:
                                im=page.images[name[0] if len(name)==1 else name].image
                                need(im is not None,"pdf_drawn_image_decoder_unavailable")
                                signature=pixels(im)
                            except (base.UnknownEvidence,base.DeliveryFailure): raise
                            except Exception as exc: raise base.UnknownEvidence("pdf_drawn_image_decode_unknown:"+type(exc).__name__)
                            filters=obj.get("/Filter",[])
                            lossy="/DCTDecode" in str(filters) or "/JPXDecode" in str(filters)
                            images.append({"signature":signature,"lossy":lossy,"name":name})
                        elif obj.get("/Subtype")=="/Form":
                            need(id(obj) not in ancestors,"pdf_recursive_form")
                            form_matrix=tuple(float(v) for v in obj.get("/Matrix",(1,0,0,1,0,0)))
                            need(len(form_matrix)==6,"pdf_form_matrix_unparseable")
                            walk(obj,obj.get("/Resources",resources),mode,name,ancestors+(id(obj),),compose(matrix,form_matrix))
                        else: raise base.UnknownEvidence("pdf_xobject_subtype_unresolved")
                    elif op==b"INLINE IMAGE":
                        raise base.UnknownEvidence("inline_pdf_image_pixel_scope_not_yet_decodable")
                need(not stack,"pdf_graphics_stack_unbalanced")
            contents=page.get_contents(); need(contents is not None,"pdf_page_content_missing")
            walk(contents,page.get("/Resources",{}))
            pages.append({"images":images,"visible_text":bool(visible)})
        return pages

    def pure_images(ctx,did,p,kind):
        guard(p,[])
        pages=[]
        for path in actual_files(ctx,did,["pdf"]):
            pages.extend(painted_pdf(ctx,path))
        for page in pages:
            require(bool(page["images"]),"pdf_page_does_not_paint_image")
            require(not page["visible_text"],"visible_native_text_outside_raster_image")
        return {"image_pages":len(pages),"hidden_ocr_text_allowed":True}

    def source_path(ctx,name):
        aliases=ctx.evidence.get("current_attempt_file_aliases",{})
        value=aliases.get(name,name)
        if isinstance(value,dict): value=value.get("path")
        need(isinstance(value,str),"current_source_alias_unresolved")
        path=ctx.path(value)
        need(path.exists() and path.is_file(),"current_source_image_missing")
        initial=ctx.evidence.get("initial_sha256")
        inputs=ctx.evidence.get("declared_input_sha256")
        need(isinstance(initial,dict) and isinstance(inputs,dict),"current_source_attempt_snapshot_missing")
        need(base.sha(path) not in set(initial.values())|set(inputs.values()),"current_source_is_unchanged_input_or_initial_file")
        info=ctx.info(path)
        need(info.get("family")=="image","current_source_not_image")
        return path

    def image_signature(ctx,path):
        from PIL import Image
        need(ctx.info(path).get("family")=="image","source_payload_not_image")
        with Image.open(path) as im: return pixels(im)

    def pdf_order(ctx,did,p,kind):
        guard(p,["ordered_source_names"])
        names=p.get("ordered_source_names")
        need(isinstance(names,list) and names and all(isinstance(x,str) for x in names),"ordered_image_sources_missing")
        expected=[image_signature(ctx,source_path(ctx,name)) for name in names]
        pages=[]
        for path in actual_files(ctx,did,["pdf"]): pages.extend(painted_pdf(ctx,path))
        require(len(pages)==len(expected),"pdf_source_page_count_mismatch")
        for i,page in enumerate(pages):
            require(len(page["images"])==1,"pdf_page_not_single_source_image")
            image=page["images"][0]
            if image["signature"]!=expected[i]:
                if image["signature"] in expected:
                    raise base.DeliveryFailure("pdf_current_source_order_mismatch")
                need(not image["lossy"],"pdf_lossy_pixel_match_unproven")
                raise base.DeliveryFailure("pdf_current_source_pixels_mismatch")
        return {"source_images_verified":len(expected)}

    def outline_count(ctx,did,p,kind):
        guard(p,["outline_delivery_id"])
        source=p.get("outline_delivery_id")
        need(isinstance(source,str) and source in ctx.targets,"current_outline_delivery_binding_missing")
        items=numbered_entries(text(ctx,source))
        need(items and all(body for _,body in items) and len({n for n,_ in items})==len(items),"current_outline_items_not_identifiable")
        pages=[]
        for path in actual_files(ctx,did,["pdf"]): pages.extend(painted_pdf(ctx,path))
        require(len(pages)==len(items),"pdf_page_count_differs_from_current_outline")
        require(all(len(page["images"])==1 for page in pages),"pdf_page_does_not_have_one_outline_image")
        return {"current_outline_count":len(items),"actual_image_pages":len(pages)}

    def image_container_count(ctx,path):
        from PIL import Image
        info=ctx.info(path)
        if info.get("family")=="image":
            with Image.open(path) as im: im.load()
            return 1
        if info["format"]=="pdf":
            return sum(len(page["images"]) for page in painted_pdf(ctx,path))
        if info["format"]=="docx":
            members=info["members"]; rels=ET.fromstring(members.get("word/_rels/document.xml.rels",b"<Relationships/>"))
            mapping={r.get("Id"):r for r in rels}; count=0
            for node in info["tree"].findall(".//a:blip",base.NS):
                rel=mapping.get(node.get("{"+base.NS["r"]+"}embed"))
                need(rel is not None and rel.get("TargetMode")!="External","embedded_photo_relationship_missing")
                part=posixpath.normpath(posixpath.join("word",rel.get("Target","")))
                need(part in members,"embedded_photo_part_missing")
                with Image.open(io.BytesIO(members[part])) as im: im.load()
                count+=1
            return count
        if info["format"]=="html":
            parser=ImageTags(); parser.feed(info["text"]); count=0
            for _,value in parser.images:
                need(bool(value),"html_image_source_empty")
                if value.startswith("data:image/"):
                    try:
                        data=base64.b64decode(value.split(",",1)[1],validate=True)
                        with Image.open(io.BytesIO(data)) as im: im.load()
                    except Exception as exc: raise base.DeliveryFailure("html_image_payload_invalid:"+type(exc).__name__)
                    count+=1
                else:
                    need(not re.match(r"https?://",value,re.I),"uncollected_external_image_unknown")
                    source=ctx.path(str(path.parent/unquote(value)))
                    require(ctx.info(source).get("family")=="image","html_image_source_not_image")
                    with Image.open(source) as im: im.load()
                    count+=1
            return count
        raise base.UnknownEvidence("unsupported_embedded_photo_container")

    def named_images(ctx,did,p,kind):
        guard(p,["names"])
        need(isinstance(p.get("names"),list) and p["names"],"named_photo_requirements_missing")
        try: value=ctx.text(did,allow_files=False)
        except base.UnknownEvidence: value=""
        entries=[]
        if value.strip():
            entries=[(caption,path,ctx.workspace) for caption,path in re.findall(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+[^)]*)?\)",value)]
            parser=ImageTags(); parser.feed(value)
            entries.extend((caption,path,ctx.workspace) for caption,path in parser.images)
        if not value.strip():
            for f in ctx.files(did,["html"]):
                html=ctx.info(f)["text"]
                parser=ImageTags(); parser.feed(html)
                entries.extend((caption,path,f.parent) for caption,path in parser.images)
        need(bool(entries),"visible_photo_entries_not_identifiable")
        for name in p["names"]:
            matched=[(caption,path,parent) for caption,path,parent in entries if flat(name) in flat(caption)]
            require(bool(matched),"named_photo_entry_missing:"+name)
            for _,value,parent in matched:
                need(not re.match(r"https?://",value,re.I),"named_photo_remote_payload_uncollected")
                path=ctx.path(str(parent/unquote(value)))
                require(image_container_count(ctx,path)>0,"named_photo_actual_payload_empty")
        return {"names_bound":len(p["names"]),"person_identity_verified":False}

    def independent_visual(ctx,did,p,kind):
        guard(p,["requirement","text","trusted_receipt_sha256"])
        pin=p.get("trusted_receipt_sha256")
        need(isinstance(pin,str) and re.fullmatch(r"[a-fA-F0-9]{64}",pin),"independent_visual_receipt_pin_missing")
        value=ctx.evidence.get("independent_basic_receipts",{}).get(did)
        need(isinstance(value,str),"independent_visual_receipt_missing")
        path=ctx.path(value)
        need(path.exists() and base.sha(path).casefold()==pin.casefold(),"independent_visual_receipt_pin_mismatch")
        receipt=json.loads(path.read_text("utf-8-sig"))
        need(isinstance(receipt,dict) and receipt.get("origin")=="independent_basic_inspection"
             and receipt.get("source_session_id")==ctx.contract.get("sid",ctx.contract.get("session_id"))
             and receipt.get("delivery_id")==did and receipt.get("requirement")==p.get("requirement")
             and receipt.get("text")==p.get("text") and isinstance(receipt.get("evidence"),dict)
             and receipt["evidence"].get("inspection") and receipt["evidence"].get("page_numbers"),
             "independent_visual_receipt_scope_unproven")
        files=actual_files(ctx,did)
        need(receipt.get("artifact_sha256") in [base.sha(f) for f in files],"visual_receipt_actual_artifact_sha_unbound")
        need(type(receipt.get("observed")) is bool,"visual_receipt_observation_missing")
        require(receipt["observed"],"independently_observed_requirement_absent")
        return {"independent_presence_observed":True,"artifact_sha256":receipt["artifact_sha256"]}

    def distinct(ctx,did,p,kind):
        guard(p,["other_delivery_ids"])
        need(isinstance(p.get("other_delivery_ids"),list) and p["other_delivery_ids"],"distinct_other_delivery_ids_missing")
        mine=actual_files(ctx,did)
        for other in p["other_delivery_ids"]:
            need(other in ctx.targets,"distinct_other_delivery_unbound")
            for a in mine:
                for b in actual_files(ctx,other):
                    require(not os.path.samefile(a,b),"explicit_independent_delivery_reuses_same_file")
        return {"separate_objects":True}

    def current_nonreuse(ctx,did,p,kind):
        guard(p,["before_user_turn_index"])
        turn=p.get("before_user_turn_index")
        need(type(turn) is int and turn>=0,"image_baseline_turn_missing")
        snapshot=ctx.evidence.get("image_baseline_snapshots",{}).get(did)
        need(isinstance(snapshot,dict) and snapshot.get("observation")=="before_user_dispatch"
             and snapshot.get("before_user_turn_index")==turn,"same_attempt_pre_turn_image_snapshot_missing")
        items=snapshot.get("items"); need(isinstance(items,list) and items,"prior_current_attempt_images_missing")
        prior=[]
        for item in items:
            need(isinstance(item,dict) and item.get("path") and item.get("sha256"),"image_baseline_binding_invalid")
            path=ctx.path(item["path"])
            need(path.exists() and base.sha(path)==item["sha256"],"image_baseline_actual_sha_mismatch")
            prior.append(image_signature(ctx,path))
        final=[]
        for path in actual_files(ctx,did):
            info=ctx.info(path)
            if info.get("family")=="image": final.append(image_signature(ctx,path))
            elif info["format"]=="pdf":
                for page in painted_pdf(ctx,path):
                    for im in page["images"]: final.append(im["signature"])
            else: raise base.UnknownEvidence("final_image_container_not_measured")
        require(bool(final),"final_decodable_image_payload_missing")
        require(all(sig not in prior for sig in final),"final_image_reuses_prior_current_attempt_pixels")
        return {"new_pixel_payloads":len(final),"same_attempt_baseline_images":len(prior)}

    def records(ctx,did,p,kind):
        guard(p,["count","record_type"])
        need(type(p.get("count")) is int and p["count"]>0,"named_record_count_invalid")
        value=text(ctx,did); items=numbered_entries(value)
        if items:
            labels=[flat(body.splitlines()[0]) for _,body in items if body]
            require(len(items)==len(labels),"named_record_empty")
        else:
            rows=table_rows(value); need(len(rows)>1,"named_record_structure_not_identifiable")
            columns=[i for i,h in enumerate(rows[0]) if re.search(r"公司|企业|company|corporation",h,re.I)] if p.get("record_type")=="company" else [0]
            need(len(columns)==1,"named_company_column_not_identifiable")
            column=columns[0]
            require(all(len(row)>column and flat(row[column]) for row in rows[1:]),"named_record_empty")
            labels=[flat(row[column]) for row in rows[1:]]
        require(len(labels)==p["count"],"named_record_count_mismatch")
        require(len(set(labels))==len(labels),"named_record_duplicate_label")
        return {"record_count":len(labels),"record_type":p.get("record_type"),"identity_verified":False}

    def grouped(ctx,did,p,kind):
        guard(p,["groups","require_reference_field"])
        need(isinstance(p.get("groups"),list) and p["groups"],"grouped_list_requirements_missing")
        need(type(p.get("require_reference_field",False)) is bool,"invalid_grouped_reference_policy")
        value=text(ctx,did); rows=table_rows(value); counts=[]; references_checked=0
        for group in p["groups"]:
            need(isinstance(group,dict) and set(group)=={"route","country","count"} and type(group["count"]) is int,"grouped_requirement_invalid")
            selected=[]
            if len(rows)>1:
                route_cols=[i for i,h in enumerate(rows[0]) if re.search(r"路线|技术|route",h,re.I)]
                country_cols=[i for i,h in enumerate(rows[0]) if re.search(r"国家|国别|地区|country",h,re.I)]
                name_cols=[i for i,h in enumerate(rows[0]) if re.search(r"机构|导师|教授|院校|姓名|institution|teacher|name",h,re.I)]
                ref_cols=[i for i,h in enumerate(rows[0]) if re.search(r"参考|文献|出处|来源|reference|citation",h,re.I)]
                if len(route_cols)==len(country_cols)==len(name_cols)==1:
                    if p.get("require_reference_field"): need(len(ref_cols)==1,"group_reference_column_not_identifiable")
                    for row in rows[1:]:
                        if len(row)>max(route_cols[0],country_cols[0],name_cols[0]) and flat(group["route"]) in flat(row[route_cols[0]]) and flat(group["country"]) in flat(row[country_cols[0]]):
                            selected.append(row[name_cols[0]])
                            if p.get("require_reference_field"):
                                require(len(row)>ref_cols[0] and flat(row[ref_cols[0]]),"group_entry_reference_field_empty")
                                references_checked+=1
            if not selected:
                lines=value.splitlines(); starts=[i for i,line in enumerate(lines) if flat(group["route"]) in flat(line) and flat(group["country"]) in flat(line)]
                need(len(starts)==1,"grouped_list_scope_not_identifiable")
                start=starts[0]; end=len(lines)
                for i in range(start+1,len(lines)):
                    if re.match(r"^\s*#{1,6}\s",lines[i]): end=i; break
                units=numbered_entries("\n".join(lines[start+1:end]))
                need(bool(units),"grouped_list_entries_not_identifiable")
                selected=[body for _,body in units]
                if p.get("require_reference_field"):
                    for body in selected:
                        need(bool(re.search(r"参考|文献|出处|来源|reference|citation|https?://",body,re.I)),"group_entry_reference_field_not_identifiable")
                        references_checked+=1
            require(len(selected)==group["count"] and all(flat(x) for x in selected),"grouped_list_count_mismatch")
            counts.append({"route":group["route"],"country":group["country"],"entries":len(selected)})
        return {"group_counts":counts,"reference_entries_checked":references_checked,"identity_or_rank_verified":False}

    def questionnaire(ctx,did,p,kind):
        guard(p,["section_count","accepted_question_types","time_notice_max_minutes"])
        need(type(p.get("section_count")) is int and isinstance(p.get("accepted_question_types"),list)
             and type(p.get("time_notice_max_minutes")) in (int,float),"questionnaire_parameters_invalid")
        value=text(ctx,did)
        sections=re.findall(r"(?m)^\s*(?:#{1,6}\s*)?(?:第\s*[一二三四五六七八九十\d]+\s*(?:部分|模块)|[一二三四五六七八九十]+[、.．]\s*[^\n]+)",value)
        need(bool(sections),"questionnaire_sections_not_identifiable")
        require(len(sections)==p["section_count"],"questionnaire_section_count_mismatch")
        labels=[x for x in p["accepted_question_types"] if x in value]
        require(bool(labels),"question_type_annotation_missing")
        questions=numbered_entries(value)
        need(bool(questions),"questionnaire_questions_not_identifiable")
        for _,body in questions:
            first=body.splitlines()[0] if body else ""
            require(any(label in first for label in p["accepted_question_types"]),"question_type_annotation_missing_on_identified_question")
        require(bool(re.search(r"跳转|跳过|无需回答|不需填写|skip|if .*then",value,re.I)),"questionnaire_skip_notice_missing")
        minutes=re.findall(r"(\d+(?:\.\d+)?)\s*(?:分钟|minutes?\b|min\b)",value,re.I)
        need(bool(minutes),"questionnaire_time_notice_not_identifiable")
        require(any(0<float(x)<=p["time_notice_max_minutes"] for x in minutes),"questionnaire_time_notice_exceeds_max")
        return {"section_count":len(sections),"question_type_labels":labels,"advertised_minutes":minutes,"actual_duration_verified":False}

    definitions=[
        ("text_character_count_minimum",minimum,{"min_characters","count_mode"}),
        ("text_numbered_item_count",item_count,{"count"}),
        ("exact_status_only_text_diagnostic",status_only,{"phrases"}),
        ("skill_declared_input_formats_present",formats,{"formats","aliases"}),
        ("file_numeric_and_reference_markers_present",numeric_reference,{"require_numeric_token"}),
        ("pdf_text_or_ocr_literal_fields_present",literals,{"fields"}),
        ("text_named_sections_equal_to_user_baseline",sections_unchanged,{"frozen_baseline_text","section_heading_keys"}),
        ("quotation_named_numeric_fields",quote_fields,{"fields","groups","field","value","unit"}),
        ("quotation_numeric_bounds",quote_bounds,{"bounds"}),
        ("quotation_clause_fields_present",clause_observation,{"clauses"}),
        ("inquiry_reference_pairing_fields_present",inquiry_observation,set()),
        ("download_result_manifest_coverage",downloads,{"query_group_hints"}),
        ("pdf_external_text_absent",pure_images,set()),
        ("pdf_page_images_match_current_sources",pdf_order,{"ordered_source_names"}),
        ("pdf_image_count_matches_current_outline",outline_count,{"outline_delivery_id"}),
        ("named_image_delivery_entries",named_images,{"names"}),
        ("basic_visual_requirement_attestation",independent_visual,{"requirement","text","trusted_receipt_sha256"}),
        ("file_delivery_distinct_from",distinct,{"other_delivery_ids"}),
        ("final_image_sources_not_reusing_prior_current_attempt_images",current_nonreuse,{"before_user_turn_index"}),
        ("named_record_count",records,{"count","record_type"}),
        ("grouped_list_entry_counts",grouped,{"groups","require_reference_field"}),
        ("questionnaire_basic_form_structure",questionnaire,{"section_count","accepted_question_types","time_notice_max_minutes"})]
    for name,fn,allowed in definitions:
        base.register(fn,name); base.PARAMETERS[fn]=allowed

    extras={"allow_embedded_image_payloads","allowed_image_containers","require_actual_decodable_image_payload",
            "no_local_file_only_restriction","header_scope","headers_empty_scope","ignore_orphan_header_parts",
            "header_renderable_payload_absent","active_sections_only","include_image_and_field_payloads"}
    original_file_names=set(base.FILE_PARAMETER_NAMES)
    original_handlers={name:base.HANDLERS[name] for name in ("delivered_file_open","file_delivery_open","final_file_native_open")}

    def active_headers(info):
        members=info["members"]; tree=info["tree"]
        relationships=ET.fromstring(members.get("word/_rels/document.xml.rels",b"<Relationships/>"))
        relmap={r.get("Id"):r for r in relationships}
        settings=ET.fromstring(members.get("word/settings.xml",b"<settings/>"))
        even=settings.find(".//w:evenAndOddHeaders",base.NS)
        even_on=even is not None and even.get("{"+base.NS["w"]+"}val","1") not in ("0","false","off")
        inherited={}; active=[]
        for section in tree.findall(".//w:sectPr",base.NS):
            for reference in section.findall("w:headerReference",base.NS):
                inherited[reference.get("{"+base.NS["w"]+"}type","default")]=reference.get("{"+base.NS["r"]+"}id")
            title=section.find("w:titlePg",base.NS)
            title_on=title is not None and title.get("{"+base.NS["w"]+"}val","1") not in ("0","false","off")
            types=["default"]+(["first"] if title_on else [])+(["even"] if even_on else [])
            for typ in types:
                if typ not in inherited: continue
                rid=inherited[typ]; rel=relmap.get(rid)
                need(rel is not None and rel.get("TargetMode")!="External","active_header_relationship_unresolved")
                part=posixpath.normpath(posixpath.join("word",rel.get("Target","")))
                need(part in members,"active_header_part_missing")
                header=ET.fromstring(members[part])
                active.append(part)
                payload="".join(n.text or "" for n in header.findall(".//w:t",base.NS))
                paint=any(header.findall(".//"+tag,base.NS) for tag in ["w:drawing","w:pict","w:fldSimple","w:instrText","w:object","w:altChunk"])
                require(not payload.strip() and not paint,"active_section_header_has_renderable_payload")
        return len(set(active))

    def file_open(ctx,did,p,kind):
        guard(p,original_file_names|extras)
        for flag in extras-{"allowed_image_containers","header_scope","headers_empty_scope"}:
            if flag in p:
                need(p[flag] is True,"unsupported_file_policy_flag:"+flag)
        clean={k:v for k,v in p.items() if k not in extras}
        if p.get("allow_embedded_image_payloads"):
            allowed=p.get("allowed_image_containers",["image","pdf","html","docx"])
            need(isinstance(allowed,list) and allowed and set(allowed)<={"image","pdf","html","docx"},"unsupported_photo_containers")
            clean.pop("format",None); clean.pop("formats",None); clean["allowed_formats"]=allowed
            clean.pop("headers_empty",None)
            paths=ctx.opened(did,clean); total=sum(image_container_count(ctx,path) for path in paths)
            require(total>0,"actual_decodable_embedded_photo_payload_missing")
            return {"embedded_image_payloads":total,"files_opened":len(paths)}
        scoped=any(k in p for k in extras if k.startswith("header") or k in ("ignore_orphan_header_parts","active_sections_only","include_image_and_field_payloads"))
        if p.get("headers_empty") and scoped:
            for key in ("header_scope","headers_empty_scope"):
                if key in p: need(p[key] in ("active_section_references","active_section_headers","effective_section_headers"),"unsupported_header_scope")
            clean.pop("headers_empty",None)
            paths=ctx.opened(did,clean); count=0
            for path in paths:
                info=ctx.info(path); need(info["format"]=="docx","active_header_check_requires_docx")
                count+=active_headers(info)
            return {"active_headers":count,"files_opened":len(paths),"orphan_headers_ignored":True}
        return original_handlers[kind](ctx,did,clean,kind)

    base.FILE_PARAMETER_NAMES|=extras
    for name in original_handlers: base.HANDLERS[name]=file_open
