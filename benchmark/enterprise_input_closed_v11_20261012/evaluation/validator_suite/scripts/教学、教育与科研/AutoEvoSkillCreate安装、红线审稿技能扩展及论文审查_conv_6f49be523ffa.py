"""AutoEvoSkillCreate安装、红线审稿技能扩展及论文审查: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_6f49be523ffa'
CONTRACT_SHA256 = '3d5d87d0e9b068dac8dde458edc535ceab08dd3f7acf16b5b4db28b6f22f2cf8'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
