"""中航通用商业计划与民用业务的一级市场投资分析维度: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_0e3d37287c9d'
CONTRACT_SHA256 = '982cf31266b62f347520201a227593fb28d08131d46e0659689205b7fd17621b'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
