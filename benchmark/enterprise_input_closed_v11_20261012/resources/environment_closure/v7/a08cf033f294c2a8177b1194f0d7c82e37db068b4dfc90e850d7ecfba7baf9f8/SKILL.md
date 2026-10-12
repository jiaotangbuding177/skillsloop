---
name: karpathy-wiki
description: "Build and maintain a personal LLM Wiki: source files → compiled wiki → index. Supports Mode A (个人知识库/) and Mode B (workspace scan). Triggers: wiki, 知识库, 知识管理, 收录, 知识库初始化, 整理知识库, ingest, 知识入库, 搜索知识, query wiki, lint wiki, 查一下, 搜一下, 了解一下, look up, find out, search. MANDATORY: query local wiki BEFORE any web search."
---

# LLM Wiki Bootstrap for OpenClaw

## Global Concurrency Control (CRITICAL)

**NEVER fire more than 2 `task()` calls in a single response.** This is the #1 source of API rate-limit errors.

| Rule                 | Action                                                                    |
| -------------------- | ------------------------------------------------------------------------- |
| **Max groups**       | Split work into **2 groups only**                                         |
| **Per group**        | **1 task at a time** — within each group, process items sequentially      |
| **Total concurrent** | Max 2 agents running (1 from Group A + 1 from Group B)                    |
| **Collect results**  | Wait for both agents to complete before firing the next pair              |
| **On error/timeout** | Immediately degrade: process remaining items 1 at a time (no more groups) |
| **NEVER**            | Do NOT fire 3, 5, 6, 8+ agents at once                                    |

**Why this matters**: Linting 10 wiki articles = 2 groups of 5 each, process 1+1 concurrently (one from Group A, one from Group B), NOT 10 agents. Ingesting 9 sources = 2 groups of [5, 4], NOT 9 agents.

**If you are about to fire more than 3 agents in one response: STOP. Batch them instead.**

---

## Core Philosophy

**Knowledge base = source files → compiled wiki → index**

Two modes, automatically detected:

### Mode A: 个人知识库 Mode (Preferred)

- `个人知识库/` — Your curated knowledge files. PDFs, docs, spreadsheets, text, images. The LLM reads from here, NEVER modifies existing files.
- `个人知识库/wiki/` — Synthesized, structured knowledge. Created and maintained by the skill.

### Mode B: Workspace Scan Mode (Fallback, when `个人知识库/` doesn't exist)

- **Entire workspace** becomes the knowledge source — but ONLY documentation/research files are scanned (see exclusion rules below).
- `wiki/` at workspace root — Skill-managed wiki directory.

**index** — Directory of everything. The "table of contents" for your wiki.

The LLM is not a database — it is a reasoning engine. The wiki exists so the LLM reads only relevant content at the right time.

## Directory Structure

### Mode A: 个人知识库 exists (Preferred)

```
├── 个人知识库/                    # User's knowledge base (DO NOT modify existing files)
│   ├── some-paper.pdf            # Source files live here
│   ├── report.xlsx               # The LLM reads these, never edits them
│   ├── notes.docx                # Any file type is fine
│   ├── article.md                # Text/markdown files too
│   ├── subfolder/                # Subfolders are scanned recursively
│   └── wiki/                     # Skill-managed wiki (CREATED by the skill)
│       ├── index.md              # Master index of all topics, entities, concepts
│       ├── log.md                # Log of all changes to the wiki
│       └── {slug}.md             # Individual wiki articles
```

### Mode B: Workspace Scan (Fallback — when `个人知识库/` doesn't exist)

```
├── wiki/                         # Skill-managed wiki at workspace root
│   ├── index.md
│   ├── log.md
│   └── {slug}.md
└── (scanning all workspace recursively, with exclusions below)
```

### Source Scan Exclusion Rules (APPLIES TO BOTH MODES)

When scanning any source directory (`个人知识库/` in Mode A, entire workspace in Mode B), these files and directories are **ALWAYS excluded**:

**Excluded directories** (language dependencies, artifacts):

