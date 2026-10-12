"""未来产业合伙人第一批延续资助申请表填写: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_bf4371170343'
CONTRACT_SHA256 = '90d3b3ace25f6ba4b21868fad189b368b3672d94421ca3fc33b294528872e627'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
