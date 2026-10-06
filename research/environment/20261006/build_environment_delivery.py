"""Write Chinese research delivery lists from audited metadata, never from private text."""
import csv
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
coverage = json.loads((ROOT / 'private/retained_skill_coverage.json').read_text(encoding='utf-8'))
downloads = json.loads((ROOT / 'public_skill_downloads.json').read_text(encoding='utf-8'))
remotion = json.loads((ROOT / 'remotion_archive.json').read_text(encoding='utf-8'))
archive_file = ROOT / 'additional_archives.json'
additional = json.loads(archive_file.read_text(encoding='utf-8')) if archive_file.exists() else []
runtime_file = PROJECT / 'research/reviews/2026-10-06_tool_readiness_probe/local_inventory.json'
inventory = json.loads(runtime_file.read_text(encoding='utf-8'))
public = {r['skill']: r for r in downloads if r['status'] == 'downloaded'}
if remotion['status'] == 'downloaded_archive':
    public[remotion['skill']] = remotion
for record in additional:
    if record.get('skill') and record['status'] == 'downloaded_archive':
        public[record['skill']] = record
native_candidates = {'image-generation', 'evomind-paper-scan', 'pdf_zzz4ai', 'evomind-auto', 'zzz4ai-search-engine'}
purposes = {
    'image-generation': '平台图片生成服务调用',
    'evomind-paper-scan': '论文检索与研读的 EvoMind 适配',
    'pdf_zzz4ai': '平台 PDF 处理服务适配',
    'evomind-auto': 'EvoMind 自动研究流程',
    'zzz4ai-search-engine': '平台搜索服务适配',
}

def write_csv(path, rows, fields):
    with path.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fields)
        writer.writeheader()
        writer.writerows(rows)

def table(rows, fields):
    out = ['| ' + ' | '.join(fields) + ' |', '|' + '|'.join('---' for _ in fields) + '|']
    for row in rows:
        out.append('| ' + ' | '.join(str(row.get(field, '')).replace('|', '/').replace('\n', ' ') for field in fields) + ' |')
    return '\n'.join(out)

def license_label(record):
    if record.get('repo') == 'dontbesilent2025/dbskill':
        return 'CC BY-NC 4.0（保存条款，不当作MIT或无限制使用）'
    directory = pathlib.Path(record['download_path'])
    for name in ('LICENSE.txt', 'LICENSE', 'LICENSE.md', '_upstream_notices/LICENSE.txt', '_upstream_notices/LICENSE', '_upstream_notices/LICENSE.md'):
        file = directory / name
        if file.is_file():
            text = file.read_text(encoding='utf-8', errors='replace')
            if 'Anthropic' in text and 'ADDITIONAL RESTRICTIONS' in text:
                return 'Anthropic 源码可见限制许可；不能当开源使用'
            if 'GNU AFFERO GENERAL PUBLIC LICENSE' in text:
                return 'AGPL-3.0（保存了全文）'
            if 'Apache License' in text:
                return 'Apache-2.0（保存了全文）'
            if 'MIT License' in text or 'Permission is hereby granted, free of charge' in text:
                return 'MIT（保存了全文）'
    return '包内许可或发布者说明需逐项核对；不视为无条件开源'

