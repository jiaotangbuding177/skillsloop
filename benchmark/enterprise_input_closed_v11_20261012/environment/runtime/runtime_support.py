"""Compatibility for actually admitted Gitee skill packages, without edits."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil


def configure(workspace, context=None):
    workspace = Path(workspace).resolve()
    skills = workspace / 'skills'
    aliases = []
    guides = []
    pdf = skills / 'pdf_zzz4ai'
    if (pdf / 'SKILL.md').is_file():
        for old, actual in (('REFERENCE.md', 'reference.md'), ('FORMS.md', 'forms.md')):
            target = pdf / actual
            alias = pdf / old
            if not target.is_file():
                raise FileNotFoundError('Admitted pdf_zzz4ai reference missing: ' + str(target))
            if alias.exists() or alias.is_symlink():
                # Windows-backed Docker workspaces may already resolve both
                # case spellings to the same native file without a symlink.
                if not alias.samefile(target):
                    raise ValueError('PDF case-compatibility path conflicts: ' + str(alias))
            else:
                alias.symlink_to(actual)
            aliases.append({'path':str(alias),'target':str(target),
                            'reason':'upstream capitalized references on a case-sensitive Linux filesystem',
                            'changes_source_package_bytes':False})
        guides.append('pdf_zzz4ai 的原文大写 REFERENCE.md/FORMS.md 已映射到同包真实小写文件；上游文件内容和SHA未改。')
    scan = skills / 'evomind-paper-scan'
    if (scan / 'SKILL.md').is_file():
        wrapper = shutil.which('evo-paper-scan')
        font = Path('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc')
        if not wrapper or not font.is_file() or importlib.util.find_spec('paperconan') is None:
            raise RuntimeError('Admitted evomind-paper-scan needs evo-paper-scan, fonts-wqy-zenhei and paperconan 0.5.0')
        guides.append('evomind-paper-scan 上游脚本保留原文；Linux运行请使用 evo-paper-scan --skill-dir /workspace/skills/evomind-paper-scan -- --paper <真实论文路径> --source-data <真实数据目录> --out-dir /workspace/outputs/reports --title <题名> --docx --pdf。省略source-data时只审计论文自身。该包装器将Windows字体相对路径临时映射到Linux中文字体，不改扫描算法、正文或结果。')
    if (skills / 'image-generation' / 'SKILL.md').is_file():
        guides.append('本轮用户指定图片统一采用ECNU适配：image-generation 使用 python /opt/eval-adapter/ecnu_tools.py image --text "描述" --size WIDTHxHEIGHT --output /workspace/outputs/结果.png。非原生尺寸按保持内容比例的缩放和补边交付，receipt记录实际接口尺寸及转换。')
    if (skills / 'image-editing' / 'SKILL.md').is_file():
        guides.append('image-editing 使用 python /opt/eval-adapter/ecnu_tools.py image-edit --image-path "原图" --text "要求" --output /workspace/outputs/结果.png；多参考用 --image-paths "主图" "参考图"，明确拼为编号参考图后单图上传ECNU，receipt披露此适配，禁止声称原生多图API已恢复。')
    if (skills / 'image-ocr' / 'SKILL.md').is_file():
        if not shutil.which('image-ocr'):
            raise RuntimeError('Original image-ocr command dependency missing')
        guides.append('image-ocr <图片路径> --lang chi_sim+eng 使用实际Tesseract执行中文／英文OCR；该命令为独立CLI薄包装，原skill正文未改。')
    if (skills / 'guizang-ppt-skill' / 'SKILL.md').is_file():
        if not shutil.which('guizang-swiss-validate'):
            raise RuntimeError('Guizang original validator Linux browser wrapper missing')
        guides.append('归藏原SWISS检查器在Linux用 guizang-swiss-validate --skill-dir /workspace/skills/guizang-ppt-skill -- <实际index.html路径> 执行同一个原始validate-swiss-deck.mjs。包装器只将其Playwright默认缓存浏览器路径适配为已安装/usr/bin/chromium，并加入容器root所需no-sandbox参数；不跳过渲染或结构检查。其它presenter检查仍直接用node执行原脚本。')
    if (skills / 'karpathy-wiki' / 'SKILL.md').is_file():
        wrapper = Path(__file__).parent / 'wiki_doc_extractor_compat.py'
        if not wrapper.is_file():
            raise RuntimeError('Karpathy wiki current odfdo API compatibility wrapper missing')
        guides.append('karpathy-wiki 原doc_extractor.py保留原字节；当前odfdo库读取API从Document.open变为构造器，使用 python /opt/eval-adapter/wiki_doc_extractor_compat.py --skill-dir /workspace/skills/karpathy-wiki -- <实际文件路径> [--max-pages N] [--max-rows N]。包装仅补同义Document.open入口，不更换抽取算法；EasyOCR中英模型已在镜像中缓存，可离线读取图片。')
    dcf = skills / 'dcf-model'
    support = workspace / 'reference_support/gitee_dcf/recalc.py'
    if (dcf / 'SKILL.md').is_file() and support.is_file():
        helper = support.parent / 'office/soffice.py'
        if not helper.is_file():
            raise FileNotFoundError('DCF recalc transitive office.soffice dependency missing: ' + str(helper))
        alias = dcf / 'recalc.py'
        if alias.exists() or alias.is_symlink():
            if not alias.samefile(support):
                raise ValueError('DCF recalc path conflicts with declared support')
        else:
            alias.symlink_to(support)
        aliases.append({'path':str(alias),'target':str(support),
                        'reason':'original DCF instructions refer to a recalc.py not included in its package; same-commit XLSX helper supplied as a transitive tool only',
                        'changes_source_package_bytes':False})
        guides.append('dcf-model 原包未附 recalc.py；已提供同一Gitee提交xlsx包的原生重算工具及office.soffice依赖作辅助资源，未增加active xlsx skill。可从dcf目录运行 python recalc.py <实际工作簿> 30，或用绝对路径 python /workspace/reference_support/gitee_dcf/recalc.py <实际工作簿> 30。')
    return {'aliases':aliases,'guide':'\n'.join(guides),
            'scope':'only actually admitted original baseline skill packages',
            'changes_source_package_bytes':False}
