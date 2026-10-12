"""配置创作伙伴人格并检查SOUL、USER和BOOTSTRAP记忆行为: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_e0ea2802f1e7'
CONTRACT_SHA256 = '5a0edd94047ab5ffdadbe132815392491958a2be8d96bc17087e0062a5eb9156'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
