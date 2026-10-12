"""美鲸灵、冰美肌及中科芯飞部门岗位说明系列Word: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_bf54448ce875'
CONTRACT_SHA256 = 'd664bdffe4b25e9fe5b92c0bffbd592b391453825d42aa7e0917400b3ac1dd8d'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
