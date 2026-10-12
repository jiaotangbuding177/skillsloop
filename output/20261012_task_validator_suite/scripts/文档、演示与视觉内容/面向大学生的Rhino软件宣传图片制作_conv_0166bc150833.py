"""面向大学生的Rhino软件宣传图片制作: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_0166bc150833'
CONTRACT_SHA256 = '71f630e2df1221c5b604c28c977211f2c1746d7c91d6d30d88c7e32cd8daed15'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
