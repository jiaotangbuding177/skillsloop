"""优化简历并融入学校岗位价值说明、生成PDF保存学生资料: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_343600b6d59a'
CONTRACT_SHA256 = '49da026eb3b6b38ef852bfa8feba1e472cae9afc2a02424926a36c1197d0ec9f'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
