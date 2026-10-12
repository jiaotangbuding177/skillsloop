---
name: image-ppt-generation
description: "图片式PPT生成。把每一页幻灯片直接生成为整页图片，支持无参考图的文本生图，也支持通过 image[] 重复字段上传多张参考图进行图片编辑式生成；逐页保存到本地，生成好一页就立即向用户报告路径，全部完成后再把图片汇总成 .pptx 文件。适用于 图片PPT、生图PPT、逐页生成PPT、PPT创作、视觉演示文稿、直接生成图片式PPT，或用户明确希望用图片生成而不是可编辑版式制作幻灯片的任务。"
version: 1.0.0
---

## 概述

使用本 skill 创建图片优先的演示文稿。每一页幻灯片都生成为一张位图图片，生成后立即保存并把本地路径告诉用户，最后再把所有图片按顺序全幅嵌入一个 PPTX 文件。

本 skill 产出的是不可编辑的图片式幻灯片。如果用户需要可编辑文字、图表或形状，简短说明这一点，并建议改用常规 PPT 制作流程；如果用户明确要图片生成式幻灯片，则继续执行。

## 必须流程

1. 在生成任何图片前，必须先和用户讨论 PPT 框架与设计方向，包括目标受众、使用场景、页数、叙事主线、章节结构、视觉风格、配色、参考素材、内容密度和输出比例。
2. 基于讨论结果形成完整 PPT 大纲。大纲至少包含每页页码、标题、核心信息。
3. 把完整大纲发给用户确认。未获得用户确认前，不要调用图片生成接口。
4. 大纲确认后，创建输出目录，例如 `outputs/slides/`。
5. 按页推进。生成每一页之前，先向用户展示该页的具体内容方案，包括页面标题、所有需要出现在图上的文字、布局结构、视觉元素；获得用户对该页的确认后，才生成该页图片。
6. 使用下方图片生成接口逐页生成幻灯片。
7. 每生成好一页，就解码返回的 `b64_json`，保存为 `slide_001.png`、`slide_002.png` 等文件，然后在生成下一页之前立即告诉用户该页本地路径。
8. 所有页面图片保存完成后，把每张图片作为整页幻灯片汇总成PPTX文件。
9. 告诉用户最终 PPTX 路径，并附上所有页面图片路径列表。

不要把 base64 图片数据返回给用户。

## 用户确认门禁

本 skill 必须采用“两级确认”：

- 第一级：完整大纲确认。只有当用户确认整体框架、大纲和设计方向后，才能进入逐页制作。
- 第二级：逐页内容确认。每页生成前都要单独确认该页内容和画面方案；用户确认第 N 页后，只生成第 N 页，不要跳过确认直接批量生成后续页面。

如果用户要求“直接生成”“不用确认”或表达同等意思，可以跳过逐页确认，但仍应先给出一个简短完整大纲并说明将按该大纲执行。否则默认必须确认。

## 图片生成设置

每一页都使用 `gpt-image-2`。根据是否有参考图片选择接口：

### 无参考图：文本直接生图

没有可用参考图片文件时，使用文本生图接口。

- API endpoint: `https://llmapi.zzz4ai.com/v1/images/generations`
- 模型：`gpt-image-2`
- API key：只从 `ZZZ4AI_IMAGE_KEY` 读取
- PPT 默认尺寸：16:9 使用 `2048x1152`
- 默认质量：`low`
- 默认 `n`：`1`
- 默认 `output_format`：`png`
- 默认 `output_compression`：`100`
- 客户端超时：至少 `600` 秒

curl 模板：

```bash
curl --max-time 600 --location 'https://llmapi.zzz4ai.com/v1/images/generations' \
  --header "Authorization: Bearer $ZZZ4AI_IMAGE_KEY" \
  --header "Content-Type: application/json" \
  --data '{
    "model": "gpt-image-2",
    "prompt": "Create page 1 of a master thesis defense PPT as a polished academic cover slide in Chinese...",
    "size": "2048x1152",
    "quality": "low",
    "n": 1,
    "output_format": "png",
    "output_compression": 100
  }'
```

Python 模板：

