"""两条Bilibili视频学习型PPT大纲及时间分段: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_c86b3a8429e4'
CONTRACT_SHA256 = '0608e157641d3f105131ecb2441e0fcb1c7ce7ecc425531f3d6bfc63770aba4a'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
