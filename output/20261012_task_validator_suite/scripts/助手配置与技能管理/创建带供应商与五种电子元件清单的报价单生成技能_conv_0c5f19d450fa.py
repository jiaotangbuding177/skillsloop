"""创建带供应商与五种电子元件清单的报价单生成技能: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_0c5f19d450fa'
CONTRACT_SHA256 = '94f391510b5eb6c8adb9aa1eb6491ec340bf3098c72da55581fcd75bdb9872f1'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
