"""集中配置管理 — 支持环境变量覆盖"""

import os
from pathlib import Path

# 数据库默认路径（可通过 SINOMEM_DB_PATH 环境变量覆盖）
DEFAULT_DB_PATH = Path(
    os.environ.get(
        "SINOMEM_DB_PATH", str(Path.home() / ".sinomem" / "memory.db")
    )
)

# 嵌入模型默认路径（可通过 SINOMEM_MODEL_DIR 环境变量覆盖）
# core/config.py -> core/ -> sinomem/ -> 项目根
_DEFAULT_MODEL_DIR = (
    Path(__file__).parent.parent.parent / "models" / "embedding"
)
DEFAULT_MODEL_DIR = Path(
    os.environ.get("SINOMEM_MODEL_DIR", str(_DEFAULT_MODEL_DIR))
)
