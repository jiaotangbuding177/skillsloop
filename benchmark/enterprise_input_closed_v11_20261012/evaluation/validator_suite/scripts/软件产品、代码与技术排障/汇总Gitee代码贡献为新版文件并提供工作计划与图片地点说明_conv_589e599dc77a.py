"""汇总Gitee代码贡献为新版文件并提供工作计划与图片地点说明: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_589e599dc77a'
CONTRACT_SHA256 = 'ac44d0ac760c53dd4ff231208493d207706d93ab54c5728871a1b705a692930b'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
