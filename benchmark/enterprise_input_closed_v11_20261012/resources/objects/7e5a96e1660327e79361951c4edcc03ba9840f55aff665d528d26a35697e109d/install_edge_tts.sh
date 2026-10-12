#!/usr/bin/env bash
# 安装/复用 Edge TTS 环境（优先虚拟环境，不破坏系统 Python）。
# 用法: bash install_edge_tts.sh [venv_dir]
# 行为:
#   1. 已可用则直接退出成功（不重复安装）
#   2. 使用项目级/用户级虚拟环境（默认 .venv-tts）
#   3. 不修改系统 Python、不修改任何系统安全配置
set -u

VENV_DIR="${1:-.venv-tts}"
PYPI_MIRROR="${PYPI_MIRROR:-}"   # 可选: https://pypi.tuna.tsinghua.edu.cn/simple

say() { printf '%s\n' "$*"; }

# 1) 检测已安装
if command -v edge-tts >/dev/null 2>&1; then
  say "[OK] edge-tts 已可用: $(edge-tts --version 2>/dev/null)"
  exit 0
fi
if python3 -c "import edge_tts" >/dev/null 2>&1; then
  say "[OK] edge_tts 模块已可用 (系统 python3)"
  exit 0
fi
if [ -x "$VENV_DIR/bin/edge-tts" ]; then
  say "[OK] edge-tts 已可用: $VENV_DIR/bin/edge-tts $($VENV_DIR/bin/edge-tts --version 2>/dev/null)"
  exit 0
fi

say "[..] 未检测到 edge-tts，准备安装到虚拟环境: $VENV_DIR"

# 2) 创建虚拟环境（兼容无 ensurepip 的 Debian 系统）
if [ ! -x "$VENV_DIR/bin/python" ]; then
  if python3 -m venv "$VENV_DIR" 2>/dev/null; then
    say "[OK] venv 创建成功: $VENV_DIR"
  else
    say "[..] venv 缺少 ensurepip，使用 --without-pip 创建并引导安装 pip"
    python3 -m venv --without-pip "$VENV_DIR" || { say "[ERR] venv 创建失败"; exit 1; }
    GETPIP="$VENV_DIR/get-pip.py"
    curl -fsSL --max-time 120 -o "$GETPIP" https://bootstrap.pypa.io/get-pip.py \
      || curl -fsSL --max-time 120 -o "$GETPIP" https://mirrors.aliyun.com/pypi/get-pip.py \
      || { say "[ERR] get-pip.py 下载失败"; exit 1; }
    PIP_ARGS=()
    [ -n "$PYPI_MIRROR" ] && PIP_ARGS+=("-i" "$PYPI_MIRROR")
    "$VENV_DIR/bin/python" "$GETPIP" --quiet "${PIP_ARGS[@]}" || { say "[ERR] pip 引导安装失败"; exit 1; }
  fi
fi

# 3) 安装 edge-tts
PIP_ARGS=()
[ -n "$PYPI_MIRROR" ] && PIP_ARGS+=("-i" "$PYPI_MIRROR")
if ! "$VENV_DIR/bin/pip" install --quiet edge-tts "${PIP_ARGS[@]}"; then
  # 兜底: 尝试默认 PyPI
  "$VENV_DIR/bin/pip" install --quiet edge-tts || { say "[ERR] edge-tts 安装失败"; exit 1; }
fi

# 4) 最小中文语音测试
say "[..] 运行最小中文配音测试..."
if "$VENV_DIR/bin/edge-tts" \
  --voice zh-CN-XiaoxiaoNeural \
  --text "这是一段人工智能视频配音测试。" \
  --write-media /tmp/remotion-tts-test.mp3 >/dev/null 2>&1 \
  && [ -s /tmp/remotion-tts-test.mp3 ]; then
  say "[OK] Edge TTS 安装并测试通过: $VENV_DIR/bin/edge-tts ($($VENV_DIR/bin/edge-tts --version 2>/dev/null))"
  rm -f /tmp/remotion-tts-test.mp3
  exit 0
fi

say "[ERR] edge-tts 安装完成但测试失败，请检查网络（需可访问 speech.platform.bing.com）"
exit 1
