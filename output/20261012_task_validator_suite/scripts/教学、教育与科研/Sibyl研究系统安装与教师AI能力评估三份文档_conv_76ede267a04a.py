"""Sibyl研究系统安装与教师AI能力评估三份文档: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_76ede267a04a'
CONTRACT_SHA256 = 'b8d03f8cf25a981447de784a6be7f39511548c062ba696fbcd0190f850b65152'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
