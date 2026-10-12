"""云知师AI与EvoMind发展方案文件、业务记忆及网班调研: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_4be7342d0195'
CONTRACT_SHA256 = 'f7a718135d7d27f5a99f9ef1c50a2c8213c250f86b4731ece4967c0d4eb10c64'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
