"""提炼功能材料项目PPT为一页简介内容稿: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_383a91943829'
CONTRACT_SHA256 = '6ba2bea6a77e91380dac87f49958662ab1274126505488b2f01d05296d8d76e3'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
