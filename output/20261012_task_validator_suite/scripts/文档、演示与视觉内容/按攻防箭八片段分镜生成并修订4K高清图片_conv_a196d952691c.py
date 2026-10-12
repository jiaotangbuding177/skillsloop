"""按攻防箭八片段分镜生成并修订4K高清图片: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_a196d952691c'
CONTRACT_SHA256 = '83d34b042d2586a48110ddc2070cd3d70c58ac403f563bd9871dcc702c86f9d9'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
