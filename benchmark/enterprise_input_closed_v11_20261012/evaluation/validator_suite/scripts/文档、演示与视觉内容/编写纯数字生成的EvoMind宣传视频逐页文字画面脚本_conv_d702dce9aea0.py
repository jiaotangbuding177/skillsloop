"""编写纯数字生成的EvoMind宣传视频逐页文字画面脚本: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_d702dce9aea0'
CONTRACT_SHA256 = 'b5e464227e7630abb80bb17f9bae5d312f48aa6a87dd360ed4b0b1c918375c07'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
