"""启东成果转化介绍、十页政府汇报图片及产业Word报告: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_8dbc2e14c3fc'
CONTRACT_SHA256 = '045139e98c44b033654b3f7f5e4562fed6e532a75b6dd0f391c6b9aa196490e9'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
