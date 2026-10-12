"""结合产品介绍图形成EvoMind销售建议: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_59024c2ff574'
CONTRACT_SHA256 = '0799ca0744497960fc4bc23da0505bf0843de3ce4b14b7adee1d96028a81523d'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
