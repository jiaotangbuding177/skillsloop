"""汇总Gitee代码贡献为新版文件并提供工作计划与图片地点说明: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_589e599dc77a'
CONTRACT_SHA256 = '20b56184436a34ae829629e25626971ea5b76c7399724bf42b05d37cfb08b936'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
