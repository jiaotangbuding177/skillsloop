"""将EvoMind企业案例ZIP解压到AI工作区顶层: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_bb5e39c2a2aa'
CONTRACT_SHA256 = '6209f6fa82076a0495ec0363c61bfe82540b60d65ca324c003ca22ce8e25214d'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
