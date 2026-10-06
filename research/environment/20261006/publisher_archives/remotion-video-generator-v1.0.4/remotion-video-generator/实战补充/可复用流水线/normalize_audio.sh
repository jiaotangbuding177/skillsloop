#!/usr/bin/env bash
# 旁白后期：8 段 TTS 拼接 → 响度标准化 -16 LUFS → public/narration.m4a
#
# 用法：
#   ./normalize_audio.sh              # 默认读 audio_r30/s1..s8.mp3
#   ./normalize_audio.sh audio_r20    # 指定分段目录（换语速时用）
#
# 为什么需要这一步：
#   edge-tts 原始输出约 -24 LUFS，直接混进成片在手机外放会明显偏轻。
#   本脚本做两遍 EBU R128 归一化到 -16 LUFS / -1.5 dBTP。
#   linear=true 表示只施加恒定增益、不压缩动态范围，人声不会发闷。
#   抖音 / 视频号 / 小红书平台归一化目标普遍在 -14~-16 LUFS，这个档位不会被二次拉扯。

set -euo pipefail
cd "$(dirname "$0")"

SEG_DIR="${1:-audio_r50}"
OUT="public/narration.m4a"
RAW="public/narration_tts_raw.mp3"
SUBS="src/compositions/stigmergy/subs.ts"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# 目标时长（秒）——以 subs.ts 的 TOTAL_FRAMES 为准。
# 不能读已渲染视频的时长：换语速后旧成片还是旧长度，会把新音频错误补齐。
FPS=30
# 行形如：export const TOTAL_FRAMES = 2994;  → 数字在第 5 个字段
VIDEO_DUR=$(awk -v fps="$FPS" '/TOTAL_FRAMES =/{gsub(/[^0-9]/,"",$5); printf "%.4f", $5/fps; exit}' "$SUBS")
if [ -z "$VIDEO_DUR" ] || [ "$VIDEO_DUR" = "0.0000" ]; then
  echo "无法从 $SUBS 解析 TOTAL_FRAMES"; exit 1
fi

# ---- 拼接 8 段（先转无损 wav 中间体，避免 mp3 帧头导致的时间戳漂移）----
INPUTS=()
FILTER=""
for i in $(seq 1 8); do
  f="${SEG_DIR}/s${i}.mp3"
  [ -f "$f" ] || { echo "缺少分段文件: $f"; exit 1; }
  INPUTS+=(-i "$f")
  FILTER+="[$((i-1)):a]"
done
FILTER+="concat=n=8:v=0:a=1[a]"

echo "拼接 ${SEG_DIR}/s1..s8.mp3 ..."
ffmpeg -hide_banner -loglevel error -y "${INPUTS[@]}" \
  -filter_complex "$FILTER" -map "[a]" -ar 48000 -ac 2 -c:a pcm_s16le "$TMP/raw.wav"

# 同时留一份 mp3 备份（TTS 原始响度，便于以后换标准重做）
ffmpeg -hide_banner -loglevel error -y -i "$TMP/raw.wav" -c:a libmp3lame -b:a 192k "$RAW"

# ---- 第一遍：测量 ----
echo "[1/2] 测量响度..."
MEASURE=$(ffmpeg -hide_banner -i "$TMP/raw.wav" \
  -af loudnorm=I=-16:TP=-1.5:LRA=7:print_format=json \
  -f null /dev/null 2>&1 | tail -14)

get() { echo "$MEASURE" | grep "\"$1\"" | sed -E 's/.*: *"([^"]*)".*/\1/'; }

I=$(get input_i); TP=$(get input_tp); LRA=$(get input_lra)
TH=$(get input_thresh); OFF=$(get target_offset)

echo "      测得 I=${I} LUFS  TP=${TP} dBTP  LRA=${LRA}  offset=${OFF}"

# ---- 第二遍：应用（线性增益 + 尾部静音补齐到视频长度）----
echo "[2/2] 应用线性增益 → $OUT"
ffmpeg -hide_banner -loglevel error -y -i "$TMP/raw.wav" \
  -af "loudnorm=I=-16:TP=-1.5:LRA=7:measured_I=${I}:measured_TP=${TP}:measured_LRA=${LRA}:measured_thresh=${TH}:offset=${OFF}:linear=true,apad" \
  -t "$VIDEO_DUR" -ar 48000 -ac 2 -c:a aac -b:a 320k "$OUT"

RESULT=$(ffmpeg -hide_banner -i "$OUT" -af ebur128=framelog=quiet -f null /dev/null 2>&1 \
  | grep 'I:' | head -1 | tr -s ' ')
echo "完成: $OUT  对齐时长 ${VIDEO_DUR}s  ${RESULT}"
