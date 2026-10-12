"""Anisoprint股权转让协议出让方审阅与关键内容总结: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_512bed807235'
CONTRACT_SHA256 = 'cfd8e4a40c0786399580bdd8fc64bf27a7881c9600719c620e5c4066be573feb'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
