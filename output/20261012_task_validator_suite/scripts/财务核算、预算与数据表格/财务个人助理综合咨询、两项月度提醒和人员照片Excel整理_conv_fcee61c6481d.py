"""财务个人助理综合咨询、两项月度提醒和人员照片Excel整理: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_fcee61c6481d'
CONTRACT_SHA256 = 'e01a1f3024b662b4386d5bb1f7136a4e489e51cfd8c5840b1e7f8be618b675ed'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
