# 简单的 HTML 文档生成工具

如果你觉得 MkDocs 的自动化太差，写笔记本身都要赶上做项目了，这里推荐几个**更简单、更自动化**的工具。

## 🚀 推荐工具对比

| 工具 | 自动化程度 | 配置复杂度 | 样式美观度 | 推荐度 |
|------|-----------|-----------|-----------|--------|
| **pdoc3** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **pdoc** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **pydoc** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐ |
| **MkDocs** | ⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

## 1. pdoc3（最推荐）

### 特点

- ✅ **零配置**：安装后直接使用
- ✅ **自动生成**：直接从代码生成 HTML
- ✅ **样式美观**：现代化的界面
- ✅ **支持多种 docstring 风格**：Google、Sphinx、NumPy
- ✅ **一键生成**：一条命令搞定

### 安装

```bash
pip install pdoc3
```

### 使用方法

#### 方法 1：命令行（最简单）

```bash
# 生成单个模块
pdoc3 --html --output-dir docs/html NTRT.data_cleaner

# 生成整个包
pdoc3 --html --output-dir docs/html NTRT

# 启动本地服务器（实时预览）
pdoc3 --http :8080 NTRT
```

#### 方法 2：Python 脚本（已在项目中创建）

运行 `MkDocs_doc/scripts/generate_html_docs.py`：

```python
# 修改配置
MODULE_PATH = "NTRT.data_cleaner"
OUTPUT_DIR = Path("docs/html_docs")
USE_PDOC3 = True

# 运行即可
```

#### 方法 3：在代码中使用

```python
import pdoc

# 生成 HTML 字符串
html = pdoc.html("NTRT.data_cleaner")

# 或生成到文件
pdoc.pdoc("NTRT.data_cleaner", output_directory="docs/html")
```

### 输出示例

生成的 HTML 包含：
- ✅ 自动生成的导航
- ✅ 类和方法列表
- ✅ 完整的 docstring
- ✅ 源代码链接
- ✅ 搜索功能

### 优点

- **完全自动化**：不需要写任何 Markdown
- **零配置**：安装即用
- **代码更新自动同步**：重新运行即可
- **样式现代**：比 pydoc 好看很多

### 缺点

- 样式不如 MkDocs Material 主题精美
- 自定义能力有限

---

## 2. pdoc（轻量级）

### 特点

- ✅ 更轻量
- ✅ 零配置
- ✅ 简单易用

### 安装

```bash
pip install pdoc
```

### 使用

```bash
pdoc --html --output-dir docs/html NTRT.data_cleaner
```

---

## 3. pydoc（Python 内置）

### 特点

- ✅ **无需安装**：Python 自带
- ✅ **零配置**
- ✅ 样式较基础

### 使用

```bash
# 生成 HTML
python -m pydoc -w NTRT.data_cleaner

# 启动服务器
python -m pydoc -p 8080
```

---

## 4. 快速对比

### MkDocs（当前方案）

**优点**：
- 样式最精美
- 功能最强大
- 支持搜索、导航等

**缺点**：
- ❌ 需要写 Markdown 文件
- ❌ 需要配置 mkdocs.yml
- ❌ 需要了解 mkdocstrings 语法
- ❌ 自动化程度低

### pdoc3（推荐替代方案）

**优点**：
- ✅ **完全自动化**：一条命令生成
- ✅ **零配置**：无需配置文件
- ✅ **代码即文档**：代码更新，文档自动更新
- ✅ **简单易用**：不需要写 Markdown

**缺点**：
- 样式不如 MkDocs Material
- 自定义能力有限

---

## 🎯 推荐方案

### 如果你想要：

1. **最简单的方案** → 使用 **pdoc3**
   ```bash
   pip install pdoc3
   pdoc3 --html --output-dir docs/html NTRT
   ```

2. **最精美的方案** → 继续使用 **MkDocs**（但需要更多配置）

3. **折中方案** → 使用 **pdoc3 生成 HTML** + **手动整理重要文档**

---

## 📝 实际使用示例

### 使用 pdoc3 生成文档

```bash
# 1. 安装
pip install pdoc3

# 2. 生成文档（一条命令）
pdoc3 --html --output-dir docs/html NTRT

# 3. 查看结果
# 打开 docs/html/NTRT/index.html
```

### 使用项目中的脚本

1. 打开 `MkDocs_doc/scripts/generate_html_docs.py`
2. 修改配置：
   ```python
   MODULE_PATH = "NTRT.data_cleaner"
   OUTPUT_DIR = Path("docs/html_docs")
   ```
3. 在 PyCharm 中运行

---

## 🔄 工作流程对比

### MkDocs 工作流程

```
写代码 → 写 Markdown → 配置 mkdocs.yml → 
运行脚本生成语法 → mkdocs build → 查看文档
```

**步骤多，配置复杂**

### pdoc3 工作流程

```
写代码 → pdoc3 --html → 查看文档
```

**两步搞定！**

---

## 💡 建议

如果你觉得 MkDocs 太复杂，可以：

1. **短期方案**：使用 pdoc3 快速生成 HTML 文档
2. **长期方案**：继续使用 MkDocs，但简化流程
   - 只维护 `api.md`（自动生成）
   - 其他文档手动编写

或者**混合使用**：
- 使用 pdoc3 生成完整的 API 文档（HTML）
- 使用 MkDocs 生成项目概述和使用指南（Markdown）

---

## 📚 相关资源

- [pdoc3 官方文档](https://pdoc3.github.io/pdoc/)
- [pdoc 官方文档](https://github.com/mitmproxy/pdoc)
- 项目中的生成脚本：`MkDocs_doc/scripts/generate_html_docs.py`

