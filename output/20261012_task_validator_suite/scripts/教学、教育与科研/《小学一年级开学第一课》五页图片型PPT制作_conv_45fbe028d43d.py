"""《小学一年级开学第一课》五页图片型PPT制作: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_45fbe028d43d'
CONTRACT_SHA256 = 'b7c3e877fdd2b1ac104e09e026b7a3e6ca67bc3650343498ebd79398af53a592'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
