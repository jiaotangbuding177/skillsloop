"""Positive, negative and unknown offline controls for basic text/artifact rules."""
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import zipfile

import pytest
from PIL import Image
from pypdf import PdfWriter
from pypdf.generic import (DictionaryObject, NameObject, DecodedStreamObject,
                          NumberObject, ArrayObject)

SUITE = Path(__file__).resolve().parents[1]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def engine():
    base = load(SUITE / "vendor/final_state_scorer.py", "text_fixture_base")
    for name in ("_artifact_extensions", "_extensions", "_text_extensions"):
        load(SUITE / (name + ".py"), "text_fixture" + name).register_extensions(base)
    return base


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def context(base, tmp_path, text=None, files=None, extra=None):
    bound = {}
    if text is not None:
        bound["text"] = text
    if files is not None:
        bound["files"] = files
    evidence = {"schema": "final-state-evidence-v1", "source_session_id": "text_fixture",
                "conversation_complete": True, "initial_sha256": {},
                "declared_input_sha256": {}, "deliveries": {"d": bound}}
    if extra:
        evidence.update(extra)
    return base.Context(
        {"task_id": "text_fixture", "source_session_id": "text_fixture", "workspace": str(tmp_path),
         "result": {}, "evidence": evidence},
        {"sid": "text_fixture", "final_deliverables":
         [{"id": "d", "name": "Control delivery", "kind": "text_or_file"}]})


def run(base, ctx, kind, parameters):
    unsupported = base.parameter_support({"kind": kind, "parameters": parameters})
    if unsupported:
        raise base.UnknownEvidence("unsupported:" + ",".join(unsupported))
    return base.HANDLERS[kind](ctx, "d", parameters, kind)


def raster(path, color):
    Image.new("RGB", (3, 2), color).save(path)


