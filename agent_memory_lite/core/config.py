"""集中配置管理 — 支持环境变量覆盖"""

import os
from pathlib import Path

# 数据库默认路径（可通过 AML_DB_PATH 环境变量覆盖）
DEFAULT_DB_PATH = Path(
    os.environ.get(
        "AML_DB_PATH", str(Path.home() / ".agent-memory" / "memory.db")
    )
)

# 嵌入模型默认路径（可通过 AML_MODEL_DIR 环境变量覆盖）
# core/config.py -> core/ -> agent_memory_lite/ -> 项目根
_DEFAULT_MODEL_DIR = (
    Path(__file__).parent.parent.parent / "models" / "embedding"
)
DEFAULT_MODEL_DIR = Path(
    os.environ.get("AML_MODEL_DIR", str(_DEFAULT_MODEL_DIR))
)
