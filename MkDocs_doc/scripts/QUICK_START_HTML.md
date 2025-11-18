# 快速生成 HTML 文档（最简单方案）

如果你觉得 MkDocs 太复杂，这里是最简单的方案：**直接从代码生成 HTML，无需任何配置！**

## 🚀 最快方案：pdoc3

### 1. 安装（只需一次）

```bash
pip install pdoc3
```

### 2. 生成文档（一条命令）

```bash
# 生成单个模块
pdoc3 --html --output-dir docs/html NTRT.data_cleaner

# 生成整个包
pdoc3 --html --output-dir docs/html NTRT
```

### 3. 查看结果

打开 `docs/html/NTRT/index.html` 即可！

**就这么简单！** 不需要：
- ❌ 写 Markdown 文件
- ❌ 配置 mkdocs.yml
- ❌ 了解 mkdocstrings 语法
- ❌ 运行脚本生成语法

## 📝 在 PyCharm 中使用

### 方法 1：使用项目脚本

1. 打开 `MkDocs_doc/scripts/generate_html_docs.py`
2. 修改配置：
   ```python
   MODULE_PATH = "NTRT.data_cleaner"  # 要生成的模块
   OUTPUT_DIR = Path("docs/html_docs")  # 输出目录
   ```
3. 右键运行

### 方法 2：直接在终端运行

在 PyCharm 的终端中：

```bash
cd MkDocs_doc
pip install pdoc3
pdoc3 --html --output-dir docs/html NTRT
```

## 🎯 对比

### MkDocs 方案（当前）

```
写代码 → 写 Markdown → 配置 mkdocs.yml → 
运行脚本 → mkdocs build → 查看文档
```

**6 个步骤，需要写文档**

### pdoc3 方案（推荐）

```
写代码 → pdoc3 --html → 查看文档
```

**2 个步骤，完全自动化！**

## 💡 建议

- **快速生成文档** → 使用 pdoc3
- **精美文档站点** → 使用 MkDocs（但需要更多工作）

或者**混合使用**：
- pdoc3 生成 API 文档（HTML）
- MkDocs 只写项目概述和使用指南

## 📚 更多信息

查看 `docs/guide/simple-html-tools.md` 了解详细对比和更多工具。

