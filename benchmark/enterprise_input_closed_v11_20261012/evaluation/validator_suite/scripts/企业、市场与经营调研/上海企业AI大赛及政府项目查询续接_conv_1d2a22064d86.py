"""上海企业AI大赛及政府项目查询续接: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_1d2a22064d86'
CONTRACT_SHA256 = '8d0239f6ff0bb15aba4ddfd580d84574b779e0811a4553e125a4c4bb964b3f41'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
