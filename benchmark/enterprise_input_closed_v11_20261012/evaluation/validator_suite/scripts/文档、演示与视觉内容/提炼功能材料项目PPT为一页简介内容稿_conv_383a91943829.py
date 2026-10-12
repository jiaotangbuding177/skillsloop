"""提炼功能材料项目PPT为一页简介内容稿: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_383a91943829'
CONTRACT_SHA256 = '2be8b0ed61f0581d8ce057d17617276ed99caa4a9943543a098620ed8d2bd549'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