- `node_modules/`, `.next/`, `.nuxt/`, `dist/`, `build/`, `out/`
- `__pycache__/`, `.venv/`, `venv/`, `env/`, `.env/`
- `.git/`, `.github/`, `.vscode/`, `.idea/`, `target/`
- `vendor/`, `.bundle/`, `coverage/`, `.cache/`, `tmp/`, `temp/`
- `gen/`, `generated/`, `.dart_tool/`, `.pub-cache/`, `.cargo/`
- `.terraform/`, `.serverless/`, `.wrangler/`
- `bin/`, `obj/`, `lib/` (for Dart/Flutter), `Pods/`, `.gradle/`

**Excluded file extensions** (code/script/config files — not knowledge content):

- Code: `.js`, `.jsx`, `.ts`, `.tsx`, `.py`, `.java`, `.go`, `.rs`, `.cpp`, `.c`, `.h`, `.hpp`, `.rb`, `.php`, `.swift`, `.kt`, `.scala`, `.cs`, `.fs`, `.sh`, `.bash`, `.zsh`, `.ps1`, `.bat`, `.cmd`, `.mjs`, `.cjs`
- Styles: `.css`, `.scss`, `.sass`, `.less`, `.styl`, `.pcss`, `.postcss`
- Config: `.json`, `.toml`, `.yml`, `.yaml`, `.ini`, `.cfg`, `.conf`
- Lockfiles: `.lock`, `.sum`, `.lock.json`, `.lock.yaml`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`
- Build artifacts: `.min.js`, `.min.css`, `.map`, `.chunk.js`, `.hot-update.js`

**Included** (these ARE knowledge content — in both modes):

- Documents: `.pdf`, `.docx`, `.doc`, `.pptx`, `.xlsx`, `.xls`, `.rtf`, `.epub`, `.odt`, `.ods`, `.odp`
- Text: `.md`, `.txt`, `.csv`, `.text`
- Images (OCR-eligible): `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.bmp`, `.svg`

**Key rules**:

- All paths are relative to the workspace root
- Never modify existing user files — read only
- wiki/ (or 个人知识库/wiki/) is the only directory the skill creates and writes to
- Source files are always scanned recursively, excluding wiki/ subdirectory and exclusions above

---

## Document Extraction

When ingesting non-text files, the LLM **MUST** use the extraction script instead of reading raw bytes:

```bash
python {skill_dir}/scripts/doc_extractor.py "<filepath>"
python {skill_dir}/scripts/doc_extractor.py "<filepath>" --max-pages 50
python {skill_dir}/scripts/doc_extractor.py "<filepath>" --max-rows 10000
```

Where `{skill_dir}` is the directory containing this SKILL.md file.

**Supported formats**:
| Format | Extension | Library | Notes |
|--------|-----------|---------|-------|
| PDF | `.pdf` | PyMuPDF | `sort=True` for reading order, checks encryption |
| Excel | `.xlsx` | openpyxl | `read_only=True, data_only=True` |
| Excel (legacy) | `.xls` | xlrd | For older Excel files |
| Word | `.docx` | python-docx | Preserves headings and tables |
| PowerPoint | `.pptx` | python-pptx | Slides, tables, speaker notes, group shapes |
| RTF | `.rtf` | striprtf | Handles various codepages gracefully |
| EPUB | `.epub` | ebooklib + BeautifulSoup | Spine-ordered chapter extraction |
| OpenDocument Text | `.odt` | odfdo | Paragraphs, tables; markdown conversion fallback |
| OpenDocument Spreadsheet | `.ods` | odfdo | Table extraction with sheet names |
| OpenDocument Presentation | `.odp` | odfdo | Slide text from draw pages |
| Images (OCR) | `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.bmp` | EasyOCR | CJK+EN mixed content, `~ch_sim`+`en` models, paragraph=False |
| SVG | `.svg` | Inline text → svglib+reportlab → OCR fallback | Extract `<text>/<tspan>` elements first, rasterize then OCR if empty |

**Setup** (one-time): Install dependencies. **Use Chinese mirror if default pip timeout:**

```bash
# Try default first
pip install PyMuPDF openpyxl python-docx xlrd python-pptx striprtf ebooklib beautifulsoup4 lxml odfdo svglib reportlab