```python
import base64
import os
from pathlib import Path

import requests


def generate_slide_from_text(prompt: str, output_path: str) -> str:
    url = "https://llmapi.zzz4ai.com/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {os.environ['ZZZ4AI_IMAGE_KEY']}",
        "Content-Type": "application/json",
    }
    response = requests.post(
        url,
        headers=headers,
        json={
            "model": "gpt-image-2",
            "prompt": prompt,
            "size": "2048x1152",
            "quality": "low",
            "n": 1,
            "output_format": "png",
            "output_compression": 100,
        },
        timeout=600,
    )
    response.raise_for_status()
    payload = response.json()

    image_b64 = payload["data"][0]["b64_json"]
    if image_b64.startswith("data:"):
        _, _, image_b64 = image_b64.partition(",")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_bytes(base64.b64decode(image_b64))
    return output_path
```

### 有参考图：多图上传编辑生成

当用户提供模板图、历史页截图，或已完成前序页面生成，使用多图上传编辑接口。通过重复字段 `image[]` 传入多张图片。

- API endpoint: `https://llmapi.zzz4ai.com/v1/images/edits`
- 模型：`gpt-image-2`
- API key：只从 `ZZZ4AI_IMAGE_KEY` 读取
- 图片字段：重复传入 `image[]`
- 文本字段：`model`、`prompt`、`quality`、`output_format`、`output_compression`
- 默认质量：`low`
- 默认 `output_format`：`png`
- 默认 `output_compression`：`100`
- 输出：读取 `resp["data"][0]["b64_json"]`，解码保存为当前页图片
- 客户端超时：至少 `600` 秒

curl 模板：

```bash
curl --location 'https://llmapi.zzz4ai.com/v1/images/edits' \
  --header "Authorization: Bearer $ZZZ4AI_IMAGE_KEY" \
  -F "model=gpt-image-2" \
  -F "quality=low" \
  -F "output_format=png" \
  -F "output_compression=100" \
  -F "image[]=@./image-a.png" \
  -F "image[]=@./image-b.png" \
  -F "image[]=@./image-c.png" \
  -F "prompt=Create page 11 of a master's thesis defense PPT as a polished academic slide in Chinese..."
```

Python 模板：

```python
import base64
import os
from pathlib import Path

import requests


def generate_slide_with_references(prompt: str, image_paths: list[str], output_path: str) -> str:
    url = "https://llmapi.zzz4ai.com/v1/images/edits"
    headers = {"Authorization": f"Bearer {os.environ['ZZZ4AI_IMAGE_KEY']}"}
    files = []
    handles = []
    try:
        for path in image_paths:
            handle = open(path, "rb")
            handles.append(handle)
            files.append(("image[]", (Path(path).name, handle, "image/png")))

        response = requests.post(
            url,
            headers=headers,
            files=files,
            data={
                "model": "gpt-image-2",
                "prompt": prompt,
                "quality": "low",
                "output_format": "png",
                "output_compression": "100",
            },
            timeout=600,
        )
        response.raise_for_status()
        payload = response.json()
    finally:
        for handle in handles:
            handle.close()

    image_b64 = payload["data"][0]["b64_json"]
    if image_b64.startswith("data:"):
        _, _, image_b64 = image_b64.partition(",")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_bytes(base64.b64decode(image_b64))
    return output_path
```

## 页面风格延续

必须按顺序生成页面，并通过文字 prompt 上下文延续风格：

- 第 1 页：默认作为封面页，除非用户明确要求不是封面。
- 第 2 页：参考第 1 页风格继续生成。
- 第 N 页，且 N >= 3：均参考第2页风格继续生成。

如果前页图片文件已经存在，优先把应参考的前页图片作为 `image[]` 上传到多图编辑接口；如果没有可用图片文件，再把视觉特征转写成下一页 prompt 的风格描述。

执行过程中维护一个简短的风格记录：配色、字体气质、构图、光照、质感、图标或插画风格、重复视觉母题。根据上面的参考窗口规则决定当前页应该继承哪些前页风格。

## Prompt 模式

每一页 prompt 优先使用“英文结构化指令 + 中文页面文本”的格式。英文负责描述版式、风格、一致性和渲染要求；中文负责页面标题、栏目名、指标、结论等需要出现在图上的文字，并尽量逐条列出，避免混在长段落里。

