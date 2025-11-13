# 大项目文档编写和部署指南

## 一、大项目应该写哪些 .rst 文件？

### 原则：按模块组织，分层管理

对于大项目，建议按以下方式组织文档：

### 1. 项目结构示例

假设你的项目结构是这样的：

```
src/
├── data_cleaner.py          # 数据清洗模块
├── base_mysql.py            # 数据库基础模块
├── utils/                   # 工具模块
│   ├── __init__.py
│   ├── logger.py
│   └── validator.py
├── application/             # 应用模块
│   ├── __init__.py
│   ├── NsfcTopicRcmdModels.py
│   └── api/
│       ├── __init__.py
│       └── handlers.py
└── tests/                   # 测试模块
    └── test_data_cleaner.py
```

### 2. 推荐的 .rst 文件组织

#### 方案 A：按功能模块组织（推荐）

```
sphinx_doc/source/
├── index.rst                    # 主入口
├── modules.rst                  # 模块总览
├── data_cleaner.rst             # 数据清洗模块
├── base_mysql.rst               # 数据库模块
├── utils.rst                    # 工具模块
│   ├── logger.rst               # 日志工具
│   └── validator.rst            # 验证工具
└── application.rst              # 应用模块
    ├── models.rst               # 模型
    └── api.rst                  # API
```

#### 方案 B：按层级组织

```
sphinx_doc/source/
├── index.rst
├── core/                        # 核心模块
│   ├── data_cleaner.rst
│   └── base_mysql.rst
├── utils/                       # 工具模块
│   ├── index.rst
│   ├── logger.rst
│   └── validator.rst
└── application/                 # 应用模块
    ├── index.rst
    ├── models.rst
    └── api.rst
```

### 3. 具体文件内容示例

#### index.rst（主入口）

```rst
项目文档
========

欢迎使用项目文档！

目录
----

.. toctree::
   :maxdepth: 2
   :caption: 核心模块:

   modules
   data_cleaner
   base_mysql

.. toctree::
   :maxdepth: 2
   :caption: 工具模块:

   utils/index

.. toctree::
   :maxdepth: 2
   :caption: 应用模块:

   application/index
```

#### modules.rst（模块总览）

```rst
模块总览
========

本项目包含以下主要模块：

核心模块
--------

.. toctree::
   :maxdepth: 1

   data_cleaner
   base_mysql

工具模块
--------

.. toctree::
   :maxdepth: 1

   utils/index

应用模块
--------

.. toctree::
   :maxdepth: 1

   application/index
```

#### data_cleaner.rst（单个模块）

```rst
data\_cleaner 模块
==================

概述
----

数据清洗模块，负责数据库操作和数据清洗流程。

.. automodule:: data_cleaner
   :members:
   :show-inheritance:
   :undoc-members:
```

#### utils/index.rst（子模块索引）

```rst
工具模块
========

本模块提供各种工具函数。

.. toctree::
   :maxdepth: 2

   logger
   validator
```

#### utils/logger.rst（具体工具）

```rst
日志工具
========

.. automodule:: utils.logger
   :members:
   :show-inheritance:
```

### 4. 决定写哪些 .rst 文件的原则

#### ✅ 应该写 .rst 的文件：

1. **主要模块**：用户会直接使用的模块
   - 例如：`data_cleaner.py`、`base_mysql.py`

2. **公共 API**：对外提供的接口
   - 例如：`application/api/handlers.py`

3. **重要工具类**：常用的工具函数
   - 例如：`utils/logger.py`、`utils/validator.py`

4. **核心类**：项目的主要类
   - 例如：`DataCleaner`、`BaseCRUD`

#### ❌ 不需要写 .rst 的文件：

1. **内部实现**：仅供内部使用的模块
   - 例如：`_internal_helper.py`

2. **测试文件**：通常不需要文档
   - 例如：`tests/test_*.py`

3. **配置文件**：配置相关的文件
   - 例如：`config.py`、`settings.py`

