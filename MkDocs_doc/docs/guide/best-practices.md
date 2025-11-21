# Python 风格基线

## 命名与结构

- 模块/包：`snake_case`，避免缩写；类：`PascalCase`；常量：`ALL_CAPS`。
- 单文件长度建议 < 400 行，逻辑块拆分为函数或 dataclass。
- 业务常量集中到 `settings.py` 或 `conf/`，便于 mkdocstrings 统一引用。

## 异常与日志

- 捕获具体异常类型，避免裸 `except`。
- 统一使用 `structlog`/`logging`，追加 `extra={"project": "...", "trace_id": ...}` 方便检索。
- 在 Pipeline/Spider/Task 层抛出自定义异常，结合 [日志与监控指南](../operations/logging-monitoring.md) 统计。

## 文档与注释

- 所有公共函数/类必须具备 Google/NumPy 风格 docstring，可复用 [Docstring 标准](mkdocstrings-comments.md) 示例。
- 模块级别提供「用途 + 依赖 + 示例」，方便 mkdocstrings 渲染根目录摘要。
- 复杂流程使用 Mermaid 或时序图辅助说明。

## 测试与质量

- 单元测试并入 `tests/`，命名为 `test_<module>.py`，断言覆盖主干逻辑与边界。
- 关键模块启用 `pytest --maxfail=1 --durations=10`，结合 CI 阶段的缓存策略。
- 对外接口变更必须附带示例/契约更新，保持文档与代码同步。

## 自动化检查

1. `pre-commit` 默认包含 `black`, `isort`, `flake8`, `mypy`, `codespell`。
2. 提交前运行 `pre-commit run --all-files`，CI 失败则禁止合并。
3. 对格式化敏感的 Markdown/JSON/YAML 建议启用 `mdformat`、`yamlfmt` 钩子。

> 以上约定与 [工具链集成指南](../standards/tooling.md) 配套，必要时可在项目级别追加更严格规则。