rows = []
for skill in coverage['skills']:
    name = skill['skill']
    fetched = public.get(name)
    if name in native_candidates:
        group = 'A：平台品牌/服务适配，优先取原包'
        request = '请确认原创/第三方改造归属，提供实际完整包与相应服务契约'
    elif fetched:
        group = 'B：已有公开参考，原运行包等价尚未确认'
        request = '先给原运行包的上游URL、版本和SHA256；有平台改造再提供实际原包'
    elif name == 'tencent-meeting-mcp':
        group = 'C：官方服务技能存在，匿名包未取得'
        request = '腾讯会议官方Skill需登录生成安装信息；提供合法导出的包或官方授权获取方式，不归为EvoMind原生'
    else:
        group = 'C：来源未确认，先请平台按标识辨认'
        request = '请注明平台原创/改造第三方/原样第三方/个人自建；原创或改造给原包，原样第三方给URL和commit'
    rows.append({'技能标识': name, '用途线索': purposes.get(name, skill.get('purpose_hint', '待原包确认')), '涉及会话': skill['retained_sessions'], '保留学习会话': skill['KEEP'], '暂存会话': skill['HOLD'], '获取分组': group, '旧来源标签': skill['original_source_class'], '实际需要对方提供': request, '公开来源': fetched.get('source_url', '') if fetched else '', '已下载位置': fetched.get('download_path', '') if fetched else '', '历史原包一致性': '尚未确认', '用途认证': '用途按标识理解，非有效消费或业务成功认证'})
rows.sort(key=lambda row: (row['获取分组'][0], -row['涉及会话'], row['技能标识']))
fields = list(rows[0])
write_csv(ROOT / 'skills_全部获取清单.csv', rows, fields)
needed = [row for row in rows if row['技能标识'] not in public]
write_csv(ROOT / 'skills_需平台确认与补交.csv', needed, fields)

download_rows = []
for record in downloads:
    download_rows.append({'技能标识': record['skill'], '下载结果': '完整下载' if record['status'] == 'downloaded' else '未完成', '来源': record['source_url'], '固定版本': record['commit'], '保存目录': record['download_path'], '文件数': record.get('file_count', 0), '许可': license_label(record) if record['status'] == 'downloaded' else '下载未完成', '与历史包一致': '未确认', '已在Demo注册': '否', '已完成执行验收': '否'})
download_rows.append({'技能标识': remotion['skill'], '下载结果': '组合ZIP已保存' if remotion['status'] == 'downloaded_archive' else '未完成', '来源': remotion['source_url'], '固定版本': '发布者 ZIP v1.0.4，已冻结归档SHA256', '保存目录': remotion.get('download_path', ''), '文件数': remotion.get('file_count', 0), '许可': '组合包5份许可，含Remotion专门条款；未完成兼容性审核', '与历史包一致': '未确认', '已在Demo注册': '否', '已完成执行验收': '否'})
for record in additional:
    if record.get('skill'):
        download_rows.append({'技能标识': record['skill'], '下载结果': '固定版本ZIP已保存' if record['status'] == 'downloaded_archive' else '未完成', '来源': record['source_url'], '固定版本': record['version'], '保存目录': record['download_path'], '文件数': record.get('file_count', 0), '许可': 'ClawHub作者发布页标MIT-0，包内无独立许可全文，仍待核', '与历史包一致': '未确认', '已在Demo注册': '否', '已完成执行验收': '否'})
write_csv(ROOT / 'skills_已下载公开参考.csv', download_rows, list(download_rows[0]))

errors = []
checked_files = 0
for record in downloads:
    if record['status'] != 'downloaded':
        errors.append({'skill': record['skill'], 'error': record.get('error')})
        continue
    directory = pathlib.Path(record['download_path'])
    for entry in record['files']:
        file = directory / entry['path']
        if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != entry['sha256']:
            errors.append({'skill': record['skill'], 'file': entry['path'], 'error': 'missing or hash mismatch'})
        checked_files += 1
for archive_record in [remotion] + additional:
    if archive_record['status'] != 'downloaded_archive':
        errors.append({'archive': archive_record.get('skill', archive_record.get('context_for')), 'error': archive_record.get('error')})
    for entry in archive_record.get('files', []):
        file = pathlib.Path(archive_record['download_path']) / entry['path']
        if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != entry['sha256']:
            errors.append({'archive': archive_record.get('skill', archive_record.get('context_for')), 'file': entry['path'], 'error': 'missing or hash mismatch'})
        checked_files += 1