# If timeout, use Alibaba mirror:
pip install --index-url https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com PyMuPDF openpyxl python-docx xlrd python-pptx striprtf ebooklib beautifulsoup4 lxml odfdo svglib reportlab
```

**⚠️ Note**: First EasyOCR call takes ~30s to initialize models (cached afterward). Subsequent OCR calls are fast.

**For text files** (.md, .txt, .csv, .json, etc.): Use the Read tool directly — no extraction needed.

---

## Resource Paths

All paths are relative to this skill's directory (where SKILL.md lives):

| Resource | Path | Purpose |
|----------|------|---------|
| Article template | `references/article-template.md` | Wiki article structure for ingest |
| Index template | `references/index-template.md` | Master index initial structure |
| Log template | `references/log-template.md` | Change log initial structure |
| Raw template | `references/raw-template.md` | Raw source extraction notes |
| Archive template | `references/archive-template.md` | Archive section structure |
| Doc extractor | `scripts/doc_extractor.py` | PDF/Excel/Word/PPT/OCR extraction |

**Usage**: Replace `{skill_dir}` with the absolute path to this skill directory before running commands.

---

## 0. Initialization (One-time Setup)

On first use, detect mode and initialize accordingly:

### Detect Mode

1. Check if `个人知识库/` directory exists
   - **Yes** → Mode A: use `个人知识库/wiki/`
   - **No** → Mode B: use `wiki/` at workspace root (entire workspace scan with exclusions)

### Initialize (both modes)

1. Create wiki directory: `个人知识库/wiki/` (Mode A) or `wiki/` (Mode B)
2. Create `wiki/index.md` from **references/index-template.md**
3. Create `wiki/log.md` from **log-template.md**
4. Scan source files recursively:
   - **Mode A**: scan `个人知识库/` (excluding `wiki/` and excluded patterns)
   - **Mode B**: scan entire workspace, applying all exclusion rules (see `Source Scan Exclusion Rules` above)
5. Catalog existing source files and record initialization in `wiki/log.md`

After setup, read `wiki/index.md` and `wiki/log.md` into context before any operation.

---

## 1. Ingest (Add Knowledge)

### When to Trigger

**English triggers**: "add to wiki", "ingest", "save this", "read this URL", "save these files", "fetch this", "archive this research"
**Chinese triggers**: "添加到知识库", "收录", "保存这个", "读取这个链接", "保存这些文件", "抓取这个", "归档这个研究", "记录这个", "记下来", "收藏这个"

### Flow

**Autonomous but transparent**: Don't ask unnecessary questions, but ALWAYS show progress during multi-step operations.

**⚠️ Global concurrency rule: MAX 2 task() calls per response.** Split work into 2 groups, process 1 item per group concurrently. See `Global Concurrency Control` above.

1. **Locate the source** —
   
   - If the user provides a URL: fetch the content using available tools
   - If the user provides a file path: use the file from its location
   - If the user provides pasted text: save it to `{source_dir}/{slug}.md` first
   - If the user says "ingest all" or "收录全部": scan source directory recursively (applying exclusion rules in Mode B) for unprocessed files
   
   > **Note**: `{source_dir}` = `个人知识库/` (Mode A) or entire workspace (Mode B). Exclusion rules apply to both modes.

2. **Confirm scope (if > 1 source)** — 
   
   When processing multiple sources, show a progress summary BEFORE starting:
   ```
   即将收录 N 个源文件:
   1. file-a.pdf
   2. file-b.pdf
   3. ...
   开始处理? (y/n 或直接继续)
   ```
   For single-source ingest, skip this step. Proceed silently.

3. **Extract content** —
   
   - For `.pdf`, `.xlsx`, `.xls`, `.docx`, `.pptx`, `.rtf`, `.epub`, `.odt`, `.ods`, `.odp`: Run `python {skill_dir}/scripts/doc_extractor.py "<filepath>"`
   - For images (`.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.bmp`, `.svg`): Run `python {skill_dir}/scripts/doc_extractor.py "<filepath>"` (uses EasyOCR, ~30s first call only)
   - For text files (`.md`, `.txt`, `.csv`, `.json`): Use the Read tool directly
   - For URLs: Use web fetch tools
   
   **⚠️ Extraction failure fallback**: If `doc_extractor.py` fails on any file, log the error, skip to the next file, and report failures at the end. Do NOT stop the entire ingest process.

4. **Compile to wiki/** — Synthesize into knowledge at `wiki/{slug}.md` using **references/article-template.md**
   
   - Write in your own words — this is understanding, not a summary
   - Include: Overview, Key Ideas, Details, Connections, References
   - If the article already exists, add new info as a new section with a source attribution header

5. **Update index.md** — Add/modify entries in the appropriate sections (Topics, Entities, Concepts, Sources)
   
   - Every wiki article must appear in index.md
   - Sort alphabetically within each section
   - One line per entry: `**[[{slug}]]**: {2-5 word description}`

6. **Update log.md** — Append an entry with date, action, and brief description

7. **Show progress (multi-source only)** — 
   
   After each pair completes (every 2 sources), show: `已处理 X/N，剩余 Y`
   At the end, show a completion summary with links to created wiki articles.

### Ingest Rules

- **Source files are read-only for existing files**: Never modify user files. The LLM may only CREATE new files here (e.g., saving pasted text or URL content).
- **wiki/ is your understanding**: Synthesize, don't just summarize. Add connections, implications, and your own insights.
- **Index must be complete**: Every wiki file must be listed in index.md.
- **Filenames for wiki articles**: Keep them short, lowercase, hyphenated. e.g., `attention-is-all-you-need.md`
- **Type classification**: Infer from the source. URL → `page`, GitHub repo → `repo`, PDF paper → `paper`, blog post → `article`, conversation → `transcript`, raw notes → `note`
- **Extraction failure**: If `doc_extractor.py` fails, log the error with filename and error message, skip to next source, report all failures at the end
- **OCR failure**: EasyOCR may fail on low-quality images; fallback to reporting the source as "unparseable image" in log.md

### Subagent Delegation for Multi-Source Ingest

When ingesting **multiple sources at once** (e.g., "收录全部", "ingest all", or user provides multiple files/URLs):

**Step 1: Collect all source paths.** Scan `{source_dir}` recursively (applying exclusion rules in Mode B, excluding `wiki/` always).

**Step 2: Split sources into 2 groups.** Example: 8 sources → Group A: [1,2,3,4], Group B: [5,6,7,8].

**Step 3: Fire 2 agents — 1 from each group** (MAX 2 `task()` calls):

```
task(category="deep", run_in_background=true, load_skills=[], prompt="Source {filepath_Ai}: extract content via doc_extractor.py, compile wiki article, return wiki content + index entry + log entry.")
task(category="deep", run_in_background=true, load_skills=[], prompt="Source {filepath_Bi}: same.")
```

**STOP. End your response.** Wait for both to complete.

**Step 4: Collect results → write wiki files → fire next pair** (next item from Group A + next item from Group B). Repeat until both groups exhausted.

**Step 5: Error/timeout handling.** If ANY agent errors or times out, stop batching. Process all remaining sources 1 at a time.

**Step 6: After all wiki articles written**, batch-update `index.md` + `log.md` in one pass.

### Template: wiki articles

See **Resource Paths** table above for the full path. The wiki article must follow `references/article-template.md` and have:

- YAML frontmatter with: status (always "compiled"), type, date, source
- **Overview** — 2-3 sentence essence of the topic
- **Key Ideas** — Numbered list of central claims in your own words
- **Details** — Important details, mechanisms, processes that support Key Ideas
- **Connections** — Links to other wiki entries and how this topic relates
- **References** — Paths/links back to source files

---

## 2. Query (Find & Use Knowledge)

### When to Trigger

**English triggers**: "search wiki", "what do I know about", "query wiki", "find in wiki", "what does my wiki say about"
**Chinese triggers**: "搜索知识库", "wiki 里有没有", "知识库里关于", "查一下 wiki", "wiki 说了什么", "我的知识库里", "找找关于"

### Flow

**DO NOT ask questions.** Just answer:

1. **Load context**: Read `wiki/index.md` and `wiki/log.md`
2. **Search**: Look for the query topic in index.md to find relevant wiki articles
3. **Read**: Read the relevant wiki articles from `wiki/`
4. **Answer**: Use the wiki content to answer the user's question directly
   - **Cite your sources**: At the end, list which wiki articles were referenced
5. **Optional Archive**: If the answer doesn't exist in the wiki, inform the user and offer to ingest new sources. If the user wants to ingest, proceed immediately.

### LLM-Powered Search Advantage

Unlike Obsidian/Notion that only do text matching, you can:

- Find semantically related topics even if the exact keywords aren't present
- Connect multiple wiki entries to form a comprehensive answer
- Infer relationships between topics that aren't explicitly linked

### Query Rules

- Always read index.md first — it's the map to your knowledge
- If an article is missing, tell the user and optionally ingest
- When answering, note which wiki articles you referenced (implicit citation)

---

## 2.5. Priority Query (Local Knowledge First)

### MANDATORY: Query Local Wiki BEFORE Web Search

**This is the most important rule of this skill. NEVER skip wiki search when this skill is active.**

When the LLM needs to look up information, research a topic, or answer a question that might benefit from existing knowledge, it **MUST** follow this priority order:

```
1. Query wiki FIRST: `{wiki_dir}/index.md` ({wiki_dir} = `个人知识库/wiki/` or `wiki/`)
2. If wiki has relevant content → use it as primary knowledge source
3. If wiki content is insufficient → THEN supplement with web search
4. After web search yields valuable new info → offer to ingest into wiki
```

### When to Apply Priority Query

**Trigger conditions** (apply BEFORE any web_search, brave-search, baidu-search, miaoda-web-search, or agent-reach):

- User asks a factual question that the wiki might cover
- User asks "what is X", "how does Y work", "tell me about Z"
- LLM is about to call any web search tool
- User says "search for", "look up", "find out about" any topic
- User says "查一下", "搜一下", "了解一下", "找找" any topic
- Any knowledge retrieval or research scenario

### Priority Query Flow

1. **Check wiki first**: Read `wiki/index.md`, search for relevant entries
2. **If found**: Read the relevant wiki articles, use this as the PRIMARY source for answering
   - Cite wiki articles as sources: "根据本地知识库中的 [[article-slug]]..."
   - If wiki_content is partial or outdated, note what's missing
3. **If not found or insufficient**: Proceed with web search, BUT:
   - Always mention: "本地知识库中未找到相关内容，正在搜索网络..."
   - After getting web results, offer to ingest the new knowledge: "是否将此内容收录到知识库？"
4. **After web search + ingest**: The knowledge is now in the wiki for future queries

### Integration with Other Skills (Wiki-First Interceptor)

When this skill is active, wiki-first is **AUTOMATIC** before any external search:

| Other Skill Action | What Happens |
| --- | --- |
| `brave-search` / `baidu-search` / web search tools | Check wiki first → use wiki if found → supplement with web |
| `agent-reach` search | Same — wiki is the first stop |
| `ima-skill` knowledge query | Check local wiki first, then use IMA if needed |
| Any URL fetch for research | Check if wiki already covers the topic |

### Chinese Triggers for Priority Query

- "查一下" / "搜一下" / "了解一下" / "找找" → 先查本地知识库
- "帮我看看" / "帮我查查" → 先查本地知识库
- "XX是什么" / "XX怎么样" → 先查本地知识库
- 任何需要联网搜索的场景 → 先查本地知识库

### Enforcement Rule

**When this skill is loaded, wiki-first is AUTOMATIC.** The LLM should NOT need to be reminded — it MUST happen before ANY external search.

---

## 3. Lint (Maintain Quality)

### When to Trigger

**English triggers**: "lint wiki", "check wiki health", "fix wiki", "validate wiki", "wiki maintenance"
**Chinese triggers**: "整理知识库", "检查 wiki", "修复 wiki", "wiki 维护", "检查知识库健康"

### Flow

**⚠️ Global rule: MAX 2 task() calls per response.** See `Global Concurrency Control` above.

**⚠️ Checkpoint rule**: Show progress during multi-file lint. After each pair (2 files), report: `已检查 X/N，剩余 Y`

See `### Lint Subagent Delegation (MANDATORY)` below for the detailed 2-group workflow.

