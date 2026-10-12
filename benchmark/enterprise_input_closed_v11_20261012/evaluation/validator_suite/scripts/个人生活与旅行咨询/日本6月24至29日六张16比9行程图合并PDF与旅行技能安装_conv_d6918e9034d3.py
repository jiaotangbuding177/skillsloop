"""日本6月24至29日六张16比9行程图合并PDF与旅行技能安装: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_d6918e9034d3'
CONTRACT_SHA256 = 'be7b45437de54d955684109f64a5e3349333e4c04124a0f06f6e2698b898e128'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
