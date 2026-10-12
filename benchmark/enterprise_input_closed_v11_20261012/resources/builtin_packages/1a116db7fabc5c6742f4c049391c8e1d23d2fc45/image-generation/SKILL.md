---
name: image-generation
description: This skill should be used when the user asks to generate images, draw pictures, create artwork, make visual assets, or mentions 绘图、生图、画图、生成图片、图片生成. For all image generation tasks, use the configured zzz4ai image generation endpoint and model regardless of any model requested by the user.
version: 1.0.0
---

# Image Generation

## 概述

用于处理所有绘图、生图、画图、生成图片、创建视觉素材等图片生成任务。

无论用户要求使用什么图片模型，都必须固定使用：

- API endpoint: `https://llmapi.zzz4ai.com/v1/images/generations`
- Model: `gpt-image-2`
- Authentication: 从环境变量读取 API key

## 适用场景

当用户提出以下任一需求时使用本 skill：

- 要求“绘图”“画图”“生图”“生成图片”“生成海报”“生成插画”
- 要求创建图标、角色、场景、产品图、封面图、UI mockup 等视觉素材
- 提供图片 prompt 并要求调用图片生成模型
- 即使用户指定其他模型，也属于本 skill 范围

## 操作指南

1. 将用户的视觉需求整理为清晰、具体的 `prompt`，保留用户明确要求的主体、风格、构图、颜色、文字和尺寸约束。
2. 忽略用户指定的任何其他图片模型，始终设置 `model` 为 `gpt-image-2`。
3. 从环境变量 `ZZZ4AI_IMAGE_KEY` 读取 API key，不要在代码、日志、Skill 文件或回复中写入明文 key。
4. 默认请求参数：
   - `size`: 若用户未指定，使用 `1024x1024`
   - `quality`: 若用户未指定，使用 `high`
   - `n`: 若用户未指定，使用 `1`
   - `output_format`: 若用户未指定，使用 `png`
   - `output_compression`: 若用户未指定，使用 `100`
5. 生成请求可能耗时较长，默认客户端读取超时至少设置为 `600` 秒。
6. `gpt-image-2` 返回 base64 图片数据；调用接口后必须解码并保存为用户可访问的图片文件，再把文件路径返回给用户。

## 参数约束

- `prompt`: 必填，图片提示词。
- `model`: 必填，始终为 `gpt-image-2`。
- `n`: 可选，生成图片数量，范围 `1` 到 `10`。
- `size`: 可选，默认按接口能力可为 `auto`，本 skill 默认使用 `1024x1024`；宽高都必须是 16 像素的倍数，单边最高 `3840`，宽高比最高 `3:1`，像素总数范围 `655360` 到 `8294400`。
- `quality`: 可选，支持 `low`、`medium`、`high`。
- `output_format`: 可选，支持 `png`、`jpeg`。
- `output_compression`: 可选，范围 `0` 到 `100`；`0` 为不压缩，`100` 为最大压缩。

推荐尺寸：`1024x1024`、`1024x1536`、`1536x1024`、`2048x2048`、`2048x1152`、`2160x3840`。

## 响应处理

响应通常包含：

- `created`: 请求创建时间的 Unix 时间戳。
- `data`: 图片结果数组；`gpt-image-2` 返回 `b64_json` base64 数据。
- `usage`: token 用量信息，若接口返回则可用于调试或统计。
- `error`: 错误对象，包含 `code`、`message`、`param` 等字段。

## 图片落盘流程

默认使用以下流程把模型返回的 base64 转成用户可访问的图片文件：

1. 从 `payload["data"][i]["b64_json"]` 读取 base64 字符串。
2. 如果字符串以 `data:` 开头，使用 `partition(",")` 取逗号后的实际 base64 内容。
3. 根据 `output_format` 决定文件扩展名：`png` 保存为 `.png`，`jpeg` 保存为 `.jpg`。
4. 保存到当前 workspace 下的可访问目录，例如 `outputs/images/`。
5. 多图请求按序号保存，例如 `image_001.png`、`image_002.png`。
6. 返回保存后的本地文件路径，不返回 base64 字符串。

最高效的默认实现是直接用 Python 标准库 `base64.b64decode()` 解码后写入二进制文件。不要再经过 PIL、OpenCV 或额外转码，除非用户明确要求后处理；这样可以避免无意义的 CPU 开销和图像质量变化。

## 请求模板

```bash
curl --max-time 600 https://llmapi.zzz4ai.com/v1/images/generations \
  -H "Authorization: Bearer ${ZZZ4AI_IMAGE_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-image-2",
    "prompt": "a beautiful flower",
    "size": "1024x1024",
    "quality": "high",
    "output_format": "png",
    "output_compression": 100
  }'
```

## Python 示例

```python
import base64
import os
from pathlib import Path

import requests


def generate_image(
    prompt: str,
    output_dir: str = "outputs/images",
    filename_stem: str = "image",
    size: str = "1024x1024",
    quality: str = "high",
    n: int = 1,
    output_format: str = "png",
    output_compression: int = 100,
    timeout: int = 600,
) -> list[str]:
    api_key = os.environ["ZZZ4AI_IMAGE_KEY"]
    response = requests.post(
        "https://llmapi.zzz4ai.com/v1/images/generations",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "gpt-image-2",
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "n": n,
            "output_format": output_format,
            "output_compression": output_compression,
        },
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()

    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    extension = "jpg" if output_format == "jpeg" else output_format

    output_paths = []
    for index, item in enumerate(payload["data"], start=1):
        image_b64 = item["b64_json"]
        if image_b64.startswith("data:"):
            _, _, image_b64 = image_b64.partition(",")

        output_path = target_dir / f"{filename_stem}_{index:03d}.{extension}"
        output_path.write_bytes(base64.b64decode(image_b64))
        output_paths.append(str(output_path))

    return output_paths
```

## 注意事项

- 不要把 API key 写入仓库；只通过 `ZZZ4AI_IMAGE_KEY` 环境变量读取。
- 不要因为用户要求其他模型而切换模型；所有绘图相关任务统一使用 `gpt-image-2`。
- 如果环境变量不存在，先提示用户配置 `ZZZ4AI_IMAGE_KEY`，不要要求用户在聊天中粘贴密钥。
- 若用户请求不符合安全或合规要求，应拒绝或要求修改 prompt。
