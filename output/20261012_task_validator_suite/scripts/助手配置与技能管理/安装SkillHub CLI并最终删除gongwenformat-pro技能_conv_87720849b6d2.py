"""安装SkillHub CLI并最终删除gongwenformat-pro技能: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_87720849b6d2'
CONTRACT_SHA256 = '369a4bd4e1bf8b36dc9da2b1c01ba69703492b0da737e353edc12d5c00556a38'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
