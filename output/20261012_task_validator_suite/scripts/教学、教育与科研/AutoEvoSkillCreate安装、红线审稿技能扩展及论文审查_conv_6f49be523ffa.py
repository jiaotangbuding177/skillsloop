"""AutoEvoSkillCreate安装、红线审稿技能扩展及论文审查: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_6f49be523ffa'
CONTRACT_SHA256 = 'a147e01e3b812fa6c9692a42c2fbca34326863aa602fb68dd0ccaabd4dea50dd'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
