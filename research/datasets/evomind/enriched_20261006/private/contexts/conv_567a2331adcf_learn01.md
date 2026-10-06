# Python低版本语法兼容排障

会话：conv_567a2331adcf；候选：conv_567a2331adcf:learn01

这是带上下文的学习材料，扩入消息不等于同一任务，也不是完整黄金轨迹。

可学习线索：运行环境低于Python 3.10时检查str | None等联合类型，使用typing Optional/Union等兼容写法后再验证

边界：原始时序未独立核验；附件与产物字节未提供；方法适用性及任务结果未独立验收

## 原筛选种子 · 用户

u_ea2f30c989fda051ac

你刚刚修复的脚本有 Python 3.10+ 语法兼容问题，具体是什么问题，告诉我我来修复下

## 原筛选种子 · AI

a_a45d8531581f6bcb7a

好的，刚才遇到的 Python 3.10+ 语法兼容问题主要有两个：

## 问题 1：联合类型语法 `str | None`

**原代码（Python 3.10+）：**
```python
def _call_api_sync(course: dict, material: str | None, preference: str | None) -> dict:
```

**问题**：`str | None` 是 Python 3.10 引入的新联合类型语法，在 Python 3.9 中不支持。

**修复方案（Python 3.9 兼容）：**
```python
from typing import Optional

def _call_api_sync(course: dict, material: Optional[str], preference: Optional[str]) -> dict:
```

---

## 问题 2：泛型下标语法 `dict[str, Any]`

**原代码（Python 3.10+）：**
```python
def _build_course_args(args: argparse.Namespace) -> dict[str, Any]:
```

**问题**：`dict[str, Any]` 这种直接用内置类型做泛型下标的语法是 Python 3.9+ 支持的，但为了保险起见（以及代码中其他类似用法），最好统一用 `typing` 模块。

**修复方案（Python 3.9 兼容）：**
```python
from typing import Dict, Any

def _build_course_args(args: argparse.Namespace) -> Dict[str, Any]:
```

---

## 完整修复清单

需要修改的地方共 **5 处**：

| 行号 | 原代码 | 修复后 |
|------|--------|--------|
| imports | `from typing import Any` | `from typing import Any, Optional, Dict` |
| `_call_api_sync` 参数 | `material: str \| None, preference: str \| None` | `material: Optional[str], preference: Optional[str]` |
| `_call_api_sync` 返回 | `-> dict` | `-> Dict[str, Any]` |
| `_build_course_args` 返回 | `-> dict[str, Any]` | `-> Dict[str, Any]` |
| `_validate_course_args` 参数 | `raw: dict[str, Any]` | `raw: Dict[str, Any]` |
| `_map_course_fields` 参数/返回 | `raw: dict[str, Any] -> dict[str, Any]` | `raw: Dict[str, Any] -> Dict[str, Any]` |

---

## 修复命令

你可以用这个 sed 命令一键修复：

```bash
sed -i 's/from typing import Any/from typing import Any, Optional, Dict/g' \
     -e 's/str | None/Optional[str]/g' \
     -e 's/dict\[str, Any\]/Dict[str, Any]/g' \
     -e 's/-> dict/-> Dict[str, Any]/g' \
     /opt/openclaw-shared-skills/lesson-plan-generator/scripts/generate.py
```

或者手动编辑文件，在 `scripts/generate.py` 中：

1. 第 18 行左右，修改 import：
   ```python
   from typing import Any, Optional, Dict
   ```

2. 全局替换 `str | None` 为 `Optional[str]`

3. 全局替换 `dict[str, Any]` 为 `Dict[str, Any]`

4. 全局替换 `-> dict` 为 `-> Dict[str, Any]`

---

修复后，脚本就能在 Python 3.9 环境中正常运行了。需要我帮你直接提交修复吗？
