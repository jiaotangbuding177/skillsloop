"""编写纯数字生成的EvoMind宣传视频逐页文字画面脚本: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_d702dce9aea0'
CONTRACT_SHA256 = 'f8830857d6738c31901c9f895806b1945031d0831982500d59a5f83a9794b449'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
