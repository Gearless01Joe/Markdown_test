# MkDocs 多层级结构实现指南

## 一、基础多层级导航配置

### 1. 文档目录结构

创建多层级目录结构：

```
docs/
├── index.md                    # 首页
├── guide/                      # 指南目录
│   ├── index.md                # 指南首页
│   ├── getting-started.md      # 入门指南
│   └── advanced/               # 高级指南
│       ├── index.md
│       └── configuration.md
├── api/                        # API 文档目录
│   ├── index.md                # API 首页
│   ├── project1/               # 项目1
│   │   ├── index.md
│   │   ├── modules.md
│   │   └── classes.md
│   ├── project2/               # 项目2
│   │   ├── index.md
│   │   └── api.md
│   └── project3/               # 项目3
│       └── api.md
├── examples/                    # 示例目录
│   ├── index.md
│   └── tutorials/
│       ├── tutorial1.md
│       └── tutorial2.md
└── reference/                  # 参考文档
    ├── index.md
    └── glossary.md
```

### 2. mkdocs.yml 多层级导航配置

```yaml
site_name: Python技术文档库
site_url: https://Gearless01Joe.github.io/Markdown_test/

nav:
  # 第一层：首页
  - 首页: index.md
  
  # 第二层：指南（带子菜单）
  - 指南:
    - 指南首页: guide/index.md
    - 入门指南: guide/getting-started.md
    - 高级指南:
      - 高级指南首页: guide/advanced/index.md
      - 配置说明: guide/advanced/configuration.md
  
  # 第二层：API 文档（多项目）
  - API 文档:
    - API 首页: api/index.md
    - 项目1 - 数据清洗:
      - 项目1 首页: api/project1/index.md
      - 模块文档: api/project1/modules.md
      - 类文档: api/project1/classes.md
    - 项目2 - 数据库:
      - 项目2 首页: api/project2/index.md
      - API 参考: api/project2/api.md
    - 项目3 - 工具库:
      - API 参考: api/project3/api.md
  
  # 第二层：示例
  - 示例:
    - 示例首页: examples/index.md
    - 教程:
      - 教程1: examples/tutorials/tutorial1.md
      - 教程2: examples/tutorials/tutorial2.md
  
  # 第二层：参考文档
  - 参考文档:
    - 参考首页: reference/index.md
    - 术语表: reference/glossary.md
```

## 二、多项目支持配置

### 1. 使用 mkdocs-multirepo-plugin（推荐）

**安装插件**：
```bash
pip install mkdocs-multirepo-plugin
```

**配置 mkdocs.yml**：
```yaml
site_name: 团队技术文档库

nav:
  - 首页: index.md
  - 项目1: '!include projects/project1/mkdocs.yml'
  - 项目2: '!include projects/project2/mkdocs.yml'
  - 项目3: '!include projects/project3/mkdocs.yml'

plugins:
  - search
  - multirepo:
      repos:
        - url: https://github.com/team/project1
          branch: main
          docs_dir: docs
        - url: https://github.com/team/project2
          branch: main
          docs_dir: docs
        - url: https://github.com/team/project3
          branch: main
          docs_dir: docs
```

### 2. 使用符号链接 + 统一配置（适合本地开发）

**目录结构**：
```
MkDocs_doc/
├── mkdocs.yml
├── docs/
│   ├── index.md
│   ├── project1/
│   │   └── api.md
│   ├── project2/
│   │   └── api.md
│   └── project3/
│       └── api.md
└── projects/              # 符号链接到各个项目
    ├── project1 -> ../../project1/src
    ├── project2 -> ../../project2/src
    └── project3 -> ../../project3/src
```

**mkdocs.yml 配置**：
```yaml
site_name: 团队技术文档库

nav:
  - 首页: index.md
  - 项目文档:
    - 项目1:
      - API 参考: project1/api.md
      - 使用指南: project1/guide.md
    - 项目2:
      - API 参考: project2/api.md
    - 项目3:
      - API 参考: project3/api.md

plugins:
  - search
  - mkdocstrings:
      default_handler: python
      handlers:
        python:
          paths: 
            - projects/project1
            - projects/project2
            - projects/project3
          options:
            docstring_style: google
            show_source: true
            show_root_heading: true
```

