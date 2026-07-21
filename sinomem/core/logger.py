"""结构化日志模块"""

import logging
import time
from contextlib import contextmanager


def get_logger(name: str = "sinomem") -> logging.Logger:
    """获取模块级 logger（INFO 级别，格式含时间戳）"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


@contextmanager
def timed(logger: logging.Logger, label: str):
    """上下文管理器：记录操作耗时（INFO 级别）

    用法:
        with timed(logger, "keyword_search"):
            results = self._keyword_search(query, limit)
    """
    start = time.perf_counter()
    yield
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info("%s took %.1f ms", label, elapsed_ms)