4. **简单的工具函数**：如果功能很简单，可以合并到一个 .rst 中

### 5. 实际项目示例（基于你的项目）

根据你的项目结构：

```
src/
├── data_cleaner.py
├── base_mysql.py
└── application/
    └── NsfcTopicRcmdModels.py
```

**建议的 .rst 文件**：

```
sphinx_doc/source/
├── index.rst
├── modules.rst
├── data_cleaner.rst          # ✅ 主要模块
├── base_mysql.rst            # ✅ 数据库基础模块
└── application.rst           # ✅ 应用模块
    └── models.rst            # ✅ 模型类
```

**index.rst**：
```rst
项目文档
========

.. toctree::
   :maxdepth: 2
   :caption: 目录:

   modules
   data_cleaner
   base_mysql
   application/models
```

**modules.rst**：
```rst
模块总览
========

.. toctree::
   :maxdepth: 1

   data_cleaner
   base_mysql
   application/models
```

**data_cleaner.rst**：
```rst
data\_cleaner 模块
==================

.. automodule:: data_cleaner
   :members:
   :show-inheritance:
```

**base_mysql.rst**：
```rst
base\_mysql 模块
================

.. automodule:: base_mysql
   :members:
   :show-inheritance:
```

**application/models.rst**：
```rst
应用模型
========

.. automodule:: application.NsfcTopicRcmdModels
   :members:
   :show-inheritance:
```

---

## 二、如何让团队其他电脑都能看到文档？

生成的 HTML 默认只能在本地查看，有几种方式可以让团队访问：

### 方法 1：使用 GitHub Pages（推荐，免费）

#### 步骤：

1. **生成文档**：
   ```bash
   cd sphinx_doc
   make html
   ```

2. **创建 GitHub 仓库**（如果还没有）：
   - 在 GitHub 上创建仓库
   - 将项目代码推送到仓库

3. **配置 GitHub Pages**：
   - 在仓库设置中启用 GitHub Pages
   - 选择 `gh-pages` 分支或 `docs` 目录

4. **部署文档**：

   **方法 A：使用 gh-pages 分支**
   ```bash
   # 生成文档
   cd sphinx_doc
   make html
   
   # 切换到 gh-pages 分支
   git checkout -b gh-pages
   
   # 复制生成的文档
   cp -r build/html/* .
   
   # 提交并推送
   git add .
   git commit -m "Update documentation"
   git push origin gh-pages
   ```

   **方法 B：使用 GitHub Actions 自动部署**
   
   创建 `.github/workflows/docs.yml`：
   ```yaml
   name: Deploy Documentation
   
   on:
     push:
       branches: [ main ]
       paths:
         - 'src/**'
         - 'sphinx_doc/**'
   
   jobs:
     deploy:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2
         
         - name: Set up Python
           uses: actions/setup-python@v2
           with:
             python-version: '3.8'
         
         - name: Install dependencies
           run: |
             pip install sphinx
             pip install -r requirements.txt
         
         - name: Build documentation
           run: |
             cd sphinx_doc
             make html
         
         - name: Deploy to GitHub Pages
           uses: peaceiris/actions-gh-pages@v3
           with:
             github_token: ${{ secrets.GITHUB_TOKEN }}
             publish_dir: ./sphinx_doc/build/html
   ```

5. **访问文档**：
   - 文档会在 `https://你的用户名.github.io/仓库名/` 可访问
   - 例如：`https://liuzidu.github.io/Markdown/`

#### 优点：
- ✅ 免费
- ✅ 自动更新（使用 GitHub Actions）
- ✅ 团队可以直接访问链接
- ✅ 版本控制

#### 缺点：
- ❌ 需要 GitHub 账号
- ❌ 文档是公开的（除非使用私有仓库）

---

### 方法 2：使用 Read the Docs（推荐，免费）

Read the Docs 是专门为文档设计的平台。

#### 步骤：