for source in coverage['input_files'].values():
    file = pathlib.Path(source['path'])
    if hashlib.sha256(file.read_bytes()).hexdigest() != source['sha256']:
        errors.append({'input_file': source['path'], 'error': 'frozen source changed'})
assert len(rows) == len({r['技能标识'] for r in rows}) == 74
assert len(public) + len(needed) == 74
summary = {'date': '2026-10-06', 'included_conversations': 1224, 'known_skill_identifiers': 74, 'known_skill_evidence_conversations': 376, 'evidence_conversations_including_masked': 378, 'platform_branded_candidates': 5, 'original_ownership_certified': 0, 'standalone_github_packages_downloaded': sum(r['status'] == 'downloaded' for r in downloads), 'standalone_clawhub_packages_downloaded': sum(bool(r.get('skill')) and r['status'] == 'downloaded_archive' for r in additional), 'publisher_bundle_downloaded': remotion['status'] == 'downloaded_archive', 'publisher_nested_skills': len(remotion.get('skill_paths', [])), 'downloaded_public_reference_identifiers': len(public), 'identifiers_without_downloaded_public_reference': len(needed), 'remaining_bundle_requests_excluding_platform_candidates': len(needed) - 5, 'downloaded_artifact_files_hash_checked': checked_files, 'original_source_hashes_checked': len(coverage['input_files']), 'errors': errors, 'all_checks_passed': not errors, 'model_calls': 0, 'demo_changes': False, 'skills_globally_registered': False, 'end_to_end_consumption_run': False}
(ROOT / 'verification.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')

request_rows = [r for r in rows if r['技能标识'] in native_candidates]
unknown_rows = [r for r in needed if r['技能标识'] not in native_candidates]
request_text = '''# 给 EvoMind 的技能原包和服务契约请求

日期：2026-10-06。范围为筛选后1224条真实会话，不要求重新跑历史任务或补造已遗失中间产物。

我们已自行下载有明确公开地址的参考包。请优先提供下列5项平台品牌/服务适配的实际原包，并明确来源；目前仅有品牌/适配证据，尚不能认证全部由EvoMind原创。

'''
request_text += table(request_rows, ['技能标识', '用途线索', '涉及会话'])
request_text += '''

每项请交：完整SKILL.md、scripts、references、assets、许可证；当前可提供版本及SHA256（历史版本保留则额外提供）；Python/Node/系统程序依赖和版本；调用服务的非秘密接口说明、参数和返回样例、错误码及测试开通方式。不要把密钥写入导出包。说明与历史运行包的差异，不要求恢复不存在的历史版本。

图片/搜索/PDF/自动研究涉及专属服务时，仅有SKILL.md不足以执行。请提供可独立调用的测试接口或可本地部署的实现及依赖；无需默认交付整个kmagent源码。

以下实际包来源或获取方式尚未落实。请先按技能标识给一份来源表：平台原创、平台改造第三方、原样第三方、用户自建/系统生成及实际包拥有者。只有平台原创/改造包需要平台交原包；原样公开第三方请给准确仓库URL、子目录和commit，我们继续自行下载。个人自建包可由拥有者导出，请平台帮助定位。腾讯会议已有官方Skill说明，但须账号登录后获取，请走官方授权或已有合法包导出，不称EvoMind原生。列表不是“全部EvoMind原生”的认证，也不是要求全部成为评测前置条件。

'''
request_text += table(unknown_rows, ['技能标识', '用途线索', '涉及会话'])
request_text += '''

已有公开参考的标识见本目录 skills_已下载公开参考.csv。请仅补其运行版本与上游对应关系；若有改造再补原包。不要用同名公开最新版代替历史运行版本而不说明。

另有3条脱敏技能读取/脚本记录：请按关联工具事件补真实技能标识映射；它们不代表已确认3种额外skills。来源锚点在 private/retained_skill_coverage.json，原正文无需再次导出。

优先级由将要执行的任务实际依赖决定，不把所有74项都列成必须先齐备。若执行最新单主题试跑方案的表格生成与核验，应先冻结可用表格基础技能、Python/Node库、公式计算及文件评分能力，不必等这5个专属服务全部到齐。若做合同/文档任务，则先确认contract-review-cn、contract-review（已有公开同名参考）、PDF/Word处理及产物交付依赖，再按其他主题扩展。
'''
(ROOT / '向EvoMind索取skills清单.md').write_text(request_text, encoding='utf-8')

