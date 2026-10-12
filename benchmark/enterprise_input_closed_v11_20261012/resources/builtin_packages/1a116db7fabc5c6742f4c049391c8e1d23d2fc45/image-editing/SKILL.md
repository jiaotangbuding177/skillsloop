---
name: image-editing
description: Edit or transform one or more existing images with GPT Image 2 through the configured zzz4ai image edits endpoint. Use when the user asks to 修改图片、改图、局部重绘、替换或删除元素、换背景、修图、扩图、风格迁移、保持人物或产品一致性，or generate a new composition from one or more reference images. Do not use for text-only image generation with no input image, or for ordinary deterministic operations such as simple cropping or format conversion.
---

# Image Editing

## 概述

使用一张或多张输入图片完成图片修改、局部编辑和参考图生成。始终通过 zzz4ai 的 GPT Image 2 图片编辑接口执行，不要切换到其他模型或服务。

本 skill 只处理至少包含一张输入图片的任务：

- 单图修改：添加、删除、替换元素，换背景，调整材质、光照、颜色或风格。
- 局部编辑：使用可选 mask 指示主要编辑区域。
- 多参考图生成：把主图、人物、产品、构图或风格参考组合成新图。
- 一致性编辑：尽量保留人物身份、产品外观、品牌元素和未指定区域。

如果用户没有提供任何输入图片，改用 `image-generation`。如果目标是逐页生成图片式 PPT，改用 `image-ppt-generation`。简单裁剪、旋转、缩放或格式转换优先使用确定性的本地图像工具，不要调用生成模型。

## 固定服务配置

- API endpoint：`https://llmapi.zzz4ai.com/v1/images/edits`
- Model：`gpt-image-2`
- Authentication：只从环境变量 `ZZZ4AI_IMAGE_KEY` 读取
- Content-Type：`multipart/form-data`，让 HTTP 客户端自动生成 boundary
- 图片字段：按顺序重复传入 `image[]`
- 可选遮罩字段：`mask`
- 客户端超时：至少 `600` 秒
- 默认 `quality`：`low`
- 默认 `n`：`1`
- 默认 `size`：`auto`
- 默认 `output_format`：`png`
- 默认 `output_compression`：`100`

不要手工设置 multipart 的 `Content-Type` 请求头，否则可能丢失 boundary。

## 执行流程

1. 确认至少有一张可读取的本地图片；不要仅凭聊天中的缩略图或失效路径发起请求。
2. 明确每张图片的角色。默认把第 1 张作为主图或主画布，其余图片作为人物、产品、风格、材质或构图参考。
3. 明确编辑目标和必须保留的内容。只有当“修改什么”或“保留什么”存在实质歧义时才提问；需求清楚时直接执行。
4. 检查用户要求的输出比例、尺寸、格式和质量。未指定尺寸时使用 `auto`，避免无故把原图压成正方形。
5. 把输入图片按角色顺序作为重复的 `image[]` 字段上传。不要把图片转成 base64 后塞进普通 JSON。
6. 如果提供 mask，把 mask 作为独立的 `mask` 文件字段上传，并把要修改的主图放在第 1 个 `image[]`。
7. 发起请求，检查 HTTP 状态和响应 JSON，再从 `data[0].b64_json` 解码图片。
8. 把结果保存到当前 workspace 下的可访问目录，例如 `outputs/images/edited_001.png`，然后返回本地路径。不要向用户返回 base64。
9. 视觉检查输出是否满足修改目标、保留要求、尺寸和文件格式。若失败，先收紧 prompt；只有瞬时网络或服务错误才原样重试。

## 输入图片与角色顺序

把图片顺序写进 prompt，避免模型误解参考图用途：

- `Image 1`：主图、主画布或需要直接修改的图片。
- `Image 2..N`：人物身份、产品细节、服装、风格、材质、配色或构图参考。
- 使用 mask 时，mask 只约束第 1 张图片；不要期待它精确控制其他参考图。

多参考图不等于简单拼贴。明确说明应从每张图继承什么，以及哪些内容不得继承。例如：

```text
Image 1 is the primary canvas. Keep its camera angle, composition, subject identity, and background geometry.
Image 2 is a clothing reference. Transfer only the jacket design and fabric texture.
Image 3 is a color reference. Use only its muted navy-and-amber palette.

Edit: replace the subject's current jacket with the jacket from Image 2.
Preserve: face, body proportions, pose, hands, lighting direction, and all unmentioned objects.
Output: photorealistic, no extra text, same aspect ratio as Image 1.
```

## Prompt 规范

把 prompt 写成明确的编辑合同，优先包含以下部分：

1. `Image roles`：逐张声明主图和参考图用途。
2. `Edit`：只描述需要发生的变化，使用清晰的动作词。
3. `Preserve`：列出不得改变的身份、构图、文字、Logo、产品结构或背景元素。
4. `Remove/Avoid`：列出必须移除或禁止新增的内容。
5. `Output`：声明写实程度、风格、宽高比、文字要求和最终用途。

对于局部修改，明确使用“只修改……，其余保持不变”。对于人物或产品一致性，具体列出必须保留的面部特征、比例、Logo、包装文字、材质和拍摄角度。不要只写“保持一致”。

如果图片中包含必须精确保留的文字，逐字列出原文并要求保持拼写；完成后仍要视觉检查，因为生成模型不能保证像素级文字准确。

## 案例参考

处理“产品白底图 → 场景化广告海报”或相似的产品身份保持任务时，读取 [矿泉水产品广告案例](references/mineral-water-poster-example.md)。该案例包含输入与结果图片、结构化 prompt、产品保留要求、版式说明和验收清单；其他任务不要加载它。