Quick summary:

1. Read index.md → list all wiki files
2. **Checkpoint**: Show file count and ask user confirmation if > 5 files: `即将检查 N 个 wiki 文件，预计耗时 X 分钟。开始?`
3. Split files into 2 groups only (never more)
4. Fire 1 from Group A + 1 from Group B (2 calls MAX) → STOP → wait for results
5. Repeat for next pair until both groups exhausted (show progress after each pair)
6. Fire 1 source scan + 1 index audit (can be in any pair, count toward the 2-limit)
7. Collect ALL results → **Checkpoint**: Show report preview, ask for confirmation before auto-fixing
8. After user confirms → apply auto-fixes → write final report + log

```
## Lint Report — {date}

### Auto-fixed (N items)
- [x] Added `missing-topic.md` to index.md
- [x] Sorted index.md alphabetically
- [ ] ...

### Manual fixes needed (N items)
- [ ] `stale-topic.md` — last modified 45 days ago. Review for accuracy?
- [ ] Unprocessed source: `个人知识库/report.pdf` — no wiki article exists
- [ ] ...
```

### Lint Subagent Delegation (MANDATORY)

**The Lint process is SLOW if done sequentially, but TOO MANY agents cause rate-limit errors.**

**Concurrency limit: Split all work into 2 groups only. Each group processes items 1 at a time.**

