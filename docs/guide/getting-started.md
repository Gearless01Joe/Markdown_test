# 环境搭建指南

!!! info "适用范围"
    Windows 10/11、macOS 13+、Linux (Ubuntu 22.04)。需要具备 Git 与 Python 3.10 以上环境。

## 1. 初始化工作区

```bash
git clone git@github.com:xxx/Markdown.git
cd Markdown/MkDocs_doc
python -m venv .venv
source .venv/bin/activate  # Windows 使用 .\.venv\Scripts\activate
pip install -r requirements.txt
```

- 若需同时调试爬虫代码，请为 `code_liu`、`src` 目录创建独立虚拟环境，以免依赖冲突。
- 推荐在 IDE 中启用 `Black`/`Flake8`/`MyPy` 扩展，与 `pre-commit` 配置保持一致。

## 2. 本地预览与热更新

```bash
mkdocs serve
```

- 默认地址：`http://127.0.0.1:8000`
- 支持 `-a 0.0.0.0:8001` 开放到局域网，方便现场演示。
- Material 主题支持浏览器深浅色联动，如渲染异常，请检查 `stylesheets/` 自定义样式。

## 3. 自动生成 API 文档

```bash
python scripts/generate_mkdocstrings_md.py
```

- 该脚本会扫描 `../code_liu` 与 `../src`，并在 `docs/projects/*/api.md` 中注入 `::: package.module` 语句。
- 若新增模块，请在 `mkdocs.yml > plugins.mkdocstrings.handlers.python.paths` 中追加路径，再执行脚本。

## 4. 常用调试命令

| 场景 | 命令 | 说明 |
| --- | --- | --- |
| 构建发布版 | `mkdocs build` | 输出到 `site/`，供 GitHub Pages/OSS 托管 |
| 清除缓存 | `mkdocs build --clean` | 解决旧版本残留 |
| 依赖安全升级 | `pip install -U -r requirements.txt` | 建议季度执行，并跑一次 `mkdocs build` |

## 5. 提交规范速览

1. 新建分支：`feat/`、`fix/`、`docs/`、`chore/` 前缀。
2. 提交信息遵循 `<type>: <summary>`，示例：`docs: add logging guide`。
3. PR 勾选检查清单：`mkdocs build`、`pre-commit`、截图或录屏（若涉及 UI）。

> 完成上述步骤后，即可继续执行 [第一小时任务](../handbook/first-hour.md)。
# 环境搭建指南

!!! info "适用范围"
    Windows 10/11、macOS 13+、Linux (Ubuntu 22.04)。需要具备 Git 与 Python 3.10 以上环境。

## 1. 初始化工作区

```bash
git clone git@github.com:xxx/Markdown.git
cd Markdown/MkDocs_doc
python -m venv .venv
source .venv/bin/activate  # Windows 使用 .\.venv\Scripts\activate
pip install -r requirements.txt
```

- 若需同时调试爬虫代码，请为 `code_liu`、`src` 目录创建独立虚拟环境，以免依赖冲突。
- 推荐在 IDE 中启用 `Black`/`Flake8`/`MyPy` 扩展，与 `pre-commit` 配置保持一致。

## 2. 本地预览与热更新

```bash
mkdocs serve
```

- 默认地址：`http://127.0.0.1:8000`
- 支持 `-a 0.0.0.0:8001` 开放到局域网，方便现场演示。
- Material 主题支持浏览器深浅色联动，如渲染异常，请检查 `stylesheets/` 自定义样式。

## 3. 自动生成 API 文档

```bash
python scripts/generate_mkdocstrings_md.py
```

- 该脚本会扫描 `../code_liu` 与 `../src`，并在 `docs/projects/*/api.md` 中注入 `::: package.module` 语句。
- 若新增模块，请在 `mkdocs.yml > plugins.mkdocstrings.handlers.python.paths` 中追加路径，再执行脚本。

## 4. 常用调试命令

| 场景 | 命令 | 说明 |
| --- | --- | --- |
| 构建发布版 | `mkdocs build` | 输出到 `site/`，供 GitHub Pages/OSS 托管 |
| 清除缓存 | `mkdocs build --clean` | 解决旧版本残留 |
| 依赖安全升级 | `pip install -U -r requirements.txt` | 建议季度执行，并跑一次 `mkdocs build` |

## 5. 提交规范速览

1. 新建分支：`feat/`、`fix/`、`docs/`、`chore/` 前缀。
2. 提交信息遵循 `<type>: <summary>`，示例：`docs: add logging guide`。
3. PR 勾选检查清单：`mkdocs build`、`pre-commit`、截图或录屏（若涉及 UI）。

> 完成上述步骤后，即可继续执行 [第一小时任务](../handbook/first-hour.md)。

