"""集中配置管理"""

from pathlib import Path

# 数据库默认路径
DEFAULT_DB_PATH = Path.home() / ".agent-memory" / "memory.db"

# 嵌入模型默认路径
# core/config.py -> core/ -> agent_memory_lite/ -> 项目根
DEFAULT_MODEL_DIR = (
    Path(__file__).parent.parent.parent / "models" / "embedding"
)

# 搜索默认参数
DEFAULT_SEARCH_LIMIT = 5
DEFAULT_KEYWORD_WEIGHT = 0.4
