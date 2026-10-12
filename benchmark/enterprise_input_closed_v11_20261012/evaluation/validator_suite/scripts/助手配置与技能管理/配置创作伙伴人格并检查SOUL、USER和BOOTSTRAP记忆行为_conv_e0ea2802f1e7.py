"""配置创作伙伴人格并检查SOUL、USER和BOOTSTRAP记忆行为: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_e0ea2802f1e7'
CONTRACT_SHA256 = '8c58afa2a1044f1b523bb33081b61002b7b0b1ff205b02d9398d7c1f64704759'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
