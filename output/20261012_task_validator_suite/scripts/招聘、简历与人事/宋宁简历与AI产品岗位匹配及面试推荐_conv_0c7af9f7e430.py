"""宋宁简历与AI产品岗位匹配及面试推荐: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_0c7af9f7e430'
CONTRACT_SHA256 = 'ea87e56342e033a9ca93ed6dda32f26f8984c9a3e4fa89f6d6f722dd929d7e3d'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
