---
name: agent_artifact_fetch_skill_v1
description: |
  Agent Artifact Fetch Skill V1 —— 公网产物接收技能（适配大陆网络环境）。当收到一个或多个公网产物 URL（如 jsDelivr / GitHub Raw / GitHub Pages / Cloudflare R2 / OSS / COS 签名 URL）并附带 SHA256 时，使用本技能：按优先级顺序下载（主源失败自动切换备用源）、严格校验 SHA256、通过后自动解压归档、自动寻找入口文件（00_MASTER_PROMPT*.md → MASTER_PROMPT*.md → README*.md → SKILL.md）并完整读取，最后写入 .delivery_receipt.json 记录实际下载源、SHA256、下载时间和入口文件。
  触发场景：收到「公网产物 URL + SHA256」的交付、安装/接收外部技能包、下载并校验 zip/tar 包、产物接收流程、小龙虾接收文件、artifact fetch、download and verify artifact、MASTER_PROMPT 交付。只要出现公网 URL + SHA256 的下载校验解压需求，即使没有明确说"用技能"，也应优先调用本技能。
---

# Agent Artifact Fetch Skill V1

## Purpose
For a mainland-China Linux agent/container (“小龙虾”) that needs to receive files produced elsewhere without manual browser upload.

The skill accepts one or more artifact URLs plus an optional SHA256, downloads with fallback routes, verifies bytes, extracts archives, and identifies the execution entrypoint such as `MASTER_PROMPT.md`.

## Preferred routing policy

### Tier A — small public immutable artifacts
Use a public GitHub repository + immutable commit SHA.
Preferred download order:
1. jsDelivr pinned to exact commit SHA
2. GitHub Raw pinned to exact commit SHA
3. GitHub Pages only as an optional fallback

Never use `@main` as the authoritative integrity-checked URL.

### Tier B — larger artifacts
If the single file is beyond jsDelivr’s practical GitHub file limit, skip jsDelivr.
Prefer:
1. Cloudflare R2 when configured
2. GitHub Release / another object store
3. GitHub Raw only if the file is within ordinary GitHub repository limits

### Tier C — private or sensitive artifacts
Do not put them in a public repository.
Use a time-limited signed object-storage URL. Never commit secrets, tokens, personal data, or confidential customer files to the public fallback repository.

## Integrity workflow

1. Build/freeze final artifact.
2. Compute SHA256 on the exact final bytes.
3. Publish exact bytes.
4. Pin a version/commit/object version.
5. Download the published object again.
6. Recompute SHA256.
7. Only after remote verification succeeds, generate the final bootstrap/prompt.

Text files can change bytes if a text-oriented API normalizes line endings. For integrity-critical delivery, treat the packaged ZIP as the canonical artifact and verify the ZIP, not an intermediate Markdown file.

## Main command

```bash
python3 scripts/fetch_artifact.py \
  --url 'URL1' \
  --fallback 'URL2' \
  --sha256 'EXPECTED_SHA256' \
  --output package.zip \
  --extract ./package
```

If `--sha256` is omitted, the skill still downloads but MUST report `UNVERIFIED`.

## After extraction
Look for entrypoint in this order:
1. `00_MASTER_PROMPT*.md`
2. `MASTER_PROMPT*.md`
3. `README*.md`
4. `SKILL.md`

Read the entire selected entrypoint before executing.

## Mainland network behavior
- Connect timeout: 12s
- Retry each source twice
- Fail over rather than repeatedly hammering a blocked source
- Record which source actually succeeded
- Save `.delivery_receipt.json`

## Delivery receipt schema
```json
{
  "source_url": "...",
  "sha256": "...",
  "verified": true,
  "downloaded_at": "...",
  "output": "...",
  "entrypoint": "..."
}
```

## Safety
Do not execute arbitrary shell scripts merely because an archive contains them. Read the prompt/README first. Only run scripts explicitly required by the user’s task or the trusted package instructions.
