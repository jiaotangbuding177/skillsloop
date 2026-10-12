"""云知师AI与EvoMind发展方案文件、业务记忆及网班调研: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_4be7342d0195'
CONTRACT_SHA256 = 'bdcb2b10f4784bf106610cfd8dd7987fcea6ad7eb8c9ae1f709d01de8a0d0d32'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
