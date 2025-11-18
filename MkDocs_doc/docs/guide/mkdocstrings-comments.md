# mkdocstrings 与代码注释

## 重要说明

**mkdocstrings 主要解析 docstring（三引号字符串），不是普通的 `# 注释`**

但是，通过 `show_source: true` 选项，可以显示源代码，源代码中会包含所有注释。

## 两种注释类型

### 1. Docstring（会被解析）

**格式**：使用三引号 `"""` 或 `'''`

```python
class DataCleaner:
    """数据清洗类，负责数据库操作和数据清洗流程
    
    这个类提供了以下功能：
    - 清洗 breadth_search 字段
    - 清洗 cited_articles 字段
    - 批量处理数据库记录
    """
    
    def __init__(self):
        """初始化数据清洗器。
        
        :author: LZD
        :date: 2025/11/10
        """
        pass
```

**mkdocstrings 会解析**：
- ✅ 类的 docstring
- ✅ 方法的 docstring
- ✅ 函数的 docstring
- ✅ 模块的 docstring

### 2. 普通注释（不会直接解析，但可以显示）

**格式**：使用 `#` 开头

```python
class DataCleaner:
    # 这是普通注释，mkdocstrings 不会解析
    # 但可以通过 show_source 显示源代码时看到
    
    def __init__(self):
        self.db_key = DEFAULT_DB_KEY  # 数据库键名
        self.batch_size = BATCH_SIZE  # 批处理大小
```

**mkdocstrings 不会解析**：
- ❌ 普通 `#` 注释
- ❌ 行内注释

**但可以通过 `show_source: true` 显示源代码**，源代码中会包含所有注释。

## 实际示例

### 示例 1：解析 Docstring

**代码**：
```python
class DataCleaner:
    """数据清洗类，负责数据库操作和数据清洗流程
    
    这个类提供了以下功能：
    - 清洗 breadth_search 字段
    - 清洗 cited_articles 字段
    """
    
    def run(self):
        """执行所有清洗任务。
        
        :author: LZD
        :date: 2025/11/10
        """
        pass
```

**在 .md 文件中使用**：
```markdown
::: NTRT.data_cleaner.DataCleaner
    handler: python
    options:
      show_root_heading: true
```

**mkdocstrings 会显示**：
- ✅ 类的 docstring："数据清洗类，负责数据库操作..."
- ✅ 方法的 docstring："执行所有清洗任务..."
- ✅ 参数说明（如果有）
- ✅ 返回值说明（如果有）

### 示例 2：显示源代码（包含注释）

**代码**：
```python
class DataCleaner:
    """数据清洗类"""
    
    def __init__(self):
        """初始化"""
        # 设置数据库键名
        self.db_key = DEFAULT_DB_KEY
        # 设置批处理大小
        self.batch_size = BATCH_SIZE
```

**在 .md 文件中使用**：
```markdown
::: NTRT.data_cleaner.DataCleaner
    handler: python
    options:
      show_root_heading: true
      show_source: true  # 显示源代码
```

**mkdocstrings 会显示**：
- ✅ 类的 docstring
- ✅ 源代码（包含所有 `#` 注释）

### 示例 3：完整示例

让我们看看实际代码中的例子：

**实际代码**（`code_liu/NTRT/data_cleaner.py`）：

```python
class DataCleaner:
    """数据清洗类，负责数据库操作和数据清洗流程"""

    def __init__(self):
        """初始化数据清洗器。

        :author: LZD
        :date: 2025/11/10
        """
        self.db_key = DEFAULT_DB_KEY
        self.batch_size = BATCH_SIZE
        try:
            self._task_list_model = NsfcTopicRcmdTaskListModel()
            self._topic_list_model = NsfcTopicRcmdTaskTopicListModel()
            self._app_info_model = NsfcTopicRcmdTaskAppInfoModel()
        except Exception as exc:
            raise RuntimeError(f"初始化数据模型失败: {exc}") from exc

    def _process_records(self, records, field_name, processor_func):
        """对查询结果进行处理并生成更新内容。
        
        :param records: 原始记录列表
        :param field_name: 需要处理的字段名
        :param processor_func: 数据处理函数
        :return: (updates, processed_count, skipped_count)
        """
        # ORM 会自动将 JSON 字段反序列化为 Python 对象（dict/list）
        # 如果已经是 dict 或 list，直接使用；如果是字符串，则解析 JSON
        updates = []
        processed_count = 0
        skipped_count = 0
        
        for record in records:
            # 处理每条记录...
            pass
```

