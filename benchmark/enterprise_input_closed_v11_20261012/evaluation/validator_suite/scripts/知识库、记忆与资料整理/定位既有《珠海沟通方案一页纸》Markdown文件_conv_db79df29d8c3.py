"""定位既有《珠海沟通方案一页纸》Markdown文件: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_db79df29d8c3'
CONTRACT_SHA256 = '7f620fba7066d1482c9938b72130c54dd466cecc3a3208eaf68beaa97ccbd31d'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
