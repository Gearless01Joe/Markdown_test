# MkDocs 完整 Docstring 指南

## 一、MkDocs 期望的完整 Docstring 结构

MkDocs 使用 mkdocstrings 插件来解析 docstring，支持 Google、NumPy、Sphinx 三种风格。由于你使用的是 Google 风格，下面以 Google 风格为例说明。

## 二、Google 风格 Docstring 完整结构

### 1. 模块级别 Docstring

```python
"""模块的简短描述（一行）。

模块的详细描述，可以多行。
这里可以说明模块的主要功能、用途等。

本模块提供了以下功能：
- 功能1
- 功能2
- 功能3

示例:
    >>> import module
    >>> obj = module.Class()
    >>> obj.method()

注意:
    重要注意事项或警告信息。

作者: 作者名
日期: 2025/01/01
版本: 1.0.0
"""
```

### 2. 类级别 Docstring

```python
class MyClass:
    """类的简短描述（一行）。
    
    类的详细描述，可以多行。
    说明类的主要功能、用途、设计思路等。
    
    本类提供了以下功能：
    - 功能1
    - 功能2
    
    属性:
        attr1 (type): 属性1的描述
        attr2 (type): 属性2的描述
    
    使用示例:
        >>> obj = MyClass(param1, param2)
        >>> result = obj.method()
    
    注意:
        使用注意事项。
    
    警告:
        重要警告信息。
    
    作者: 作者名
    日期: 2025/01/01
    """
```

### 3. 方法/函数级别 Docstring（完整版）

```python
def my_function(param1, param2, param3=None, *args, **kwargs):
    """函数的简短描述（一行）。
    
    函数的详细描述，可以多行。
    说明函数的功能、用途、工作原理等。
    
    Args:
        param1 (type): 参数1的描述
            可以多行描述，说明参数的详细要求。
        param2 (type): 参数2的描述
        param3 (type, optional): 可选参数的描述，默认值为 None
        *args: 可变位置参数的描述
        **kwargs: 可变关键字参数的描述
            - key1 (type): 关键字参数1的描述
            - key2 (type): 关键字参数2的描述
    
    Returns:
        type: 返回值的描述
            可以多行描述返回值的格式、内容等。
    
    Yields:
        type: 如果是生成器，描述 yield 的值
    
    Raises:
        ValueError: 当参数无效时抛出
        TypeError: 当类型错误时抛出
        RuntimeError: 当运行时错误时抛出
    
    示例:
        >>> result = my_function(1, 2, param3=3)
        >>> print(result)
        6
        
        更复杂的示例:
        >>> data = [1, 2, 3]
        >>> result = my_function(data, process=True)
        >>> print(result)
        [2, 4, 6]
    
    注意:
        使用注意事项。
    
    警告:
        重要警告信息。
    
    作者: 作者名
    日期: 2025/01/01
    """
```

## 三、各部分详细说明

### 1. 简短描述（必需）

**格式**：第一行，简洁明了

```python
def my_function():
    """这是简短描述。"""
```

**要求**：
- 一行，不超过 80 个字符
- 以句号结尾
- 使用祈使语气（"处理数据"而不是"这个函数处理数据"）

### 2. 详细描述（可选但推荐）

**格式**：简短描述后的空行，然后是多行描述

```python
def my_function():
    """简短描述。
    
    这是详细描述，可以多行。
    说明函数的工作原理、使用场景等。
    """
```

### 3. Args（参数说明）

**格式**：
```python
Args:
    param_name (type): 参数描述
    param_name2 (type, optional): 可选参数描述，默认值为 value
```

**完整示例**：
```python
Args:
    records (list[dict]): 原始记录列表，格式为 [{'id': 1, 'data': {...}}, ...]
    field_name (str): 需要处理的字段名，必须是有效的字段名
    processor_func (callable): 数据处理函数
        函数签名: (data: dict) -> dict
        函数应该接收原始数据，返回处理后的数据
    batch_size (int, optional): 批处理大小，默认值为 100
        建议值范围: 10-1000
```

**类型说明**：
- `int`: 整数
- `str`: 字符串
- `list`: 列表
- `dict`: 字典
- `list[dict]`: 字典列表
- `callable`: 可调用对象（函数）
- `Optional[type]`: 可选类型，等同于 `(type, optional)`
- `Union[type1, type2]`: 联合类型

### 4. Returns（返回值说明）

**格式**：
```python
Returns:
    type: 返回值描述
```

**完整示例**：
```python
Returns:
    tuple[list[tuple[int, dict]], int, int]: 包含三个元素的元组
        - 第一个元素: 更新列表，格式为 [(id, processed_data), ...]
        - 第二个元素: 处理成功的数量
        - 第三个元素: 跳过的数量
```

