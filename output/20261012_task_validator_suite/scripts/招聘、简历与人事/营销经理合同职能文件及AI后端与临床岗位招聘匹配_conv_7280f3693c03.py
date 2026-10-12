"""营销经理合同职能文件及AI后端与临床岗位招聘匹配: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_7280f3693c03'
CONTRACT_SHA256 = 'f252c1e402ee689c39b74ef20cf8f13949cff37c869c5d2c854f3984037b2782'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
