"""按攻防箭八片段分镜生成并修订4K高清图片: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_a196d952691c'
CONTRACT_SHA256 = '2882dd43f0917c4a181473f0f36e465affb9aead3a43d48ee9296ae1f2056aa1'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
