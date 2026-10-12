"""英特尔CNDA签署人风险评估（会话e3d8）: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_e3d8dd0683ed'
CONTRACT_SHA256 = 'a608c3f6a1c13077dd13d62de6284f8babeb3f7eea2f017058fd14ba07f25c12'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
