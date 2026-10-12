"""食品与益生菌目录、痛风活菌药推进及会话总结: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_5138176e8aae'
CONTRACT_SHA256 = 'fa6be5cb9e9dd835bc23049008d8f27f9bf951d7eb8b47aff7a3589c479d582a'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
