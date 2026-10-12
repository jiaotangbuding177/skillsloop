"""信托股票质押融资增持、场内场外差异及监管依据咨询: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_e3ba4e591e36'
CONTRACT_SHA256 = '0b6c4e5e79df460fc518bef6ab5ada4285fc8c530db5b53d085400a2b4289219'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
