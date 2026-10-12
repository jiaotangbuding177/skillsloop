#!/usr/bin/env bash
# 检查视频生成所需的环境组件，输出状态表。只读检查，不做任何修改。
set -u

echo "=== AI Video Production Environment Check ==="

check() { # name, cmd...
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then echo "  [OK]   $name"; else echo "  [MISS] $name"; fi
}

echo "--- Core ---"
check "node"            node --version
check "npm"             npm --version
check "git"             git --version
check "python3"         python3 --version

echo "--- Browser (Remotion render) ---"
if [ -n "${CHROME_PATH:-}" ]; then
  echo "  [ENV]  CHROME_PATH=${CHROME_PATH}"
fi
for c in /usr/bin/chromium /usr/bin/chromium-browser /usr/bin/google-chrome /usr/bin/google-chrome-stable; do
  [ -x "$c" ] && { echo "  [OK]   chromium: $c"; CHROME_FOUND=1; break; }
done
[ -n "${CHROME_FOUND:-}" ] || echo "  [MISS] chromium (set CHROME_PATH to use a custom browser)"

echo "--- AI Image ---"
if [ -n "${IMAGE_API_KEY:-}" ]; then
  echo "  [OK]   IMAGE_API_KEY set (${#IMAGE_API_KEY} chars)"
elif [ -n "${ZZZ4AI_IMAGE_KEY:-}" ]; then
  echo "  [OK]   ZZZ4AI_IMAGE_KEY set (${#ZZZ4AI_IMAGE_KEY} chars, zzz4ai provider)"
else
  echo "  [MISS] IMAGE_API_KEY (AI image generation will be unavailable)"
fi
echo "  (endpoint: ${IMAGE_API_URL:-https://llmapi.zzz4ai.com/v1/images/generations})"

echo "--- TTS (Edge TTS) ---"
TTS_PY="${TTS_PYTHON:-}"
if [ -n "${TTS_PYTHON:-}" ]; then
  echo "  [ENV]  TTS_PYTHON=${TTS_PYTHON}"
  if "$TTS_PYTHON" -c "import edge_tts" >/dev/null 2>&1; then
    echo "  [OK]   edge_tts module (via TTS_PYTHON)"
  else
    echo "  [MISS] edge_tts module in TTS_PYTHON"
  fi
else
  if command -v edge-tts >/dev/null 2>&1; then
    echo "  [OK]   edge-tts CLI: $(edge-tts --version 2>/dev/null)"
  elif python3 -c "import edge_tts" >/dev/null 2>&1; then
    echo "  [OK]   edge_tts module (system python3)"
  elif [ -x .venv-tts/bin/edge-tts ]; then
    echo "  [OK]   edge-tts CLI: .venv-tts/bin/edge-tts $(.venv-tts/bin/edge-tts --version 2>/dev/null)"
  else
    echo "  [MISS] edge-tts (run scripts/install_edge_tts.sh)"
  fi
fi

echo "--- Audio/Video utilities ---"
check "ffprobe (optional)" ffprobe --version
check "ffmpeg  (optional)" ffmpeg -version

echo "--- Fonts (Chinese) ---"
if command -v fc-list >/dev/null 2>&1 && fc-list 2>/dev/null | grep -qiE "cjk|noto sans sc|noto serif sc|wqy"; then
  echo "  [OK]   CJK fonts"
else
  echo "  [MISS] CJK fonts (Chinese text may render as boxes)"
fi
