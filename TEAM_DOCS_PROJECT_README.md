# 团队技术文档库项目说明

## 项目目标

这是一个**集中式技术文档生成和部署系统**，用于：
1. 自动从多个项目的 `src` 目录读取 Python 代码
2. 提取代码中的 docstring，自动生成 Markdown 文档
3. 将所有项目的文档整合到一个统一的文档站点
4. 自动部署到 GitHub Pages，供团队访问

## 项目结构

```
团队文档库/
├── README.md                    # 项目说明（本文件）
├── mkdocs.yml                   # MkDocs 配置文件
├── requirements.txt             # Python 依赖
├── .gitignore                   # Git 忽略文件
├── docs/                        # 文档源文件目录
│   ├── index.md                 # 首页
│   ├── project1/                # 项目1的文档
│   │   └── api.md               # 自动生成的 API 文档
│   ├── project2/                # 项目2的文档
│   │   └── api.md
│   └── project3/                # 项目3的文档
│       └── api.md
├── projects/                    # 各个项目的代码目录
│   ├── project1/                # 项目1的代码（可以是符号链接或克隆）
│   │   └── src/
│   ├── project2/
│   │   └── src/
│   └── project3/
│       └── src/
└── scripts/                     # 自动化脚本
    └── generate_docs.py         # 自动生成文档的脚本
```

## 核心功能

### 1. 自动扫描项目
- 扫描 `projects/` 目录下的所有项目
- 自动检测每个项目的 `src` 目录
- 识别 Python 模块（`.py` 文件）

### 2. 自动生成文档
- 为每个项目生成 `docs/项目名/api.md`
- 使用 mkdocstrings 插件读取 docstring
- 自动生成模块、类、函数的文档

### 3. 统一导航
- 在 `mkdocs.yml` 中自动添加所有项目到导航
- 支持多层级导航结构

### 4. 自动部署
- 支持本地预览（`mkdocs serve`）
- 支持部署到 GitHub Pages（`mkdocs gh-deploy`）

## 实现步骤

### 第一步：创建项目结构

1. 创建目录结构：
   ```bash
   mkdir -p docs scripts projects
   ```

2. 创建 `requirements.txt`：
   ```
   mkdocs>=1.5.0
   mkdocstrings[python]>=0.23.0
   mkdocs-material>=9.0.0
   ```

3. 创建 `.gitignore`：
   ```
   site/
   .venv/
   __pycache__/
   *.pyc
   .DS_Store
   ```

### 第二步：配置 mkdocs.yml

创建 `mkdocs.yml`，配置：
- 站点名称和 URL
- 导航结构（可以手动或自动生成）
- mkdocstrings 插件配置
- 主题设置

### 第三步：编写自动生成脚本

创建 `scripts/generate_docs.py`，实现：
- 扫描 `projects/` 目录
- 为每个项目生成 `api.md`
- 自动更新 `mkdocs.yml` 的导航（可选）

### 第四步：设置项目代码

有两种方式：
1. **符号链接**（推荐，如果所有项目在同一台机器）：
   ```bash
   ln -s /path/to/project1/src projects/project1
   ```

2. **Git Submodule**（推荐，如果项目在 Git 仓库）：
   ```bash
   git submodule add https://github.com/team/project1.git projects/project1
   ```

### 第五步：生成和部署

```bash
# 1. 生成文档
python scripts/generate_docs.py

# 2. 本地预览
mkdocs serve

# 3. 部署到 GitHub Pages
mkdocs gh-deploy
```

## 详细配置说明

### mkdocs.yml 示例

```yaml
site_name: 团队技术文档库
site_url: https://your-username.github.io/team-docs/

nav:
  - 首页: index.md
  - 项目1: project1/api.md
  - 项目2: project2/api.md
  - 项目3: project3/api.md

plugins:
  - search
  - mkdocstrings:
      default_handler: python
      handlers:
        python:
          paths: 
            - projects/project1/src
            - projects/project2/src
            - projects/project3/src
          options:
            docstring_style: google
            show_source: true
            show_root_heading: true

theme:
  name: material
  features:
    - navigation.tabs
    - navigation.sections
    - search.suggest
```

### generate_docs.py 脚本示例

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动生成文档脚本

