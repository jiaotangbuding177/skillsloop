"""制作用户反馈及研发关联分析文档、Excel和能力技能: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_edc9bbda3d45'
CONTRACT_SHA256 = '004ca58ffca057725ee17910da78c5986d5009ed9a1e45b85ddda3d478614d5f'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