**Step 1: Read index.md and list all wiki files.** Get the full inventory.

**Step 2: Split wiki files into 2 groups only.** Example: 10 files → Group A: [1,2,3,4,5], Group B: [6,7,8,9,10].

**Step 3: Fire 1 lint agent from Group A + 1 from Group B** (MAX 2 `task()` calls):

```
task(category="deep", run_in_background=true, load_skills=[], prompt="Lint: {filepath_Ai}. Check: 1) Frontmatter status 2) Back-links 3) Stale >30 days 4) Missing sections. Return structured report.")
task(category="deep", run_in_background=true, load_skills=[], prompt="Lint: {filepath_Bi}. Same checks.")
```

**STOP. End your response.** Wait for both to complete.

**Step 4: Collect results → fire next pair.** Take next item from Group A + next from Group B. Repeat until both groups exhausted.

**Step 5: Source scan** (counts toward the 2-limit — fire it instead of one lint agent in any round):

```
task(category="deep", run_in_background=true, load_skills=[], prompt="Scan source directory {source_dir} (applying exclusion rules if Mode B). Return list of source files without corresponding wiki articles.")
```

**Step 6: Index audit** (counts toward the 2-limit — fire it instead of one lint agent):

```
task(category="deep", run_in_background=true, load_skills=[], prompt="Audit wiki/index.md: check sorting, duplicates, missing entries, orphaned references. Return fix list.")
```

