#!/bin/bash
#
# 通用校验脚本：检查 Skill 的目录结构与 frontmatter 是否符合 Agent Skills 规范。
# 不依赖任何特定 Agent 的装配文件，Cursor / Claude Code / Codex / CodeBuddy 都能跑。
#
# 用法： cd remotion-video-generator && ./validate-plugin.sh
#

echo "🔍 Validating Remotion Video Generator Skills..."
echo ""

FAIL=0

# ---------- 1. 结构检查 ----------
for skill in video-generator scene-planner environment-setup \
             remotion-best-practices lucide-icons bgm-library; do
    if [ -f "skills/$skill/SKILL.md" ]; then
        echo "✓ Skill: $skill"
    else
        echo "❌ Skill missing: $skill"
        FAIL=1
    fi
done

for template in explainer-video.md product-demo.md social-media.md presentation.md; do
    if [ -f "templates/$template" ]; then
        echo "✓ Template: $template"
    else
        echo "❌ Template missing: $template"
        FAIL=1
    fi
done

[ -f "README.md" ] && echo "✓ README.md exists" || echo "⚠ README.md missing"

# ---------- 2. frontmatter 规范检查 ----------
# Agent Skills 规范要求：name 只能含小写字母、数字与连字符，且必须与父目录名一致。
# 写成 "Video Generator" 这类带大写或空格的名字，CodeBuddy 能容忍，
# 但 Claude Code / Cursor / Codex 会按规范校验并直接跳过整个 Skill —— 静默失效，很难排查。
echo ""
echo "Checking frontmatter against the Agent Skills spec..."

python3 - <<'PYEOF'
import glob, os, re, sys

ok = True
for d in sorted(glob.glob('skills/*/')):
    dirname = os.path.basename(d.rstrip('/'))
    path = os.path.join(d, 'SKILL.md')
    txt = open(path, encoding='utf-8').read()

    m = re.match(r'^---\n(.*?)\n---\n', txt, re.S)
    if not m:
        print(f"  ❌ {dirname}: no YAML frontmatter")
        ok = False
        continue

    fm = m.group(1)
    nm = re.search(r'^name:\s*(.+)$', fm, re.M)
    ds = re.search(r'^description:\s*(.+)$', fm, re.M)

    name = nm.group(1).strip() if nm else None
    if not name:
        print(f"  ❌ {dirname}: missing name")
        ok = False
    elif not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', name):
        print(f"  ❌ {dirname}: name {name!r} must be lowercase letters, digits and hyphens only")
        ok = False
    elif name != dirname:
        print(f"  ❌ {dirname}: name {name!r} must match the directory name")
        ok = False
    elif not ds or not ds.group(1).strip():
        print(f"  ❌ {dirname}: missing description")
        ok = False
    else:
        print(f"  ✓ {dirname}: name / description valid")

sys.exit(0 if ok else 1)
PYEOF

[ $? -ne 0 ] && FAIL=1

echo ""
if [ $FAIL -eq 0 ]; then
    echo "✅ All checks passed."
else
    echo "❌ Validation failed."
    exit 1
fi
