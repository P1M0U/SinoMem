"""Hermes 插件发现锚点 — ⚠️ 本文件及 plugin.yaml 不可删除

Hermes 通过扫描本目录下的 plugin.yaml 发现并加载插件。
所有业务逻辑请修改 sinomem/plugins/hermes/provider.py。

这个双轨结构的原因：
- hermes_plugin/ = Hermes 的插件发现入口（目录扫描 + plugin.yaml）
- sinomem/plugins/hermes/ = 业务逻辑（pip 可安装的包内路径）
"""

from sinomem.plugins.hermes.provider import (
    SinoMemProvider,
    register,
)

__all__ = ["SinoMemProvider", "register"]
