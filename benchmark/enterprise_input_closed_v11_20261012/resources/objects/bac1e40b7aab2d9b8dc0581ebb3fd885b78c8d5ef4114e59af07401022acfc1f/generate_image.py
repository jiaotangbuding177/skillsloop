#!/usr/bin/env python3
"""通过 zzz4ai 图片生成 API（gpt-image-2）生成视频素材，保存为 PNG。

用法：
  python3 generate_image.py --prompt "深蓝色渐变科技感背景，16:9" \
      [--size 1536x1024] [--quality high] [--out-dir public] [--stem bg]

说明：
  - API key 从环境变量 ZZZ4AI_IMAGE_KEY 读取（不要写入任何文件/日志）。
  - 模型固定为 gpt-image-2，不要按用户要求切换其他模型。
  - 生成结果保存为 <out-dir>/<stem>_NNN.png，并打印文件路径。
  - 纯标准库实现，无需 pip 安装。
"""
import argparse
import base64
import json
import os
import sys
import urllib.request
from pathlib import Path

API_URL = "https://llmapi.zzz4ai.com/v1/images/generations"
MODEL = "gpt-image-2"
TIMEOUT = 600


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a video asset image via zzz4ai gpt-image-2")
    parser.add_argument("--prompt", required=True, help="图片提示词（描述主体/风格/构图/颜色/文字/尺寸约束）")
    parser.add_argument("--size", default="1024x1024", help="尺寸，如 1024x1024 / 1536x1024(16:9) / 1024x1536(9:16)")
    parser.add_argument("--quality", default="high", choices=["low", "medium", "high"])
    parser.add_argument("--out-dir", default="public", help="输出目录（视频项目 public/ 目录可直接被 staticFile 引用）")
    parser.add_argument("--stem", default="asset", help="文件名前缀")
    args = parser.parse_args()

    api_key = os.environ.get("ZZZ4AI_IMAGE_KEY")
    if not api_key:
        print("ERROR: 环境变量 ZZZ4AI_IMAGE_KEY 未设置，请先配置后再生成素材。", file=sys.stderr)
        return 1

    payload = {
        "model": MODEL,
        "prompt": args.prompt,
        "size": args.size,
        "quality": args.quality,
        "n": 1,
        "output_format": "png",
        "output_compression": 100,
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: 图片生成请求失败: {exc}", file=sys.stderr)
        return 1

    if "error" in result:
        print(f"ERROR: API 返回错误: {result['error']}", file=sys.stderr)
        return 1

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for index, item in enumerate(result.get("data", []), start=1):
        image_b64 = item.get("b64_json", "")
        if not image_b64:
            print("ERROR: 响应中没有 b64_json 数据", file=sys.stderr)
            return 1
        if image_b64.startswith("data:"):
            _, _, image_b64 = image_b64.partition(",")
        out_path = out_dir / f"{args.stem}_{index:03d}.png"
        out_path.write_bytes(base64.b64decode(image_b64))
        paths.append(str(out_path))

    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
