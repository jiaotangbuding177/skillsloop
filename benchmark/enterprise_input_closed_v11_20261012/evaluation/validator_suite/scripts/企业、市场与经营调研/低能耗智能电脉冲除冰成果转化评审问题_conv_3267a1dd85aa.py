"""低能耗智能电脉冲除冰成果转化评审问题: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_3267a1dd85aa'
CONTRACT_SHA256 = 'e7dc494abde7e33dc097cddd832bf9a041a1c04814def7ddd5076e06a94fef85'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
