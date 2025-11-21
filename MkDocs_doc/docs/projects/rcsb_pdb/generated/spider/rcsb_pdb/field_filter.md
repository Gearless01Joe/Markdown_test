# field_filter

字段过滤模块 - 根据配置精确控制提取哪些字段

**模块路径**: `code_liu.RCSB_PDB.src.spiders.rcsb_pdb.field_filter`

## 导入

- `json`
- `pathlib.Path`
- `typing.Any`
- `typing.Dict`
- `typing.List`
- `typing.Optional`

## 类

### FieldFilter

字段过滤器

#### 方法

##### filter_data

```python
def filter_data( self, data: <ast.Subscript object at 0x0000028BFF63EB10>, section: str )  -> <ast.Subscript object at 0x0000028BFF65E9D0>
```

根据配置过滤指定板块的数据。

参数:
    data (Dict[str, Any]): 待过滤的数据。
    section (str): 配置中定义的板块名称。
返回:
    Dict[str, Any]: 过滤后的数据。

## 函数

### filter_data

```python
def filter_data( self, data: <ast.Subscript object at 0x0000028BFF63EB10>, section: str )  -> <ast.Subscript object at 0x0000028BFF65E9D0>
```

根据配置过滤指定板块的数据。

参数:
    data (Dict[str, Any]): 待过滤的数据。
    section (str): 配置中定义的板块名称。
返回:
    Dict[str, Any]: 过滤后的数据。