1. **注册账号**：
   - 访问 https://readthedocs.org/
   - 使用 GitHub 账号登录

2. **导入项目**：
   - 点击 "Import a Project"
   - 选择你的 GitHub 仓库

3. **配置项目**：
   - 项目名称：你的项目名
   - Repository URL：你的 GitHub 仓库地址
   - 默认分支：通常是 `main` 或 `master`
   - 配置文件路径：`sphinx_doc/source/conf.py`

4. **构建文档**：
   - Read the Docs 会自动检测 Sphinx 项目
   - 点击 "Build" 按钮构建文档

5. **访问文档**：
   - 文档会在 `https://项目名.readthedocs.io/` 可访问
   - 例如：`https://markdown.readthedocs.io/`

#### 优点：
- ✅ 免费
- ✅ 自动构建和更新
- ✅ 支持版本管理
- ✅ 专业的文档平台
- ✅ 支持 PDF 下载

#### 缺点：
- ❌ 需要注册账号
- ❌ 构建可能需要一些时间

---

### 方法 3：部署到服务器

如果你有自己的服务器，可以部署文档。

#### 步骤：

1. **生成文档**：
   ```bash
   cd sphinx_doc
   make html
   ```

2. **上传到服务器**：
   ```bash
   # 使用 scp 上传
   scp -r build/html/* user@server:/var/www/docs/
   
   # 或使用 rsync
   rsync -av build/html/ user@server:/var/www/docs/
   ```

3. **配置 Web 服务器**（Nginx 示例）：
   ```nginx
   server {
       listen 80;
       server_name docs.yourcompany.com;
       
       root /var/www/docs;
       index index.html;
       
       location / {
           try_files $uri $uri/ =404;
       }
   }
   ```

4. **访问文档**：
   - 通过 `http://docs.yourcompany.com` 访问

#### 优点：
- ✅ 完全控制
- ✅ 可以设置访问权限
- ✅ 可以自定义域名

#### 缺点：
- ❌ 需要服务器
- ❌ 需要维护

---

### 方法 4：使用内网共享（简单但有限）

#### 步骤：

1. **生成文档**：
   ```bash
   cd sphinx_doc
   make html
   ```

2. **共享文件夹**：
   - 将 `build/html` 目录放到共享文件夹
   - 或使用文件共享服务（如 OneDrive、Google Drive）

3. **团队访问**：
   - 团队成员通过共享链接访问
   - 或直接打开 `index.html` 文件

#### 优点：
- ✅ 简单快速
- ✅ 不需要服务器

#### 缺点：
- ❌ 需要手动更新
- ❌ 访问可能不方便
- ❌ 不适合大团队

---

### 方法对比

| 方法 | 难度 | 成本 | 自动更新 | 访问便利性 | 推荐度 |
|------|------|------|----------|------------|--------|
| GitHub Pages | 中 | 免费 | ✅ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Read the Docs | 低 | 免费 | ✅ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 服务器部署 | 高 | 需服务器 | ❌ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 内网共享 | 低 | 免费 | ❌ | ⭐⭐ | ⭐⭐ |

---

## 三、undoc-members 详解

### 什么是"没有文档的成员"？

**"没有文档的成员"** 指的是没有文档字符串（docstring）的类、函数、方法、变量等。

### 实际例子

#### 例子 1：有文档的成员

```python
class DataCleaner:
    """数据清洗类，负责数据库操作和数据清洗流程"""  # ← 有文档字符串
    
    def run(self):
        """执行所有清洗任务。"""  # ← 有文档字符串
        pass
```

这些成员**有文档字符串**，无论 `undoc-members` 是 `True` 还是 `False`，都会显示。

#### 例子 2：没有文档的成员

```python
class DataCleaner:
    """数据清洗类，负责数据库操作和数据清洗流程"""
    
    def run(self):
        """执行所有清洗任务。"""
        pass
    
    def some_method(self):  # ← 没有文档字符串
        pass                # 这就是"没有文档的成员"
    
    def another_method(self):  # ← 也没有文档字符串
        # 只有注释，没有文档字符串
        pass
```

