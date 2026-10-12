"""IMA全部笔记导入工作区并保存暂停进度: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_24bc635473a8'
CONTRACT_SHA256 = 'be34c1e0b49f44fe98a77cc597d9d7866ceb6e714b4c23f3fa3dfa699416c0eb'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
