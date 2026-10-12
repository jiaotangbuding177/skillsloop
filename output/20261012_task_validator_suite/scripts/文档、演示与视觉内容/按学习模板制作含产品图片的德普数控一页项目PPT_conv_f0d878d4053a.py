"""按学习模板制作含产品图片的德普数控一页项目PPT: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_f0d878d4053a'
CONTRACT_SHA256 = '3b9fb3ce0610410f3b676c9c1ee0173ffd66dc34fa4cbf40cb4fe9a95dbc408d'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