**在 .md 文件中使用**：

```markdown
::: NTRT.data_cleaner.DataCleaner
    handler: python
    options:
      show_root_heading: true
      show_source: true
      show_signature_annotations: true
```

**mkdocstrings 会显示**：

1. **类的 docstring**："数据清洗类，负责数据库操作..."
2. **方法的 docstring**：
   - `__init__`: "初始化数据清洗器..."
   - `_process_records`: "对查询结果进行处理..."
3. **参数说明**（从 docstring 中解析）：
   - `records`: 原始记录列表
   - `field_name`: 需要处理的字段名
   - `processor_func`: 数据处理函数
4. **返回值说明**：`(updates, processed_count, skipped_count)`
5. **源代码**（如果 `show_source: true`）：
   - 包含所有 `#` 注释
   - 包含完整的代码实现

## 最佳实践

### 1. 使用 Docstring 而不是普通注释

**推荐**：
```python
def process_data(data):
    """处理数据。
    
    这个函数会对输入数据进行清洗和标准化处理。
    
    Args:
        data: 原始数据字典
    
    Returns:
        处理后的数据字典
    """
    # 实现代码...
```

**不推荐**（只使用注释）：
```python
def process_data(data):
    # 处理数据
    # 这个函数会对输入数据进行清洗和标准化处理
    # 参数：data - 原始数据字典
    # 返回：处理后的数据字典
    pass
```

### 2. 结合使用 Docstring 和源代码显示

```markdown
::: NTRT.data_cleaner.DataCleaner
    handler: python
    options:
      show_root_heading: true
      show_source: true  # 显示源代码（包含注释）
```

这样既能看到：
- ✅ 结构化的文档（从 docstring 解析）
- ✅ 完整的源代码（包含所有注释）

### 3. 在 Docstring 中添加详细说明

```python
def complex_function(param1, param2):
    """复杂函数说明。
    
    这个函数实现了以下功能：
    1. 数据验证
    2. 数据转换
    3. 数据存储
    
    Args:
        param1: 参数1说明
            - 类型：dict
            - 必需字段：['id', 'name']
        param2: 参数2说明
    
    Returns:
        处理结果字典，包含：
        - success: 是否成功
        - data: 处理后的数据
        - errors: 错误列表
    
    Raises:
        ValueError: 当参数格式不正确时
        RuntimeError: 当处理失败时
    
    Example:
        >>> result = complex_function({'id': 1, 'name': 'test'}, 'option')
        >>> print(result['success'])
        True
    
    Note:
        这个函数是线程安全的。
    
    Warning:
        大量数据可能导致内存问题。
    """
    pass
```

## 查看实际效果

### 方法 1：查看生成的文档

运行：
```bash
cd MkDocs_doc
mkdocs serve
```

访问：
- `http://127.0.0.1:8000/projects/ntrt/api/`
- 查看 `DataCleaner` 类的文档

### 方法 2：查看源代码

在文档页面中，如果设置了 `show_source: true`，会显示：
- 完整的源代码
- 所有 `#` 注释
- 代码结构

## 总结

| 注释类型 | mkdocstrings 是否解析 | 如何显示 |
|---------|---------------------|---------|
| **Docstring** (`"""`) | ✅ 是 | 自动解析并结构化显示 |
| **普通注释** (`#`) | ❌ 否 | 通过 `show_source: true` 显示源代码时可见 |

**建议**：
- ✅ 使用 Docstring 编写主要文档
- ✅ 使用 `#` 注释解释代码逻辑
- ✅ 设置 `show_source: true` 显示完整源代码

这样既能获得结构化的文档，又能看到完整的代码实现和注释。

