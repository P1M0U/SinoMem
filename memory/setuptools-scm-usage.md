---
name: setuptools-scm-usage
description: 项目使用 setuptools-scm 自动管理版本号的方法
metadata:
  type: project
---

## setuptools-scm 版本管理

本项目已引入 `setuptools-scm`，版本号唯一来源是 Git tag，无需手动修改任何文件。

### 发版流程

```bash
# 1. 确保当前代码已提交
git status

# 2. 打 tag（这是唯一需要做的）
git tag v0.7.0 -m "v0.7.0: 版本说明"
git push origin main --tags
git push gitee main --tags

# 完成！无需修改 pyproject.toml 或 __init__.py
```

### 版本号规则

| Git 状态 | 生成的版本号 |
|----------|-------------|
| HEAD 正好是 tag `v0.6.0` | `0.6.0` |
| tag `v0.6.0` 之后 + 3 个 commit | `0.6.1.dev3` |
| 有未提交的修改 | `0.6.1.dev3+d20260707` |

### 实现细节

- `pyproject.toml`: `version` 声明为 `dynamic`，由 `setuptools-scm` 在构建时注入
- `build-system.requires`: 包含 `setuptools>=64` 和 `setuptools-scm>=8`
- `agent_memory_lite/__init__.py`: 通过 `importlib.metadata.version("agent-memory-lite")` 读取运行时版本，未安装时降级为 `"0.0.0.dev0"`
- `[tool.setuptools.packages.find]` 配置 `include = ["agent_memory_lite*"]` 避免误包含 `dicts/`、`hermes_plugin/` 等非包目录

### 注意事项

- **发版前必须先提交所有改动**，否则版本号会带脏标记
- tag 必须以 `v` 开头（如 `v0.7.0`）
- 从 `v0.6.0` tag 之后第一次引入，当前开发版本自动显示为 `0.6.1.dev0+gXXXXXXX`
- `setuptools-scm` 是构建时依赖，运行时通过 `importlib.metadata` 读取已注入的版本号，不依赖 git
