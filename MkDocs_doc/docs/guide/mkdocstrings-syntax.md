# mkdocstrings 完整语法指南

## 基本语法

### 最简单的用法

```markdown
::: 模块路径
```

**示例**：
```markdown
::: NTRT.data_cleaner
```

这会显示整个模块的内容。

### 引用类

```markdown
::: 模块路径.类名
```

**示例**：
```markdown
::: NTRT.data_cleaner.DataCleaner
```

### 引用函数

```markdown
::: 模块路径.函数名
```

**示例**：
```markdown
::: NTRT.data_cleaner.some_function
```

## 完整语法格式

### 标准格式

```markdown
::: 模块路径
    handler: python
    options:
      选项名: 值
```

### 所有可用选项

```markdown
::: 模块路径
    handler: python
    options:
      # 显示选项
      show_root_heading: true          # 显示根标题
      show_root_toc_entry: true        # 在目录中显示根条目
      show_root_full_path: false       # 显示完整路径
      show_root_members_full_path: false  # 显示成员完整路径
      
      # 源代码选项
      show_source: true                # 显示源代码
      show_signature: true             # 显示函数签名
      show_signature_annotations: true # 显示类型注解
      separate_signature: false        # 单独显示签名
      
      # 内容选项
      show_if_no_docstring: false      # 没有 docstring 也显示
      show_submodules: true            # 显示子模块
      show_object_full_path: false     # 显示对象完整路径
      
      # 成员选项
      members:                         # 只显示指定的成员
        - method1
        - method2
      members_order: alphabetical      # 成员排序：alphabetical, source
      filters: []                      # 过滤规则
      
      # 类选项
      merge_init_into_class: true      # 将 __init__ 合并到类文档
      show_bases: true                 # 显示基类
      show_inheritance: false          # 显示继承关系
      
      # 文档字符串选项
      docstring_style: google          # 风格：google, numpy, sphinx
      docstring_options: {}            # docstring 解析选项
      
      # 其他选项
      heading_level: 1                 # 标题级别
      line_length: 79                  # 代码行长度
      paths: []                        # 额外搜索路径
```

## 常用配置示例

### 示例 1：显示类及其所有方法

```markdown
::: NTRT.data_cleaner.DataCleaner
    handler: python
    options:
      show_root_heading: true
      show_source: true
      show_signature_annotations: true
      merge_init_into_class: true
```

### 示例 2：只显示特定方法

```markdown
::: NTRT.data_cleaner.DataCleaner
    handler: python
    options:
      show_root_heading: true
      members:
        - run_all
        - clean_breadth_search
        - clean_cited_articles_topic
```

### 示例 3：显示模块及其所有类和函数

```markdown
::: NTRT.data_cleaner
    handler: python
    options:
      show_root_heading: true
      show_submodules: true
      show_source: true
```

### 示例 4：不显示没有 docstring 的方法

```markdown
::: NTRT.data_cleaner.DataCleaner
    handler: python
    options:
      show_root_heading: true
      show_if_no_docstring: false  # 没有 docstring 就不显示
```

### 示例 5：显示继承关系

```markdown
::: NTRT.data_cleaner.DataCleaner
    handler: python
    options:
      show_root_heading: true
      show_bases: true
      show_inheritance: true
```

## 高级用法

### 组合多个引用

```markdown
# 数据清洗模块

## DataCleaner 类

::: NTRT.data_cleaner.DataCleaner
    handler: python
    options:
      show_root_heading: true
      show_source: true

## 相关模型

::: NTRT.application.NsfcTopicRcmdModels
    handler: python
    options:
      show_root_heading: true
```

### 使用别名

```markdown
::: NTRT.data_cleaner.DataCleaner
    handler: python
    options:
      show_root_heading: true
      heading_level: 2
```

### 过滤私有成员

```markdown
::: NTRT.data_cleaner.DataCleaner
    handler: python
    options:
      show_root_heading: true
      filters:
        - "!^_"  # 排除以 _ 开头的成员
```

## 模块路径规则

### 路径计算

