# 系统全景 - API 参考

本文档使用 `mkdocstrings` 自动从代码生成，会实时反映代码的最新状态。

> **提示**：本文档中的 API 信息直接从源代码提取，包括类、方法、参数、返回值等。代码更新后，运行 `mkdocs serve` 即可看到最新内容。

## 爬虫模块

### RcsbAllApiSpider

主爬虫类，负责从 RCSB PDB 获取蛋白质结构数据。

::: RCSB_PDB.src.spider.rcsb_pdb.rcsb_pdb_spider.RcsbAllApiSpider
    handler: python
    options:
      show_root_heading: true
      show_source: true
      show_signature_annotations: true
      merge_init_into_class: true
      show_submodules: false

### FieldFilter

字段过滤器，用于根据配置文件过滤不需要的字段。

::: RCSB_PDB.src.spider.rcsb_pdb.field_filter.FieldFilter
    handler: python
    options:
      show_root_heading: true
      show_source: true
      show_signature_annotations: true
      merge_init_into_class: true

## 数据项模块

### RcsbAllApiItem

RCSB PDB 数据项定义，用于标准化数据输出格式。

::: RCSB_PDB.src.items.rcsb_pdb_item.RcsbAllApiItem
    handler: python
    options:
      show_root_heading: true
      show_source: true
      show_signature_annotations: true
      merge_init_into_class: true

## 管道模块

### RcsbPdbPipeline

数据入库管道，负责将数据写入 MongoDB。

::: RCSB_PDB.src.pipelines.rcsb_pdb_pipeline.RcsbPdbPipeline
    handler: python
    options:
      show_root_heading: true
      show_source: true
      show_signature_annotations: true
      merge_init_into_class: true

## 配置模块

### settings

项目配置文件，包含 Scrapy 配置、数据库配置、日志配置等。

::: RCSB_PDB.src.settings
    handler: python
    options:
      show_root_heading: true
      show_source: true
      show_submodules: false

## 使用说明

### 查看源代码

每个 API 文档都包含源代码链接，点击可以查看完整的源代码实现。

### 参数说明

- **参数类型**：显示在方法签名中
- **参数说明**：从 docstring 中提取
- **默认值**：如果有默认值会显示

### 返回值说明

- **返回类型**：显示在方法签名中
- **返回值说明**：从 docstring 中提取

### 注意事项

- 文档内容直接从代码生成，确保代码中的 docstring 完整准确
- 使用 Google 风格的 docstring 格式可以获得更好的文档效果
- 代码更新后，文档会自动反映最新变化

## 相关文档

- [快速开始](getting-started.md) - 了解如何使用项目
- [核心模块](guide.md) - 详细的模块说明
- [使用示例](examples.md) - 代码使用示例
- [配置说明](configuration.md) - 配置参数详解
