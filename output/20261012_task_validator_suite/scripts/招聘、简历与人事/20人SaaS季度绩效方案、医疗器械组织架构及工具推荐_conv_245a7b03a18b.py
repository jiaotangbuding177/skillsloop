"""20人SaaS季度绩效方案、医疗器械组织架构及工具推荐: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_245a7b03a18b'
CONTRACT_SHA256 = 'b73b365eceed90cc048ac0dfc4c46efbb1bd2ba51db5b5f1c974578c2872f9ad'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
