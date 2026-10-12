"""分析Gitee提交与issue、下载财务制度并分析差旅和作业提交: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_e09b70c51b19'
CONTRACT_SHA256 = '9246f1824d58d1594c2cc3abd40c9899fb5934b076645d9d9fe4c1d0b752215d'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
