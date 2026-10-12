"""南京航空航天大学十一项成果的投资孵化价值比较: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_61d7cc938e6d'
CONTRACT_SHA256 = '917a91fc1ab4b708e895982f0f74b1d31a406cbdec3f4a50e1ef00dc721c1f0f'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
