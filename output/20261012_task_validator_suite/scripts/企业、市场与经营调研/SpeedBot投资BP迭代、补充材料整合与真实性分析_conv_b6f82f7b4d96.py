"""SpeedBot投资BP迭代、补充材料整合与真实性分析: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_b6f82f7b4d96'
CONTRACT_SHA256 = 'b8c0ecbca97b7b206a2945377b88e6e36a78bc6bd46c334cdb492c266d643b76'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