每一页 prompt 都要包含：

- PPT 主题、受众、语言和宽高比。
- 当前页码和页面角色，例如封面、目录、概念、对比、时间线、结尾。
- 当前页核心信息。
- 按页面风格延续规则确定的风格参考。
- 全幅 16:9 演示文稿页面，无页边距；除非用户要求，不要模拟设备外框。
- 清晰列出页面布局，例如 `left half + right half + bottom summary strip`。
- 清晰列出每个 section、card、flow、metric、banner 里的原文。
- 页面文字要短、分区清楚、字号可读。学术答辩类页面可以密集，但必须使用清楚的标题层级、圆角框、图标、流程线、统计卡片和留白分隔，避免整页段落堆叠。

prompt参考：
```text
Create slide 12 of the same master's thesis defense deck. Match the visual style of Image A (original template) and keep strong consistency with Image B (page 11 anchor) and Image C (previous results-style slide): white background, maroon/red theme, top-left page-number box, top-right East China Normal University logo and name, thin maroon top divider, dense academic layout, rounded boxes, clear icons and infographics.

Slide number: 12. Title: "教学图式与数据合成机制".

Layout: left half + right half + bottom summary strip.

Left half section 1 header: "1. 学科知识图谱构建". Show a 3-step vertical mini-flow with arrows:
Step 1 "自动关系抽取": source textbooks from 人教版/北师大版等数学教材, GPT-5.2 zero-shot extraction, "候选三元组约 12,000 条".
Step 2 "初级审核与精炼": "两名数学研究生独立审核" ; "保留约 6,800 条三元组" ; "同义实体规范化合并".
Step 3 "专家复核与验证": "2 名中学数学教师复核" ; "最终 620 个实体节点、5,847 条关系边" ; "Cohen’s Kappa = 0.91".
Beside or below, show a small legend of entity types and relation types:
Entity types: "知识概念/定理节点" ; "题型节点".
Relation types: "is_prerequisite_of" ; "leads_to" ; "is_generalization_of" ; "is_variant_of".
Also show a tiny local graph sketch with nodes like 因式分解、一元二次方程、勾股定理、正弦定理、解斜三角形（变式题型）.

Right half section 2 header: "2. 五段式教学图式". Display a clear 5-stage horizontal or vertical flow with boxes titled exactly:
"题干陈述" → "知识分析" → "解题过程" → "结论" → "教学启示".
Under the flow, list the three operational characteristics in a compact callout: "外显性" ; "可监督性" ; "迁移导向性".
Also add a small one-line explanation: "图式显式建模‘知识点激活—依赖关系—推理步骤—教学策略’链路。"

Lower middle/right section 3 header: "3. 受控条件变式与图式数据合成". Show four variant types as four cards with icons: "数值变式" ; "结构变式" ; "条件变式" ; "目标变式". Under each give a short phrase:
数值变式: "修改数字参数";
结构变式: "改变数学结构";
条件变式: "增删已知条件";
目标变式: "改变求解目标".
Connect these to a central output box: "原题—变式题对 D_syn".

Bottom statistics band: summarize exact key data in 3 compact metric cards:
Card 1: "图式标注数据 D_schema：2,640 条" and domain counts "代数875 / 几何623 / 数论564 / 计数与概率578".
Card 2: "合成数据集 D_syn：18,400 条高质量原题-变式题对" ; "每道原题平均生成 2.3 个高一致性变式".
Card 3: "知识依赖路径采样长度 L = 2–5" ; "短/中/长路径比例约 3:4:3".

Bottom conclusion banner: "知识图谱提供结构骨架，教学图式提供认知模板，受控变式提供泛化信号，共同支撑高质量蒸馏数据生成。"
```

## 构建 PPTX

所有页面图片都存在后，在不修改所有页面图片的前提下，按文件名顺序把每张图片全幅嵌入幻灯片，最终输出pptx文件给用户。

## 失败处理

- 如果某一页生成失败，用更简单的 prompt 重试该页一次。保留已经生成成功的页面文件。
- 如果 PPTX 汇总失败，报告已保存图片路径和错误，然后只修复汇总步骤，不要重新生成已成功页面。