`some_method` 和 `another_method` 就是**没有文档的成员**。

### undoc-members 的作用

#### 如果 `undoc-members = True`：

```python
autodoc_default_options = {
    'members': True,
    'undoc-members': True,  # ← 显示没有文档的成员
    'show-inheritance': True,
}
```

**效果**：
- 文档中会显示 `some_method` 和 `another_method`
- 但只会显示方法签名，没有说明文字
- 例如：
  ```
  DataCleaner
  ===========
  
  .. automethod:: DataCleaner.run
      执行所有清洗任务。
  
  .. automethod:: DataCleaner.some_method
      (没有文档)
  
  .. automethod:: DataCleaner.another_method
      (没有文档)
  ```

#### 如果 `undoc-members = False`：

```python
autodoc_default_options = {
    'members': True,
    'undoc-members': False,  # ← 不显示没有文档的成员
    'show-inheritance': True,
}
```

**效果**：
- 文档中**不会显示** `some_method` 和 `another_method`
- 只显示有文档的成员
- 例如：
  ```
  DataCleaner
  ===========
  
  .. automethod:: DataCleaner.run
      执行所有清洗任务。
  ```

### 实际项目中的例子

#### 你的代码中可能有：

```python
class DataCleaner:
    """数据清洗类，负责数据库操作和数据清洗流程"""
    
    def __init__(self):
        """初始化数据清洗器。"""
        self.db_key = DEFAULT_DB_KEY
        self.batch_size = BATCH_SIZE
    
    def run(self):
        """执行所有清洗任务。"""
        pass
    
    def _process_records(self, records, field_name, processor_func):
        """对查询结果进行处理并生成更新内容。"""
        pass
    
    # 假设有这个方法，但没有文档字符串
    def _helper_method(self):  # ← 没有文档字符串
        # 这是一个辅助方法
        pass
```

#### 如果 `undoc-members = True`：

文档会显示：
- ✅ `__init__`（有文档）
- ✅ `run`（有文档）
- ✅ `_process_records`（有文档）
- ✅ `_helper_method`（没有文档，但也会显示）

#### 如果 `undoc-members = False`：

文档会显示：
- ✅ `__init__`（有文档）
- ✅ `run`（有文档）
- ✅ `_process_records`（有文档）
- ❌ `_helper_method`（没有文档，不显示）

### 如何判断成员是否有文档？

#### 有文档的成员：

```python
def function():
    """这是文档字符串。"""  # ← 有文档字符串
    pass

class MyClass:
    """类的文档字符串。"""  # ← 有文档字符串
    pass
```

#### 没有文档的成员：

```python
def function():
    # 只有注释，没有文档字符串  # ← 没有文档字符串
    pass

def another_function():
    pass  # ← 完全没有文档字符串

class MyClass:
    pass  # ← 没有文档字符串
```

### 建议

#### 对于公共 API（用户会使用的）：

```python
autodoc_default_options = {
    'members': True,
    'undoc-members': False,  # 只显示有文档的成员
    'show-inheritance': True,
}
```

**原因**：
- 用户只需要看有文档的 API
- 没有文档的成员可能是未完成的或内部的
- 文档更简洁

#### 对于内部开发文档：

```python
autodoc_default_options = {
    'members': True,
    'undoc-members': True,  # 显示所有成员
    'show-inheritance': True,
}
```

**原因**：
- 开发人员需要看到所有成员
- 即使没有文档，也能看到方法签名
- 有助于代码审查

### 总结

- **有文档的成员**：有文档字符串（`"""..."""`）的类、函数、方法
- **没有文档的成员**：没有文档字符串的类、函数、方法
- **`undoc-members = True`**：显示所有成员（包括没有文档的）
- **`undoc-members = False`**：只显示有文档的成员

**建议**：对于用户文档，通常设为 `False`；对于开发文档，可以设为 `True`。

