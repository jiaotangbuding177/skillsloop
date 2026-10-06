# PPT Generator

根据 PPT 大纲，用 AI 逐页生成视觉风格统一的 PPT 图片。

## 效果

提供一份 Markdown 格式的 PPT 大纲，技能自动：

1. 生成风格自洽的封面页
2. 用 AI 分析封面提取视觉风格（配色、字体、氛围）
3. 以封面为锚点，逐页生成风格统一的内页
4. 输出一套完整的 PPT 图片文件

**最终产出**：每页一张 16:9、2K 分辨率的 PNG 图片，风格高度统一。

## 核心机制

**双通道风格锚定**，确保整套 PPT 视觉一致：

| 手段 | 作用 | 优先级 |
|------|------|--------|
| 封面图作为参考图传入每页 | 最强锚定，图生图直接匹配颜色/字体/材质 | 最高 |
| DESIGN SPEC 具体设计要素 | 精确复现颜色值、字体特征、排版比例 | 高 |
| STYLE DESCRIPTION 氛围描述 | 引导整体质感和文化参照 | 中 |
| 统一布局百分比规范 | 确保排版结构一致 | 高 |

## 支持的 AI 工具

| 工具 | 安装路径 | 说明 |
|------|----------|------|
| Claude Code | `~/.claude/skills/` | 最常用 |
| OpenClaw (QClaw) | `~/.agents/skills/` | 技能格式完全兼容 |
| OpenAI Codex | `~/.codex/skills/` | 额外支持 `agents/openai.yaml` |

## 快速开始

### 1. 安装技能

根据你使用的工具，复制到对应目录：

```bash
# Claude Code
cp -r ppt-generator ~/.claude/skills/

# OpenClaw (QClaw)
cp -r ppt-generator ~/.agents/skills/

# OpenAI Codex
cp -r ppt-generator ~/.codex/skills/
```

### 2. 配置 API 密钥

编辑 `SKILL.md`，将配置信息中的占位符替换为你的 API 密钥：

```yaml
# 替换前
- base_url: `<YOUR_BASE_URL>`
- api_key: `<YOUR_API_KEY>`

# 替换后
- base_url: `https://api.your-provider.com/v1`
- api_key: `sk-your-actual-api-key`
```

需要支持 **gpt-5.5**（风格提取）和 **gpt-image-2**（图片生成）两个模型的 API。

### 3. 使用

在 AI 工具对话中，直接提供大纲：

```
帮我生成这个PPT：

# 我的产品调研 PPT大纲

## 封面页
标题：产品调研报告
副标题：市场分析与用户洞察

## 第1页：市场概况
- 市场规模达 500 亿
- 年增长率 23%

## 第2页：用户画像
- 核心用户 25-35 岁
- 付费意愿中等偏上
```

也可以指定风格：

```
帮我生成这个PPT，风格用暗黑科技风：

# ...
```

## 前置依赖

- **gpt-image 技能**：用于图片生成，支持传入参考图（内页风格一致性依赖此技能）
- **Python 3**：运行大纲解析脚本

## 文件说明

| 文件 | 作用 |
|------|------|
| `SKILL.md` | 技能主文件，定义完整的工作流程、提示词模板、配置信息 |
| `scripts/parse_outline.py` | 大纲解析脚本，将 Markdown 大纲解析为结构化的页面列表 |
| `使用教程.md` | 详细使用教程，含三种 AI 工具的安装和排错指引 |

## 许可证

MIT
