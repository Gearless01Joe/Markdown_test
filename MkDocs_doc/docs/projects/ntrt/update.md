# 更新日志

本文记录 NTRT 项目的重要变更和迭代历史。

---

## 2025-01

### 文档体系升级
- 新增完整文档栈：概述 / 快速开始 / 架构 / API / 核心模块 / 配置 / 示例 / 故障排查
- 将 API 说明改为 mkdocstrings 动态生成，去除 `code_to_markdown.py` 依赖
- 调整导航结构，与 RCSB PDB 项目保持一致

### 代码与配置
- 梳理 `cleaning_plan`，明确各字段处理流程
- 提炼 `BATCH_SIZE`、`DEFAULT_DB_KEY` 等常量，便于运行时调整
- 更新 `application/settings.py` 示例，补充测试/生产多库说明

---

## 2024-12

### 功能
- 构建 `DataCleaner` 主流程，覆盖 `breadth_search` / `cited_articles` 等核心字段
- 引入 `CleaningModelMixin`，统一 `fetch_records_for_cleaning` 与 `batch_update_field`
- 封装 `BaseCRUD`，提供批量插入、条件更新、分页查询等能力

### 数据与规则
- 输出《数据清洗流程说明》《文件调用关系说明》等参考文档
- 提供 JSON 示例文件（项目/文章/引用）作为测试数据源

---

## 版本说明

| 版本 | 日期 | 说明 |
| --- | --- | --- |
| 1.1.0 | 2025-01 | 文档体系升级，API 改用 mkdocstrings |
| 1.0.0 | 2024-12 | 发布清洗流程与 ORM 封装的初版 |

版本号遵循 `主版本号.次版本号.修订号` 规则：
- **主版本号**：重大架构或功能调整
- **次版本号**：新增特性或文档
- **修订号**：修复缺陷或小幅改进

---

未来计划：
- 将 `cleaning_plan` 抽象为可配置 YAML/JSON
- 引入标准日志与监控指标
- 结合调度平台实现增量/全量自动化运行

