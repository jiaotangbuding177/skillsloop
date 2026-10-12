"""小红书餐厅食物地址及近六个月评论提取与浏览技能查询: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_cedd7472177e'
CONTRACT_SHA256 = 'f1775576c337dfc0e27801466fc5b4f9f7f0a66fe832dddaebf5787d8a355a19'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
