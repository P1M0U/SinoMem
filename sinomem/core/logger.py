"""结构化日志模块（基于 loguru）

不修改 loguru 全局配置（保留宿主进程的自定义 handler），
仅通过 bind 在日志中标注来源模块。
"""

from contextlib import contextmanager

from loguru import logger


def get_logger(name: str = "sinomem"):
    """获取 loguru logger（绑定来源模块名，便于过滤）"""
    return logger.bind(module=name)


@contextmanager
def timed(logger, label: str):
    """上下文管理器：记录操作耗时（INFO 级别）

    用法:
        with timed(logger, "keyword_search"):
            results = self._keyword_search(query, limit)
    """
    import time

    start = time.perf_counter()
    yield
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info("{} took {:.1f} ms", label, elapsed_ms)