## 三、Material 主题的层级增强

### 1. 启用导航标签（Tabs）

```yaml
theme:
  name: material
  features:
    - navigation.tabs          # 顶部标签导航
    - navigation.sections      # 章节导航
    - navigation.expand        # 可展开导航
    - navigation.top           # 返回顶部
    - search.suggest           # 搜索建议
    - search.highlight         # 搜索结果高亮
    - content.code.copy        # 代码复制按钮
```

### 2. 配置导航图标

```yaml
nav:
  - 首页: 
    - index.md
    - icon: material/home
  - 指南:
    - guide/index.md
    - icon: material/book-open-variant
  - API 文档:
    - api/index.md
    - icon: material/api
```

### 3. 多层级侧边栏配置

```yaml
theme:
  name: material
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.expand
  palette:
    - scheme: default
      primary: blue
      accent: blue
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    - scheme: slate
      primary: blue
      accent: blue
      toggle:
        icon: material/brightness-4
        name: Switch to light mode
```

## 四、实际配置示例（针对你的项目）

### 完整 mkdocs.yml 配置

```yaml
# 网页标题
site_name: Python技术文档库
site_url: https://Gearless01Joe.github.io/Markdown_test/

# 多层级导航
nav:
  # 第一层
  - 首页: index.md
  
  # 第二层：项目文档（多项目）
  - 项目文档:
    - 项目文档首页: projects/index.md
    - 国自然选题推荐:
      - 项目首页: projects/nsfc/index.md
      - API 参考: projects/nsfc/api.md
      - 使用指南: projects/nsfc/guide.md
    - 数据库工具:
      - 项目首页: projects/database/index.md
      - API 参考: projects/database/api.md
    - 数据清洗:
      - 项目首页: projects/cleaner/index.md
      - API 参考: projects/cleaner/api.md
  
  # 第二层：开发指南
  - 开发指南:
    - 指南首页: guide/index.md
    - 快速开始: guide/getting-started.md
    - 最佳实践: guide/best-practices.md
    - 高级主题:
      - 高级主题首页: guide/advanced/index.md
      - 性能优化: guide/advanced/performance.md
      - 扩展开发: guide/advanced/extensions.md
  
  # 第二层：参考文档
  - 参考文档:
    - 参考首页: reference/index.md
    - 术语表: reference/glossary.md
    - 更新日志: update.md

# 插件配置
plugins:
  - search:
      lang: ['zh', 'en']
      prebuild_index: true  # 预构建索引，提升搜索速度
  - mkdocstrings:
      default_handler: python
      handlers:
        python:
          paths: 
            - ../src                    # 当前项目
            - projects/nsfc/src         # 项目1
            - projects/database/src      # 项目2
            - projects/cleaner/src       # 项目3
          options:
            docstring_style: google
            show_source: true
            show_root_heading: true
            show_root_toc_entry: true    # 显示根目录条目
            show_signature_annotations: true  # 显示类型注解

# 主题配置
theme:
  name: material
  language: zh
  features:
    - navigation.tabs          # 顶部标签
    - navigation.sections      # 章节导航
    - navigation.expand        # 可展开
    - navigation.top           # 返回顶部
    - search.suggest           # 搜索建议
    - search.highlight         # 搜索结果高亮
    - content.code.copy        # 代码复制
    - content.code.annotate    # 代码注释
  palette:
    - scheme: default
      primary: blue
      accent: blue
      toggle:
        icon: material/brightness-7
        name: 切换到深色模式
    - scheme: slate
      primary: blue
      accent: blue
      toggle:
        icon: material/brightness-4
        name: 切换到浅色模式
```

## 五、文档组织最佳实践

### 1. 项目文档结构

```
docs/projects/nsfc/
├── index.md          # 项目首页（概述、快速开始）
├── api.md            # API 文档（使用 mkdocstrings）
├── guide.md          # 使用指南
├── examples.md       # 示例代码
└── changelog.md      # 更新日志
```

