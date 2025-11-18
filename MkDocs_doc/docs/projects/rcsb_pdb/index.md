# RCSB PDB 项目概述

RCSB PDB 项目是一个围绕 _Protein Data Bank_ 数据构建的企业级采集与入库系统。它由 Scrapy 爬虫、字段过滤器、Mongo/Redis 辅助组件以及多条 Pipeline 组成，支持全量与增量双模式，能够同步结构条目、聚合实体、自动拉取 ChemComp/DrugBank 元数据，并将结果落盘及落库。


---

## 文档索引

| 文档 | 作用 |
| --- | --- |
| [快速开始](getting-started.md) | 本地环境准备、脚本运行、常见命令 |
| [架构设计](architecture.md) | 组件划分、数据流、依赖关系 |
| [系统全景](api.md) | 基于 mkdocstrings 的 API 参考（代码即文档） |
| [核心模块](guide.md) | 核心 Item/Pipeline/Spider 的行为说明 |
| [配置说明](configuration.md) | 数据库、日志、Scrapy/Playwright 参数 |
| [使用示例](examples.md) | 全量、增量、手动 PDB 调试等场景 |
| [故障排查](troubleshooting.md) | 网络、API、入库失败、增量游标等问题 |
| [更新日志](update.md) | 近期迭代与版本记录 |

---

## 系统亮点

- **多源 API 聚合**：Search、Entry、Polymer/Nonpolymer/ChemComp/DrugBank 多接口协同。
- **智能增量**：Redis + Mongo 双游标，支持按 revision_date 去重与回溯。
- **字段裁剪**：`FieldFilter` 支持 JSON 配置的白名单/黑名单与嵌套规则。
- **多副本落地**：同时生成 JSON 文件、Mongo 文档与 OSS/本地文件。
- **可控并发与重试**：自定义中间件 + Playwright/代理/验证码支持。

---

## 目录速览

```
code_liu/RCSB_PDB/
├── firing.py                  # 任务入口
├── README.md                  # 项目说明
└── src/
    ├── settings.py            # Scrapy / 数据库 / 中间件配置
    ├── items/
    │   └── rcsb_pdb_item.py   # Item 定义
    ├── pipelines/
    │   └── rcsb_pdb_pipeline.py
    └── spider/rcsb_pdb/
        ├── field_filter.py    # 字段裁剪
        └── rcsb_pdb_spider.py # 主爬虫
```

所有文档均位于 `MkDocs_doc/docs/projects/ntrt/` 目录，可直接通过 `mkdocs serve` 浏览。若需新增内容，建议遵循概览 → 快速开始 → 架构 → 模块 → 配置 → 排障的阅读顺序，确保团队成员能在 5 分钟内定位到所需信息。
