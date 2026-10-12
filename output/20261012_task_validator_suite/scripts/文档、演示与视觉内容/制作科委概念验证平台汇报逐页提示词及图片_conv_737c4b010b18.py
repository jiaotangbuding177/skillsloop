"""制作科委概念验证平台汇报逐页提示词及图片: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_737c4b010b18'
CONTRACT_SHA256 = '49ec261cbc2e04fed37b104bb1b42520b465fa33dfe4d2e22fcc4fca4c03c021'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