**多返回值示例**：
```python
Returns:
    dict: 操作结果字典
        - result (bool): 操作是否成功
        - msg (str): 操作结果消息
        - data (dict, optional): 返回的数据，仅在成功时存在
```

### 5. Yields（生成器说明）

**格式**：
```python
Yields:
    type: yield 的值描述
```

**示例**：
```python
def parse_items(self, response):
    """解析响应并生成项目。
    
    Yields:
        scrapy.Item: 解析得到的项目对象
    """
    for item in items:
        yield item
```

### 6. Raises（异常说明）

**格式**：
```python
Raises:
    ExceptionType: 异常描述
```

**完整示例**：
```python
Raises:
    ValueError: 当参数无效时抛出，例如 field_name 不存在
    TypeError: 当参数类型错误时抛出
    RuntimeError: 当运行时错误时抛出，例如数据库连接失败
    KeyError: 当字典键不存在时抛出
```

### 7. 示例（Examples）

**格式**：
```python
示例:
    >>> code_example()
    result
    
    更复杂的示例:
    >>> complex_example()
    result
```

**完整示例**：
```python
示例:
    >>> cleaner = DataCleaner()
    >>> cleaner.run()
    开始执行数据清洗任务
    数据库: medicine
    ============================================================
    
    批量处理示例:
    >>> records = [{'id': 1, 'data': {...}}, {'id': 2, 'data': {...}}]
    >>> result = process_records(records, 'field_name', processor)
    >>> print(result)
    ([(1, {...}), (2, {...})], 2, 0)
```

### 8. 注意（Note）

**格式**：
```python
注意:
    注意事项说明。
```

**示例**：
```python
注意:
    - 此方法会修改数据库，请谨慎使用
    - 建议在生产环境使用前先测试
    - 处理大量数据时可能需要较长时间
```

### 9. 警告（Warning）

**格式**：
```python
警告:
    警告信息。
```

**示例**：
```python
警告:
    此方法会清空数据库，请确保已备份数据！
```

### 10. 作者和日期（可选）

**格式**：
```python
作者: 作者名
日期: 2025/01/01
版本: 1.0.0
```

## 四、实际代码示例

### 示例1：简单函数

```python
def add(a, b):
    """计算两个数字之和。
    
    Args:
        a (int | float): 第一个数字
        b (int | float): 第二个数字
    
    Returns:
        int | float: 两个数字的和
    
    示例:
        >>> add(1, 2)
        3
        >>> add(1.5, 2.5)
        4.0
    """
    return a + b
```

### 示例2：复杂方法

```python
def process_records(self, records, field_name, processor_func):
    """对查询结果进行处理并生成更新内容。
    
    遍历记录列表，对每条记录调用处理函数，生成更新列表。
    处理过程中会跳过无效记录和解析失败的记录。
    
    Args:
        records (list[dict]): 原始记录列表
            格式: [{'id': record_id, field_name: field_value}, ...]
        field_name (str): 需要处理的字段名
            必须是记录字典中存在的键
        processor_func (callable): 数据处理函数
            函数签名: (data: dict | list) -> dict | None
            接收原始数据，返回处理后的数据
            如果返回 None，该记录将被跳过
    
    Returns:
        tuple[list[tuple[int, dict]], int, int]: 处理结果元组
            - 第一个元素: 更新列表，格式为 [(record_id, processed_data), ...]
            - 第二个元素: 处理成功的记录数量
            - 第三个元素: 跳过的记录数量
    
    Raises:
        KeyError: 当 field_name 在记录中不存在时
        json.JSONDecodeError: 当 JSON 解析失败时（内部处理，不会抛出）
    
    示例:
        >>> records = [{'id': 1, 'data': {'key': 'value'}}]
        >>> def processor(data):
        ...     return {'new_key': data['key']}
        >>> updates, processed, skipped = process_records(records, 'data', processor)
        >>> print(updates)
        [(1, {'new_key': 'value'})]
        >>> print(processed, skipped)
        (1, 0)
    
    注意:
        - 处理函数应该是纯函数，不修改输入数据
        - 大量数据时建议使用批量处理
    
    作者: LZD
    日期: 2025/11/10
    """
```

### 示例3：类 Docstring

