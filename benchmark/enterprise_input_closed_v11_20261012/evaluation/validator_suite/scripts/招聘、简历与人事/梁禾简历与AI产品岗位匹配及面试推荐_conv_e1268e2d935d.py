"""梁禾简历与AI产品岗位匹配及面试推荐: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_e1268e2d935d'
CONTRACT_SHA256 = 'c22025d5a5b5a425eb4cf17d5f9a12f0aebeb16d19169f10911c4be2fc23e59f'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
