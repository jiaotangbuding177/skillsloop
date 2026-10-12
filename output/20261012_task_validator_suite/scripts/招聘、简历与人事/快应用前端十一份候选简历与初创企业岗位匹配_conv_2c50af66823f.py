"""快应用前端十一份候选简历与初创企业岗位匹配: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_2c50af66823f'
CONTRACT_SHA256 = '14e5b3defec30423e57b5886c0df9c9eb505be6c17913616071a4e5e371b93e4'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
