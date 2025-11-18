# Python 代码转 Markdown 工具

## 功能说明

`code_to_markdown.py` 可以将 Python 代码文件自动转换为结构化的 Markdown 文档。

### 主要功能

- ✅ 自动提取类和函数的 docstring
- ✅ 解析函数签名（参数、返回值、类型注解）
- ✅ 提取类继承关系
- ✅ 解析参数说明（支持 Google 和 Sphinx 风格）
- ✅ 生成格式化的 Markdown 文档
- ✅ 支持批量处理目录

## 使用方法

### 1. 转换单个文件

```bash
# 基本用法
python MkDocs_doc/scripts/code_to_markdown.py src/spiders/base_spider.py

# 指定输出文件
python MkDocs_doc/scripts/code_to_markdown.py src/spiders/base_spider.py -o docs/base_spider.md

# 指定基础路径（用于计算模块路径）
python MkDocs_doc/scripts/code_to_markdown.py src/spiders/base_spider.py -b src
```

### 2. 批量转换目录

```bash
# 转换整个目录
python MkDocs_doc/scripts/code_to_markdown.py src/spiders -o docs/generated/spiders

# 默认模式（无参数时自动转换 src/spiders）
python MkDocs_doc/scripts/code_to_markdown.py
```

### 3. 集成到 GitHub Actions

在 `.github/workflows/mkdocs-deploy.yml` 中添加：

```yaml
- name: Generate Markdown from code
  run: |
    python MkDocs_doc/scripts/code_to_markdown.py src/spiders -o MkDocs_doc/docs/generated/spiders
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
- 方法列表（包含签名、参数说明、返回值说明）

### 函数文档
- 函数签名
- docstring
- 参数说明
- 返回值说明

## 支持的 Docstring 格式

### Google 风格

```python
def function(param1, param2):
    """函数说明。
    
    Args:
        param1: 参数1说明
        param2: 参数2说明
    
    Returns:
        返回值说明
    """
```

### Sphinx 风格

```python
def function(param1, param2):
    """函数说明。
    
    :param param1: 参数1说明
    :param param2: 参数2说明
    :return: 返回值说明
    """
```

## 命令行参数

| 参数 | 说明 | 必需 |
|------|------|------|
| `input` | 输入文件或目录路径 | ✅ |
| `-o, --output` | 输出文件或目录路径 | ❌ |
| `-b, --base` | 基础路径（用于计算模块路径） | ❌ |

## 注意事项

1. **私有方法**：默认跳过以 `_` 开头的方法，如需包含可修改代码
2. **`__init__.py`**：默认跳过 `__init__.py` 文件
3. **`__pycache__`**：自动跳过缓存目录
4. **注释格式**：自动清理 `# @Time`, `# @User` 等注释格式

## 示例输出

转换 `src/spiders/base_spider.py` 会生成：

```markdown
# base_spider

基础爬虫类

**模块路径**: `spiders.base_spider`

## 类

### BaseSpider

所有爬虫的基类，提供公共功能。

**继承自**: `scrapy.Spider`

#### 方法

##### __init__

```python
def __init__(**kwargs)
```

初始化类

**参数**:
- `kwargs`: 初始化参数

...
```

## 故障排查

### 问题：解析失败

**错误**: `SyntaxError` 或 `无法解析`

**解决**:
- 检查 Python 文件语法是否正确
- 确保文件编码为 UTF-8

### 问题：模块路径不正确

**解决**:
- 使用 `-b` 参数指定正确的基础路径
- 基础路径应该是包含 `src` 的父目录

### 问题：docstring 格式不被识别

**解决**:
- 确保使用 Google 或 Sphinx 风格的 docstring
- 检查参数说明格式是否正确

## 扩展

### 自定义输出格式

修改 `MarkdownGenerator.generate()` 方法可以自定义输出格式。

### 添加更多信息

在 `CodeVisitor` 中可以提取更多信息，如：
- 装饰器信息
- 类型注解详情
- 常量定义

## 与 mkdocstrings 的区别

| 特性 | code_to_markdown | mkdocstrings |
|------|------------------|--------------|
| 输出格式 | 直接生成 .md 文件 | 在构建时生成 HTML |
| 独立性 | 可以独立使用 | 需要 MkDocs |
| 灵活性 | 完全可控的输出 | 依赖插件配置 |
| 使用场景 | 生成静态文档 | 动态文档站点 |

**建议**：
- 需要静态文档文件 → 使用 `code_to_markdown`
- 需要交互式文档站点 → 使用 `mkdocstrings`

