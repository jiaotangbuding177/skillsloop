"""盈石兄弟AI音乐项目真实性与投资可行性咨询: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_89047a8a2890'
CONTRACT_SHA256 = 'c9023266a296bd79c90eaac35751a24c3adc77e7c4453617d877a2124e0084c5'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
