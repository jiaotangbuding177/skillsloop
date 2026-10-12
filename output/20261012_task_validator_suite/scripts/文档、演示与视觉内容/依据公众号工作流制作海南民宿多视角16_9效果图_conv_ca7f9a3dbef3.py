"""依据公众号工作流制作海南民宿多视角16:9效果图: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_ca7f9a3dbef3'
CONTRACT_SHA256 = 'e2ee21afc054c712ff93db7a44247115cf370b443fa47a821dc9f368432f468d'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
