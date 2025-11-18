# mkdocstrings 自动生成文档说明

## 理解 mkdocstrings 的作用

### ❌ 误解：mkdocstrings 会自动生成 .md 文件

**不对！** mkdocstrings **不会**自动生成 .md 文件。

### ✅ 实际作用：mkdocstrings 在构建时动态生成 HTML

mkdocstrings 的工作流程：

1. **你手动写** `.md` 文件，使用 `::: 模块路径` 语法
2. **mkdocstrings 读取**这些语法
3. **构建时动态**从 Python 代码中提取文档
4. **自动渲染**成 HTML 文档

**优点**：
- ✅ 代码更新，文档自动更新（因为直接从代码读取）
- ✅ 不需要维护两份文档（代码和文档）
- ✅ 样式统一，功能强大（搜索、导航等）

**缺点**：
- ❌ 需要手动写 `::: 模块路径` 语法
- ❌ 需要知道模块路径

## 解决方案：自动化生成包含 mkdocstrings 语法的 .md 文件

我们创建了 `generate_mkdocstrings_md.py` 脚本，可以：

1. **自动扫描**代码目录
2. **自动发现**所有类和函数
3. **自动生成**包含 mkdocstrings 语法的 .md 文件
4. **自动分类**组织文档结构

### 使用方法

```bash
# 运行脚本，自动生成 api.md 文件
python MkDocs_doc/scripts/generate_mkdocstrings_md.py
```

脚本会自动：
- 扫描 `code_liu/NTRT/` 目录，生成 `docs/projects/ntrt/api.md`
- 扫描 `code_liu/RCSB_PDB/src/` 目录，生成 `docs/projects/rcsb_pdb/api.md`

### 生成的文件示例

生成的 `api.md` 文件包含：

```markdown
# NTRT 项目 - API 参考

## 数据清洗模块

### DataCleaner

::: NTRT.data_cleaner.DataCleaner
    handler: python
    options:
      show_root_heading: true
      show_source: true
      show_signature_annotations: true
```

### 然后 mkdocstrings 会自动：

当你运行 `mkdocs build` 时：
1. 读取 `::: NTRT.data_cleaner.DataCleaner`
2. 找到 `code_liu/NTRT/data_cleaner.py` 文件
3. 解析代码，提取 docstring、方法、参数等
4. 渲染成漂亮的 HTML 文档

## 完整工作流程

### 第一次使用

```bash
# 1. 运行脚本生成 .md 文件
python MkDocs_doc/scripts/generate_mkdocstrings_md.py

# 2. 查看生成的文件，可以手动添加描述
# 编辑 docs/projects/ntrt/api.md，添加说明文字

# 3. 构建文档
cd MkDocs_doc
mkdocs serve
```

### 代码更新后

```bash
# 重新运行脚本更新文档
python MkDocs_doc/scripts/generate_mkdocstrings_md.py

# 构建查看
cd MkDocs_doc
mkdocs serve
```

### 集成到 GitHub Actions

在 `.github/workflows/mkdocs-deploy.yml` 中添加：

```yaml
- name: Generate API documentation
  run: |
    python MkDocs_doc/scripts/generate_mkdocstrings_md.py
```

这样每次 push 代码时，会自动：
1. 生成最新的 api.md 文件
2. 构建文档
3. 部署到 GitHub Pages

## 两种方案对比

### 方案 1：完全手动（原始方式）

```markdown
# 手动写
::: NTRT.data_cleaner.DataCleaner
    handler: python
```

**优点**：完全控制
**缺点**：需要知道所有模块路径，容易出错

### 方案 2：脚本自动生成（推荐）

```bash
# 运行脚本自动生成
python generate_mkdocstrings_md.py
```

**优点**：
- ✅ 自动发现所有类和函数
- ✅ 自动生成正确的模块路径
- ✅ 自动分类组织
- ✅ 代码更新后重新运行即可

**缺点**：需要运行一次脚本

## 总结

1. **mkdocstrings 不会生成 .md 文件**，它是在构建时从代码读取文档
2. **你需要写 .md 文件**，使用 `::: 模块路径` 语法
3. **但可以用脚本自动生成**这些 .md 文件
4. **之后代码更新**，文档会自动更新（因为 mkdocstrings 直接从代码读取）

## 下一步

1. 运行 `python MkDocs_doc/scripts/generate_mkdocstrings_md.py`
2. 查看生成的 `api.md` 文件
3. 可以手动添加描述和说明
4. 运行 `mkdocs serve` 查看效果

