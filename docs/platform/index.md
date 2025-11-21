# 项目结构与公共组件库

## 目标

- 输出统一的项目骨架，降低新项目初始化成本。
- 维护可复用的组件清单，涵盖采集、清洗、存储、监控等环节。
- 将项目文档纳入同一导航体系，保证路径一致。

## 快速导航

| 内容 | 文件 |
| --- | --- |
| 标准目录模板 | [PROJECT_STRUCTURE.md](../guide/PROJECT_STRUCTURE.md) |
| 公共组件文档 | [components.md](components.md) |
| 项目资产入口 | [项目文档首页](../projects/index.md) |

## 如何使用

1. 按模板创建 `src/`, `tests/`, `docs/` 等目录，并补齐 `pyproject.toml`、`pre-commit`。
2. 若组件被多个项目共享，将实现代码放入 `code_liu/common` 或独立包，并在 `components.md` 补充 API。
3. 更新项目文档时，确保 `projects/<name>/` 同步新增/调整对应章节。

!!! tip
    组件/模板的新增或重大调整需同步「实施路线图」与「更新日志」，方便回溯。