**Error/timeout handling**: If ANY agent errors or times out, stop batching. Process remaining files 1 at a time.

**Step 7: After ALL results collected**, apply deterministic auto-fixes sequentially (file I/O):

- Add missing entries to index.md
- Fix frontmatter issues
- Sort index.md entries
- Remove duplicates

**Step 8: Write consolidated report + log**.

### Lint Rules

- **Deterministic = auto-fix**. If the fix is obvious and correct, just do it.
- **Heuristic = report only**. If the fix requires judgment, report it and let the user decide.
- **Always log**. Every change goes into `wiki/log.md`.
- **Never delete**. Archive instead if something is truly obsolete.
- **Never modify source files**. Lint only touches `wiki/` directory.

---

## 4. Archive (Optional)

When a wiki article becomes outdated or irrelevant, move it to an archive section in `index.md` rather than deleting. Create the archive entry in `wiki/archive.md` if needed.

Prefix the status with `archived` prefix.
In the log, record: "Archived `topic.md` — reason."

---

## Key Rules (NEVER VIOLATE)

1. **Never modify existing source files** — User's source files are sacred. Read only. Applies to both `个人知识库/` (Mode A) and workspace files (Mode B). The only exception is creating NEW files (saving pasted text or URL content).
2. **Only write to wiki/** — All skill-generated content goes here. (`个人知识库/wiki/` in Mode A, `wiki/` in Mode B)
3. **Always update index.md** — Every wiki file must be listed. Every edit to `index.md` must be sorted alphabetically.
4. **Always update log.md** — Every change to the wiki (ingest, edit, lint, archive) must be logged.
5. **Never delete** — Move to archive instead. Knowledge is cumulative.
6. **Read index.md and log.md first** — Before any ingest, query, or lint operation.
7. **Use templates** — Follow the exact structure in `references/` templates (see **Resource Paths** table for full paths).
8. **Use doc_extractor.py for documents** — Never read PDF/Excel/Word/PowerPoint/RTF/EPUB/OpenDocument files directly. Always use the extraction script.
9. **Scan recursively with exclusions** — Source files may be in subfolders. Always scan recursively, excluding `wiki/` subdirectory and all excluded directories and file extensions (see `Source Scan Exclusion Rules` above).
10. Do not clean up users' empty directories or empty files.

---

## Quick Reference: Operations

| Operation          | Triggers                               | Actions                                                                                 |
| ------------------ | -------------------------------------- | --------------------------------------------------------------------------------------- |
| **Initialize**     | First run, no `wiki/` exists           | Detect mode (A or B), create wiki/, index.md, log.md, scan sources                      |
| **Ingest**         | "add to wiki", "ingest", "保存这个", "收录"  | Extract source, **2-group parallel (1+1 concurrent)**, compile wiki/, update index, log |
| **Query**          | "search wiki", "find in wiki", "搜索知识库" | Load index, find articles, read, answer                                                 |
| **Priority Query** | Any web search trigger                 | Check wiki FIRST, then web search as supplement                                         |
| **Lint**           | "lint wiki", "整理知识库"                   | **2-group parallel (1+1 concurrent)**, auto-fix (wiki/ only), report, log               |
| **Archive**        | wiki article outdated                  | Move to archive section, update log                                                     |

---

## Quick Reference: File Extraction

| File Type                      | Method           | Command                                                           |
| ------------------------------ | ---------------- | ----------------------------------------------------------------- |
| `.pdf`                         | doc_extractor.py | `python {skill_dir}/scripts/doc_extractor.py "path/to/file.pdf"`  |
| `.xlsx`                        | doc_extractor.py | `python {skill_dir}/scripts/doc_extractor.py "path/to/file.xlsx"` |
| `.xls`                         | doc_extractor.py | `python {skill_dir}/scripts/doc_extractor.py "path/to/file.xls"`  |
| `.docx`                        | doc_extractor.py | `python {skill_dir}/scripts/doc_extractor.py "path/to/file.docx"` |
| `.pptx`                        | doc_extractor.py | `python {skill_dir}/scripts/doc_extractor.py "path/to/file.pptx"` |
| `.rtf`                         | doc_extractor.py | `python {skill_dir}/scripts/doc_extractor.py "path/to/file.rtf"`  |
| `.epub`                        | doc_extractor.py | `python {skill_dir}/scripts/doc_extractor.py "path/to/file.epub"` |
| `.odt` / `.ods` / `.odp`       | doc_extractor.py | `python {skill_dir}/scripts/doc_extractor.py "path/to/file.odt"`  |
| `.png` / `.jpg` / `.jpeg`      | doc_extractor.py | `python {skill_dir}/scripts/doc_extractor.py "path/to/file.png"`  |
| `.gif` / `.webp` / `.bmp`      | doc_extractor.py | `python {skill_dir}/scripts/doc_extractor.py "path/to/file.gif"`  |
| `.svg`                         | doc_extractor.py | `python {skill_dir}/scripts/doc_extractor.py "path/to/file.svg"`  |
| `.md`, `.txt`, `.csv`, `.json` | Read tool        | Read directly, no extraction needed                               |
| URLs                           | Web fetch tool   | Fetch content, save to source directory if needed                 |
