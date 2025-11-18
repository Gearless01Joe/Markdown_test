# 项目结构说明

## 📁 整体目录结构

```
Markdown/                          # 项目根目录
├── code_liu/                      # 源代码目录
│   ├── NTRT/                      # NTRT 项目（国自然选题推荐数据清洗）
│   │   ├── data_cleaner.py        # 数据清洗主类
│   │   ├── base_mysql.py          # 数据库基础操作
│   │   ├── application/           # 应用模块
│   │   └── *.md                   # 项目相关文档
│   └── RCSB_PDB/                  # RCSB PDB 项目（蛋白质数据库爬虫）
│       ├── src/
│       │   ├── spider/            # 爬虫模块
│       │   ├── items/             # 数据项定义
│       │   └── pipelines/         # 数据处理管道
│       └── *.md                   # 项目相关文档
│
├── MkDocs_doc/                    # MkDocs 文档项目
│   ├── docs/                      # 文档源文件目录
│   │   ├── index.md               # 首页
│   │   ├── api.md                 # API 总览
│   │   ├── projects/              # 项目文档
│   │   │   ├── index.md          # 项目文档首页
│   │   │   ├── ntrt/             # NTRT 项目文档
│   │   │   │   ├── index.md      # 项目概述
│   │   │   │   ├── api.md        # API 参考（自动生成）
│   │   │   │   ├── guide.md      # 使用指南
│   │   │   │   └── update.md     # 更新日志
│   │   │   └── rcsb_pdb/         # RCSB PDB 项目文档
│   │   │       ├── index.md
│   │   │       ├── api.md
│   │   │       ├── guide.md
│   │   │       └── update.md
│   │   ├── guide/                 # 开发指南
│   │   │   ├── index.md
│   │   │   ├── getting-started.md
│   │   │   ├── best-practices.md
│   │   │   ├── mkdocstrings-workflow.md    # mkdocstrings 工作流程
│   │   │   ├── mkdocstrings-syntax.md      # mkdocstrings 语法参考
│   │   │   ├── mkdocstrings-comments.md    # mkdocstrings 与注释
│   │   │   └── advanced/          # 高级主题
│   │   │       ├── index.md
│   │   │       └── performance.md
│   │   └── reference/             # 参考文档
│   │       ├── index.md
│   │       └── glossary.md
│   │
│   ├── scripts/                   # 自动化脚本
│   │   ├── generate_mkdocstrings_md.py  # 自动生成包含 mkdocstrings 语法的 .md 文件
│   │   ├── code_to_markdown.py         # 将 Python 代码转换为 Markdown
│   │   ├── README_auto_generate.md     # 自动生成脚本说明
│   │   └── README_code_to_markdown.md  # 代码转 Markdown 说明
│   │
│   ├── mkdocs.yml                 # MkDocs 配置文件
│   ├── requirements.txt           # Python 依赖
│   └── site/                      # 构建输出目录（自动生成）
│
└── .github/
    └── workflows/
        └── mkdocs-deploy.yml      # GitHub Actions 自动部署配置
```

## 🎯 核心组件说明

### 1. 源代码目录 (`code_liu/`)

**作用**：存放项目的 Python 源代码

**结构**：
- `NTRT/` - 国自然选题推荐数据清洗项目
- `RCSB_PDB/` - RCSB PDB 爬虫项目

**用途**：
- mkdocstrings 从这里读取代码
- 自动生成 API 文档

### 2. 文档源文件 (`MkDocs_doc/docs/`)

**作用**：存放所有 Markdown 文档源文件

**主要目录**：
- `projects/` - 项目文档（每个项目一个子目录）
- `guide/` - 开发指南和使用说明
- `reference/` - 参考文档

### 3. 自动化脚本 (`MkDocs_doc/scripts/`)

#### `generate_mkdocstrings_md.py`
**功能**：自动生成包含 mkdocstrings 语法的 .md 文件

**使用**：
```bash
python MkDocs_doc/scripts/generate_mkdocstrings_md.py
```

**作用**：
- 扫描代码目录
- 自动发现所有类和函数
- 生成包含 `::: 模块路径` 语法的 .md 文件

#### `code_to_markdown.py`
**功能**：将 Python 代码直接转换为 Markdown 文档

**使用**：
```bash
python MkDocs_doc/scripts/code_to_markdown.py <输入路径> -o <输出路径>
```

**作用**：
- 解析 Python 代码
- 提取 docstring、类、函数等信息
- 生成完整的 Markdown 文档

### 4. 配置文件 (`mkdocs.yml`)

**主要配置**：

#### 导航配置 (`nav`)
```yaml
nav:
  - 首页: index.md
  - 项目文档:
    - 国自然选题推荐数据清洗:
      - 文档概述: projects/ntrt/index.md
      - 系统全景: projects/ntrt/api.md
      - 核心模块: projects/ntrt/guide.md
      - 更新日志: projects/ntrt/update.md
  - 开发指南: ...
  - 参考文档: ...
```

#### 插件配置 (`plugins`)
```yaml
plugins:
  - search:                    # 搜索功能
  - autorefs:                  # 自动引用
  - mkdocstrings:              # 从代码提取文档
    handlers:
      python:
        paths: 
          - ../code_liu        # 代码路径
          - ../src
```

