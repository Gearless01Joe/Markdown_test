# PyCharm 中使用 code_to_markdown.py

## 快速开始

### 在 PyCharm 中直接运行

1. **打开脚本**：`MkDocs_doc/scripts/code_to_markdown.py`

2. **修改配置**（脚本顶部，第 534-548 行）：

```python
# ========== PyCharm 直接运行配置 ==========
# 配置：要转换的源代码目录或文件
CONVERT_NTRT_PROJECT = True      # 是否转换 NTRT 项目
CONVERT_RCSB_PDB_PROJECT = True  # 是否转换 RCSB PDB 项目

# 选项2: 转换单个文件（如果设置了，会优先使用）
CONVERT_SINGLE_FILE = None       # 例如: "code_liu/NTRT/data_cleaner.py"

# 输出目录配置
OUTPUT_TO_DOCS = True            # 是否输出到 docs 目录
OUTPUT_SUBDIR = "generated"      # docs 下的子目录
```

3. **右键运行**：在 PyCharm 中右键点击脚本 → `Run 'code_to_markdown'`

## 配置选项说明

### 转换目标配置

#### 选项 1：转换整个项目

```python
CONVERT_NTRT_PROJECT = True      # 转换 NTRT 项目
CONVERT_RCSB_PDB_PROJECT = True  # 转换 RCSB PDB 项目
```

**输出位置**：
- `docs/generated/NTRT/` - NTRT 项目的文档
- `docs/generated/RCSB_PDB/` - RCSB PDB 项目的文档

#### 选项 2：转换单个文件

```python
CONVERT_SINGLE_FILE = "code_liu/NTRT/data_cleaner.py"
```

**输出位置**：
- `docs/generated/data_cleaner/data_cleaner.md`

**注意**：如果设置了 `CONVERT_SINGLE_FILE`，会优先使用，忽略项目配置。

### 输出目录配置

```python
OUTPUT_TO_DOCS = True            # 输出到 docs 目录
OUTPUT_SUBDIR = "generated"      # 子目录名称
```

**输出路径**：
- `True` → `MkDocs_doc/docs/generated/`
- `False` → 源代码目录下的 `_docs` 目录

## 使用示例

### 示例 1：转换 NTRT 项目

```python
CONVERT_NTRT_PROJECT = True
CONVERT_RCSB_PDB_PROJECT = False
CONVERT_SINGLE_FILE = None
```

**结果**：只转换 NTRT 项目，输出到 `docs/generated/NTRT/`

### 示例 2：转换单个文件

```python
CONVERT_SINGLE_FILE = "code_liu/NTRT/data_cleaner.py"
CONVERT_NTRT_PROJECT = False
```

**结果**：只转换 `data_cleaner.py`，输出到 `docs/generated/data_cleaner/data_cleaner.md`

### 示例 3：转换所有项目

```python
CONVERT_NTRT_PROJECT = True
CONVERT_RCSB_PDB_PROJECT = True
CONVERT_SINGLE_FILE = None
```

**结果**：转换两个项目，分别输出到对应的目录

## Sphinx 风格 Docstring 支持

脚本**优先支持 Sphinx 风格**的 docstring，支持以下格式：

### 参数说明

```python
def function(param1, param2):
    """函数说明。
    
    :param param1: 参数1的说明
    :param param2: 参数2的说明
    :type param1: str
    :type param2: int
    """
```

### 返回值说明

```python
def function():
    """函数说明。
    
    :return: 返回值说明
    :rtype: dict
    """
```

### 异常说明

```python
def function():
    """函数说明。
    
    :raises ValueError: 当参数无效时
    :raises RuntimeError: 当处理失败时
    """
```

### 完整示例

```python
def process_data(data, max_size=100):
    """处理数据。
    
    这个函数会对输入数据进行清洗和标准化处理。
    
    :param data: 原始数据字典，必须包含 'id' 和 'name' 字段
    :type data: dict
    :param max_size: 最大处理数量，默认为 100
    :type max_size: int
    :return: 处理结果字典，包含 success 和 processed_count
    :rtype: dict
    :raises ValueError: 当 data 格式不正确时
    :raises RuntimeError: 当处理失败时
    """
    pass
```

## 输出示例

转换后的 Markdown 文档包含：

### 模块信息
- 模块 docstring
- 模块路径
- 导入信息

### 类文档
- 类名和 docstring
- 继承关系
- 类属性列表
- 方法列表（包含签名、参数说明、返回值说明、异常说明）

### 函数文档
- 函数签名
- docstring
- 参数说明（从 Sphinx 风格解析）
- 返回值说明（从 Sphinx 风格解析）
- 异常说明（从 Sphinx 风格解析）

## 常见问题

### Q: 如何只转换一个文件？

A: 设置 `CONVERT_SINGLE_FILE = "code_liu/NTRT/data_cleaner.py"`，并设置项目配置为 `False`。

### Q: 输出到哪里？

A: 默认输出到 `MkDocs_doc/docs/generated/` 目录。可以通过 `OUTPUT_TO_DOCS` 和 `OUTPUT_SUBDIR` 配置。

### Q: 支持哪些 docstring 风格？

A: **优先支持 Sphinx 风格**，如果没有找到 Sphinx 风格，会回退到 Google 风格。

### Q: 如何查看转换结果？

A: 转换完成后，查看 `MkDocs_doc/docs/generated/` 目录下的 `.md` 文件。

## 与 mkdocstrings 的区别

| 特性 | code_to_markdown | mkdocstrings |
|------|------------------|--------------|
| 输出格式 | 直接生成 .md 文件 | 在构建时生成 HTML |
| Docstring 解析 | 自己解析（支持 Sphinx） | 使用 griffe 解析 |
| 独立性 | 可以独立使用 | 需要 MkDocs |
| 使用场景 | 生成静态文档文件 | 动态文档站点 |

**建议**：
- 需要静态文档文件 → 使用 `code_to_markdown`
- 需要交互式文档站点 → 使用 `mkdocstrings`

