"""SpeedBot投资BP迭代、补充材料整合与真实性分析: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_b6f82f7b4d96'
CONTRACT_SHA256 = '916aa25b33da6ce5c4e0839067d614a7700a0cde11f6f4b61afde0214727dea1'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
