# 工具链集成指南

## pre-commit

1. 安装：`pip install pre-commit`，在根目录执行 `pre-commit install`.
2. `.pre-commit-config.yaml` 建议包含：
   ```yaml
   repos:
     - repo: https://github.com/psf/black
       rev: 24.10.0
       hooks:
         - id: black
     - repo: https://github.com/pycqa/flake8
       rev: 7.1.0
       hooks:
         - id: flake8
     - repo: https://github.com/pre-commit/mirrors-mypy
       rev: v1.11.0
       hooks:
         - id: mypy
     - repo: https://github.com/igorshubovych/markdownlint-cli
       rev: v0.41.0
       hooks:
         - id: markdownlint
   ```
3. 针对大型文件可配置 `exclude` 或 `args: [--config=...]`，减少误报。

## 格式化与静态检查

- **Black + isort**：统一格式与 import 顺序，`pyproject.toml` 中设置 `line-length = 100`。
- **Flake8**：启用插件 `flake8-bugbear`, `flake8-comprehensions`，提升潜在缺陷发现率。
- **MyPy**：`mypy.ini` 指定 `plugins = pydantic.mypy`（若使用 Pydantic），并开启 `disallow_any_generics`.

## 文档质量

- **mdformat/markdownlint**：保证 Markdown 缩进、列表、表格一致。
- **yamlfmt**：格式化 `mkdocs.yml`、GitHub Actions、Dependabot 配置。
- **linkcheck**：可通过 `mkdocs serve -a 0.0.0.0` + 浏览器插件或 `pytest --md-link-check` 批量验证链接。

## CI/CD 集成

| 阶段 | 工具 | 触发条件 |
| --- | --- | --- |
| Lint | pre-commit + GitHub Actions | 每次 PR/MR |
| Test | pytest / 脚本自检 | feature 分支、每日定时任务 |
| Docs | `python scripts/generate_mkdocstrings_md.py && mkdocs build` | release 分支、合并主干 |

!!! note "故障应对"
    - 若工具版本升级导致差异，可在 PR 中附 `before/after` 截图或 diff 说明。
    - 对于难以自动修复的历史文件，使用 `# noqa` 或 `noqa: disable` 前请先评估影响，并在文档记录。