```python
class DataCleaner:
    """数据清洗类，负责数据库操作和数据清洗流程。
    
    本类提供了完整的数据清洗功能，包括：
    - 批量处理数据库记录
    - 清洗和标准化 JSON 字段
    - 支持多种数据模型
    
    属性:
        db_key (str): 数据库键名，默认为 'medicine'
        batch_size (int): 批处理大小，默认为 100
    
    使用示例:
        >>> cleaner = DataCleaner()
        >>> cleaner.run()
        开始执行数据清洗任务
        ...
    
    注意:
        - 确保数据库连接正常
        - 建议在生产环境使用前先测试
        - 处理大量数据时可能需要较长时间
    
    作者: LZD
    日期: 2025/11/10
    """
    
    def __init__(self):
        """初始化数据清洗器。
        
        创建数据清洗器实例，初始化数据库连接和模型。
        
        Raises:
            RuntimeError: 如果模型初始化失败
        
        注意:
            - 初始化时会尝试连接数据库
            - 如果连接失败，会在后续操作时抛出异常
        """
```

### 示例4：静态方法

```python
@staticmethod
def _process_cited_articles(data):
    """将引用文献数组整理成以 object_id 为键的字典。
    
    处理引用文献数组，将每个文献项转换为字典格式。
    对于项目类型的文献，会进行标准化处理。
    
    Args:
        data (list[dict]): 原始引用数组
            格式: [
                {
                    'object_id': 'id1',
                    'object_type': 'project' | 'article',
                    'object_info': {...}
                },
                ...
            ]
    
    Returns:
        dict[str, dict] | None: 标准化后的引用信息字典
            键为 object_id，值为处理后的 object_info
            如果输入不是列表，返回 None
    
    示例:
        >>> data = [
        ...     {'object_id': '1', 'object_type': 'project', 'object_info': {...}},
        ...     {'object_id': '2', 'object_type': 'article', 'object_info': {...}}
        ... ]
        >>> result = _process_cited_articles(data)
        >>> print(result)
        {'1': {...}, '2': {...}}
    """
```

## 五、MkDocs 显示效果

### 完整 Docstring 在 MkDocs 中的显示

当你使用完整的 docstring 时，MkDocs 会显示：

1. **函数/方法签名**：参数和类型注解
2. **简短描述**：第一行描述
3. **详细描述**：多行描述
4. **参数列表**：每个参数的名称、类型、描述
5. **返回值**：返回类型和描述
6. **异常**：可能抛出的异常
7. **示例**：代码示例
8. **注意/警告**：重要信息
9. **源代码链接**：如果启用了 `show_source: true`

## 六、最佳实践

### 1. 必需部分（最低要求）

```python
def my_function(param1, param2):
    """简短描述。
    
    Args:
        param1 (type): 参数1描述
        param2 (type): 参数2描述
    
    Returns:
        type: 返回值描述
    """
```

### 2. 推荐部分（建议添加）

```python
def my_function(param1, param2):
    """简短描述。
    
    详细描述，说明功能、用途等。
    
    Args:
        param1 (type): 参数1描述
        param2 (type): 参数2描述
    
    Returns:
        type: 返回值描述
    
    Raises:
        ExceptionType: 异常描述
    
    示例:
        >>> my_function(1, 2)
        result
    """
```

### 3. 完整版（最佳实践）

包含所有部分：Args、Returns、Raises、示例、注意、警告等。

## 七、常见问题

### Q1: 参数类型可以是多个吗？

**A**: 可以，使用 `|` 或 `Union`：
```python
param1 (int | str): 可以是整数或字符串
param2 (Union[int, str, None]): 可以是整数、字符串或 None
```

### Q2: 可选参数怎么表示？

**A**: 使用 `optional` 关键字：
```python
param (type, optional): 可选参数，默认值为 value
```

### Q3: 复杂类型怎么表示？

**A**: 使用类型注解语法：
```python
param1 (list[dict]): 字典列表
param2 (dict[str, int]): 字符串到整数的字典
param3 (tuple[int, str, dict]): 包含三个元素的元组
```

### Q4: 生成器函数怎么文档化？

**A**: 使用 `Yields` 而不是 `Returns`：
```python
Yields:
    type: yield 的值描述
```

### Q5: 私有方法需要 docstring 吗？

**A**: 建议添加，但可以简化：
```python
def _private_method(self):
    """私有方法，用于内部处理。"""
```

## 八、总结

### MkDocs 期望的完整 Docstring 包括：

1. ✅ **简短描述**（必需）
2. ✅ **详细描述**（推荐）
3. ✅ **Args**（参数说明，推荐）
4. ✅ **Returns**（返回值说明，推荐）
5. ✅ **Raises**（异常说明，如果有）
6. ✅ **示例**（代码示例，推荐）
7. ✅ **注意/警告**（重要信息，可选）
8. ✅ **作者/日期**（元信息，可选）

### 优先级

- **高优先级**：简短描述、Args、Returns
- **中优先级**：详细描述、Raises、示例
- **低优先级**：注意、警告、作者信息

### 记住

- 即使不完整，MkDocs 也能工作
- 逐步改进，不需要一次性完善所有 docstring
- 优先为公共 API 添加完整 docstring

