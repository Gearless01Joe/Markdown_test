# NTRT 项目概述

NTRT（National Science Foundation Topic Recommendation）项目是一套围绕国自然选题推荐数据的清洗与标准化工具链。它以 `DataCleaner` 为核心，结合 SQLAlchemy ORM、JSON 规则与批处理策略，实现 `breadth_search`、`cited_articles` 等复杂字段的拆解、转换与回写。

---

## 项目定位

- **服务对象**：国自然申报辅助系统、学术推荐平台
- **核心目标**：将多源 JSON 字段转换成结构化、可检索的数据
- **主要能力**：
  - 批量扫描并筛选需要清洗的记录
  - 针对不同字段应用差异化处理逻辑
  - 统一写入 MySQL，保证事务一致性
  - 灵活切换不同数据库、批次大小与处理策略

---

## 文档导航

| 文档 | 说明 |
| --- | --- |
| [快速开始](getting-started.md) | 环境准备、依赖安装、任务启动 |
| [架构设计](architecture.md) | 组件关系、数据流、批处理策略 |
| [系统全景](api.md) | 基于 mkdocstrings 的 API 参考 |
| [核心模块](guide.md) | 关键模块与扩展点解析 |
| [配置说明](configuration.md) | 数据库/批次/日志等配置项说明 |
| [使用示例](examples.md) | 常见运行场景与代码片段 |
| [故障排查](troubleshooting.md) | 数据库、JSON、事务相关问题排查 |
| [更新日志](update.md) | 版本历史、功能变更 |

---

## 系统优势

- **ORM + 批处理**：在 SQLAlchemy 框架下封装通用 `BaseCRUD`，保证增删改查统一。
- **字段级策略**：`Field processor` 细粒度处理项目/文章/引用等不同字段。
- **弹性批次**：通过 `BATCH_SIZE` 控制遍历与更新规模，兼顾性能与安全。
- **多数据库适配**：`session_dict` 支持一次性创建多实例，运行期自由切换。

---

## 目录速览

```
code_liu/NTRT/
├── data_cleaner.py          # 清洗入口，封装完整流程
├── base_mysql.py            # SQLAlchemy 封装与 CRUD 基类
├── application/
│   ├── settings.py          # 数据库/批次/环境配置
│   ├── NsfcTopicRcmdModels.py
│   └── ChatPaperPolishTaskList.py
├── *.json / *.md            # 业务规则、字段对照、调研笔记
└── application/.venv        # 可选的独立虚拟环境
```

> 业务背景、字段释义等可参考根目录下的「数据清洗流程说明.md」「文件调用关系说明.md」等手册。

---

## 下一步

1. 阅读 [快速开始](getting-started.md)，完成环境初始化
2. 根据 [配置说明](configuration.md) 设定数据库与批次参数
3. 参照 [使用示例](examples.md) 启动清洗任务
4. 如果需要定制新的字段处理逻辑，请先查阅 [核心模块](guide.md)