#### 主题配置 (`theme`)
```yaml
theme:
  name: material               # Material 主题
  language: zh                # 中文
  features:                   # 功能特性
    - navigation.tabs
    - search.suggest
    - content.code.copy
    ...
```

## 🔄 工作流程

### 文档生成流程

```
1. 编写/更新 Python 代码
   ↓
2. 运行自动生成脚本
   python scripts/generate_mkdocstrings_md.py
   ↓
3. 生成包含 mkdocstrings 语法的 .md 文件
   docs/projects/ntrt/api.md
   ↓
4. 运行 mkdocs build/serve
   mkdocs serve
   ↓
5. mkdocstrings 从代码读取文档
   解析 docstring、类、函数等
   ↓
6. 生成 HTML 文档
   site/ 目录
```

### 自动部署流程

```
1. 本地修改代码/文档
   ↓
2. Git 提交并推送
   git push markdown test
   ↓
3. GitHub Actions 自动触发
   .github/workflows/mkdocs-deploy.yml
   ↓
4. 自动运行脚本生成文档
   python scripts/generate_mkdocstrings_md.py
   ↓
5. 构建并部署到 GitHub Pages
   mkdocs gh-deploy
   ↓
6. 文档自动更新
   https://Gearless01Joe.github.io/Markdown_test/
```

## 📋 文档组织

### 项目文档结构

每个项目包含 4 个文档：

1. **index.md** - 项目概述
   - 项目介绍
   - 快速开始
   - 项目结构
   - 文档导航

2. **api.md** - API 参考（自动生成）
   - 使用 `generate_mkdocstrings_md.py` 生成
   - 包含 `::: 模块路径` 语法
   - mkdocstrings 自动从代码提取文档

3. **guide.md** - 使用指南
   - 核心模块说明
   - 使用示例
   - 最佳实践
   - 常见问题

4. **update.md** - 更新日志
   - 版本历史
   - 更新记录

### 开发指南结构

- **index.md** - 指南首页
- **getting-started.md** - 快速开始
- **best-practices.md** - 最佳实践
- **mkdocstrings-workflow.md** - mkdocstrings 工作流程
- **mkdocstrings-syntax.md** - mkdocstrings 语法参考
- **mkdocstrings-comments.md** - mkdocstrings 与注释
- **advanced/** - 高级主题

## 🛠️ 工具和脚本

### 主要工具

1. **MkDocs** - 文档生成框架
2. **Material for MkDocs** - 主题
3. **mkdocstrings** - 从代码提取文档
4. **GitHub Actions** - 自动部署

### 自动化脚本

1. **generate_mkdocstrings_md.py**
   - 自动生成包含 mkdocstrings 语法的 .md 文件
   - 扫描代码，发现类和函数
   - 生成正确的模块路径

2. **code_to_markdown.py**
   - 将 Python 代码转换为 Markdown
   - 提取 docstring、类、函数等信息
   - 生成完整的文档内容

## 📝 关键文件说明

### `mkdocs.yml`
- MkDocs 主配置文件
- 定义导航结构
- 配置插件和主题
- 设置代码路径

### `requirements.txt`
- Python 依赖包
- mkdocs、mkdocs-material、mkdocstrings 等

### `.github/workflows/mkdocs-deploy.yml`
- GitHub Actions 工作流
- 自动构建和部署文档
- 集成自动生成脚本

## 🎨 文档特性

### Material 主题功能

- ✅ 多层级导航
- ✅ 全文搜索
- ✅ 代码高亮
- ✅ 代码复制按钮
- ✅ 响应式设计
- ✅ 暗色模式支持

### mkdocstrings 功能

- ✅ 自动从代码提取文档
- ✅ 解析 docstring
- ✅ 显示类型注解
- ✅ 显示源代码
- ✅ 支持 Google/Sphinx/NumPy 风格

## 📊 项目统计

### 当前项目

- **NTRT 项目**：11 个类/函数
- **RCSB PDB 项目**：4 个类/函数

### 文档页面

- **项目文档**：2 个项目 × 4 个页面 = 8 页
- **开发指南**：7 个页面
- **参考文档**：3 个页面
- **总计**：约 18 个页面

## 🚀 快速开始

### 1. 本地开发

```bash
# 安装依赖
cd MkDocs_doc
pip install -r requirements.txt

# 生成 API 文档
python scripts/generate_mkdocstrings_md.py

# 本地预览
mkdocs serve
```

### 2. 更新文档

```bash
# 代码更新后，重新生成文档
python scripts/generate_mkdocstrings_md.py

# 查看效果
mkdocs serve
```

### 3. 部署

```bash
# 推送到 GitHub，自动部署
git add .
git commit -m "Update docs"
git push markdown test
```

## 📚 相关文档

- [mkdocstrings 工作流程](mkdocstrings-workflow.md)
- [mkdocstrings 语法参考](mkdocstrings-syntax.md)
- [mkdocstrings 与注释](mkdocstrings-comments.md)
- 自动生成脚本说明：`MkDocs_doc/scripts/README_auto_generate.md`

