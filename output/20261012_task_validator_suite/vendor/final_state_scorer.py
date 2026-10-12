"""Offline command scorer for current-attempt, final-state basic delivery only.

Unknown evidence is an invalid measurement, never an invented task failure.
The scorer reads no historical conversations and executes no actor/model calls.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import posixpath
import re
import sys
import subprocess
import tempfile
from urllib.parse import unquote, urlparse
import xml.etree.ElementTree as ET
import zipfile


NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
      's': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
IMAGE_EXT = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.tif', '.tiff', '.svg'}
TEXT_EXT = {'.md', '.txt', '.html', '.htm', '.csv', '.tsv', '.json', '.yaml', '.yml', '.xml', '.py', '.js'}
NATIVE_IMAGE = 'sha256:2a45d063a0945811fc5405c652736347898e494c9dc40762e4d606f9bb46c4f0'


class UnknownEvidence(Exception):
    """The requirement cannot be measured from the supplied final evidence."""


class DeliveryFailure(Exception):
    """An observed final delivery does not meet the mechanical requirement."""


def source_id(request):
    """Use the pinned source identity; permit only the known legacy heldout ID form."""
    rubric = request.get('rubric') or {}
    explicit = request.get('source_session_id') or rubric.get('source_session_id') or rubric.get('contract_id')
    if explicit:
        if not isinstance(explicit, str): raise UnknownEvidence('invalid_source_session_id')
        if request.get('task_id') not in (explicit, 'heldout_' + explicit):
            raise UnknownEvidence('task_and_source_identity_mismatch')
        return explicit
    task = request.get('task_id', '')
    if re.fullmatch(r'heldout_conv_[a-f0-9]{12}', task): return task[len('heldout_'):]
    return task


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def parameters(check):
    merged = {}
    for name in ('expected', 'params', 'parameters'):
        if isinstance(check.get(name), dict):
            merged.update(check[name])
    return merged


def stripped(text):
    return re.sub(r'\s+', '', text)


def check_assert(condition, reason):
    if not condition:
        raise DeliveryFailure(reason)


def image_info(path):
    if path.suffix.lower() == '.svg':
        root = ET.fromstring(path.read_bytes())
        check_assert(root.tag in ('svg', '{http://www.w3.org/2000/svg}svg'), 'svg_root_invalid')
        view = root.get('viewBox', '').replace(',', ' ').split()
        def dimension(name, fallback):
            value = root.get(name, fallback)
            match = re.fullmatch(r'([0-9]+(?:\.[0-9]+)?)(?:px)?', str(value))
            if not match: raise UnknownEvidence('svg_intrinsic_dimensions_not_resolved')
            return float(match.group(1))
        width = dimension('width', view[2] if len(view) == 4 else '')
        height = dimension('height', view[3] if len(view) == 4 else '')
        check_assert(width > 0 and height > 0 and len(root) > 0, 'svg_payload_empty')
        return {'width': width, 'height': height, 'format': 'SVG'}
    from PIL import Image
    with Image.open(path) as image:
        image.load()
        return {'width': image.width, 'height': image.height, 'format': image.format}


def office(path):
    """Validate ZIP integrity and parse the actual main XML part, not its suffix."""
    with zipfile.ZipFile(path) as z:
        check_assert(z.testzip() is None, 'archive_member_crc_error')
        ET.fromstring(z.read('[Content_Types].xml'))
        ext = path.suffix.lower()
        main = {'.docx': 'word/document.xml', '.pptx': 'ppt/presentation.xml',
                '.xlsx': 'xl/workbook.xml'}[ext]
        tree = ET.fromstring(z.read(main))
        check_assert(tree.tag == {'docx': '{'+NS['w']+'}document',
                                  'pptx': '{'+NS['p']+'}presentation',
                                  'xlsx': '{'+NS['s']+'}workbook'}[ext[1:]], 'invalid_main_xml_root')
        files = {n: z.read(n) for n in z.namelist() if not n.endswith('/')}
    return tree, files


def presentation_slides(tree, files):
    relpart = 'ppt/_rels/presentation.xml.rels'
    if relpart not in files: raise DeliveryFailure('pptx_presentation_relationships_missing')
    rels = {r.get('Id'): r for r in ET.fromstring(files[relpart])}
    slides = []
    for sid in tree.findall('p:sldIdLst/p:sldId', NS):
        rel = rels.get(sid.get('{'+NS['r']+'}id'))
        check_assert(rel is not None and rel.get('TargetMode') != 'External', 'pptx_slide_relationship_missing')
        name = posixpath.normpath(posixpath.join('ppt', rel.get('Target', ''))).lstrip('/')
        check_assert(name in files, 'pptx_linked_slide_part_missing')
        ET.fromstring(files[name]); slides.append(name)
    check_assert(bool(slides) and len(set(slides)) == len(slides), 'pptx_invalid_slide_list')
    return slides


def docker_path(path):
    """Map host files to the existing WSL Docker backend without shell interpolation."""
    path = str(Path(path).resolve())
    if os.name == 'nt':
        match = re.match(r'^([A-Za-z]):[\\/](.*)$', path)
        if not match: raise UnknownEvidence('native_parser_host_path_not_mappable')
        return '/mnt/' + match.group(1).lower() + '/' + match.group(2).replace('\\', '/')
    return path


def legacy_office_info(path):
    """Use the already pinned LibreOffice image as an offline native decoder."""
    target_format = 'docx' if path.suffix.lower() == '.doc' else 'xlsx'
    with tempfile.TemporaryDirectory(prefix='skillloop_final_native_open_') as tmp:
        prefix = ['wsl', '-d', 'Ubuntu', '--', 'docker'] if os.name == 'nt' else ['docker']
        command = prefix + ['run', '--rm', '--network', 'none', '--read-only',
                            '--tmpfs', '/tmp:rw,size=512m', '-e', 'HOME=/tmp',
                            '--mount', 'type=bind,source=' + docker_path(path.parent) + ',target=/input,readonly',
                            '--mount', 'type=bind,source=' + docker_path(tmp) + ',target=/output',
                            '--entrypoint', '/usr/bin/soffice', NATIVE_IMAGE,
                            '-env:UserInstallation=file:///tmp/final-score-lo', '--headless',
                            '--convert-to', target_format, '--outdir', '/output', '/input/' + path.name]
        try:
            result = subprocess.run(command, capture_output=True, timeout=120,
                                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise UnknownEvidence('native_office_decoder_unavailable:' + type(exc).__name__) from exc
        if result.returncode:
            raise UnknownEvidence('native_office_decoder_runtime_error:' + str(result.returncode))
        converted = Path(tmp) / (path.stem + '.' + target_format)
        check_assert(converted.is_file(), 'legacy_office_native_open_failed')
        info = native_info(converted)
        info['format'] = path.suffix.lower()[1:]
        info['native_decoder'] = 'pinned_libreoffice_container'
        info['native_decoder_image'] = NATIVE_IMAGE
        return info


def native_info(path):
    """Native structure/open checks. Missing parser is unknown, corrupt bytes fail."""
    check_assert(path.is_file(), 'file_missing')
    check_assert(path.stat().st_size > 0, 'file_empty')
    ext = path.suffix.lower()
    try:
        if ext in IMAGE_EXT:
            data = image_info(path)
            native_format = {'JPEG': 'jpg', 'TIFF': 'tif'}.get(data['format'], data['format'].lower())
            return {'format': native_format, 'family': 'image', 'text': '', **{k: v for k, v in data.items() if k != 'format'}}
        if ext in {'.docx', '.pptx', '.xlsx'}:
            tree, files = office(path)
            if ext == '.docx':
                text = '\n'.join(''.join(p.itertext()) for p in tree.findall('.//w:p', NS))
                check_assert(bool(stripped(text)) or bool(tree.findall('.//w:drawing', NS)), 'docx_payload_empty')
            elif ext == '.pptx':
                slides = presentation_slides(tree, files)
                text = '\n'.join(''.join(ET.fromstring(files[n]).itertext()) for n in slides)
            else:
                sheets = [n for n in files if re.fullmatch(r'xl/worksheets/sheet\d+\.xml', n)]
                check_assert(bool(sheets), 'xlsx_has_no_worksheets')
                cells = sum(len(ET.fromstring(files[n]).findall('.//s:c', NS)) for n in sheets)
                check_assert(cells > 0, 'xlsx_payload_empty')
                text = '\n'.join(''.join(ET.fromstring(files[n]).itertext()) for n in sheets)
                if 'xl/sharedStrings.xml' in files:
                    text += '\n' + ''.join(ET.fromstring(files['xl/sharedStrings.xml']).itertext())
            return {'format': ext[1:], 'text': text, 'tree': tree, 'members': files}
        if ext == '.pdf':
            from pypdf import PdfReader
            reader = PdfReader(str(path), strict=True)
            check_assert(not reader.is_encrypted, 'pdf_encrypted_unreadable')
            check_assert(len(reader.pages) > 0, 'pdf_has_no_pages')
            check_assert(any(page.get_contents() is not None and page.get_contents().get_data().strip()
                             for page in reader.pages), 'pdf_payload_empty')
            text = '\n'.join(p.extract_text() or '' for p in reader.pages)
            return {'format': 'pdf', 'text': text, 'reader': reader, 'pages': len(reader.pages)}
        if ext == '.zip':
            with zipfile.ZipFile(path) as z:
                check_assert(z.testzip() is None, 'archive_member_crc_error')
                check_assert(any(not n.endswith('/') for n in z.namelist()), 'archive_empty')
            return {'format': 'zip', 'text': ''}
        if ext in TEXT_EXT:
            text = path.read_text(encoding='utf-8-sig')
            check_assert(bool(stripped(text)), 'text_file_payload_empty')
            if ext == '.json': json.loads(text)
            elif ext in {'.yaml', '.yml'}:
                import yaml
                yaml.safe_load(text)
            elif ext == '.xml': ET.fromstring(text)
            elif ext in {'.html', '.htm'}:
                check_assert(bool(re.search(r'<(?:html|body|div|main|section|table|canvas)\b', text, re.I)), 'html_markup_missing')
            elif ext in {'.csv', '.tsv'}:
                check_assert(bool(list(csv.reader(io.StringIO(text), delimiter='\t' if ext == '.tsv' else ','))), 'table_file_empty')
            return {'format': 'html' if ext == '.htm' else ext[1:], 'text': text}
        if ext in {'.xls', '.doc'}:
            return legacy_office_info(path)
        raise UnknownEvidence('native_parser_not_configured:' + ext)
    except (UnknownEvidence, DeliveryFailure):
        raise
    except ImportError as exc:
        raise UnknownEvidence('native_parser_dependency_missing:' + str(exc)) from exc
    except Exception as exc:
        raise DeliveryFailure('native_open_failed:' + type(exc).__name__) from exc


def links(text):
    return [unquote(v.strip('<>')) for v in re.findall(r'\]\(([^\n]+?)\)', text)
            if not urlparse(v.strip('<>')).scheme in {'http', 'https', 'app', 'codex'}]


class Context:
    def __init__(self, request, contract):
        self.request = request
        self.contract = contract
        self.result = request.get('result') or {}
        self.workspace = Path(request['workspace']).resolve()
        evidence = request.get('evidence') or self.result.get('final_state_evidence') or {}
        evidence_path = request.get('evidence_path') or self.result.get('final_state_evidence_path')
        if evidence_path:
            evidence = read_json(evidence_path)
        if not isinstance(evidence, dict): raise UnknownEvidence('invalid_evidence_object')
        if self.result.get('evidence_collection_required') and evidence.get('schema') != 'final-state-evidence-v1':
            raise UnknownEvidence('required_final_state_evidence_missing_or_invalid')
        self.evidence = evidence
        expected_sid = contract.get('sid', contract.get('session_id'))
        evidence_sid = evidence.get('source_session_id', evidence.get('task_id'))
        if evidence_sid and evidence_sid != expected_sid:
            raise UnknownEvidence('evidence_source_mismatch')
        if source_id(request) != expected_sid:
            raise UnknownEvidence('scoring_request_source_mismatch')
        if evidence.get('conversation_complete') is False:
            raise UnknownEvidence('conversation_not_complete')
        if evidence.get('workspace') and Path(evidence['workspace']).resolve() != self.workspace:
            raise UnknownEvidence('evidence_workspace_mismatch')
        self.targets = {d['id']: d for d in contract['final_deliverables']}
        self.cache = {}

    def path(self, value):
        value = unquote(str(value).strip('<>'))
        if value.startswith('sandbox:'): value = value[8:]
        if value.startswith('file://'): value = urlparse(value).path.lstrip('/')
        # Runtime container paths are mapped only into this attempt's workspace.
        if value == '/workspace': return self.workspace
        if value.startswith('/workspace/'): value = value[len('/workspace/'):]
        p = Path(value)
        if not p.is_absolute(): p = self.workspace / p
        p = p.resolve()
        if not p.is_relative_to(self.workspace):
            raise UnknownEvidence('delivery_path_outside_current_attempt')
        return p

    def target(self, did):
        if did not in self.targets: raise UnknownEvidence('unknown_delivery_id:' + str(did))
        return self.targets[did]

    def binding(self, did):
        bindings = self.evidence.get('deliveries', {})
        if isinstance(bindings, list): bindings = {v['delivery_id']: v for v in bindings}
        return bindings.get(did, {})

    def text(self, did, allow_files=True):
        bound = self.binding(did)
        if 'text' in bound: return str(bound['text'])
        if 'items' in bound: return '\n\n'.join(str(v) for v in bound['items'])
        target = self.target(did)
        turns = target.get('turn_indices', [])
        answers = self.result.get('turn_answers', [])
        matching = [a for i, a in enumerate(answers) if i in turns and isinstance(a, str)]
        text_targets = [v for v in self.targets.values() if v['kind'] in ('text', 'text_or_file')]
        overlapping = [v for v in text_targets if set(v.get('turn_indices', [])) & set(turns)]
        if matching and len(overlapping) <= 1:
            return matching[-1]
        if len(text_targets) == 1 and target['kind'] in ('text', 'text_or_file'):
            return str(self.result.get('answer', ''))
        if allow_files and ('files' in bound or 'directory' in bound):
            return '\n'.join(self.info(p).get('text', '') for p in self.files(did))
        if not self.result.get('answer') and not answers and not bound:
            return ''
        raise UnknownEvidence('multiple_text_targets_need_distinct_final_binding')

    def files(self, did, formats=None):
        target = self.target(did); bound = self.binding(did)
        if 'files' in bound:
            values = bound['files']
        elif 'directory' in bound:
            directory = self.path(bound['directory'])
            values = list(directory.rglob('*')) if directory.exists() else []
        else:
            answers = self.result.get('turn_answers', [])
            indices = target.get('turn_indices', [])
            values = []
            for i in sorted(indices, reverse=True):
                if i < len(answers):
                    values = links(answers[i])
                    if values: break
            if not values:
                file_targets = [v for v in self.targets.values() if v['kind'] == 'file']
                declared = self.result.get('artifacts', [])
                if len(file_targets) > 1 and declared:
                    raise UnknownEvidence('multiple_file_targets_need_distinct_final_binding')
                values = declared or links(str(self.result.get('answer', '')))
        paths = list(dict.fromkeys(self.path(v.get('path') if isinstance(v, dict) else v) for v in values))
        if formats:
            formats = set(formats)
            paths = [p for p in paths if (p.suffix.lower()[1:] in formats or
                                         ('image' in formats and p.suffix.lower() in IMAGE_EXT))]
        return paths

    def info(self, path):
        if path not in self.cache: self.cache[path] = native_info(path)
        return self.cache[path]

    def opened(self, did, p):
        fmts = p.get('allowed_formats', p.get('formats'))
        if not fmts:
            fmt = p.get('format', self.target(did).get('format'))
            fmts = [fmt] if isinstance(fmt, str) else fmt
        if fmts and 'directory' in fmts:
            value = self.binding(did).get('directory') or self.evidence.get('workspace_ai_root')
            if not value: raise UnknownEvidence('delivered_directory_binding_missing')
            directory = self.path(value)
            check_assert(directory.is_dir(), 'delivered_directory_missing')
            members = [f for f in directory.rglob('*') if f.is_file()]
            check_assert(bool(members), 'delivered_directory_empty')
            for file in members: file.read_bytes()
            return members
        paths = self.files(did, fmts)
        minimum = p.get('required_distinct_file_count', p.get('min_files', p.get('count', 1)))
        check_assert(len(paths) >= minimum, 'delivered_file_count_below_requirement')
        if 'count' in p: check_assert(len(paths) == p['count'], 'delivered_file_count_mismatch')
        for file in paths:
            data = self.info(file)
            if fmts:
                equivalents = {data['format'], data.get('family')}
                if data['format'] == 'jpg': equivalents.add('jpeg')
                if data['format'] == 'tif': equivalents.add('tiff')
                check_assert(bool(equivalents & set(fmts)), 'actual_file_format_mismatch')
            if 'pages' in p: check_assert(data.get('pages') == p['pages'], 'pdf_page_count_mismatch')
            if p.get('headers_empty'):
                check_assert(data['format'] == 'docx', 'header_check_requires_docx')
                headers = [b for n, b in data['members'].items() if re.fullmatch(r'word/header\d+\.xml', n)]
                check_assert(all(not stripped(''.join(ET.fromstring(b).itertext())) and
                                 not ET.fromstring(b).findall('.//w:drawing', NS) for b in headers), 'docx_header_not_empty')
            check_assert(not any(v in file.name for v in p.get('filename_excludes', [])), 'forbidden_filename_fragment')
        if p.get('separate_file'):
            other = {q for other_id in self.targets if other_id != did
                     for q in (self.files(other_id) if self.binding(other_id).get('files') else [])}
            check_assert(not set(paths) & other, 'independent_deliveries_share_same_file')
        return paths

    def readbacks(self, did, service=None):
        rows = [r for r in self.evidence.get('service_readbacks', [])
                if r.get('delivery_id') == did and (service is None or r.get('service') == service)]
        if not rows: raise UnknownEvidence('authoritative_final_service_readback_missing')
        for row in rows:
            if not (row.get('observation') == 'final_readback' and row.get('authoritative') is True and row.get('complete') is True):
                raise UnknownEvidence('service_evidence_is_not_complete_final_readback')
            if row.get('error'): raise UnknownEvidence('service_readback_failed')
            if not isinstance(row.get('records'), list): raise UnknownEvidence('service_readback_records_missing')
        return [record for row in rows for record in row['records']]

    def manifest(self, did, kind):
        value = self.binding(did).get('manifests', {}).get(kind)
        if value is None: value = self.evidence.get('manifests', {}).get(did, {}).get(kind)
        if value is None: raise UnknownEvidence('current_attempt_manifest_missing:' + kind)
        return value


def text_check(ctx, did, p, kind):
    text = ctx.text(did); check_assert(bool(stripped(text)), 'delivered_body_empty')
    if kind == 'delivered_text_or_file_nonempty' and p.get('accepted_forms') and 'text' not in ctx.binding(did) and ctx.binding(did).get('files'):
        formats = p['accepted_forms']
        check_assert(any(ctx.info(f)['format'] in formats for f in ctx.files(did)), 'text_or_file_delivery_format_mismatch')
    count = len(stripped(text))
    if kind == 'text_character_count_report_only':
        return {'characters': count, 'requested_approximate_count': p.get('requested_approximate_count'), 'scorable': False}
    if kind in ('text_character_count_max', 'text_basic_format'):
        check_assert(count <= p.get('maximum', p.get('max_characters', count)), 'character_count_exceeds_explicit_maximum')
    if kind == 'text_basic_format':
        if p.get('single_paragraph'): check_assert(len([v for v in re.split(r'\n\s*\n', text) if v.strip()]) == 1, 'multiple_paragraphs')
        if p.get('heading_absent'): check_assert(not re.search(r'(?m)^\s*#{1,6}\s', text), 'heading_present')
        if p.get('markdown_markers_absent'): check_assert(not re.search(r'(?:\*\*|__|```|!\[|\]\()', text), 'markdown_markers_present')
    if kind == 'text_forbidden_characters_absent':
        check_assert(not any(c in text for c in p['characters']), 'forbidden_character_present')
    if kind == 'delivered_http_url_parseable':
        urls = re.findall(r'https?://[^\s<>\]\)]+', text)
        valid = [v for v in urls if urlparse(v).scheme in p.get('schemes', ['http', 'https']) and urlparse(v).netloc]
        check_assert(len(valid) >= p.get('minimum_count', 1), 'parseable_http_url_missing')
    if kind == 'list_count':
        entries = re.findall(r'(?m)^\s*(?:[-*+] |\d+[.、)]\s*)(\S[^\n]*)', text)
        check_assert(len(entries) == p['count'], 'list_count_mismatch')
        if p.get('duplicates_disallowed'): check_assert(len(set(entries)) == len(entries), 'duplicate_list_entries')
    if kind == 'outline_list_structure_and_time_pattern':
        heads = re.findall(r'(?m)^\s*#{1,2}\s+.+', text)
        check_assert(len([v for v in heads if re.match(r'^\s*#\s', v)]) == p['outline_count'], 'outline_count_mismatch')
        check_assert(bool(re.search(p['time_interval_regex'], text)), 'time_interval_missing')
        modules = re.split(r'(?m)^\s*##\s+[^\n]*\n', text)[1:]
        check_assert(bool(modules), 'second_level_modules_missing')
        for module in modules:
            bullets = re.findall(r'(?m)^\s*(?:[-*+] |\d+[.)]\s+)\S', module)
            check_assert(p['module_bullet_count_min'] <= len(bullets) <= p['module_bullet_count_max'], 'module_bullet_count_mismatch')
    return {'characters': count}


def count_check(ctx, did, p, kind):
    fmt = ctx.target(did).get('format')
    paths = ctx.files(did, [fmt] if isinstance(fmt, str) else fmt)
    for path in paths: ctx.info(path)
    # Copies of the exact same image bytes are not distinct delivered images.
    unique = {sha(f) for f in paths if f.is_file()}
    count = len(unique)
    if 'minimum' in p: check_assert(count >= p['minimum'], 'artifact_count_below_minimum')
    elif 'count' in p: check_assert(count == p['count'], 'artifact_count_mismatch')
    return {'distinct_artifacts': count}


def image_check(ctx, did, p, kind):
    files = ctx.files(did, ['image']); check_assert(bool(files), 'image_delivery_missing')
    dimensions = []
    for path in files:
        data = ctx.info(path); w, h = data['width'], data['height']; dimensions.append([w, h])
        ratio = p.get('ratio', p.get('aspect_ratio'))
        if ratio: check_assert(w * ratio[1] == h * ratio[0], 'image_aspect_ratio_mismatch')
        if kind == 'image_4k_dimensions':
            check_assert(max(w, h) >= p['min_long_edge'] and min(w, h) >= p['min_short_edge'], 'image_below_explicit_4k_dimensions')
    return {'dimensions': dimensions}


def ppt_check(ctx, did, p, kind):
    paths = ctx.opened(did, {'format': 'pptx'}); counts = []
    for path in paths:
        data = ctx.info(path); members = data['members']
        slides = presentation_slides(data['tree'], members)
        counts.append(len(slides)); count = p.get('slide_count', p.get('count'))
        if count is not None: check_assert(len(slides) == count, 'pptx_slide_count_mismatch')
        if 'minimum' in p: check_assert(len(slides) >= p['minimum'], 'pptx_slide_count_below_minimum')
        if 'slide_count_min' in p: check_assert(len(slides) >= p['slide_count_min'], 'pptx_slide_count_below_minimum')
        if 'slide_count_max' in p: check_assert(len(slides) <= p['slide_count_max'], 'pptx_slide_count_above_maximum')
        if p.get('each_slide_image_present') or p.get('each_slide_at_least_one_embedded_image') or 'minimum_image_count' in p:
            total_images = 0
            for name in slides:
                tree = ET.fromstring(members[name]); rel = posixpath.dirname(name) + '/_rels/' + posixpath.basename(name) + '.rels'
                relations = ET.fromstring(members[rel]) if rel in members else None
                lookup = {r.attrib['Id']: r for r in relations} if relations is not None else {}
                embedded = []
                for node in tree.findall('.//a:blip', NS):
                    rid = node.get('{'+NS['r']+'}embed'); relationship = lookup.get(rid)
                    if relationship is not None and relationship.get('TargetMode') != 'External':
                        target = posixpath.normpath(posixpath.join(posixpath.dirname(name), relationship.get('Target', ''))).lstrip('/')
                        if target in members:
                            from PIL import Image
                            try:
                                with Image.open(io.BytesIO(members[target])) as im: im.load()
                                embedded.append(target)
                            except Exception: pass
                total_images += len(embedded)
                if p.get('each_slide_image_present') or p.get('each_slide_at_least_one_embedded_image'):
                    check_assert(bool(embedded), 'pptx_slide_has_no_decodable_embedded_image')
            if 'minimum_image_count' in p:
                check_assert(total_images >= p['minimum_image_count'], 'pptx_embedded_image_count_below_minimum')
    return {'slide_counts': counts}


def skill_check(ctx, did, p, kind):
    if 'cli' in p:
        probes = ctx.evidence.get('final_command_probes', [])
        matches = [r for r in probes if r.get('command') == [p['cli']] + p.get('probe', []) and r.get('observation') == 'final_probe']
        if not matches: raise UnknownEvidence('final_cli_probe_missing')
        check_assert(any(r.get('returncode') == 0 and bool(r.get('stdout')) for r in matches), 'final_cli_probe_failed')
        return {'cli_available': True}
    bound = ctx.binding(did)
    roots = []
    if bound.get('directory'): roots.append(ctx.path(bound['directory']))
    if p.get('skill_name'):
        roots.extend(ctx.path(v) for v in ctx.evidence.get('skill_roots', []))
        matches = [r / p['skill_name'] for r in roots]
        if p.get('state') == 'uninstalled':
            if not roots: raise UnknownEvidence('final_skill_search_roots_missing')
            check_assert(not any(r.exists() for r in matches), 'skill_still_installed')
            return {'state': 'uninstalled'}
        roots = matches
    elif not roots:
        all_roots = [ctx.path(v) for v in ctx.evidence.get('skill_roots', [])]
        hints = p.get('target_hints', [])
        if hints:
            roots = [r for parent in all_roots if parent.is_dir() for r in parent.iterdir()
                     if r.is_dir() and any(h.casefold() in r.name.casefold() for h in hints)]
        else:
            raise UnknownEvidence('generated_or_installed_directory_final_binding_missing')
    marker = p.get('marker', p.get('entry', 'SKILL.md'))
    candidates = [r / marker for r in roots]
    check_assert(any(r.is_file() and r.stat().st_size > 0 for r in candidates), 'final_install_entry_missing_or_empty')
    require_frontmatter = p.get('skill_frontmatter_name_description', marker == 'SKILL.md')
    for entry in candidates:
        if not entry.is_file(): continue
        text = entry.read_text('utf-8-sig')
        if require_frontmatter:
            import yaml
            match = re.match(r'\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)', text, re.S)
            check_assert(bool(match), 'skill_frontmatter_missing')
            header = yaml.safe_load(match.group(1))
            check_assert(isinstance(header, dict) and all(isinstance(header.get(k), str) and header[k].strip() for k in ('name', 'description')), 'skill_frontmatter_invalid')
        if p.get('must_be_changed') or p.get('new_generated_skill_required'):
            key = entry.relative_to(ctx.workspace).as_posix()
            initial = ctx.evidence.get('initial_sha256')
            if not isinstance(initial, dict): raise UnknownEvidence('initial_skill_state_missing')
            check_assert(initial.get(key) != sha(entry), 'skill_entry_not_new_or_changed')
    return {'readable_entries': [str(v.relative_to(ctx.workspace)) for v in candidates if v.is_file()]}


def state_check(ctx, did, p, kind):
    if kind == 'workspace_paths_final_state':
        if p.get('target_skill'):
            roots = ctx.evidence.get('skill_roots')
            if not roots: raise UnknownEvidence('final_skill_search_roots_missing')
            exists = any((ctx.path(r) / p['target_skill']).exists() for r in roots)
            check_assert(exists == p['expected_present'], 'skill_presence_mismatch')
            return {'present': exists}
        root = ctx.path(p.get('root', '.'))
        for rel in p.get('absent', []): check_assert(not (root / rel).exists(), 'cleanup_target_still_present')
        for rel in p.get('present_unchanged', []):
            file = root / rel; check_assert(file.is_file(), 'preserved_file_missing')
            key = file.relative_to(ctx.workspace).as_posix()
            initial = ctx.evidence.get('initial_sha256', {})
            if key not in initial: raise UnknownEvidence('initial_sha256_missing_for_preserved_file')
            check_assert(sha(file) == initial[key], 'preserved_file_changed')
        return {'paths_verified': True}
    if kind == 'persisted_memory_present':
        rows = ctx.binding(did).get('files', ctx.evidence.get('memory_files'))
        if rows is None: raise UnknownEvidence('current_source_persisted_memory_binding_missing')
        files = [ctx.path(v) for v in rows]
        check_assert(any(f.is_file() and bool(stripped(f.read_text('utf-8-sig'))) for f in files), 'persisted_memory_empty_or_missing')
        return {'persisted_records': len(files)}
    bound = ctx.binding(did)
    if bound.get('files'):
        actual = [ctx.info(f) for f in ctx.files(did)]
        check_assert(bool(actual), 'final_state_files_missing')
        if kind == 'knowledge_import_checkpoint_readback':
            # The progress record must be a real current JSON file, not a declaration in the answer.
            checkpoints = [read_json(f) for f in ctx.files(did) if f.suffix.lower() == '.json']
            check_assert(any(isinstance(v, dict) and any(k in v for k in ('progress', 'checkpoint', 'imported', 'pending', 'remaining'))
                             for v in checkpoints), 'knowledge_import_progress_checkpoint_missing')
        return {'state_files_read': len(actual)}
    records = ctx.readbacks(did)
    check_assert(bool(records), 'final_state_records_empty')
    return {'record_count': len(records)}


def service_check(ctx, did, p, kind):
    service = p.get('service')
    records = ctx.readbacks(did, service)
    expected = dict(p.get('expected') or {})
    if kind == 'scheduler_record_fields':
        for required in p['records']:
            check_assert(any(all(r.get(k) == v for k, v in required.items()) for r in records), 'scheduled_record_fields_mismatch')
        return {'matching_records': len(p['records']), 'actual_trigger_evaluated': False}
    minimum = p.get('min_records', 1)
    if p.get('assignee'):
        records = [r for r in records if r.get('assignee') == p['assignee']]
    check_assert(len(records) >= minimum, 'final_service_record_count_below_requirement')
    # These describe scoring policy rather than required remote record fields.
    policy = {'not_required', 'same_task_repetition', 'actual_trigger_not_evaluated', 'meeting_id_readback'}
    overrides = ctx.evidence.get('resolved_parameters', {}).get(did, {})
    raised_timeout = expected.get('timeout') == 'raised_value_recorded_but_no_exact_target_user_value'
    if raised_timeout and 'timeout' in overrides.get('expected', {}):
        raise UnknownEvidence('raised_timeout_requires_actual_change_not_observed_value_as_expected')
    expected.update(overrides.get('expected', {}))
    symbolic = {'current_authorized_personal_account', 'current_experiment_wecom',
                'user_turn_4_full_task_text', 'meeting number of final retained meeting',
                'raised_value_recorded_but_no_exact_target_user_value'}
    for key, value in expected.items():
        if key in policy: continue
        if key == 'timeout' and raised_timeout: continue
        if isinstance(value, str) and (value in symbolic or re.fullmatch(r'(?:Monday|daily|weekly|monthly) .+', value)):
            if key not in overrides.get('expected', {}):
                raise UnknownEvidence('relative_or_symbolic_service_parameter_unresolved:' + key)
    # One final object must satisfy the target's whole predicate. Independent
    # any(records) checks would splice a correct name from one job and a correct
    # payload from another, falsely accepting two incomplete objects.
    if expected.get('meeting_id_readback'):
        records = [r for r in records if r.get('meeting_id')]
        check_assert(bool(records), 'meeting_id_readback_missing')
    if p.get('schedule_hints'):
        records = [r for r in records if all(str(h) in str(r.get('schedule', '')) for h in p['schedule_hints'])]
        check_assert(bool(records), 'schedule_hint_missing')
    for key, value in expected.items():
        if key in policy: continue
        if key == 'timeout' and raised_timeout: continue
        if key == 'created':
            if value is True:
                records = [r for r in records if r.get('id') or r.get('meeting_id') or r.get('created') is True]
            else:
                records = [r for r in records if r.get('created') == value]
            check_assert(bool(records), 'created_service_record_missing')
            continue
        records = [r for r in records if r.get(key) == value]
        check_assert(bool(records), 'final_service_field_mismatch:' + key)
    if raised_timeout:
        transitions = [row for row in ctx.evidence.get('timeout_change_readbacks', [])
                       if row.get('delivery_id') == did and row.get('observation') == 'final_readback'
                       and row.get('authoritative') is True and row.get('complete') is True
                       and not row.get('error')]
        matched = []
        for record in records:
            target_id = record.get('id', record.get('job_id'))
            for transition in transitions:
                if not target_id or transition.get('job_id') != target_id: continue
                initial = transition.get('initial_timeout_seconds'); final = transition.get('final_timeout_seconds')
                if any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in (initial, final)):
                    continue
                if type(transition.get('before_dispatch_index')) is not int or transition['before_dispatch_index'] < 0:
                    continue
                if not all(re.fullmatch(r'[a-f0-9]{64}', str(transition.get(k, ''))) for k in
                           ('initial_config_sha256', 'final_config_sha256')):
                    continue
                if 'timeoutSeconds' in record and record['timeoutSeconds'] != final:
                    raise UnknownEvidence('timeout_transition_and_final_job_readback_differ')
                matched.append((record, initial, final))
        if not matched:
            raise UnknownEvidence('same_final_job_native_timeout_change_readback_missing')
        records = [record for record, initial, final in matched if final > initial]
        check_assert(bool(records), 'final_native_timeout_not_increased')
    check_assert(len(records) >= minimum, 'matching_final_service_record_count_below_requirement')
    return {'matching_records': len(records), 'actual_trigger_evaluated': False}


def docx_check(ctx, did, p, kind):
    paths = ctx.opened(did, {'format': 'docx'})
    for path in paths:
        data = ctx.info(path); tree = data['tree']; members = data['members']
        if kind == 'docx_track_change_elements_exist':
            check_assert(any(tree.findall('.//' + name, NS) for name in p.get('elements', ['w:ins', 'w:del'])), 'docx_track_change_elements_missing')
            continue
        # Resolve defaults, basedOn style inheritance, paragraph style, run style, then direct formatting.
        styles = ET.fromstring(members['word/styles.xml']) if 'word/styles.xml' in members else None
        index = {n.get('{'+NS['w']+'}styleId'): n for n in styles.findall('w:style', NS)} if styles is not None else {}
        def props(node, typ):
            return {n.tag: dict(n.attrib) for n in node.find(typ, NS)} if node is not None and node.find(typ, NS) is not None else {}
        def inherited(sid, typ, visited=None):
            visited = set() if visited is None else visited
            if sid not in index or sid in visited: return {}
            visited.add(sid); node = index[sid]; base = node.find('w:basedOn', NS)
            out = inherited(base.get('{'+NS['w']+'}val'), typ, visited) if base is not None else {}
            merge_props(out, props(node, typ)); return out
        default_run = {}; default_para = {}
        if styles is not None:
            n = styles.find('w:docDefaults/w:rPrDefault', NS); default_run = props(n, 'w:rPr')
            n = styles.find('w:docDefaults/w:pPrDefault', NS); default_para = props(n, 'w:pPr')
        runs_seen = 0
        for para in tree.findall('.//w:p', NS):
            text = ''.join(para.itertext())
            if not stripped(text): continue
            ps = para.find('w:pPr/w:pStyle', NS); sid = ps.get('{'+NS['w']+'}val') if ps is not None else 'Normal'
            paragraph_props = {k: dict(v) for k, v in default_para.items()}; merge_props(paragraph_props, inherited(sid, 'w:pPr')); merge_props(paragraph_props, props(para, 'w:pPr'))
            if 'line_spacing_multiple' in p:
                spacing = paragraph_props.get('{'+NS['w']+'}spacing', {})
                line = spacing.get('{'+NS['w']+'}line'); rule = spacing.get('{'+NS['w']+'}lineRule', 'auto')
                check_assert(line is not None and rule == 'auto' and float(line)/240 == p['line_spacing_multiple'], 'docx_effective_line_spacing_mismatch')
            if 'first_line_indent_characters' in p:
                indent = paragraph_props.get('{'+NS['w']+'}ind', {})
                chars = indent.get('{'+NS['w']+'}firstLineChars')
                twips = indent.get('{'+NS['w']+'}firstLine')
                wanted = p['first_line_indent_characters']
                native_match = chars is not None and float(chars)/100 == wanted
                if not native_match and twips is not None and 'font_size_pt' in p:
                    native_match = float(twips) == wanted * p['font_size_pt'] * 20
                check_assert(native_match, 'docx_effective_first_line_indent_mismatch')
            for run in para.findall('.//w:r', NS):
                rt = ''.join(run.itertext())
                if not stripped(rt): continue
                runs_seen += 1
                rp = {k: dict(v) for k, v in default_run.items()}; merge_props(rp, inherited(sid, 'w:rPr'))
                rs = run.find('w:rPr/w:rStyle', NS)
                if rs is not None: merge_props(rp, inherited(rs.get('{'+NS['w']+'}val'), 'w:rPr'))
                merge_props(rp, props(run, 'w:rPr'))
                fonts = rp.get('{'+NS['w']+'}rFonts', {})
                if 'eastAsia_font' in p and re.search(r'[\u3400-\u9fff]', rt):
                    check_assert(fonts.get('{'+NS['w']+'}eastAsia') == p['eastAsia_font'], 'docx_effective_eastAsia_font_mismatch')
                if 'numeric_latin_font_family' in p and re.search(r'[A-Za-z0-9]', rt):
                    check_assert(fonts.get('{'+NS['w']+'}ascii') == p['numeric_latin_font_family'], 'docx_effective_latin_font_mismatch')
                if 'font_size_pt' in p:
                    size = rp.get('{'+NS['w']+'}sz', {}).get('{'+NS['w']+'}val')
                    check_assert(size is not None and float(size)/2 == p['font_size_pt'], 'docx_effective_font_size_mismatch')
        check_assert(runs_seen > 0, 'docx_no_text_runs')
        if p.get('image_bytes_present'):
            check_assert(bool(tree.findall('.//w:drawing', NS)) and any(n.startswith('word/media/') and b for n, b in members.items()), 'docx_image_media_missing')
        if 'header_text' in p:
            headers = [b for n, b in members.items() if re.fullmatch(r'word/header\d+\.xml', n)]
            check_assert(any(p['header_text'] in ''.join(ET.fromstring(b).itertext()) for b in headers), 'docx_required_header_text_missing')
        if p.get('page_number_field_present'):
            parts = [b for n, b in members.items() if n == 'word/document.xml' or re.fullmatch(r'word/(?:header|footer)\d+\.xml', n)]
            fields = []
            for part in parts:
                root = ET.fromstring(part)
                fields.extend(''.join(n.itertext()) for n in root.findall('.//w:instrText', NS))
                fields.extend(n.get('{'+NS['w']+'}instr', '') for n in root.findall('.//w:fldSimple', NS))
            check_assert(any(re.search(r'\bPAGE\b', v) for v in fields), 'docx_page_number_field_missing')
    return {'docx_files_checked': len(paths)}


def table_check(ctx, did, p, kind):
    try: text = ctx.text(did)
    except UnknownEvidence: text = ''
    paths = ctx.files(did) if ctx.binding(did).get('files') else []
    alltext = text; table_count = len(re.findall(r'<table\b', text, re.I))
    column_headers = []
    for head in re.findall(r'<tr\b[^>]*>(.*?)</tr>', text, re.I | re.S):
        column_headers.append(re.sub(r'<[^>]+>', '', head))
    lines = text.splitlines()
    for i, line in enumerate(lines[1:], 1):
        if re.match(r'^\s*\|?\s*:?-{3,}', line) and '|' in lines[i-1]: column_headers.append(lines[i-1])
    table_count += len(re.findall(r'(?m)^\s*\|?[^\n]*\|[^\n]*\n\s*\|?\s*:?-{3,}', text))
    for path in paths:
        data = ctx.info(path); alltext += '\n' + data.get('text', '')
        if data['format'] == 'docx':
            tables = data['tree'].findall('.//w:tbl', NS); table_count += len(tables)
            column_headers.extend(''.join(row.itertext()) for table in tables for row in table.findall('w:tr', NS)[:1])
        if data['format'] == 'xlsx':
            table_count += 1; members = data['members']; strings = []
            if 'xl/sharedStrings.xml' in members:
                strings = [''.join(v.itertext()) for v in ET.fromstring(members['xl/sharedStrings.xml']).findall('s:si', NS)]
            for name, blob in members.items():
                if not re.fullmatch(r'xl/worksheets/sheet\d+\.xml', name): continue
                rows = ET.fromstring(blob).findall('.//s:row', NS)
                if not rows: continue
                cells = []
                for cell in rows[0].findall('s:c', NS):
                    value = cell.find('s:v', NS)
                    if cell.get('t') == 's' and value is not None:
                        cells.append(strings[int(value.text)])
                    else: cells.append(''.join(cell.itertext()))
                column_headers.append('\t'.join(cells))
        if data['format'] in ('csv', 'tsv'):
            table_count += 1
            column_headers.append('\t'.join(next(csv.reader(io.StringIO(data['text']), delimiter='\t' if data['format']=='tsv' else ','))))
    if kind == 'delivered_table_present': check_assert(table_count >= p.get('minimum_table_count', 1), 'parseable_table_missing')
    if kind == 'table_column_labels_presence':
        check_assert(any(all(v in head for v in p['columns']) for head in column_headers), 'required_table_column_label_missing')
    return {'tables': table_count}


def merge_props(target, other):
    """A direct font override can change eastAsia without removing inherited ascii."""
    for key, value in other.items():
        target.setdefault(key, {}).update(value)


def literal_check(ctx, did, p, kind):
    bound = ctx.binding(did)
    if p.get('scope') == 'generated_skill_and_examples':
        if not bound.get('directory'): raise UnknownEvidence('generated_skill_directory_binding_missing')
        root = ctx.path(bound['directory'])
        files = [f for f in root.rglob('*') if f.is_file() and f.suffix.lower() in TEXT_EXT]
        text = '\n'.join(f.read_text('utf-8-sig') for f in files)
    else: text = ctx.text(did)
    check_assert(all(v in text for v in p['literals']), 'explicit_literal_field_missing')
    return {'literal_count': len(p['literals'])}


def body_items_check(ctx, did, p, kind):
    bound = ctx.binding(did)
    if 'items' in bound:
        items = [v for v in bound['items'] if isinstance(v, str) and stripped(v)]
    elif 'files' in bound:
        items = [ctx.info(f).get('text', '') for f in ctx.files(did)]
        items = [v for v in items if stripped(v)]
    else:
        raise UnknownEvidence('independent_body_items_binding_missing')
    check_assert(len(set(items)) >= p['required_count'], 'distinct_delivered_body_items_missing')
    return {'distinct_body_items': len(set(items))}


def manifest_check(ctx, did, p, kind):
    mk = {'manifest_corresponding_artifacts': 'pages', 'view_manifest_files_exist': 'views',
          'image_outline_count_matches': 'outline_pages', 'unique_input_output_manifest': 'input_outputs'}[kind]
    records = ctx.manifest(did, mk)
    source_reference = None
    if isinstance(records, dict):
        source_reference = records.get('source_delivery_id')
        declared_sha = records.get('source_body_sha256')
        records = records.get('items')
        if source_reference:
            body = ctx.text(source_reference)
            check_assert(declared_sha == hashlib.sha256(body.encode('utf-8')).hexdigest(), 'manifest_not_bound_to_current_source_body')
    check_assert(isinstance(records, list) and bool(records), 'artifact_manifest_empty')
    if kind == 'view_manifest_files_exist':
        check_assert(set(p['required_view_labels']).issubset({v.get('label') for v in records}), 'required_view_label_missing')
    if kind == 'unique_input_output_manifest':
        inputs = ctx.evidence.get('unique_input_pdf_ids')
        if not isinstance(inputs, list): raise UnknownEvidence('unique_current_input_pdf_ids_missing')
        check_assert(set(inputs) == {v.get('input_id') for v in records}, 'input_output_manifest_coverage_mismatch')
    for row in records:
        if not row.get('path'): raise UnknownEvidence('manifest_artifact_path_missing')
        ctx.info(ctx.path(row['path']))
    check_assert(len({ctx.path(v['path']) for v in records}) == len(records), 'manifest_reuses_one_artifact_for_multiple_items')
    if kind == 'image_outline_count_matches':
        if not source_reference: raise UnknownEvidence('current_bp_outline_source_binding_missing')
        files = ctx.files(did, ['image'])
        check_assert(len(files) == len(records), 'image_count_does_not_match_current_outline')
    return {'manifest_items_verified': len(records)}


def archive_check(ctx, did, p, kind):
    values = [v.get('path') if isinstance(v, dict) else v for v in ctx.evidence.get('input_files', [])]
    candidates = [ctx.path(v) for v in values if str(v).lower().endswith('.zip')]
    # The same provided archive can have canonical and original-path aliases.
    # Distinct bytes are different inputs; identical bytes are one source archive.
    inputs = list({sha(v): v for v in candidates if v.is_file()}.values())
    if len(inputs) != 1: raise UnknownEvidence('single_current_input_zip_binding_missing')
    destination = ctx.evidence.get('workspace_ai_root')
    if not destination: raise UnknownEvidence('current_workspace_ai_root_binding_missing')
    root = ctx.path(destination); count = 0
    with zipfile.ZipFile(inputs[0]) as z:
        for info in z.infolist():
            if info.is_dir(): continue
            path = (root / info.filename).resolve()
            if not path.is_relative_to(root): raise UnknownEvidence('input_zip_member_outside_destination')
            check_assert(path.is_file(), 'extracted_archive_member_missing')
            check_assert(path.read_bytes() == z.read(info), 'extracted_archive_member_bytes_mismatch'); count += 1
    return {'members_verified': count}


def pdf_check(ctx, did, p, kind):
    paths = ctx.opened(did, {'format': 'pdf'})
    counts = []
    for path in paths:
        reader = ctx.info(path)['reader']; counts.append(len(reader.pages)); images = []
        for page in reader.pages:
            resources = page.get('/Resources', {})
            resources = resources.get_object() if hasattr(resources, 'get_object') else resources
            objects = resources.get('/XObject', {})
            objects = objects.get_object() if hasattr(objects, 'get_object') else objects
            current = [v.get_object() for v in objects.values() if v.get_object().get('/Subtype') == '/Image']
            if kind == 'pdf_image_pages_and_image_aspect_ratio':
                check_assert(bool(current), 'pdf_page_image_xobject_missing')
                ratio = p['image_aspect_ratio']
                check_assert(all(int(i['/Width'])*ratio[1] == int(i['/Height'])*ratio[0] for i in current), 'pdf_image_aspect_ratio_mismatch')
            images.extend(current)
        if kind == 'pdf_merged_image_sources_count':
            # Count actual embedded sources, not pages. Composite pages require native assembly evidence.
            wanted = p['expected_source_image_count']
            if len(images) != wanted:
                assembly = ctx.manifest(did, 'pdf_assembly')
                sources = assembly.get('sources', []) if isinstance(assembly, dict) else []
                check_assert(len(sources) == wanted, 'pdf_source_image_count_mismatch')
                if not isinstance(assembly, dict) or assembly.get('pdf_sha256') != sha(path):
                    raise UnknownEvidence('pdf_assembly_manifest_not_bound_to_actual_pdf')
                for source in sources:
                    original = ctx.path(source['path']); ctx.info(original)
                    check_assert(source.get('sha256') == sha(original), 'pdf_assembly_source_hash_mismatch')
                # A declared assembly map alone cannot prove composite bitmap content.
                raise UnknownEvidence('composite_pdf_source_coverage_not_mechanically_proven')
    return {'pdf_page_counts': counts}


def named_reference_check(ctx, did, p, kind):
    files = ctx.files(did)
    check_assert(any(f.name == p['basename'] and f.is_file() for f in files), 'named_delivered_file_reference_missing')
    for f in files:
        if f.name == p['basename']: ctx.info(f)
    return {'named_reference_resolves': True}


def sheet_image_check(ctx, did, p, kind):
    paths = ctx.opened(did, {'format': 'xlsx'}); counts = []
    for path in paths:
        members = ctx.info(path)['members']; count = 0
        drawings = [n for n in members if re.fullmatch(r'xl/drawings/drawing\d+\.xml', n)]
        for name in drawings:
            root = ET.fromstring(members[name]); relname = posixpath.dirname(name)+'/_rels/'+posixpath.basename(name)+'.rels'
            rels = ET.fromstring(members[relname]) if relname in members else []
            mapping = {r.get('Id'): r.get('Target') for r in rels if r.get('TargetMode') != 'External'}
            for node in root.findall('.//a:blip', NS):
                target = mapping.get(node.get('{'+NS['r']+'}embed'))
                if target:
                    member = posixpath.normpath(posixpath.join(posixpath.dirname(name), target))
                    if member in members:
                        from PIL import Image
                        with Image.open(io.BytesIO(members[member])) as im: im.load()
                        count += 1
        check_assert(count >= p['minimum_embedded_images'], 'xlsx_embedded_image_missing'); counts.append(count)
    return {'embedded_image_counts': counts}


HANDLERS = {}
def register(handler, names):
    for name in names.split(): HANDLERS[name] = handler


register(text_check, 'delivered_body_nonempty text_body_nonempty delivered_text_nonempty delivered_text_or_file_nonempty text_forbidden_characters_absent text_character_count_report_only delivered_http_url_parseable text_character_count_max list_count outline_list_structure_and_time_pattern text_basic_format')
register(lambda c, d, p, k: {'files_opened': len(c.opened(d, p))}, 'delivered_file_open file_delivery_open final_file_native_open')
register(count_check, 'delivered_artifact_count delivered_artifact_count_minimum')
register(image_check, 'image_aspect_ratio image_dimensions_ratio image_4k_dimensions')
register(ppt_check, 'pptx_slide_count_and_image_relationships pptx_embedded_image_presence pptx_slide_count_minimum pptx_slide_count')
register(skill_check, 'skill_final_state final_install_directory_readable')
register(state_check, 'workspace_paths_final_state persisted_memory_present final_state_readback knowledge_import_checkpoint_readback')
register(service_check, 'final_service_state scheduler_record_fields')
register(docx_check, 'docx_track_change_elements_exist docx_effective_run_and_paragraph_format docx_effective_format_and_media')
register(table_check, 'delivered_table_present table_column_labels_presence')
register(literal_check, 'literal_fields_presence')
register(body_items_check, 'distinct_delivered_body_items')
register(manifest_check, 'manifest_corresponding_artifacts unique_input_output_manifest view_manifest_files_exist image_outline_count_matches')
register(archive_check, 'archive_members_finally_available')
register(pdf_check, 'pdf_merged_image_sources_count pdf_image_pages_and_image_aspect_ratio')
register(named_reference_check, 'existing_named_file_reference_resolves')
register(sheet_image_check, 'spreadsheet_embedded_images_exist')

# Explicitly account for every supplied parameter; additions fail closed instead
# of silently becoming an ignored condition. Policy metadata does not add scores.
PARAMETERS = {
    text_check: set('strip_whitespace trim_whitespace no_minimum_words_invented semantic_completion_not_inferred source_turn_indices accepted_forms characters requested_approximate_count hard_threshold schemes minimum_count maximum scope count_rule max_characters single_paragraph heading_absent markdown_markers_absent count nonempty_entries duplicates_disallowed outline_count heading_levels module_bullet_count_min module_bullet_count_max time_interval_regex'.split()),
    count_check: {'count', 'minimum'},
    image_check: {'ratio', 'aspect_ratio', 'min_long_edge', 'min_short_edge'},
    ppt_check: set('count slide_count minimum slide_count_min slide_count_max each_slide_image_present each_slide_at_least_one_embedded_image minimum_image_count'.split()),
    skill_check: set('target_hints new_generated_skill_required entry front_matter skill_name state skill_md_parseable must_be_changed readable_final_entry export_link_required marker nonempty_marker skill_frontmatter_name_description cli probe scope'.split()),
    state_check: set('root absent present_unchanged target_skill expected_present scope nonempty_persisted_record current_source_record readable_nonempty_record separate_export_required include_notebooks include_uncategorized final_instruction completion_of_deferred_work_required'.split()),
    service_check: {'service', 'min_records', 'assignee', 'expected', 'schedule_hints', 'records', 'trigger_required'},
    docx_check: set('elements any_of eastAsia_font font_size_pt numeric_latin_font_family line_spacing_multiple first_line_indent_characters header_text page_number_field_present image_bytes_present'.split()),
    table_check: {'accepted_forms', 'minimum_table_count', 'columns'},
    literal_check: {'scope', 'literals'},
    body_items_check: {'required_count', 'files_optional', 'semantic_clause_separation_quality_not_scored'},
    manifest_check: {'count_from', 'required_view_labels', 'compare_with', 'no_historical_fixed_page_count'},
    archive_check: {'destination', 'expected'},
    pdf_check: {'expected_source_image_count', 'page_count', 'allow_composite_pages_with_native_assembly_manifest',
                'image_aspect_ratio', 'page_aspect_ratio', 'image_xobject_each_page', 'text_description_below_image_required'},
    named_reference_check: {'basename'},
    sheet_image_check: {'minimum_embedded_images'},
}
FILE_PARAMETER_NAMES = set('allowed_formats formats format required_distinct_file_count min_files count require_nonempty_payload resolve_from_current_attempt_delivery_declaration actual_file nonempty openable delivery_path_resolves decodable pages headers_empty filename_excludes separate_file'.split())
POLICY_PARAMETER_NAMES = {'score_at', 'historical_ai_is_gold'}


def parameter_support(check):
    kind = check.get('kind') or check.get('method'); handler = HANDLERS.get(kind)
    names = FILE_PARAMETER_NAMES if kind in ('delivered_file_open', 'file_delivery_open', 'final_file_native_open') else PARAMETERS.get(handler, set())
    return sorted(set(parameters(check)) - names - POLICY_PARAMETER_NAMES)


def load_contracts(path):
    result = {}
    for line in Path(path).read_text('utf-8-sig').splitlines():
        if not line.strip(): continue
        row = json.loads(line); key = row.get('sid', row.get('session_id'))
        if key in result: raise ValueError('duplicate_contract_source')
        result[key] = row
    return result


def invalid_measurement(reason, contract=None):
    checks = []
    if isinstance(contract, dict):
        checks = [{'index': i, 'delivery_id': c.get('delivery_id'),
                   'kind': c.get('kind') or c.get('method'), 'status': 'unknown',
                   'passed': None, 'reason': reason,
                   'scorable': (c.get('kind') or c.get('method')) != 'text_character_count_report_only'}
                  for i, c in enumerate(contract.get('checks', []))]
    return {'valid': False, 'score': None, 'reason': reason, 'checks': checks,
            'counts': {'unknown': len(checks)}, 'measurement_failure': True}


def score_request(request, contracts=None):
    rubric = request.get('rubric') or {}
    if rubric.get('final_contract_file_sha256'):
        try:
            if sha(rubric['final_contract_path']) != rubric['final_contract_file_sha256']:
                raise UnknownEvidence('pinned_final_contract_file_changed')
        except (OSError, KeyError, UnknownEvidence) as exc:
            return {'valid': False, 'score': None, 'reason': str(exc), 'checks': []}
    contract = request.get('final_contract') or (request.get('rubric') or {}).get('final_contract')
    if contract is None:
        try: contract = (contracts or {}).get(source_id(request))
        except UnknownEvidence as exc:
            return {'valid': False, 'score': None, 'reason': str(exc), 'checks': []}
    if not isinstance(contract, dict):
        return {'valid': False, 'score': None, 'reason': 'final_contract_missing', 'checks': []}
    for flag in ('actor_can_see_historical_ai', 'quality_scored', 'intermediate_steps_scored', 'manual_judgement_scored'):
        if contract.get(flag) is not False:
            return invalid_measurement('unsupported_scoring_policy:' + flag, contract)
    if contract.get('score_at') != 'conversation_end_only':
        return invalid_measurement('unsupported_scoring_time', contract)
    try: ctx = Context(request, contract)
    except (UnknownEvidence, OSError, ValueError) as exc:
        return invalid_measurement(str(exc), contract)
    results = []
    for i, check in enumerate(contract['checks']):
        kind = check.get('kind') or check.get('method'); did = check.get('delivery_id')
        item = {'index': i, 'delivery_id': did, 'kind': kind, 'scorable': kind != 'text_character_count_report_only'}
        try:
            ctx.target(did)
            if kind not in HANDLERS: raise UnknownEvidence('validator_not_implemented:' + str(kind))
            unsupported = parameter_support(check)
            if unsupported: raise UnknownEvidence('validator_parameters_not_implemented:' + ','.join(unsupported))
            observed = HANDLERS[kind](ctx, did, parameters(check), kind)
            item.update(status='pass', passed=True, observed=observed)
        except DeliveryFailure as exc:
            item.update(status='fail', passed=False, reason=str(exc))
        except UnknownEvidence as exc:
            item.update(status='unknown', passed=None, reason=str(exc))
        except Exception as exc:
            # Parser/configuration errors are measurement failures rather than invented task zeros.
            item.update(status='unknown', passed=None, reason='validator_exception:' + type(exc).__name__)
        results.append(item)
    scored = [v for v in results if v['scorable']]
    valid = bool(scored) and all(v['status'] != 'unknown' for v in scored)
    delivery_status = {}
    for did in ctx.targets:
        rows = [v for v in scored if v['delivery_id'] == did]
        delivery_status[did] = ('unknown' if not rows or any(v['status'] == 'unknown' for v in rows)
                                else 'pass' if all(v['passed'] for v in rows) else 'fail')
    return {'schema': 'final-state-basic-delivery-score-v1', 'task_id': request.get('task_id'),
            'scorer': 'offline_final_state', 'score_at': 'conversation_end_only',
            'valid': valid, 'score': float(all(v['passed'] for v in scored)) if valid else None,
            'check_pass_fraction': sum(v['passed'] is True for v in scored)/len(scored) if valid else None,
            'checks': results, 'delivery_status': delivery_status,
            'counts': dict(collections.Counter(v['status'] for v in results)),
            'quality_scored': False, 'intermediate_steps_scored': False, 'historical_ai_read': False}


def coverage(contracts):
    rows = []
    for sid, c in contracts.items():
        for i, check in enumerate(c['checks']):
            kind = check.get('kind') or check.get('method')
            rows.append({'sid': sid, 'index': i, 'delivery_id': check.get('delivery_id'), 'kind': kind,
                         'schema_variant': 'kind' if check.get('kind') else 'method',
                         'handler_implemented': kind in HANDLERS,
                         'unsupported_parameters': parameter_support(check),
                         'actual_business_score_computed': False})
    return {'schema': 'final-state-validator-coverage-v1', 'sessions': len(contracts),
            'deliveries': sum(len(c['final_deliverables']) for c in contracts.values()),
            'checks': len(rows), 'handler_covered_checks': sum(v['handler_implemented'] for v in rows),
            'parameter_covered_checks': sum(not v['unsupported_parameters'] for v in rows),
            'schema_variants': dict(collections.Counter(v['schema_variant'] for v in rows)),
            'kind_counts': dict(collections.Counter(v['kind'] for v in rows)),
            'unknown_evidence_is_invalid_measurement': True, 'rows': rows}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('request', nargs='?'); parser.add_argument('response', nargs='?')
    parser.add_argument('--contracts'); parser.add_argument('--coverage-output')
    args = parser.parse_args(argv)
    contracts = load_contracts(args.contracts) if args.contracts else {}
    if args.coverage_output:
        out = coverage(contracts); Path(args.coverage_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.coverage_output).write_text(json.dumps(out, ensure_ascii=False, indent=2)+'\n', 'utf-8')
        print(json.dumps({k: out[k] for k in ('sessions', 'deliveries', 'checks', 'handler_covered_checks')}))
        return 0
    if not args.request or not args.response: parser.error('request and response are required')
    result = score_request(read_json(args.request), contracts)
    Path(args.response).write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', 'utf-8')
    print(json.dumps({'valid': result['valid'], 'score': result['score'], 'counts': result.get('counts')}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