def image_pdf(path, colors=("red", "blue"), visible_text="", unused_image=False,
              invisible_text=False):
    writer = PdfWriter()
    for color in colors:
        page = writer.add_blank_page(width=300, height=200)
        raw = Image.new("RGB", (3, 2), color).tobytes()
        image = DecodedStreamObject()
        image.set_data(raw)
        image.update({NameObject("/Type"): NameObject("/XObject"),
                      NameObject("/Subtype"): NameObject("/Image"),
                      NameObject("/Width"): NumberObject(3),
                      NameObject("/Height"): NumberObject(2),
                      NameObject("/BitsPerComponent"): NumberObject(8),
                      NameObject("/ColorSpace"): NameObject("/DeviceRGB")})
        objects = DictionaryObject({NameObject("/I"): writer._add_object(image)})
        font = writer._add_object(DictionaryObject({
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica")}))
        page[NameObject("/Resources")] = DictionaryObject({
            NameObject("/XObject"): objects,
            NameObject("/Font"): DictionaryObject({NameObject("/F"): font})})
        stream = DecodedStreamObject()
        content = "q Q" if unused_image else "q 300 0 0 200 0 0 cm /I Do Q"
        if visible_text:
            content += " BT /F 12 Tf " + ("3 Tr " if invisible_text else "") + "10 10 Td (" + visible_text + ") Tj ET"
        stream.set_data(content.encode("ascii"))
        page[NameObject("/Contents")] = writer._add_object(stream)
    with path.open("wb") as handle:
        writer.write(handle)


def docx(path, header_text="", header_drawing=False, active=True,
         first_only=False, title_page=False, inherited_first=False):
    w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    r = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    reference = ('<w:headerReference w:type="' + ("first" if first_only else "default")
                 + '" r:id="header"/>') if active else ""
    section = "<w:sectPr>" + reference + ("<w:titlePg/>" if title_page else "") + "</w:sectPr>"
    if inherited_first:
        section += "<w:sectPr><w:titlePg/></w:sectPr>"
    main = '<w:document xmlns:w="' + w + '" xmlns:r="' + r + '"><w:body><w:p><w:r><w:t>body</w:t></w:r></w:p>' + section + "</w:body></w:document>"
    header = '<w:hdr xmlns:w="' + w + '"><w:p><w:r><w:t>' + header_text + "</w:t>" + ("<w:drawing/>" if header_drawing else "") + "</w:r></w:p></w:hdr>"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        archive.writestr("word/document.xml", main)
        archive.writestr("word/header1.xml", header)
        archive.writestr("word/_rels/document.xml.rels",
                         '<Relationships xmlns="' + r + '"><Relationship Id="header" Type="' + r + '/header" Target="header1.xml"/></Relationships>')


@pytest.mark.parametrize("body", [
    "第1页：封面\n说明\n第2页：市场\n分析\n第3页：总结\n行动",
    "# 1. Cover\nbody\n# 2. Market\nbody\n# 3. End\nbody",
    "slide_00: Cover\nbody\nslide_01: Market\nbody\nslide_02: End\nbody"])
def test_numbered_count_accepts_normal_variants(engine, tmp_path, body):
    out = run(engine, context(engine, tmp_path, text=body), "text_numbered_item_count", {"count": 3})
    assert out["item_count"] == 3


def test_count_wrong_blank_and_unidentifiable(engine, tmp_path):
    with pytest.raises(engine.DeliveryFailure):
        run(engine, context(engine, tmp_path, text="第1页：a\n第2页：b"), "text_numbered_item_count", {"count": 3})
    with pytest.raises(engine.DeliveryFailure):
        run(engine, context(engine, tmp_path, text="第1页：a\n第2页：\n第3页：c"), "text_numbered_item_count", {"count": 3})
    with pytest.raises(engine.UnknownEvidence):
        run(engine, context(engine, tmp_path, text="A valid prose report without numbered units."),
            "text_numbered_item_count", {"count": 3})


def test_minimum_word_count_does_not_create_2500_tolerance(engine, tmp_path):
    params = {"min_characters": 1000, "count_mode": "non_whitespace_unicode_codepoints"}
    assert run(engine, context(engine, tmp_path, text="字 " * 1000),
               "text_character_count_minimum", params)["characters"] == 1000
    with pytest.raises(engine.DeliveryFailure):
        run(engine, context(engine, tmp_path, text="字" * 999), "text_character_count_minimum", params)
    with pytest.raises(engine.UnknownEvidence):
        run(engine, context(engine, tmp_path, text="字" * 1000),
            "text_character_count_minimum", {**params, "hard_tolerance": 100})


def test_status_short_phrases_are_observation_only(engine, tmp_path):
    p = {"phrases": ["我会做", "已完成"]}
    assert run(engine, context(engine, tmp_path, text="已完成。"),
               "exact_status_only_text_diagnostic", p)["scorable"] is False
    out = run(engine, context(engine, tmp_path, text="我会做需求分析，也会用这份报告说明方案。"),
              "exact_status_only_text_diagnostic", p)
    assert not out["exact_status_only"]


def test_input_declarations_only_not_source_function(engine, tmp_path):
    d = tmp_path / "skill"; d.mkdir()
    (d / "SKILL.md").write_text("输入格式：LaTeX / Markdown / Word / PDF\n不执行科研质量判断。", "utf-8")
    c = context(engine, tmp_path); c.evidence["deliveries"]["d"] = {"directory": "skill"}
    p = {"formats": ["latex", "markdown", "word", "pdf"]}
    assert run(engine, c, "skill_declared_input_formats_present", p)["format_count"] == 4
    (d / "SKILL.md").write_text("Input formats: LaTeX, Markdown, Word", "utf-8")
    with pytest.raises(engine.DeliveryFailure):
        run(engine, c, "skill_declared_input_formats_present", p)
    (d / "SKILL.md").write_text("A miscellaneous note mentions PDF and Word.", "utf-8")
    with pytest.raises(engine.UnknownEvidence):
        run(engine, c, "skill_declared_input_formats_present", p)


def test_numeric_source_markers_are_only_form_presence(engine, tmp_path):
    p = {"require_numeric_token": True}
    good = "市场规模2.5亿元。资料出处：https://example.test/report"
    assert run(engine, context(engine, tmp_path, text=good),
               "file_numeric_and_reference_markers_present", p)["reference_count"] >= 1
    with pytest.raises(engine.DeliveryFailure):
        run(engine, context(engine, tmp_path, text="文字，无数据。来源：示例机构"),
            "file_numeric_and_reference_markers_present", p)
    with pytest.raises(engine.UnknownEvidence):
        run(engine, context(engine, tmp_path, text="2026年，某期刊记录中有一条普通描述。"),
            "file_numeric_and_reference_markers_present", p)


def test_protected_sections_use_frozen_user_text(engine, tmp_path):
    source = "一、原章\nA\n二、可变章\nB\n三、原章\nC"
    p = {"frozen_baseline_text": source, "section_heading_keys": ["一", "三"]}
    assert run(engine, context(engine, tmp_path, text="# 第一章 原章\n A \n# 第二章 改写\nNEW\n# 第三章 原章\nC"),
               "text_named_sections_equal_to_user_baseline", p)["sections_compared"] == 2
    with pytest.raises(engine.DeliveryFailure):
        run(engine, context(engine, tmp_path, text="一、原章\nEDIT\n二、可变章\nB\n三、原章\nC"),
            "text_named_sections_equal_to_user_baseline", p)
    with pytest.raises(engine.UnknownEvidence):
        run(engine, context(engine, tmp_path, text=source),
            "text_named_sections_equal_to_user_baseline", {"section_heading_keys": ["一"]})


def test_quotation_values_have_unit_and_field_scope(engine, tmp_path):
    p = {"fields": [{"name": "平台费", "value": 500000, "unit": "元"},
                    {"name": "额度", "value": 30000000, "unit": "token"}]}
    good = "平台费：50万元\n额度：3,000万token"
    assert run(engine, context(engine, tmp_path, text=good), "quotation_named_numeric_fields", p)["fields_checked"] == 2
    with pytest.raises(engine.DeliveryFailure):
        run(engine, context(engine, tmp_path, text="平台费：60万元\n额度：3000万token"),
            "quotation_named_numeric_fields", p)
    with pytest.raises(engine.UnknownEvidence):
        run(engine, context(engine, tmp_path, text="年度总价：50万元\n额度：3000万token"),
            "quotation_named_numeric_fields", p)


def test_quote_bounds_all_identified_rows_not_summary_only(engine, tmp_path):
    p = {"bounds": [{"scope": "skill", "field": "人日", "max": 10},
                    {"scope": "FDE", "field": "驻场天数", "min": 7}]}
    good = "| 项目 | 人日 | 驻场天数 |\n|---|---|---|\n| skill A | 8 | |\n| skill B | 10 | |\n| FDE | | 7 |"
    assert run(engine, context(engine, tmp_path, text=good), "quotation_numeric_bounds", p)["bound_rows_checked"] == 3
    bad = good.replace("| skill B | 10 |", "| skill B | 11 |")
    with pytest.raises(engine.DeliveryFailure):
        run(engine, context(engine, tmp_path, text=bad), "quotation_numeric_bounds", p)
    with pytest.raises(engine.UnknownEvidence):
        run(engine, context(engine, tmp_path, text="服务可能在未来实施。"), "quotation_numeric_bounds", p)


def test_download_scope_not_terminal_self_selected_subset(engine, tmp_path):
    for name in ("a.md", "b.md"):
        (tmp_path / name).write_text("Downloaded content " + name, "utf-8")
    c = context(engine, tmp_path, files=["a.md", "b.md"])
    c.evidence["manifest_snapshots"] = {"d": {"download_results": {
        "observation": "before_download", "required_item_ids": ["a", "b"],
        "query_groups": ["JH389", "AUP-16"]}}}
    c.evidence["deliveries"]["d"]["manifests"] = {"download_results": {"items": [
        {"id": "a", "path": "a.md", "sha256": sha(tmp_path / "a.md")},
        {"id": "b", "path": "b.md", "sha256": sha(tmp_path / "b.md")}]}}
    p = {"query_group_hints": ["JH389", "AUP-16"]}
    assert run(engine, c, "download_result_manifest_coverage", p)["covered_items"] == 2
    c.evidence["deliveries"]["d"]["manifests"]["download_results"]["items"].pop()
    with pytest.raises(engine.DeliveryFailure):
        run(engine, c, "download_result_manifest_coverage", p)
    c.evidence.pop("manifest_snapshots")
    with pytest.raises(engine.UnknownEvidence):
        run(engine, c, "download_result_manifest_coverage", p)


def test_pdf_order_compares_actual_drawn_pixels(engine, tmp_path):
    raster(tmp_path / "slide_00.png", "red"); raster(tmp_path / "slide_01.png", "blue")
    image_pdf(tmp_path / "out.pdf")
    p = {"ordered_source_names": ["slide_00.png", "slide_01.png"]}
    c = context(engine, tmp_path, files=["out.pdf"])
    assert run(engine, c, "pdf_page_images_match_current_sources", p)["source_images_verified"] == 2
    image_pdf(tmp_path / "out.pdf", ("blue", "red"))
    c = context(engine, tmp_path, files=["out.pdf"])
    with pytest.raises(engine.DeliveryFailure):
        run(engine, c, "pdf_page_images_match_current_sources", p)
    with pytest.raises(engine.UnknownEvidence):
        run(engine, c, "pdf_page_images_match_current_sources", {"ordered_source_names": ["unbound.png"]})


def test_pdf_image_resource_not_drawn_is_not_payload(engine, tmp_path):
    image_pdf(tmp_path / "out.pdf", ("red",), unused_image=True)
    with pytest.raises(engine.DeliveryFailure):
        run(engine, context(engine, tmp_path, files=["out.pdf"]), "pdf_external_text_absent", {})


def test_pdf_pure_image_invisible_ocr_allowed_visible_text_rejected(engine, tmp_path):
    image_pdf(tmp_path / "out.pdf", ("red",), visible_text="Caption")
    with pytest.raises(engine.DeliveryFailure):
        run(engine, context(engine, tmp_path, files=["out.pdf"]), "pdf_external_text_absent", {})
    image_pdf(tmp_path / "out.pdf", ("red",), visible_text="OCR", invisible_text=True)
    assert run(engine, context(engine, tmp_path, files=["out.pdf"]), "pdf_external_text_absent", {})["image_pages"] == 1


def test_photo_named_entries_real_bytes_not_actor_dictionary(engine, tmp_path):
    raster(tmp_path / "people.png", "red")
    p = {"names": ["徐", "黄"]}
    c = context(engine, tmp_path, text="![徐和黄照片](people.png)", files=["people.png"])
    assert run(engine, c, "named_image_delivery_entries", p)["names_bound"] == 2
    with pytest.raises(engine.DeliveryFailure):
        run(engine, context(engine, tmp_path, text="![徐照片](people.png)", files=["people.png"]),
            "named_image_delivery_entries", p)
    c = context(engine, tmp_path, files=["people.png"])
    c.evidence["deliveries"]["d"]["image_entries"] = [{"name": "徐", "path": "people.png"}, {"name": "黄", "path": "people.png"}]
    with pytest.raises(engine.UnknownEvidence):
        run(engine, c, "named_image_delivery_entries", p)


def test_embedded_photos_open_real_container_payload(engine, tmp_path):
    image_pdf(tmp_path / "photos.pdf", ("red",))
    c = context(engine, tmp_path, files=["photos.pdf"])
    c.targets["d"]["format"] = "image"
    p = {"format": "image", "allow_embedded_image_payloads": True,
         "allowed_image_containers": ["image", "pdf"]}
    assert run(engine, c, "file_delivery_open", p)["embedded_image_payloads"] == 1
    image_pdf(tmp_path / "empty.pdf", ("red",), unused_image=True)
    with pytest.raises(engine.DeliveryFailure):
        run(engine, context(engine, tmp_path, files=["empty.pdf"]), "file_delivery_open", p)


def test_active_headers_images_fields_and_orphans(engine, tmp_path):
    p = {"format": "docx", "headers_empty": True, "header_scope": "active_section_references",
         "header_renderable_payload_absent": True, "ignore_orphan_header_parts": True}
    docx(tmp_path / "out.docx", header_text="old unused", active=False)
    assert run(engine, context(engine, tmp_path, files=["out.docx"]), "file_delivery_open", p)["active_headers"] == 0
    docx(tmp_path / "out.docx", header_drawing=True)
    with pytest.raises(engine.DeliveryFailure):
        run(engine, context(engine, tmp_path, files=["out.docx"]), "file_delivery_open", p)
    docx(tmp_path / "out.docx", header_text="first page", first_only=True, active=True, title_page=False)
    assert run(engine, context(engine, tmp_path, files=["out.docx"]), "file_delivery_open", p)["active_headers"] == 0
    docx(tmp_path / "out.docx", header_text="inherited first", first_only=True, inherited_first=True)
    with pytest.raises(engine.DeliveryFailure):
        run(engine, context(engine, tmp_path, files=["out.docx"]), "file_delivery_open", p)


def test_watermark_only_independently_pinned_actual_inspection(engine, tmp_path):
    image_pdf(tmp_path / "out.pdf", ("red",), visible_text="Zhang")
    c = context(engine, tmp_path, files=["out.pdf"])
    p = {"requirement": "watermark_present", "text": "Zhang"}
    c.evidence["deliveries"]["d"]["watermark"] = {"present": True, "sha256": sha(tmp_path / "out.pdf")}
    with pytest.raises(engine.UnknownEvidence):
        run(engine, c, "basic_visual_requirement_attestation", p)
    receipt = {"origin": "independent_basic_inspection", "source_session_id": "text_fixture",
               "delivery_id": "d", "requirement": "watermark_present", "text": "Zhang",
               "artifact_sha256": sha(tmp_path / "out.pdf"), "observed": True,
               "evidence": {"page_numbers": [1], "inspection": "actual rendered artifact"}}
    path = tmp_path / "inspection.json"; path.write_text(json.dumps(receipt), "utf-8")
    c.evidence["independent_basic_receipts"] = {"d": "inspection.json"}
    pinned = {**p, "trusted_receipt_sha256": sha(path)}
    assert run(engine, c, "basic_visual_requirement_attestation", pinned)["independent_presence_observed"]
    receipt["observed"] = False; path.write_text(json.dumps(receipt), "utf-8")
    with pytest.raises(engine.DeliveryFailure):
        run(engine, c, "basic_visual_requirement_attestation", {**p, "trusted_receipt_sha256": sha(path)})
    with pytest.raises(engine.UnknownEvidence):
        run(engine, c, "basic_visual_requirement_attestation", pinned)


def test_unknown_parameters_fail_closed(engine, tmp_path):
    with pytest.raises(engine.UnknownEvidence):
        run(engine, context(engine, tmp_path, text="第1页:a"), "text_numbered_item_count",
            {"count": 1, "professional_quality": True})


def test_file_identity_not_same_bytes(engine, tmp_path):
    image_pdf(tmp_path / "a.pdf", ("red",))
    (tmp_path / "b.pdf").write_bytes((tmp_path / "a.pdf").read_bytes())
    c = context(engine, tmp_path, files=["a.pdf"])
    c.targets["other"] = {"id": "other", "kind": "file", "format": "pdf"}
    c.evidence["deliveries"]["other"] = {"files": ["b.pdf"]}
    assert run(engine, c, "file_delivery_distinct_from", {"other_delivery_ids": ["other"]})["separate_objects"]
    c.evidence["deliveries"]["other"] = {"files": ["a.pdf"]}
    with pytest.raises(engine.DeliveryFailure):
        run(engine, c, "file_delivery_distinct_from", {"other_delivery_ids": ["other"]})


def test_pixel_reuse_current_attempt_only(engine, tmp_path):
    raster(tmp_path / "out.png", "blue"); raster(tmp_path / "prior.png", "red")
    c = context(engine, tmp_path, files=["out.png"])
    c.evidence["image_baseline_snapshots"] = {"d": {"observation": "before_user_dispatch",
        "before_user_turn_index": 14, "items": [{"path": "prior.png", "sha256": sha(tmp_path / "prior.png")}]}}
    p = {"before_user_turn_index": 14}
    assert run(engine, c, "final_image_sources_not_reusing_prior_current_attempt_images", p)["new_pixel_payloads"] == 1
    raster(tmp_path / "out.png", "red")
    with pytest.raises(engine.DeliveryFailure):
        run(engine, context(engine, tmp_path, files=["out.png"],
            extra={"image_baseline_snapshots": c.evidence["image_baseline_snapshots"]}),
            "final_image_sources_not_reusing_prior_current_attempt_images", p)
    with pytest.raises(engine.UnknownEvidence):
        run(engine, context(engine, tmp_path, files=["out.png"]),
            "final_image_sources_not_reusing_prior_current_attempt_images", p)


def test_pdf_render_mode_restored_after_graphics_state_pop(engine, tmp_path):
    image_pdf(tmp_path / "out.pdf", ("red",))
    from pypdf import PdfReader
    reader = PdfReader(tmp_path / "out.pdf")
    writer = PdfWriter(); writer.add_page(reader.pages[0])
    page = writer.pages[0]
    data = page.get_contents().get_data() + b" q BT /F 12 Tf 3 Tr (hidden OCR) Tj ET Q BT /F 12 Tf 10 10 Td (VISIBLE) Tj ET"
    stream = DecodedStreamObject(); stream.set_data(data)
    page[NameObject("/Contents")] = writer._add_object(stream)
    with (tmp_path / "restored.pdf").open("wb") as handle: writer.write(handle)
    with pytest.raises(engine.DeliveryFailure):
        run(engine, context(engine, tmp_path, files=["restored.pdf"]), "pdf_external_text_absent", {})


def test_pdf_literal_real_native_field_and_unknown_ocr(engine, tmp_path):
    p = {"fields": ["Zhang"]}
    image_pdf(tmp_path / "ok.pdf", ("red",), visible_text="Zhang")
    assert run(engine, context(engine, tmp_path, files=["ok.pdf"]), "pdf_text_or_ocr_literal_fields_present", p)["fields_present"] == ["Zhang"]
    image_pdf(tmp_path / "bad.pdf", ("red",), visible_text="Li")
    with pytest.raises(engine.DeliveryFailure):
        run(engine, context(engine, tmp_path, files=["bad.pdf"]), "pdf_text_or_ocr_literal_fields_present", p)
    image_pdf(tmp_path / "raster.pdf", ("red",))
    with pytest.raises(engine.UnknownEvidence):
        run(engine, context(engine, tmp_path, files=["raster.pdf"]), "pdf_text_or_ocr_literal_fields_present", p)


def test_questionnaire_only_identifiable_basic_annotations(engine, tmp_path):
    p = {"section_count": 3, "accepted_question_types": ["单选", "多选", "填空"], "time_notice_max_minutes": 8}
    good = "预计5分钟，选否请跳过第2题。\n第一部分\n1. [单选] 使用情况\n第二部分\n2. [多选] 应用\n第三部分\n3. [填空] 建议"
    assert run(engine, context(engine, tmp_path, text=good), "questionnaire_basic_form_structure", p)["section_count"] == 3
    with pytest.raises(engine.DeliveryFailure):
        run(engine, context(engine, tmp_path, text=good.replace("预计5分钟", "预计10分钟")), "questionnaire_basic_form_structure", p)
    with pytest.raises(engine.DeliveryFailure):
        run(engine, context(engine, tmp_path, text=good.replace("[多选]", "")), "questionnaire_basic_form_structure", p)
    with pytest.raises(engine.UnknownEvidence):
        run(engine, context(engine, tmp_path, text="普通问卷文字"), "questionnaire_basic_form_structure", p)


def test_grouped_scope_and_count_not_ranking(engine, tmp_path):
    p = {"groups": [{"route": "纯电", "country": "中国", "count": 2}, {"route": "纯电", "country": "美国", "count": 1}]}
    good = "| 路线 | 国家 | 机构 |\n|---|---|---|\n| 纯电 | 中国 | A |\n| 纯电 | 中国 | B |\n| 纯电 | 美国 | C |"
    assert len(run(engine, context(engine, tmp_path, text=good), "grouped_list_entry_counts", p)["group_counts"]) == 2
    with pytest.raises(engine.DeliveryFailure):
        run(engine, context(engine, tmp_path, text=good.replace("| 纯电 | 中国 | B |", "")), "grouped_list_entry_counts", p)
    with pytest.raises(engine.UnknownEvidence):
        run(engine, context(engine, tmp_path, text="A, B, C 是好机构"), "grouped_list_entry_counts", p)


def test_named_records_structural_count_only(engine, tmp_path):
    p = {"count": 3, "record_type": "company"}
    good = "| 公司 | 案例 |\n|---|---|\n| A | x |\n| B | y |\n| C | z |"
    assert run(engine, context(engine, tmp_path, text=good), "named_record_count", p)["record_count"] == 3
    with pytest.raises(engine.DeliveryFailure):
        run(engine, context(engine, tmp_path, text=good.replace("| B |", "| A |")), "named_record_count", p)
    with pytest.raises(engine.UnknownEvidence):
        run(engine, context(engine, tmp_path, text="三家公司有以下情况。"), "named_record_count", p)


def test_clause_and_pairing_are_quality_observations(engine, tmp_path):
    c = context(engine, tmp_path, text="FDE费用；问询函网址 https://example.test")
    out = run(engine, c, "quotation_clause_fields_present", {"clauses": ["FDE费用", "合同许可"]})
    assert out["scorable"] is False and out["literal_clues_present"] == ["FDE费用"]
    assert run(engine, c, "inquiry_reference_pairing_fields_present", {})["scorable"] is False
    with pytest.raises(engine.UnknownEvidence):
        run(engine, context(engine, tmp_path), "inquiry_reference_pairing_fields_present", {})


def test_current_outline_pdf_count_not_historical_count(engine, tmp_path):
    image_pdf(tmp_path / "out.pdf")
    c = context(engine, tmp_path, files=["out.pdf"])
    c.targets["outline"] = {"id": "outline", "kind": "text", "turn_indices": [1]}
    c.evidence["deliveries"]["outline"] = {"text": "第1页：封面\n第2页：总结"}
    p = {"outline_delivery_id": "outline"}
    assert run(engine, c, "pdf_image_count_matches_current_outline", p)["current_outline_count"] == 2
    c.evidence["deliveries"]["outline"]["text"] += "\n第3页：新增"
    with pytest.raises(engine.DeliveryFailure):
        run(engine, c, "pdf_image_count_matches_current_outline", p)
    with pytest.raises(engine.UnknownEvidence):
        run(engine, c, "pdf_image_count_matches_current_outline", {"outline_delivery_id": "missing"})


def test_unit_price_group_scope_and_equivalent_months(engine, tmp_path):
    good = "期限：1年\n| 类别 | 人日单价 |\n|---|---|\n| skill开发 | 1000元/人日 |\n| 系统对接 | 1000元/人日 |"
    p = {"groups": ["skill开发", "系统对接"], "field": "人日单价", "value": 1000, "unit": "元/人日"}
    assert run(engine, context(engine, tmp_path, text=good), "quotation_named_numeric_fields", p)["fields_checked"] == 2
    assert run(engine, context(engine, tmp_path, text=good), "quotation_named_numeric_fields", {
        "fields": [{"name": "期限", "value": 12, "unit": "月", "equivalents": [{"value": 1, "unit": "年"}]}]})["fields_checked"] == 1
    with pytest.raises(engine.DeliveryFailure):
        run(engine, context(engine, tmp_path, text=good.replace("| 系统对接 | 1000", "| 系统对接 | 2000")), "quotation_named_numeric_fields", p)
    with pytest.raises(engine.UnknownEvidence):
        run(engine, context(engine, tmp_path, text="总价1000元"), "quotation_named_numeric_fields", p)


def test_embedded_html_and_docx_require_actual_linked_payload(engine, tmp_path):
    raster(tmp_path / "photo.png", "red")
    (tmp_path / "photos.html").write_text('<html><img alt="徐" src="photo.png"></html>', "utf-8")
    p = {"allow_embedded_image_payloads": True, "allowed_image_containers": ["html", "docx"]}
    assert run(engine, context(engine, tmp_path, files=["photos.html"]), "file_delivery_open", p)["embedded_image_payloads"] == 1
    (tmp_path / "empty.html").write_text('<html><p>photo will be here</p></html>', "utf-8")
    with pytest.raises(engine.DeliveryFailure):
        run(engine, context(engine, tmp_path, files=["empty.html"]), "file_delivery_open", p)
    (tmp_path / "remote.html").write_text('<html><img src="https://example.test/photo.png"></html>', "utf-8")
    with pytest.raises(engine.UnknownEvidence):
        run(engine, context(engine, tmp_path, files=["remote.html"]), "file_delivery_open", p)


def test_order_sources_reject_attempt_start_input_bytes(engine, tmp_path):
    raster(tmp_path / "slide_00.png", "red")
    image_pdf(tmp_path / "out.pdf", ("red",))
    c = context(engine, tmp_path, files=["out.pdf"], extra={
        "initial_sha256": {"slide_00.png": sha(tmp_path / "slide_00.png")}})
    with pytest.raises(engine.UnknownEvidence):
        run(engine, c, "pdf_page_images_match_current_sources", {"ordered_source_names": ["slide_00.png"]})


def test_extra_file_flag_values_fail_closed(engine, tmp_path):
    image_pdf(tmp_path / "out.pdf", ("red",))
    with pytest.raises(engine.UnknownEvidence):
        run(engine, context(engine, tmp_path, files=["out.pdf"]), "file_delivery_open", {
            "allow_embedded_image_payloads": True, "require_actual_decodable_image_payload": False})


def test_explicitly_unsupported_input_format_does_not_count_as_declared(engine, tmp_path):
    d = tmp_path / "skill"; d.mkdir()
    (d / "SKILL.md").write_text("输入格式：LaTeX / Markdown / Word\n不支持 PDF", "utf-8")
    c = context(engine, tmp_path); c.evidence["deliveries"]["d"] = {"directory": "skill"}
    with pytest.raises(engine.DeliveryFailure):
        run(engine,c,"skill_declared_input_formats_present",{"formats":["latex","markdown","word","pdf"]})


def test_named_company_records_bind_name_column_not_ordinal_column(engine, tmp_path):
    p = {"count": 2, "record_type": "company"}
    duplicate = "| 序号 | 公司 | 案例 |\n|---|---|---|\n| 1 | A | x |\n| 2 | A | y |"
    with pytest.raises(engine.DeliveryFailure):
        run(engine, context(engine, tmp_path, text=duplicate), "named_record_count", p)
    blank = duplicate.replace("| 2 | A |", "| 2 | |")
    with pytest.raises(engine.DeliveryFailure):
        run(engine, context(engine, tmp_path, text=blank), "named_record_count", p)
    assert run(engine, context(engine,tmp_path,text=duplicate.replace("| 2 | A |","| 2 | B |")),"named_record_count",p)["record_count"]==2


def test_grouped_reference_field_is_row_bound_basic_presence(engine, tmp_path):
    p={"groups":[{"route":"纯电","country":"中国","count":2}],"require_reference_field":True}
    good="| 路线 | 国家 | 机构 | 参考文献 |\n|---|---|---|---|\n| 纯电 | 中国 | A | paper1 |\n| 纯电 | 中国 | B | paper2 |"
    assert run(engine,context(engine,tmp_path,text=good),"grouped_list_entry_counts",p)["reference_entries_checked"]==2
    with pytest.raises(engine.DeliveryFailure):
        run(engine,context(engine,tmp_path,text=good.replace("| B | paper2 |","| B | |")),"grouped_list_entry_counts",p)
    with pytest.raises(engine.UnknownEvidence):
        run(engine,context(engine,tmp_path,text=good.replace("参考文献","其他")),"grouped_list_entry_counts",p)


def test_explicit_page_units_take_priority_over_nested_numbered_detail(engine,tmp_path):
    body="Page1: Cover\n1. Detail A\n2. Detail B\nPage2: End\n1. Action"
    assert run(engine,context(engine,tmp_path,text=body),"text_numbered_item_count",{"count":2})["item_count"]==2


def test_named_html_photo_uses_container_parent_not_workspace_root(engine,tmp_path):
    d=tmp_path/"out"; d.mkdir(); raster(d/"photo.png","red")
    (d/"photos.html").write_text('<html><img alt="Xu" src="photo.png"></html>',"utf-8")
    c=context(engine,tmp_path,files=["out/photos.html"])
    assert run(engine,c,"named_image_delivery_entries",{"names":["Xu"]})["names_bound"]==1


def test_pdf_zero_area_transform_image_is_not_painted_payload(engine,tmp_path):
    image_pdf(tmp_path/"out.pdf",("red",))
    from pypdf import PdfReader
    reader=PdfReader(tmp_path/"out.pdf"); writer=PdfWriter(); writer.add_page(reader.pages[0])
    stream=DecodedStreamObject(); stream.set_data(b"q 0 0 0 0 0 0 cm /I Do Q")
    writer.pages[0][NameObject("/Contents")]=writer._add_object(stream)
    with (tmp_path/"zero.pdf").open("wb") as f: writer.write(f)
    with pytest.raises(engine.DeliveryFailure):
        run(engine,context(engine,tmp_path,files=["zero.pdf"]),"pdf_external_text_absent",{})


def test_quote_fields_and_group_rules_cannot_silently_mix(engine,tmp_path):
    body="Platform:50元\n| 项目 | 单价 |\n|---|---|\n| System | 2000元 |"
    p={"fields":[{"name":"Platform","value":50,"unit":"元"}],"groups":["System"],"field":"单价","value":1000,"unit":"元"}
    with pytest.raises(engine.UnknownEvidence):
        run(engine,context(engine,tmp_path,text=body),"quotation_named_numeric_fields",p)


def test_fde_calendar_day_bound_does_not_accept_person_days(engine,tmp_path):
    body="| 项目 | 驻场天数 |\n|---|---|\n| FDE | 7人日 |"
    with pytest.raises(engine.UnknownEvidence):
        run(engine,context(engine,tmp_path,text=body),"quotation_numeric_bounds",{"bounds":[{"scope":"FDE","field":"驻场天数","min":7}]})


@pytest.mark.parametrize("policy",[{"historical_ai_is_gold":True},{"score_at":"intermediate_steps"}])
def test_extension_policy_values_fail_closed(engine,tmp_path,policy):
    with pytest.raises(engine.UnknownEvidence):
        run(engine,context(engine,tmp_path,text="第1页：A"),"text_numbered_item_count",{"count":1,**policy})