根据 `mkdocs.yml` 中的 `paths` 配置：

```yaml
paths: 
  - ../code_liu
  - ../src
```

**规则**：
1. 从 `paths` 配置的目录开始计算
2. 文件路径中的 `/` 或 `\` 替换为 `.`
3. 去掉 `.py` 扩展名

### 示例

| 文件路径 | 模块路径 |
|---------|---------|
| `code_liu/NTRT/data_cleaner.py` | `NTRT.data_cleaner` |
| `code_liu/NTRT/data_cleaner.py` 中的 `DataCleaner` 类 | `NTRT.data_cleaner.DataCleaner` |
| `code_liu/NTRT/application/NsfcTopicRcmdModels.py` | `NTRT.application.NsfcTopicRcmdModels` |
| `src/spiders/base_spider.py` | `spiders.base_spider` |
| `src/spiders/base_spider.py` 中的 `BaseSpider` 类 | `spiders.base_spider.BaseSpider` |

## 常见问题

### Q: 如何引用嵌套类？

```markdown
::: 模块路径.外部类.内部类
```

### Q: 如何引用类方法？

```markdown
::: 模块路径.类名.方法名
```

**注意**：通常不需要单独引用方法，引用类会自动显示所有方法。

### Q: 如何引用模块级别的函数？

```markdown
::: 模块路径.函数名
```

### Q: 如何引用子模块？

```markdown
::: 模块路径.子模块名
    handler: python
    options:
      show_submodules: true
```

### Q: 模块路径错误怎么办？

**错误**：`Could not find 'xxx' in the following paths`

**解决**：
1. 检查 `mkdocs.yml` 中的 `paths` 配置
2. 确认文件路径是否正确
3. 检查模块路径计算是否正确（从 `paths` 目录开始）

## 最佳实践

### 1. 组织文档结构

```markdown
# 项目 API 参考

## 核心类

### DataCleaner

数据清洗类，负责数据库操作和数据清洗流程。

::: NTRT.data_cleaner.DataCleaner
    handler: python
    options:
      show_root_heading: true
      show_source: true
      show_signature_annotations: true

## 辅助模块

### 数据库操作

::: NTRT.base_mysql
    handler: python
    options:
      show_root_heading: true
```

### 2. 添加描述

在 `::: 模块路径` 之前添加描述文字，让文档更易读：

```markdown
### DataCleaner 类

数据清洗类，负责数据库操作和数据清洗流程。

::: NTRT.data_cleaner.DataCleaner
    handler: python
    options:
      show_root_heading: true
```

### 3. 使用合适的选项

- **公共 API**：显示所有内容，包括源代码
- **内部模块**：只显示有 docstring 的内容
- **大型类**：只显示特定成员

### 4. 保持一致性

在同一个文档中使用相同的选项配置，保持风格一致。

## 完整示例

```markdown
# NTRT 项目 - API 参考

## 数据清洗模块

### DataCleaner 类

数据清洗类，负责数据库操作和数据清洗流程。

::: NTRT.data_cleaner.DataCleaner
    handler: python
    options:
      show_root_heading: true
      show_source: true
      show_signature_annotations: true
      merge_init_into_class: true
      show_if_no_docstring: false

## 应用模块

### NsfcTopicRcmdModels

国自然选题推荐相关模型模块。

::: NTRT.application.NsfcTopicRcmdModels
    handler: python
    options:
      show_root_heading: true
      show_submodules: true

#### 主要模型类

- `NsfcTopicRcmdTaskListModel`: 任务列表模型
- `NsfcTopicRcmdTaskTopicListModel`: 主题列表模型

::: NTRT.application.NsfcTopicRcmdModels.NsfcTopicRcmdTaskListModel
    handler: python
    options:
      show_root_heading: true
      show_source: true
```

## 参考资源

- [mkdocstrings 官方文档](https://mkdocstrings.github.io/python/)
- [Python Handler 选项](https://mkdocstrings.github.io/python/usage/options/)
- [工作流程说明](mkdocstrings-workflow.md)

