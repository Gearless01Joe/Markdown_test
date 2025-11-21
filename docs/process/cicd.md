# CI/CD 流水线说明

## 流程阶段

| 阶段 | 工具 | 动作 | 失败处理 |
| --- | --- | --- | --- |
| Lint | pre-commit / GitHub Actions | Black、Flake8、MyPy、Markdownlint | 修复后重推 |
| Test | pytest / 自定义脚本 | 单元、集成、爬虫冒烟 | 附日志、最小复现步骤 |
| Docs | mkdocstrings + MkDocs | `python scripts/generate_mkdocstrings_md.py && mkdocs build` | 检查缺失引用、循环引用 |
| Deploy | GitHub Pages / OSS | `mkdocs gh-deploy` 或 CI 上传 | 回滚到上一版本，记录在维护日志 |

## GitHub Actions 示例

```yaml
name: docs

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main, develop ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - run: pip install -r MkDocs_doc/requirements.txt
      - run: |
          cd MkDocs_doc
          python scripts/generate_mkdocstrings_md.py
          mkdocs build --strict
```

## 环境与密钥

- 使用 `GitHub Environments` 管理 `PAGES_TOKEN`、OSS 凭证等敏感信息。
- 需部署到多环境时，建议拆分 `deploy-staging`、`deploy-prod` 两个 Job。
- 针对私有依赖，可在 CI 步骤中配置 `PIP_INDEX_URL`。

## 版本与回滚

1. 构建成功后在 PR 中勾选「Docs Build Passed」。
2. 发布版本打 `vX.Y.Z` 标签，并在 `update.md` 记录。
3. 若部署失败，执行：
   ```bash
   git checkout main
   git revert <commit>
   mkdocs gh-deploy
   ```
4. 在 [维护日志](../operations/troubleshooting.md) 中记录问题、影响与解决方案。

!!! note
    `mkdocs build --strict` 会将缺失的引用视为错误，建议在本地与 CI 均开启，以保证结构稳定。*** End Patch}]}`

