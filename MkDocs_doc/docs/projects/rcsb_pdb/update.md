# 更新日志

记录 RCSB PDB 项目的关键演进节点与功能清单。

---

## 2025 年

### 2025-11-21 · 结构补全 & 文档对齐

**新增**
- 将 `src/spider` 统一更名为 `src/spiders`，补齐 `__init__.py`，Scrapy 能正确发现 `RcsbAllApiSpider`
- 修复 `services.py`、`RcsbPdbPipeline` 等模块对 `src.items.other` 的错误引用
- 重写六大文档（快速开始 / 架构 / 核心模块 / 配置 / 示例 / 排障），与最新代码保持同步

**优化**
- `api.md` 调整为文字概览，避免第三方依赖缺失时 mkdocstrings 报错
- `configuration.md`、`examples.md` 按场景拆分，便于直接复制命令

### 2025-11-18 · 文档体系启用

- 引入 MkDocs + Material + mkdocstrings
- 输出首版「快速开始 / 架构设计 / 使用示例 / 故障排查」

### 2025-11-17 · 功能集

- **增量更新**：Redis + Mongo 双游标，`overlap_days` 防抖
- **文件下载**：CIF/验证文件探测 + OSS 路径替换
- **多模式运行**：单条 / 全量 / 增量统一入口
- **字段过滤**：预留 `field_filter_config`（功能仍在迭代）

---

## 功能清单

### 已实现
- ✅ 单条拉取 (`pdb_id`)
- ✅ 全量/增量模式切换
- ✅ Mongo 入库 + metadata（`raw_data.rcsb_pdb_structures_all`）
- ✅ Redis 游标管理 (`rcsb_all_api:revision`)
- ✅ CIF / 验证文件下载与审计
- ✅ 自定义 Pipeline（下载 → 替换 → 入库）
- ✅ 结构化日志与重试策略

### 规划中
- ⏳ 字段过滤器前端配置化
- ⏳ 数据质检 / 清洗脚本
- ⏳ 自动化测试与基准数据集
- ⏳ 任务监控与告警
- ⏳ 数据导出 / API 推送

---

## 版本说明

当前项目版本：**1.0.0**。后续如需打标签，请同时更新本文档并补充变更摘要。

---

## 贡献指南

1. 在仓库提交 Issue，描述背景、预期、复现方式
2. 如涉及代码修改，提交 PR 并在描述中关联 Issue
3. 若改动影响文档，请同步更新对应章节并补充更新日志

---

## 相关文档

- [快速开始](getting-started.md)
- [架构设计](architecture.md)
- [核心模块](guide.md)
- [配置说明](configuration.md)
- [使用示例](examples.md)
- [故障排查](troubleshooting.md)