## Mask 规范

- mask 是可选的提示约束，不是像素级硬边界；prompt 仍需描述完整目标。
- 主图与 mask 应使用相同尺寸和格式，单个文件小于 `50MB`。
- mask 必须包含 alpha 通道。
- 多图请求中，mask 作用于第 1 张输入图。
- 如果 mask 不符合要求，先修正 mask，不要用反复请求碰运气。

## GPT Image 2 参数规范

- 始终设置 `model=gpt-image-2`。
- 不要传 `input_fidelity`；GPT Image 2 自动以高保真处理所有输入图片，接口不允许调整该参数。
- `size` 可使用 `auto` 或合法自定义分辨率。自定义尺寸必须满足：宽高均为 `16` 的倍数、单边不超过 `3840`、宽高比不超过 `3:1`、总像素数在 `655360` 到 `8294400` 之间。
- `quality` 支持 `low`、`medium`、`high`；默认使用 `low`，仅在用户明确要求更高质量时改用 `medium` 或 `high`。
- `output_format` 使用服务支持的 `png` 或 `jpeg`。需要保真或后续处理时优先 `png`；关注文件体积时使用 `jpeg`。
- `output_compression` 范围为 `0` 到 `100`，按 zzz4ai/ModelVerse 兼容接口约定传递。
- GPT Image 2 当前不支持透明背景；不要请求 `background=transparent`。

## curl 模板

```bash
curl --max-time 600 --location 'https://llmapi.zzz4ai.com/v1/images/edits' \
  --header "Authorization: Bearer $ZZZ4AI_IMAGE_KEY" \
  -F "model=gpt-image-2" \
  -F "prompt=Image 1 is the primary canvas. Replace only the mug with the product from Image 2. Preserve the person, hands, desk, lighting, and camera angle." \
  -F "image[]=@./primary.png" \
  -F "image[]=@./product-reference.png" \
  -F "quality=low" \
  -F "size=auto" \
  -F "n=1" \
  -F "output_format=png" \
  -F "output_compression=100"
```

需要局部编辑时增加：

```bash
-F "mask=@./mask.png"
```

## Python 示例

```python
import base64
import mimetypes
import os
from pathlib import Path

import requests


def edit_image(
    prompt: str,
    image_paths: list[str],
    output_path: str = "outputs/images/edited_001.png",
    mask_path: str | None = None,
    size: str = "auto",
    quality: str = "low",
    output_format: str = "png",
    output_compression: int = 100,
    timeout: int = 600,
) -> str:
    if not image_paths:
        raise ValueError("At least one input image is required")
    if output_format not in {"png", "jpeg"}:
        raise ValueError("output_format must be 'png' or 'jpeg'")

    api_key = os.environ["ZZZ4AI_IMAGE_KEY"]
    handles = []
    files = []
    try:
        for raw_path in image_paths:
            path = Path(raw_path)
            handle = path.open("rb")
            handles.append(handle)
            mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            files.append(("image[]", (path.name, handle, mime_type)))

        if mask_path:
            path = Path(mask_path)
            handle = path.open("rb")
            handles.append(handle)
            mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            files.append(("mask", (path.name, handle, mime_type)))

        response = requests.post(
            "https://llmapi.zzz4ai.com/v1/images/edits",
            headers={"Authorization": f"Bearer {api_key}"},
            files=files,
            data={
                "model": "gpt-image-2",
                "prompt": prompt,
                "size": size,
                "quality": quality,
                "n": "1",
                "output_format": output_format,
                "output_compression": str(output_compression),
            },
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
        image_b64 = payload["data"][0]["b64_json"]
        if image_b64.startswith("data:"):
            _, _, image_b64 = image_b64.partition(",")

        target = Path(output_path)
        expected_suffix = ".jpg" if output_format == "jpeg" else ".png"
        allowed_suffixes = {expected_suffix, ".jpeg"} if output_format == "jpeg" else {expected_suffix}
        if target.suffix.lower() not in allowed_suffixes:
            target = target.with_suffix(expected_suffix)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(base64.b64decode(image_b64, validate=True))
        return str(target)
    finally:
        for handle in handles:
            handle.close()
```

## 响应与错误处理

成功响应应包含 `data[0].b64_json`。保存前确认字段存在、base64 可解码且结果非空。

- `401` / `403`：检查 `ZZZ4AI_IMAGE_KEY` 是否存在和有效；不要把 key 打印出来。
- `400`：检查 prompt、图片字段、mask、尺寸和格式。不要对相同无效请求盲目重试。
- `413`：压缩或缩小输入文件后再试，不要降低必须保留细节的主图质量。
- `429`：按服务返回的等待信息退避重试。
- `5xx` 或网络超时：保留输入和 prompt，指数退避后最多重试两次。
- 内容安全拒绝：修改不合规的 prompt 或输入；不要尝试绕过安全检查。

若响应含 `error.code`、`error.message` 或请求 ID，只返回排障需要的非敏感信息。绝不记录 Authorization 头、完整请求体中的隐私图片或 base64 结果。

## 完成检查

- 确认实际调用的是 `/v1/images/edits`，而不是纯文本生成端点。
- 确认每张参考图都以独立的 `image[]` 字段上传且顺序正确。
- 确认未传 `input_fidelity`，未请求透明背景。
- 确认结果已解码落盘，扩展名与 `output_format` 一致。
- 视觉检查目标修改、主体一致性、未编辑区域、文字和品牌元素。
- 向用户返回结果路径和简短修改摘要，不返回密钥、base64 或不必要的原图副本。
