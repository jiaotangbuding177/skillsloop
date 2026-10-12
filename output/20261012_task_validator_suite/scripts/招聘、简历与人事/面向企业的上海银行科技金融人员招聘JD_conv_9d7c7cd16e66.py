"""面向企业的上海银行科技金融人员招聘JD: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_9d7c7cd16e66'
CONTRACT_SHA256 = '6c6a87e888741d873af64252c0eb9b9823fdd4373c986a06e6ab183c5c450506'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
