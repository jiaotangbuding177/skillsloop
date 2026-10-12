"""华师大商鹏程猫传腹免疫治疗项目商业价值分析: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_07d2d9c4266f'
CONTRACT_SHA256 = '9e88d9cd8cdadef3ffcb2d4c21a6b1bed71c06a86f20b41a7376a5acfff9adbb'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
