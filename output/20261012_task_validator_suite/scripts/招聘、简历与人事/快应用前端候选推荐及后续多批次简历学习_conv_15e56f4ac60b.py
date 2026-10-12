"""快应用前端候选推荐及后续多批次简历学习: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_15e56f4ac60b'
CONTRACT_SHA256 = '8ea9c311f5f0a7da00ed4aaa684b9ff83d1fd196e20671aca76ed81051d91219'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
