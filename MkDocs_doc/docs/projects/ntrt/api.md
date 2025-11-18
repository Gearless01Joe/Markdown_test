# 系统全景 - API 参考

本文档依托 `mkdocstrings` 自动从源码收集 docstring，展示 NTRT 项目的核心类与方法。代码更新后，无需手工维护，只要重新构建即可获得最新 API。

---

## 数据清洗调度

### DataCleaner

::: NTRT.data_cleaner.DataCleaner
    handler: python
    options:
      show_root_heading: true
      show_source: true
      show_signature_annotations: true
      merge_init_into_class: true

---

## ORM 与数据库封装

### BaseCRUD & session_dict

::: NTRT.base_mysql
    handler: python
    options:
      show_root_heading: true
      show_source: true
      show_submodules: false

---

## 业务模型

### NsfcTopicRcmdTaskListModel

::: NTRT.application.NsfcTopicRcmdModels.NsfcTopicRcmdTaskListModel
    handler: python
    options:
      show_root_heading: true
      show_source: true
      show_signature_annotations: true
      merge_init_into_class: true

### NsfcTopicRcmdTaskTopicListModel

::: NTRT.application.NsfcTopicRcmdModels.NsfcTopicRcmdTaskTopicListModel
    handler: python
    options:
      show_root_heading: true
      show_source: true
      show_signature_annotations: true
      merge_init_into_class: true

### NsfcTopicRcmdTaskAppInfoModel

::: NTRT.application.NsfcTopicRcmdModels.NsfcTopicRcmdTaskAppInfoModel
    handler: python
    options:
      show_root_heading: true
      show_source: true
      show_signature_annotations: true
      merge_init_into_class: true

---

## 业务配置

### application.settings

::: NTRT.application.settings
    handler: python
    options:
      show_root_heading: true
      show_source: true
      show_submodules: false

---

## 使用指南

- 查看类/方法签名：展开对应模块即可看到参数与类型注解
- Docstring 格式：建议使用 Google 或 Sphinx 风格，便于 mkdocstrings 正确解析
- 源码跳转：启用 `show_source: true` 后，可在文档中直接查看实现细节

如需新增模块，请将 Python 文件放在 `code_liu/NTRT/` 下，并在 `mkdocs.yml` 的 `paths` 中确保包含 `../code_liu`。

