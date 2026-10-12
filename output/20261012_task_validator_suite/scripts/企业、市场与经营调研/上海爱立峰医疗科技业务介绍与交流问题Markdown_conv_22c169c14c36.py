"""上海爱立峰医疗科技业务介绍与交流问题Markdown: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_22c169c14c36'
CONTRACT_SHA256 = '90b02a78d9d47f0f7ee50fecb2fca0d2c55ac931d56e35d3f481fde2008d9151'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