扫描 projects/ 目录下的所有项目，为每个项目生成 api.md 文档
"""

import os
from pathlib import Path
from typing import List

def find_python_modules(src_path: Path) -> List[str]:
    """查找 src 目录下的所有 Python 模块"""
    modules = []
    if not src_path.exists():
        return modules
    
    for py_file in src_path.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
        # 计算相对路径，转换为模块名
        rel_path = py_file.relative_to(src_path.parent)
        module_name = str(rel_path.with_suffix("")).replace(os.sep, ".")
        modules.append(module_name)
    
    return sorted(modules)

def generate_api_doc(project_name: str, src_path: Path) -> str:
    """为项目生成 api.md 内容"""
    modules = find_python_modules(src_path)
    
    if not modules:
        return f"""# {project_name} API 参考

> 未找到 Python 模块
"""
    
    content = f"""# {project_name} API 参考

"""
    
    for module in modules:
        content += f"""::: {module}
    handler: python
    options:
      show_root_heading: true
      show_source: true

"""
    
    return content

def main():
    """主函数：扫描所有项目并生成文档"""
    projects_dir = Path("projects")
    docs_dir = Path("docs")
    
    if not projects_dir.exists():
        print(f"错误：{projects_dir} 目录不存在")
        return
    
    projects_found = []
    
    # 扫描所有项目
    for project_dir in projects_dir.iterdir():
        if not project_dir.is_dir() or project_dir.name.startswith("."):
            continue
        
        src_path = project_dir / "src"
        if not src_path.exists():
            print(f"警告：{project_dir.name} 没有 src 目录，跳过")
            continue
        
        # 生成文档
        doc_content = generate_api_doc(project_dir.name, src_path)
        doc_file = docs_dir / project_dir.name / "api.md"
        doc_file.parent.mkdir(parents=True, exist_ok=True)
        doc_file.write_text(doc_content, encoding='utf-8')
        
        projects_found.append(project_dir.name)
        print(f"✓ 已为 {project_dir.name} 生成文档")
    
    print(f"\n完成！共处理 {len(projects_found)} 个项目")
    print(f"项目列表：{', '.join(projects_found)}")

if __name__ == "__main__":
    main()
```

## 使用流程

### 首次设置

1. **克隆或创建文档仓库**：
   ```bash
   git clone https://github.com/your-username/team-docs.git
   cd team-docs
   ```

2. **安装依赖**：
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **添加项目代码**（选择一种方式）：
   ```bash
   # 方式1：符号链接
   ln -s /path/to/project1/src projects/project1
   
   # 方式2：Git Submodule
   git submodule add https://github.com/team/project1.git projects/project1
   ```

4. **生成文档**：
   ```bash
   python scripts/generate_docs.py
   ```

5. **预览**：
   ```bash
   mkdocs serve
   ```

6. **部署**：
   ```bash
   mkdocs gh-deploy
   ```

### 日常更新

当项目代码更新后：

1. **更新项目代码**（如果是 submodule）：
   ```bash
   git submodule update --remote
   ```

2. **重新生成文档**：
   ```bash
   python scripts/generate_docs.py
   ```

3. **提交并部署**：
   ```bash
   git add .
   git commit -m "Update documentation"
   git push
   mkdocs gh-deploy
   ```

## 注意事项

1. **路径配置**：确保 `mkdocs.yml` 中的 `paths` 配置正确指向各个项目的 `src` 目录

2. **模块导入**：如果项目之间有依赖关系，可能需要配置 `PYTHONPATH` 或使用 `autodoc_mock_imports`

3. **文档更新**：代码更新后记得运行 `generate_docs.py` 重新生成文档

4. **Git 管理**：
   - 不要提交 `site/` 目录（已在 `.gitignore` 中）
   - 如果使用 submodule，记得提交 `.gitmodules` 文件

## 扩展功能（可选）

1. **自动更新导航**：修改 `generate_docs.py`，自动更新 `mkdocs.yml` 的 `nav` 配置

2. **CI/CD 自动化**：使用 GitHub Actions 自动生成和部署文档

3. **多语言支持**：为不同项目配置不同的 docstring 风格

4. **文档分类**：按项目类型或团队分组显示文档

## 问题排查

### 问题1：找不到模块
- 检查 `paths` 配置是否正确
- 确认项目代码路径存在
- 检查 Python 模块的导入路径

### 问题2：文档为空
- 检查代码中是否有 docstring
- 确认 docstring 风格配置正确（google/numpy/sphinx）

### 问题3：部署失败
- 检查 GitHub Pages 设置
- 确认 `gh-pages` 分支已创建
- 检查网络连接和 Git 配置

## 总结

这个项目是一个**文档生成和部署系统**，核心工作流程是：
1. 扫描多个项目的源代码
2. 自动提取 docstring 生成文档
3. 整合到统一的文档站点
4. 部署到 GitHub Pages 供团队访问

所有操作都可以通过脚本自动化，大大简化了多项目文档管理的复杂度。

