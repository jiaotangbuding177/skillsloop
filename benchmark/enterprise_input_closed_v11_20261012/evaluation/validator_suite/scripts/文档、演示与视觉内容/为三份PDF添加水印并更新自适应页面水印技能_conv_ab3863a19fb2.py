"""为三份PDF添加水印并更新自适应页面水印技能: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_ab3863a19fb2'
CONTRACT_SHA256 = '09455fca1b53883477d8d3c498276afc06d0a96f06fe2054766aae2eb15cdd2f'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