### 2. 项目首页模板（projects/nsfc/index.md）

```markdown
# 国自然选题推荐数据清洗

## 项目概述

国自然选题推荐数据清洗模块，实现 `breadth_search` 和 `cited_articles` 字段的数据清洗和标准化处理。

## 快速开始

\`\`\`python
from data_cleaner import DataCleaner

cleaner = DataCleaner()
cleaner.run()
\`\`\`

## 文档导航

- [API 参考](api.md) - 完整的 API 文档
- [使用指南](guide.md) - 详细的使用说明
- [示例代码](examples.md) - 代码示例

## 相关链接

- [GitHub 仓库](https://github.com/team/nsfc)
- [问题反馈](https://github.com/team/nsfc/issues)
```

### 3. API 文档模板（projects/nsfc/api.md）

```markdown
# 国自然选题推荐 - API 参考

## 模块概览

::: data_cleaner
    handler: python
    options:
      show_root_heading: true
      show_source: true
      show_signature_annotations: true

## 主要类

### DataCleaner

::: data_cleaner.DataCleaner
    handler: python
    options:
      show_root_heading: true
      show_source: true
      members:
        - __init__
        - run
        - _process_records
```

## 六、自动生成多层级导航脚本

创建 `scripts/generate_nav.py`：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动生成多层级导航配置
"""

import yaml
from pathlib import Path

def scan_projects():
    """扫描 projects 目录，生成导航结构"""
    projects_dir = Path("docs/projects")
    nav_items = []
    
    if not projects_dir.exists():
        return nav_items
    
    for project_dir in sorted(projects_dir.iterdir()):
        if not project_dir.is_dir() or project_dir.name.startswith("."):
            continue
        
        project_name = project_dir.name
        project_nav = {
            project_name: []
        }
        
        # 检查是否有 index.md
        if (project_dir / "index.md").exists():
            project_nav[project_name].append(f"项目首页: projects/{project_name}/index.md")
        
        # 检查其他文档
        for doc_file in sorted(project_dir.glob("*.md")):
            if doc_file.name == "index.md":
                continue
            doc_name = doc_file.stem.replace("_", " ").title()
            project_nav[project_name].append(
                f"{doc_name}: projects/{project_name}/{doc_file.name}"
            )
        
        if project_nav[project_name]:
            nav_items.append(project_nav)
    
    return nav_items

def update_mkdocs_yml():
    """更新 mkdocs.yml 的导航配置"""
    mkdocs_path = Path("mkdocs.yml")
    
    with open(mkdocs_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 生成项目导航
    projects_nav = scan_projects()
    
    # 更新导航配置
    nav = [
        {"首页": "index.md"},
        {"项目文档": projects_nav} if projects_nav else None,
        {"开发指南": "guide/index.md"},
        {"参考文档": "reference/index.md"},
    ]
    
    # 过滤 None
    nav = [item for item in nav if item is not None]
    
    config['nav'] = nav
    
    # 写回文件
    with open(mkdocs_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    print("✓ 导航配置已更新")

if __name__ == "__main__":
    update_mkdocs_yml()
```

## 七、搜索增强配置

### 1. 预构建搜索索引

```yaml
plugins:
  - search:
      lang: ['zh', 'en']
      prebuild_index: true
      index_on_prebuild: true
```

### 2. 使用 Algolia DocSearch（可选）

在 `mkdocs.yml` 中添加：

```yaml
extra:
  analytics:
    provider: algolia
    config:
      application_id: YOUR_APP_ID
      api_key: YOUR_API_KEY
      index_name: YOUR_INDEX_NAME
```

## 八、总结

实现多层级结构的关键：

1. **目录结构**：按项目/功能组织文档目录
2. **导航配置**：在 `nav` 中使用嵌套列表实现多层级
3. **Material 主题**：启用 `navigation.sections` 和 `navigation.expand`
4. **自动生成**：使用脚本自动生成导航配置
5. **搜索优化**：配置预构建索引提升搜索性能

按照这个配置，你就能实现一个支持多项目、多层级的技术文档库了！