tools_rows = [
    {'能力': 'OpenClaw基本工具', '本轮确认': 'Windows默认launcher：Node26.1.0/OpenClaw2026.9.5版本通过；read/write/edit/exec/process等已允许', '距离执行验收的差距': '允许列表不等于工具链执行成功；本轮没有启动新Agent消费'},
    {'能力': 'Office转换', '本轮确认': 'LibreOffice在PATH、常见位置、注册安装项均未检出；Pandoc2.12可达', '距离执行验收的差距': 'Word/PPT/Excel到PDF及公式重算不能因此判为可用'},
    {'能力': 'PDF渲染/提取', '本轮确认': 'pdftoppm/pdfinfo26.07.0可达，PATH的pdftotext是MiKTeX23.13.0', '距离执行验收的差距': '需固定同一套工具路径，并检查真实文件/中文排版'},
    {'能力': 'Python文档与数据库', '本轮确认': '默认3.14.3部分库导入通过，缺python-pptx/reportlab/cairosvg；Codex3.12.14另有文档库', '距离执行验收的差距': 'Codex的库不会自动成为Demo默认库；pandas导入探针超时，未验收'},
    {'能力': 'Node文档工具', '本轮确认': 'Codex依赖中找到docx/pptxgenjs/sharp/pdfjs-dist；Demo核到playwright-core', '距离执行验收的差距': '需在Agent执行的Node模块搜索路径解析，不能借宿主目录存在就说已接通'},
    {'能力': '浏览器', '本轮确认': 'Edge与Playwright Chromium二进制存在', '距离执行验收的差距': '没有启动探针或Agent浏览器测试；agent-browser技能包不等于CLI已安装'},
    {'能力': '视频/音频', '本轮确认': '通用ffmpeg/ffprobe不在PATH，仅有Playwright极简FFmpeg缓存', '距离执行验收的差距': '不证明MP4/音频功能具备；Remotion相关依赖尚未安装验收'},
    {'能力': 'Linux历史路径', '本轮确认': 'WSL仅docker-desktop且停止，未发现Ubuntu；Docker CLI有但daemon未检查', '距离执行验收的差距': '/workspace、/opt及bash脚本不自动在Windows等价运行'},
    {'能力': '平台/企业服务', '本轮确认': '有历史调用线索，未认证当前Tavily/ZZZ4AI/企业搜索等接口和权限', '距离执行验收的差距': '通用exec/web_search不能替代专属工具；需要测试接口、配置契约和授权'},
]
report = f'''# 当前本地环境与 skills 获取结果

日期：2026-10-06。**本地tools尚未齐全。已下载{summary['standalone_github_packages_downloaded'] + summary['standalone_clawhub_packages_downloaded']}个独立公开参考包（GitHub {summary['standalone_github_packages_downloaded']}＋ClawHub {summary['standalone_clawhub_packages_downloaded']}），另下载1个视频组合参考包（内含6个SKILL.md）；这不是已注册、可执行的历史技能库。**

## 核查范围和口径

以task_topics_20261006的1224条会话（716保留学习、508暂存）为本轮准备范围。历史全1466会话清单有81个技能标识，本范围仍出现74个可识别标识，449条读取/脚本尝试记录、376条会话；另3条脱敏记录合计去重覆盖378条会话。读取、脚本尝试不是有效应用或任务成功认证；本轮也没有新增模型调用、技能生成或效果实验。

旧81项中本次未再出现的7项为dcf-model、3-statements、competitive-intelligence、dbs-deconstruct、deep-research、human-resources-training、swot-analysis。原档保留，不作为本轮必须收齐的前置包。

## tools到底哪些已有，哪些还缺

'''
report += table(tools_rows, ['能力', '本轮确认', '距离执行验收的差距'])
report += '''

默认launcher确实指向Windows原生环境，不能沿用历史WSL Ubuntu/OpenClaw2026.9.7实验结论。DEMO_OPENCLAW_COMMAND可覆盖，本轮没有读取.env或进程秘密环境，后续真正运行时须冻结最终解析配置。本轮扫描未发现引用已知Demo启动脚本的活动进程；不等于排除了别处运行的服务。完整非秘密版本/路径/导入记录见../../reviews/2026-10-06_tool_readiness_probe/local_inventory.json。

## 优先向EvoMind要的5项

'''
report += table(request_rows, ['技能标识', '用途线索', '涉及会话'])
report += f'''

这5项有平台品牌或专属服务适配证据，优先要实际包及接口。**目前“平台原创已确认”数量为0，不能把来源未知的技能一概称为原生。** 本轮另外{len(unknown_rows)}项尚未取得可对应的公开参考包，需先确认来源和获取方式，再决定由平台、原作者或个人库拥有者交包；其中腾讯会议已有官方说明，须登录取得，不属于“网上不存在”的判断。详见[可直接转发的索取清单](向EvoMind索取skills清单.md)和[逐项CSV](skills_需平台确认与补交.csv)。

## 已替你下载的公开参考

'''
report += table(download_rows, ['技能标识', '下载结果', '许可', '来源'])
report += '''

GitHub独立包位于public_skills/，ClawHub固定版本包位于clawhub_skills/，保存SKILL.md及原目录附带的脚本/引用/资源，补存可取得的上游许可/README。视频包位于publisher_archives/，保存原ZIP及完整静态解压目录：该包是scene-planner/video-generator等6个嵌套技能的组合，不能当作历史同名单包已还原。文件哈希、固定Git提交、来源强度见public_skill_downloads.json、remotion_archive.json、additional_archives.json和各包_download_provenance.json。image-editing另保存完整上游上下文到shared_repo_context/image-editing/，包含MODELS.md和外层引用；不证明其API工具已接通。

AutoEvoSkillCreate此次网页元数据与完整包都可取得，许可证MIT；修正10-05“当前页面读取失败/许可未知”的当时状态，旧记录保留。frontend-design实际包许可Apache-2.0，不能与同仓4个限制许可文档包混同。imap-smtp-email发布者市场页标MIT-0而GitHub README称MIT，保留差异；未取到适用完整许可不能凭同名赋予权利。四个Anthropic文档包pdf/docx/pptx/xlsx是源码可见参考，**不是通常意义上的开源包，也没有据此取得给DashScope/OpenClaw直接使用的许可认证**。下载资料与实际可启用包必须分开。[上游README](https://github.com/anthropics/skills)、[文档许可原文](https://github.com/anthropics/skills/blob/main/skills/pdf/LICENSE.txt)。

公开“可获取”也不代表“与历史运行包等价”：agent-browser返回文档指向上游，4个包曾有用户安装请求，部分是同名参考或合集。没有完整版本/包哈希比对，不将它们写成历史原包。合同公开参考来自NOMOREKKK，不能将它自动当作EvoMind的contract-review-cn。[公开合同参考](https://github.com/NOMOREKKK/contract-review-skill)。

额外来源边界：xyq-nest-skill目录同名而当前frontmatter为xyq-skill；patent-scanner当前名称为Patent Scanner；fund-proposal-assistant发布版本1.0.0与正文自报2.1不同，均保留差异。w95合集外源技能可能另有许可，不能按根MIT覆盖；本次两个下载项在其索引标Custom，competitive-analysis取官方Apache-2.0包。dbs-chatroom上游CC BY-NC 4.0并非MIT，未自动启用。image-ocr参考来自SkillsBench特定任务随附技能，不能无说明注入未来无技能/自动学习条件的盲测库；需隔离重叠或定义各方法相同的基础能力。[SkillsBench主源](https://github.com/benchflow-ai/skillsbench)。腾讯会议有[官方Skill说明](https://meeting.tencent.com/support/articles/14/index.html)，账号登录获取和适用许可未落实，不从无许可镜像代取。

本轮没有全局安装到Codex，未加入Demo自动加载目录、未安装这些包的Python/Node依赖、未执行远程仓库脚本或企业历史命令。使用官方skill-installer下载助手并指定项目资料目录；网络请求不携带本地GitHub令牌，企业会话未发送给公开仓库。

## 怎么把准备工作收束成可跑的评测环境

1. 固定一个执行环境及解释器：当前Windows可继续做轻量文本与文件处理；若实际技能依赖bash、/opt、/workspace，另建立固定Linux运行环境，而不是临场改脚本。
2. 按将要执行的主题核对依赖。最新单主题试跑方案建议表格生成与核验，应先冻结表格基础能力、公式计算/文件评分及Python/Node环境；合同/文档再确认输入附件、合同审查原包、PDF/Word、中文字体和产物输出。视频、企业邮箱、飞书等按纳入任务再接入，不等所有74项。
3. 平台提供完整专属技能包和服务契约，而非只给技能说明；第三方原样包给准确URL/commit，我们下载。默认无需kmagent全源码。
4. 对每个纳入的新任务先做一次“Agent读技能→真实工具调用→文件产物→业务/文件验收”，再冻结工具/模型/技能依赖。所有算法基线用同一个基础技能库和工具能力，学习阶段生成的技能单独记录；不能把环境掉链子记成算法失败。
5. **先从历史会话生成skills，不需要等历史附件、KM环境或历史skills全部齐备**；仅需原始正文、生成器依赖/模型、共同的有效弱草稿及格式检查，缺失内部方法和结果保留未知，不凭公开同名包补造历史。这里的执行工具、独立新文件和评分准备用于后续消费/收益验收。公开参考替换历史包要写明，不称精确重放。

## 文件与核验

- skills_全部获取清单.csv：74项，分来源证据、公开参考、补交路线及会话覆盖。
- skills_需平台确认与补交.csv：尚未取得可对应参考包的标识，含官方服务授权获取待落实项，不是原生认证表。
- skills_已下载公开参考.csv：下载目录、固定版本、许可、注册/执行未验证状态。
- private/retained_skill_coverage.json：受控关联索引和统计，可回查原证据，原文未复制入报告。
- public_source_findings.md、public_source_business_followup.md、public_source_integration_followup.md：首轮及剩余42个非品牌/非emerged标识定向检索与同名/变体边界；deep-research已不在当前74项，故未额外下载。
- verification.json：逐文件哈希与3份冻结来源检查。没有任何认证算法收益或真实业务成功的新结论。
'''
(ROOT / 'README.md').write_text(report, encoding='utf-8')
report_link = PROJECT / 'research/reports/2026-10-06_evomind_environment_and_skill_acquisition.md'
report_link.write_text('# 本地工具环境与技能获取\n\n详细结果已保存到[完整环境和技能获取报告](../environment/20261006/README.md)。\n\n需要转发给平台的[原包和来源补交清单](../environment/20261006/向EvoMind索取skills清单.md)，以及[74项完整清单](../environment/20261006/skills_全部获取清单.csv)。\n\n本地tools尚未齐全；下载完成不等于注册和消费验收。见报告中的实际探针、来源与边界说明。\n', encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
if errors:
    raise SystemExit('Verification failed; preserve logs and repair before declaring completion')
