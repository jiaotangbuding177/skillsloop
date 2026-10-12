"""美鲸灵投资考察、企业人物查询、照片及录音会议纪要: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_19d90530d45a'
CONTRACT_SHA256 = '0656ef2b0ee8e08424ca529f4659ba659e09c92d90c4fef894fd5cd28d3dd380'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
