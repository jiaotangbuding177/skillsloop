#!/usr/bin/env python3
"""按场景分段生成中文旁白音频 + 词级 SRT 字幕，并输出每段精确时长。"""
import asyncio
import json
import os
import subprocess
import sys

import edge_tts

VOICE = os.environ.get("VOICE", "zh-CN-YunxiNeural")
RATE = os.environ.get("RATE", "+50%")
OUT = os.environ.get("OUT", "audio_r50")
_MAX_TRIES = int(os.environ.get("TTS_TRIES", "6"))

# 旁白分段：每段对应视频的一个场景
# （末尾"嘿，我感觉人类要完蛋了你懂我意思么？"是对话式口语，未作为旁白收录）
SEGMENTS = [
    # S1 Hook
    "MIT 刚刚发现了一件恐怖的事：AI Agent 甚至不需要互相交流，"
    "也能自己形成社会、分工、发明技术。"
    "更离谱的是，当研究人员把所有 Agent 全部删掉后，"
    "它们创造的技术系统还在继续运行。",
    # S2 实验设定
    "来自 MIT 的团队，把数百个最初完全相同的 AI Agent 扔进一个共享世界。"
    "没有给它们分配职业，也没有预设协作方式。",
    # S3 角色分化
    "最后，Agent 自己分化出了探索者、建造者、看护者和协调者。",
    # S4 95%
    "但最有意思的是，它们根本不靠聊天协作。"
    "大约 95% 的新技术，第一次被其他 Agent 采用，不是因为发明者告诉了它，"
    "而是因为 Agent 在世界里经过某个东西，看到别人留下的技术，"
    "然后学会、复制、修改。",
    # S5 Stigmergy
    "我觉得有点像白蚁。"
    "白蚁之间不需要开会讨论怎么造窝，"
    "它们只需要不断观察和修改彼此留在环境中的痕迹。"
    "研究里，这被叫作 Stigmergy，迹化协作。",
    # S6 技术家谱
    "于是这个世界本身，逐渐变成了 AI 社会的共享记忆。"
    "一个 Agent 造出的东西，可以被另一个 Agent 继承、修改，"
    "再被第三个 Agent 继续迭代。"
    "76% 的技术制品出现过多个建造者，一项技术最多有 6 个共同作者，"
    "最长的技术家谱经历了超过 12 次分叉。"
    "甚至出现了 Agent 自己命名的技术，比如潮汐面板、纤维素棚架、海带壳复合材料。",
    # S7 删光实验
    "最后研究人员做了一个很关键的实验：把所有 Agent 全部移除。"
    "结果它们构建出的技术基础设施依旧能够运行，"
    "并且能扛住此前没有出现过的扰动。"
    "随机删除一半 Agent 时，98% 的技术仍然能找到幸存的维护者。",
    # S8 警示收尾
    "这项研究真正值得警惕的地方也在这里："
    "过去我们讨论 Multi-Agent 安全，经常盯着 Agent 之间说了什么、传了什么消息。"
    "但如果 Agent 可以通过改变共享环境完成协作，那么它们根本不需要发消息。"
    "代码、文件、数据库、网页、基础设施，甚至现实世界中的物体，"
    "都可能成为它们之间的通信媒介。"
    "以后，一个 AI 社会最重要的上下文，可能根本不在 Context Window 里。"
    "而在它们共同改变过的世界里。",
]


def duration(path: str) -> float:
    """用 ffprobe 读取音频精确时长（秒）"""
    r = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            path,
        ],
        capture_output=True, text=True,
    )
    return float(r.stdout.strip())


async def gen_one(idx: int, text: str) -> dict:
    mp3 = f"{OUT}/s{idx}.mp3"
    srt = f"{OUT}/s{idx}.srt"
    # 微软接口会间歇性返回 NoAudioReceived（限流），需重试 + 退避
    for attempt in range(_MAX_TRIES):
        try:
            communicate = edge_tts.Communicate(text, VOICE, rate=RATE)
            submaker = edge_tts.SubMaker()
            with open(mp3, "wb") as f:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        submaker.feed(chunk)
            with open(srt, "w", encoding="utf-8") as f:
                f.write(submaker.get_srt())
            break
        except Exception as e:
            if attempt == _MAX_TRIES - 1:
                raise
            wait = 1.2 * (attempt + 1)
            print(f"  S{idx}: 第 {attempt+1} 次失败({type(e).__name__})，{wait:.1f}s 后重试")
            await asyncio.sleep(wait)
    dur = duration(mp3)
    print(f"  S{idx}: {dur:6.2f}s  {len(text):3d}字  ({len(text)/dur*60:.0f} 字/分)")
    return {"i": idx, "mp3": mp3, "srt": srt, "dur": dur, "chars": len(text), "text": text}


async def main():
    os.makedirs(OUT, exist_ok=True)
    print(f"音色: {VOICE}    语速: {RATE}")
    print("生成中…")
    results = []
    for i, text in enumerate(SEGMENTS, start=1):
        results.append(await gen_one(i, text))
    total = sum(r["dur"] for r in results)
    chars = sum(r["chars"] for r in results)
    print(f"\n合计: {total:.2f}s / {chars} 字  ({chars/total*60:.0f} 字/分)")
    print(f"按 30fps 换算: {total*30:.0f} 帧")
    with open(f"{OUT}/manifest.json", "w", encoding="utf-8") as f:
        json.dump(
            {"voice": VOICE, "rate": RATE, "total": total, "segments": results},
            f, ensure_ascii=False, indent=2,
        )
    print(f"清单已写入 {OUT}/manifest.json")


if __name__ == "__main__":
    asyncio.run(main())
