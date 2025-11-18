# mkdocstrings 适合生成哪些文档？

## 导航结构分析

根据 `mkdocs.yml` 中的配置，每个项目包含 4 个文档：

```yaml
- 国自然选题推荐数据清洗:
  - 文档概述: projects/ntrt/index.md      # 1
  - 系统全景: projects/ntrt/api.md        # 2 ⭐
  - 核心模块: projects/ntrt/guide.md      # 3
  - 更新日志: projects/ntrt/update.md     # 4
```

## 各文件用途分析

### 1. 文档概述 (index.md)

**内容**：
- 项目介绍
- 快速开始
- 项目结构
- 文档导航

**是否需要 mkdocstrings**：❌ **不需要**

**原因**：
- 主要是说明性文字
- 不涉及具体的 API 文档
- 手动编写更灵活

**示例内容**：
```markdown
# 项目概述

## 快速开始

```python
from NTRT.data_cleaner import DataCleaner
cleaner = DataCleaner()
cleaner.run()
```
```

---

### 2. 系统全景 (api.md) ⭐

**内容**：
- 所有类和函数的 API 文档
- 方法签名、参数、返回值
- 类型注解
- 源代码

**是否需要 mkdocstrings**：✅ **最适合！**

**原因**：
- 需要展示所有 API
- 需要从代码自动提取文档
- 代码更新时文档自动更新
- 结构化展示类、方法、参数等

**当前使用情况**：
```markdown
::: NTRT.data_cleaner.DataCleaner
    handler: python
    options:
      show_root_heading: true
      show_source: true
      show_signature_annotations: true
```

**推荐**：✅ **使用 `generate_mkdocstrings_md.py` 自动生成**

---

### 3. 核心模块 (guide.md)

**内容**：
- 架构说明
- 使用示例
- 最佳实践
- 常见问题

**是否需要 mkdocstrings**：⚠️ **可选**

**原因**：
- 主要是说明性文档
- 可以引用 API，但不需要完整展示
- 可以手动编写，更灵活

**使用场景**：
- 可以在 guide.md 中少量使用 mkdocstrings 引用关键类
- 但不需要像 api.md 那样完整展示所有 API

**示例**：
```markdown
## DataCleaner 类

数据清洗的核心类。

::: NTRT.data_cleaner.DataCleaner
    handler: python
    options:
      show_root_heading: true
      members:
        - run_all
        - clean_breadth_search
```

---

### 4. 更新日志 (update.md)

**内容**：
- 版本历史
- 更新记录
- 变更说明

**是否需要 mkdocstrings**：❌ **不需要**

**原因**：
- 纯文本内容
- 手动维护更合适
- 不涉及代码文档

---

## 总结对比

| 文件 | 用途 | mkdocstrings | 自动生成 | 说明 |
|------|------|-------------|---------|------|
| **index.md** | 项目概述 | ❌ 不需要 | ❌ | 说明性文档 |
| **api.md** | API 参考 | ✅ **最适合** | ✅ **推荐** | 完整 API 文档 |
| **guide.md** | 使用指南 | ⚠️ 可选 | ❌ | 少量引用即可 |
| **update.md** | 更新日志 | ❌ 不需要 | ❌ | 手动维护 |

## 推荐方案

### 方案 1：完全自动化（推荐）

**api.md** 使用脚本自动生成：

```bash
# 运行脚本自动生成
python MkDocs_doc/scripts/generate_mkdocstrings_md.py
```

**优点**：
- ✅ 自动发现所有类和函数
- ✅ 自动生成正确的模块路径
- ✅ 代码更新后重新运行即可

### 方案 2：手动编写（灵活）

**api.md** 手动编写，但使用 mkdocstrings 语法：

```markdown
# API 参考

## 核心类

### DataCleaner

::: NTRT.data_cleaner.DataCleaner
    handler: python
    options:
      show_root_heading: true
```

**优点**：
- ✅ 完全控制文档结构
- ✅ 可以添加自定义说明
- ✅ 可以选择性展示

**缺点**：
- ❌ 需要手动维护
- ❌ 容易遗漏新的类/函数

### 方案 3：混合方案（最佳实践）

1. **api.md** - 使用脚本自动生成基础结构
2. **手动编辑** - 添加描述和说明
3. **代码更新后** - 重新运行脚本更新

**工作流程**：
```bash
# 1. 自动生成基础结构
python scripts/generate_mkdocstrings_md.py

# 2. 手动编辑，添加描述
# 编辑 docs/projects/ntrt/api.md

# 3. 代码更新后，重新生成
python scripts/generate_mkdocstrings_md.py
```

## 实际使用建议

### 对于 api.md（系统全景）

✅ **强烈推荐使用 mkdocstrings**

**原因**：
1. 需要展示完整的 API
2. 代码更新时文档自动更新
3. 结构化展示更清晰
4. 减少维护成本

**当前实现**：
- ✅ 已使用 `generate_mkdocstrings_md.py` 自动生成
- ✅ 包含所有类和函数的 mkdocstrings 语法
- ✅ 代码更新后重新运行脚本即可

### 对于其他文件

- **index.md**：手动编写，不需要 mkdocstrings
- **guide.md**：手动编写，可少量引用关键 API
- **update.md**：手动维护，不需要 mkdocstrings

## 结论

**mkdocstrings 最适合生成：`api.md`（系统全景）**

这是唯一需要完整展示所有 API 的文档，使用 mkdocstrings 可以：
- ✅ 自动从代码提取文档
- ✅ 保持文档与代码同步
- ✅ 结构化展示所有 API
- ✅ 减少维护成本

其他文件（index.md、guide.md、update.md）主要是说明性文档，手动编写更合适。

