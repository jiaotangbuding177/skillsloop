"""制作用户反馈及研发关联分析文档、Excel和能力技能: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_edc9bbda3d45'
CONTRACT_SHA256 = '5ab52af541e93334ebd20553df3c01042fe1cbb05198284c5311764c672d37f7'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
