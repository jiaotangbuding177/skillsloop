"""在Gitee创建并分配给张文的测试任务: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_002ae6938a37'
CONTRACT_SHA256 = '94dd863c8ecb1021babdc125358a36fc723faa650af009797643a762dcf1d614'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
