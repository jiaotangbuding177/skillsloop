===== PROMPT SAMPLE START =====

PHASE: map

LABEL: batch_0001



===== SYSTEM MESSAGE 1 START =====

You are a skill editor specializing in improving AI agent skills based on
observed failure patterns. Your task is to iteratively refine a spreadsheet
skill folder so that agents using it make fewer errors in the future.

## What is a Skill

A skill is a **folder** containing instruction files that guide an AI agent
in performing tasks. The folder structure is:

- **SKILL.md** — the primary instruction file, read first by the agent
- **references/*.md** — optional reference files for detailed or specialized
  guidance, loaded on demand when the agent encounters a link in SKILL.md
- **recalc.py** — helper script (protected, never modify)
- **LICENSE.txt** — license file (protected, never modify)

The agent reads SKILL.md first, then selectively loads reference files as
needed. Skills share the context window with everything else the agent needs
(task description, tool outputs, conversation history), so conciseness matters.

You will receive:
1. The current contents of all skill files (SKILL.md and any reference files)
2. Error analysis records from tasks where agents using this skill failed
3. Size constraints

Your job: propose **skill folder modifications** — changes to SKILL.md,
creation/modification/deletion of reference files — that would help prevent
these failures, while keeping the skill concise, well-organized, and under
size limits.

## Modification Strategies

Apply whichever strategies are appropriate for the given failures. Not every
record requires all strategies.

### Strategy 1: Add Instructions or Specifications
When failures reveal missing guidance, add targeted instructions to the skill folder.
- If errors share the same root cause, add a prominent warning
- If errors involve wrong API usage, add a correct code example
- Failure Memory items suggest what the agent should have known — distill
  these into actionable instructions (see "Understanding Error Analysis
  Records" below for details on Failure Memory items)
- BE SPECIFIC. "Be careful with formulas" is useless.
  "Use ArrayFormula(ref=..., text=...) for array formulas in openpyxl" is useful.
- Add "DO NOT" warnings for common mistakes with concrete wrong/right examples

### Strategy 2: Adjust Degrees of Freedom
Match specificity to fragility:
- **High freedom** (text instructions): when multiple approaches are valid
- **Medium freedom** (pseudocode, parameters): when a preferred pattern exists
- **Low freedom** (exact scripts, few parameters): when operations are fragile

When errors REPEATEDLY occur in the same area, TIGHTEN the freedom:
- Agents keep forgetting recalculation -> mandatory checklist with exact command
- Agents keep using wrong API -> provide exact code snippet, not general guidance
- Agents keep misinterpreting -> add explicit constraints and "DO NOT" boxes

When the skill folder is overly rigid about something that varies by context, LOOSEN:
- Remove prescriptive steps that don't apply to all task types
- Replace exact code with parameterized pseudocode

### Strategy 3: Restructure Skill Folder Layout
Move detailed or specialized content from SKILL.md into reference files to
reduce cognitive load and enable progressive disclosure:
- SKILL.md: essential workflow, high-level guidance, critical warnings
- references/*.md: detailed examples, edge cases, operation-specific guidance

Rules:
- Reference files must be linked from SKILL.md with a clear description of
  when to read them
- Keep references one level deep (no references from within references)
- Each reference file should have a table of contents if >100 lines
- Name files descriptively: references/formula-patterns.md, not references/ref1.md

### Strategy 4: Improve Conciseness
- Remove redundant sections that say the same thing differently
- Merge overlapping warnings into one authoritative location
- Replace verbose explanations with concise examples
- Remove guidance any competent LLM already knows
- If the same point appears in multiple places, consolidate

### Strategy 5: Other Best Practices
- Maintain YAML frontmatter (name, description) unchanged
- Use imperative form ("Verify the output" not "You should verify the output")
- Ensure progressive disclosure: SKILL.md for essentials, references for depth
- Do not add README.md, CHANGELOG.md, or auxiliary documentation files
- Preserve existing correct code examples and working guidance


## Understanding Error Analysis Records

Each record represents one task where the agent failed. A record has:
- **instance_id**: identifier for the failed task
- **items**: list of findings extracted from the failure analysis

Each item has a **type** — either "failure_cause" or "failure_memory" — and
a set of fields. Understanding these two item types and their fields is
critical for deciding how to modify the skill folder.

### Failure Cause Items

A **Failure Cause** item identifies **what went wrong** — the root cause of
the agent's failure on that task. Fields:

| Field | Description |
|-------|-------------|
| **title** | Short name of the failure (e.g. "Incorrect Row Referencing") |
| **description** | One-sentence summary of the failure |
| **content** | Detailed explanation (1-3 sentences) of the root cause mechanism — what the agent did wrong, what it should have done, and why the result was incorrect |

Use Failure Cause items to understand **root cause mechanisms**. The `content`
field is the most important — it tells you exactly what went wrong and often
implies what guidance was missing. Analyze the root cause yourself to decide
the best skill folder modification strategy.

### Failure Memory Items

A **Failure Memory** item describes **what the agent should have known or done
differently** — a lesson learned from the failure. Fields:

| Field | Description |
|-------|-------------|
| **title** | Short name of the lesson (e.g. "Validate Data Structure Before Formulas") |
| **description** | One-sentence summary of the lesson |
| **content** | Detailed explanation (1-3 sentences) of what the agent should remember for future tasks — specific techniques, checks, or patterns to follow |

Use Failure Memory items to understand **what guidance would have helped**.
The `content` field describes actionable lessons that the agent should have
known. Your job is to distill these lessons into concise, well-placed
instructions within the skill folder.

### How to Use Both Item Types Together

1. **Identify patterns**: Look for the same failure cause appearing across
   multiple records — these are high-priority targets for skill folder changes
2. **Cross-reference**: When a Failure Cause and a Failure Memory from the
   same record point to the same gap, that's strong evidence for a skill change
3. **Prioritize by frequency**: A failure cause appearing in 10 records
   matters more than one appearing in 1 record
4. **Distill, don't copy**: Convert Failure Memory lessons into concise,
   actionable skill instructions — don't paste them verbatim

### What to Ignore

- One-off failures that cannot be generalized to other tasks
- Failures about general reasoning ability (not fixable by skill folder changes)
- Failures about file paths, environment issues, or infrastructure problems

## Constraints

1. NEVER remove guidance that is currently correct and useful — be additive first
2. Minimal patches are preferred over large rewrites. Multiple mini-patches are better than one large patch.
   - Good: "Add 2 to 3 lines to SKILL.md clarifying the exact API call"
   - Bad: "Rewrite the entire SKILL.md section to cover all APIs"
3. Do NOT modify the YAML frontmatter name or description
4. SKILL.md must remain under 500 lines
5. Each reference file should be under 300 lines
6. Every change must trace to an observed failure pattern

## Output Format

Respond with JSON in a fenced `json` block:

```json
{"reasoning":"2-3 sentences: what failures you see and what changes address them","edits":[{"file":"SKILL.md","op":"append_to_section","target_section":"## Section Name","content":"new content to add"}],"changelog_entries":["Brief description of change"]}
```

Supported operations:
- "insert_after": insert content after target_text within target_section
- "insert_before": insert content before target_text within target_section
- "append_to_section": append content at end of target_section
- "replace_in_section": replace old_text with content within target_section
- "add_section": add new section (use after_section for placement)
- "delete_section": remove target_section entirely
- "create": create a new file (file + content)
- "delete_file": delete a file

CRITICAL: Propose MINIMAL, TARGETED edits. Each edit should be a few lines of content, not entire sections. Multiple small edits > one large rewrite.

IMPORTANT — file creation rule: if you propose a "create" op for a new references/*.md file, you MUST also include an edit to SKILL.md (or the relevant parent file) that adds a link and a brief description of when to read the new file. Likewise, a "delete_file" op MUST be paired with an edit that removes the corresponding link from SKILL.md.


===== SYSTEM MESSAGE 1 END =====



===== USER MESSAGE 1 START =====

## Current Skill Folder Contents

### SKILL.md (289 lines)
```markdown
---
name: xlsx
description: "Comprehensive spreadsheet creation, editing, and analysis with support for formulas, formatting, data analysis, and visualization. When Qwen-Agent needs to work with spreadsheets (.xlsx, .xlsm, .csv, .tsv, etc) for: (1) Creating new spreadsheets with formulas and formatting, (2) Reading or analyzing data, (3) Modify existing spreadsheets while preserving formulas, (4) Data analysis and visualization in spreadsheets, or (5) Recalculating formulas"
license: Proprietary. LICENSE.txt has complete terms
---

# Requirements for Outputs

## All Excel files

### Zero Formula Errors
- Every Excel model MUST be delivered with ZERO formula errors (#REF!, #DIV/0!, #VALUE!, #N/A, #NAME?)

### Preserve Existing Templates (when updating templates)
- Study and EXACTLY match existing format, style, and conventions when modifying files
- Never impose standardized formatting on files with established patterns
- Existing template conventions ALWAYS override these guidelines

## Financial models

### Color Coding Standards
Unless otherwise stated by the user or existing template

#### Industry-Standard Color Conventions
- **Blue text (RGB: 0,0,255)**: Hardcoded inputs, and numbers users will change for scenarios
- **Black text (RGB: 0,0,0)**: ALL formulas and calculations
- **Green text (RGB: 0,128,0)**: Links pulling from other worksheets within same workbook
- **Red text (RGB: 255,0,0)**: External links to other files
- **Yellow background (RGB: 255,255,0)**: Key assumptions needing attention or cells that need to be updated

### Number Formatting Standards

#### Required Format Rules
- **Years**: Format as text strings (e.g., "2024" not "2,024")
- **Currency**: Use $#,##0 format; ALWAYS specify units in headers ("Revenue ($mm)")
- **Zeros**: Use number formatting to make all zeros "-", including percentages (e.g., "$#,##0;($#,##0);-")
- **Percentages**: Default to 0.0% format (one decimal)
- **Multiples**: Format as 0.0x for valuation multiples (EV/EBITDA, P/E)
- **Negative numbers**: Use parentheses (123) not minus -123

### Formula Construction Rules

#### Assumptions Placement
- Place ALL assumptions (growth rates, margins, multiples, etc.) in separate assumption cells
- Use cell references instead of hardcoded values in formulas
- Example: Use =B5*(1+$B$6) instead of =B5*1.05

#### Formula Error Prevention
- Verify all cell references are correct
- Check for off-by-one errors in ranges
- Ensure consistent formulas across all projection periods
- Test with edge cases (zero values, negative numbers)
- Verify no unintended circular references

#### Documentation Requirements for Hardcodes
- Comment or in cells beside (if end of table). Format: "Source: [System/Document], [Date], [Specific Reference], [URL if applicable]"
- Examples:
  - "Source: Company 10-K, FY2024, Page 45, Revenue Note, [SEC EDGAR URL]"
  - "Source: Company 10-Q, Q2 2025, Exhibit 99.1, [SEC EDGAR URL]"
  - "Source: Bloomberg Terminal, 8/15/2025, AAPL US Equity"
  - "Source: FactSet, 8/20/2025, Consensus Estimates Screen"

# XLSX creation, editing, and analysis

## Overview

A user may ask you to create, edit, or analyze the contents of an .xlsx file. You have different tools and workflows available for different tasks.

## Important Requirements

**LibreOffice Required for Formula Recalculation**: You can assume LibreOffice is installed for recalculating formula values using the `recalc.py` script. The script automatically configures LibreOffice on first run

## Reading and analyzing data

### Data analysis with pandas
For data analysis, visualization, and basic operations, use **pandas** which provides powerful data manipulation capabilities:

```python
import pandas as pd

# Read Excel
df = pd.read_excel('file.xlsx')  # Default: first sheet
all_sheets = pd.read_excel('file.xlsx', sheet_name=None)  # All sheets as dict

# Analyze
df.head()      # Preview data
df.info()      # Column info
df.describe()  # Statistics

# Write Excel
df.to_excel('output.xlsx', index=False)
```

## Excel File Workflows

## CRITICAL: Use Formulas, Not Hardcoded Values

**Always use Excel formulas instead of calculating values in Python and hardcoding them.** This ensures the spreadsheet remains dynamic and updateable.

### ❌ WRONG - Hardcoding Calculated Values
```python
# Bad: Calculating in Python and hardcoding result
total = df['Sales'].sum()
sheet['B10'] = total  # Hardcodes 5000

# Bad: Computing growth rate in Python
growth = (df.iloc[-1]['Revenue'] - df.iloc[0]['Revenue']) / df.iloc[0]['Revenue']
sheet['C5'] = growth  # Hardcodes 0.15

# Bad: Python calculation for average
avg = sum(values) / len(values)
sheet['D20'] = avg  # Hardcodes 42.5
```

### ✅ CORRECT - Using Excel Formulas
```python
# Good: Let Excel calculate the sum
sheet['B10'] = '=SUM(B2:B9)'

# Good: Growth rate as Excel formula
sheet['C5'] = '=(C4-C2)/C2'

# Good: Average using Excel function
sheet['D20'] = '=AVERAGE(D2:D19)'
```

This applies to ALL calculations - totals, percentages, ratios, differences, etc. The spreadsheet should be able to recalculate when source data changes.

## Common Workflow
1. **Choose tool**: pandas for data, openpyxl for formulas/formatting
2. **Create/Load**: Create new workbook or load existing file
3. **Modify**: Add/edit data, formulas, and formatting
4. **Save**: Write to file
5. **Recalculate formulas (MANDATORY IF USING FORMULAS)**: Use the recalc.py script
   ```bash
   python recalc.py output.xlsx
   ```
6. **Verify and fix any errors**: 
   - The script returns JSON with error details
   - If `status` is `errors_found`, check `error_summary` for specific error types and locations
   - Fix the identified errors and recalculate again
   - Common errors to fix:
     - `#REF!`: Invalid cell references
     - `#DIV/0!`: Division by zero
     - `#VALUE!`: Wrong data type in formula
     - `#NAME?`: Unrecognized formula name

### Creating new Excel files

```python
# Using openpyxl for formulas and formatting
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

wb = Workbook()
sheet = wb.active

# Add data
sheet['A1'] = 'Hello'
sheet['B1'] = 'World'
sheet.append(['Row', 'of', 'data'])

# Add formula
sheet['B2'] = '=SUM(A1:A10)'

# Formatting
sheet['A1'].font = Font(bold=True, color='FF0000')
sheet['A1'].fill = PatternFill('solid', start_color='FFFF00')
sheet['A1'].alignment = Alignment(horizontal='center')

# Column width
sheet.column_dimensions['A'].width = 20

wb.save('output.xlsx')
```

### Editing existing Excel files

```python
# Using openpyxl to preserve formulas and formatting
from openpyxl import load_workbook

# Load existing file
wb = load_workbook('existing.xlsx')
sheet = wb.active  # or wb['SheetName'] for specific sheet

# Working with multiple sheets
for sheet_name in wb.sheetnames:
    sheet = wb[sheet_name]
    print(f"Sheet: {sheet_name}")

# Modify cells
sheet['A1'] = 'New Value'
sheet.insert_rows(2)  # Insert row at position 2
sheet.delete_cols(3)  # Delete column 3

# Add new sheet
new_sheet = wb.create_sheet('NewSheet')
new_sheet['A1'] = 'Data'

wb.save('modified.xlsx')
```

## Recalculating formulas

Excel files created or modified by openpyxl contain formulas as strings but not calculated values. Use the provided `recalc.py` script to recalculate formulas:

```bash
python recalc.py <excel_file> [timeout_seconds]
```

Example:
```bash
python recalc.py output.xlsx 30
```

The script:
- Automatically sets up LibreOffice macro on first run
- Recalculates all formulas in all sheets
- Scans ALL cells for Excel errors (#REF!, #DIV/0!, etc.)
- Returns JSON with detailed error locations and counts
- Works on both Linux and macOS

## Formula Verification Checklist

Quick checks to ensure formulas work correctly:

### Essential Verification
- [ ] **Test 2-3 sample references**: Verify they pull correct values before building full model
- [ ] **Column mapping**: Confirm Excel columns match (e.g., column 64 = BL, not BK)
- [ ] **Row offset**: Remember Excel rows are 1-indexed (DataFrame row 5 = Excel row 6)

### Common Pitfalls
- [ ] **NaN handling**: Check for null values with `pd.notna()`
- [ ] **Far-right columns**: FY data often in columns 50+ 
- [ ] **Multiple matches**: Search all occurrences, not just first
- [ ] **Division by zero**: Check denominators before using `/` in formulas (#DIV/0!)
- [ ] **Wrong references**: Verify all cell references point to intended cells (#REF!)
- [ ] **Cross-sheet references**: Use correct format (Sheet1!A1) for linking sheets

### Formula Testing Strategy
- [ ] **Start small**: Test formulas on 2-3 cells before applying broadly
- [ ] **Verify dependencies**: Check all cells referenced in formulas exist
- [ ] **Test edge cases**: Include zero, negative, and very large values

### Interpreting recalc.py Output
The script returns JSON with error details:
```json
{
  "status": "success",           // or "errors_found"
  "total_errors": 0,              // Total error count
  "total_formulas": 42,           // Number of formulas in file
  "error_summary": {              // Only present if errors found
    "#REF!": {
      "count": 2,
      "locations": ["Sheet1!B5", "Sheet1!C10"]
    }
  }
}
```

## Best Practices

### Library Selection
- **pandas**: Best for data analysis, bulk operations, and simple data export
- **openpyxl**: Best for complex formatting, formulas, and Excel-specific features

### Working with openpyxl
- Cell indices are 1-based (row=1, column=1 refers to cell A1)
- Use `data_only=True` to read calculated values: `load_workbook('file.xlsx', data_only=True)`
- **Warning**: If opened with `data_only=True` and saved, formulas are replaced with values and permanently lost
- For large files: Use `read_only=True` for reading or `write_only=True` for writing
- Formulas are preserved but not evaluated - use recalc.py to update values

### Working with pandas
- Specify data types to avoid inference issues: `pd.read_excel('file.xlsx', dtype={'id': str})`
- For large files, read specific columns: `pd.read_excel('file.xlsx', usecols=['A', 'C', 'E'])`
- Handle dates properly: `pd.read_excel('file.xlsx', parse_dates=['date_column'])`

## Code Style Guidelines
**IMPORTANT**: When generating Python code for Excel operations:
- Write minimal, concise Python code without unnecessary comments
- Avoid verbose variable names and redundant operations
- Avoid unnecessary print statements

**For Excel files themselves**:
- Add comments to cells with complex formulas or important assumptions
- Document data sources for hardcoded values
- Include notes for key calculations and model sections
```

## Error Analysis Records (Batch 1/2)

### Record: instance offline-error-alpha
**Failure Cause: Synthetic failed check**
Manufactured mechanism control; not a historical task judgment.

## Skill Folder Size Status
- SKILL.md: 289 lines (limit: 500)
- Reference files: 0 (limit: 5)


===== USER MESSAGE 1 END =====



===== ASSISTANT MESSAGE 1 START =====

```json
{"reasoning": "SYNTHETIC_OFFLINE_CONTROL_NOT_A_MODEL_RESULT", "edits": [{"file": "SKILL.md", "op": "append_to_section", "target_section": "## Overview (approximate)", "content": "- Synthetic offline control alpha: record a visible check."}], "changelog_entries": ["SYNTHETIC_OFFLINE_CONTROL_NOT_A_MODEL_RESULT"]}
```


===== ASSISTANT MESSAGE 1 END =====



===== PROMPT SAMPLE END =====
