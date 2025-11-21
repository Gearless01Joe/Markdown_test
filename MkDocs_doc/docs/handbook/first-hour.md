# 第一小时任务清单

> 目标：在 60 分钟内完成环境验证、运行示例并提交可追踪的变更，确保具备独立迭代的最小能力。

## 0-15 分钟：仓库与依赖

1. 克隆主仓库并同步子模块：
   ```bash
   git clone git@github.com:xxx/Markdown.git
   git submodule update --init --recursive
   ```
2. `cd MkDocs_doc`，创建/激活虚拟环境，安装依赖：
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```

## 15-30 分钟：开发环境验证

1. 运行 `mkdocs serve`，确认 `http://127.0.0.1:8000` 页面正常加载并完成一次全文搜索。
2. 执行 `python scripts/generate_mkdocstrings_md.py`，确保 API 文档可自动刷新。
3. 检查 Material 主题的亮/暗色切换、导航树展开、Mermaid 图渲染是否正常。

## 30-45 分钟：示例任务

- 在 `docs/projects/rcsb_pdb/examples.md` 增加一个使用示例或 FAQ。
- 更新对应项目的 `update.md`，记录本次调整（遵循「日期 + 作者 + 摘要」格式）。

## 45-60 分钟：提交与同步

1. 自检：运行 `mkdocs build`，确保无报错；使用 `pre-commit run --all-files`（若已安装）。
2. 提交：
   ```bash
   git checkout -b chore/onboarding-yourname
   git add .
   git commit -m "docs: update onboarding example"
   ```
3. 在 PR 模板中链接相关文档，并 @ 模块 owner 进行评审。

> 若在以上任意步骤遇阻，请在群内 @ 值班同学并记录问题，帮助后续迭代完善 onboarding。

