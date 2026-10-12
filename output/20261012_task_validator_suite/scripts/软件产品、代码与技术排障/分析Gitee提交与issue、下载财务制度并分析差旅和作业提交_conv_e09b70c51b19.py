"""分析Gitee提交与issue、下载财务制度并分析差旅和作业提交: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_e09b70c51b19'
CONTRACT_SHA256 = '60aa141109669cc53ecf8bd8f58655f87fa07e72de1c064ba7eedb1215b8d855'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
