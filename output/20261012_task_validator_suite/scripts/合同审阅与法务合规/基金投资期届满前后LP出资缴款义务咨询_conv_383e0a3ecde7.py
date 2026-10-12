"""基金投资期届满前后LP出资缴款义务咨询: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_383e0a3ecde7'
CONTRACT_SHA256 = '78d778e33aa1515832c6cbee743db49357eb37e8ff56457f5d10473ca8f49c97'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
