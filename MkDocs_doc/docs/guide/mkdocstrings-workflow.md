# mkdocstrings 工作流程说明

## 工作原理

### 1. 配置路径（mkdocs.yml）

```yaml
plugins:
  - mkdocstrings:
      handlers:
        python:
          paths: 
            - ../code_liu  # 代码根目录
```

**作用**：告诉 mkdocstrings 在哪里查找 Python 代码。

### 2. 模块路径计算规则

**规则**：从 `paths` 配置的目录开始，按照 Python 包结构计算模块路径。

**示例**：

| 文件路径 | 模块路径 |
|---------|---------|
| `code_liu/NTRT/data_cleaner.py` | `NTRT.data_cleaner` |
| `code_liu/NTRT/application/NsfcTopicRcmdModels.py` | `NTRT.application.NsfcTopicRcmdModels` |
| `code_liu/RCSB_PDB/src/spiders/rcsb_pdb/rcsb_pdb_spider.py` | `RCSB_PDB.src.spiders.rcsb_pdb.rcsb_pdb_spider` |

**注意**：
- 路径中的 `/` 或 `\` 替换为 `.`
- 去掉 `.py` 扩展名
- 从 `paths` 配置的目录开始计算

### 3. 在 .md 文件中引用

使用 `::: 模块路径` 语法：

```markdown
::: NTRT.data_cleaner.DataCleaner
    handler: python
    options:
      show_root_heading: true
      show_source: true
```

### 4. 构建时自动生成

运行 `mkdocs build` 时：
1. mkdocstrings 读取 `.md` 文件中的 `::: 模块路径`
2. 根据 `paths` 配置找到对应的 Python 文件
3. 解析代码，提取 docstring、类、函数等信息
4. 渲染成 HTML 文档

## 完整工作流程

### 步骤 1：配置路径（已完成）

✅ 已在 `mkdocs.yml` 中配置：
```yaml
paths: 
  - ../code_liu
```

### 步骤 2：创建 .md 文档文件（已完成）

✅ 已创建：
- `docs/projects/ntrt/api.md`
- `docs/projects/rcsb_pdb/api.md`

### 步骤 3：运行构建

```bash
# 进入 MkDocs 目录
cd MkDocs_doc

# 本地预览（推荐先测试）
mkdocs serve

# 或直接构建
mkdocs build
```

### 步骤 4：查看结果

- **本地预览**：访问 `http://127.0.0.1:8000`
- **构建输出**：查看 `MkDocs_doc/site/` 目录

## 模块路径示例

### NTRT 项目

| 文件 | 模块路径 | 引用语法 |
|------|---------|---------|
| `code_liu/NTRT/data_cleaner.py` | `NTRT.data_cleaner` | `::: NTRT.data_cleaner` |
| `code_liu/NTRT/data_cleaner.py` 中的 `DataCleaner` 类 | `NTRT.data_cleaner.DataCleaner` | `::: NTRT.data_cleaner.DataCleaner` |
| `code_liu/NTRT/application/NsfcTopicRcmdModels.py` | `NTRT.application.NsfcTopicRcmdModels` | `::: NTRT.application.NsfcTopicRcmdModels` |
| `code_liu/NTRT/base_mysql.py` | `NTRT.base_mysql` | `::: NTRT.base_mysql` |

### RCSB_PDB 项目

| 文件 | 模块路径 | 引用语法 |
|------|---------|---------|
| `code_liu/RCSB_PDB/src/spiders/rcsb_pdb/rcsb_pdb_spider.py` | `RCSB_PDB.src.spiders.rcsb_pdb.rcsb_pdb_spider` | `::: RCSB_PDB.src.spiders.rcsb_pdb.rcsb_pdb_spider` |
| `RcsbAllApiSpider` 类 | `RCSB_PDB.src.spiders.rcsb_pdb.rcsb_pdb_spider.RcsbAllApiSpider` | `::: RCSB_PDB.src.spiders.rcsb_pdb.rcsb_pdb_spider.RcsbAllApiSpider` |
| `code_liu/RCSB_PDB/src/spiders/rcsb_pdb/field_filter.py` | `RCSB_PDB.src.spiders.rcsb_pdb.field_filter` | `::: RCSB_PDB.src.spiders.rcsb_pdb.field_filter` |

## 常见问题

### 问题 1：找不到模块

**错误**：`Could not find 'NTRT.data_cleaner' in the following paths`

**解决**：
1. 检查 `paths` 配置是否正确
2. 确认文件路径：`code_liu/NTRT/data_cleaner.py` 是否存在
3. 检查模块路径是否正确（注意大小写）

### 问题 2：模块路径错误

**错误**：`ModuleNotFoundError`

**解决**：
- 确保从 `paths` 配置的目录开始计算
- 检查目录名是否正确（`NTRT` vs `ntrt`）
- 确保 Python 文件在正确的目录结构中

### 问题 3：没有显示内容

**可能原因**：
1. 类/函数没有 docstring
2. `show_if_no_docstring: false` 且没有 docstring
3. 模块路径错误

**解决**：
- 添加 docstring
- 设置 `show_if_no_docstring: true`
- 检查模块路径

## 快速测试

### 测试单个模块

1. 创建测试文件 `docs/test.md`：
```markdown
# 测试

::: NTRT.data_cleaner.DataCleaner
    handler: python
    options:
      show_root_heading: true
      show_source: true
```

2. 运行预览：
```bash
cd MkDocs_doc
mkdocs serve
```

3. 访问 `http://127.0.0.1:8000/test/` 查看结果

### 验证模块路径

如果不确定模块路径，可以：

1. **查看文件结构**：
```bash
# Windows
tree /F code_liu

# 或使用 Python
python -c "from pathlib import Path; [print(p) for p in Path('code_liu').rglob('*.py')]"
```

2. **测试导入**：
```python
# 在 Python 中测试
import sys
sys.path.insert(0, 'code_liu')
from NTRT.data_cleaner import DataCleaner  # 如果能导入，说明路径正确
```

## 下一步

1. ✅ 配置路径（已完成）
2. ✅ 创建文档文件（已完成）
3. ⏭️ 运行 `mkdocs serve` 测试
4. ⏭️ 根据需要调整模块路径
5. ⏭️ 推送到 GitHub，自动部署

