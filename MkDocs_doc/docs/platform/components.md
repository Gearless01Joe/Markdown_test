# 公共组件文档

> 以下组件均位于 `code_liu/` 或 `src/` 目录，可通过 mkdocstrings 自动生成 API 详情。此处聚焦设计意图、依赖与常见用法。

## 数据采集层

- ### Scrapy Spider 基类

- 路径：`src/spiders/base_spider.py`
- 特性：支持自定义请求头、异常重试、代理池注入。
- 使用：项目继承后仅实现 `parse`、`build_item` 等方法即可。

- ### FieldFilter

- 路径：`src/spiders/rcsb_pdb/field_filter.py`
- 功能：在 item 输出前对字段做校验、重命名、默认值填充。
- 文档：详见 [RCSB PDB · 核心模块](../projects/rcsb_pdb/guide.md#字段过滤)。

## 数据处理层

### DataCleaner

- 路径：`code_liu/NTRT/data_cleaner.py`
- 描述：包含 `load_raw -> validate -> transform -> persist` 四阶段流水线。
- 配置：基于 `cleaning_plan` 声明任务，支持任务拆分、断点续跑。

### Pipelines

- 路径：`src/pipelines/`
- 组成：文件写入、Mongo 存储、消息推送等多条 Pipeline。
- 建议：将 I/O、序列化、重试逻辑抽出至 `mixins`，以便复用。

## 存储与抽象层

### BaseCRUD

- 路径：`code_liu/NTRT/base_mysql.py`
- 特色：封装 Session 管理、批量写入、动态路由。
- 最佳实践：结合 `session_dict` 定义多库策略，配合 `contextvars` 控制会话。

### Settings

- 路径：`src/generated/settings.md`（通过脚本生成）
- 内容：Scrapy、Playwright、Redis 等配置项，所有敏感信息需通过环境变量注入。

## 支撑工具

### generate_mkdocstrings_md.py

- 位置：`scripts/generate_mkdocstrings_md.py`
- 作用：遍历源码树，生成包含 `::: module` 的 Markdown 模板，消除手工同步成本。

### code_to_markdown.py

- 位置：`scripts/code_to_markdown.py`
- 说明：将 Python 源码转换为 Markdown，适合分享示例或教程。

## 组件接入 Checklist

1. 在 `components.md` 添加条目，描述场景、依赖、限制。
2. 若需对外开放 API，补充示例/单元测试并运行 `mkdocs build` 确认渲染。
3. 更新对应项目的 `guide.md`，提供二次封装或差异说明。
4. 在 `update.md` 标注版本与时间，必要时增加迁移指引。

