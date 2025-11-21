# Git 工作流

## 分支策略

- `main`: 可部署分支，仅通过 PR 合并。
- `develop`: 默认集成分支，日常需求首先合入此分支。
- 功能/修复：`feat/<topic>`, `fix/<issue-id>`, `docs/<module>`, `chore/<task>`。
- 紧急热修复：从 `main` 创建 `hotfix/<issue>`，完成后回合并 `main` 与 `develop`。

## 提交流程

1. `git fetch origin --prune`
2. `git checkout -b feat/new-onboarding origin/develop`
3. 完成开发并运行 `pre-commit run --all-files`、`pytest`、`mkdocs build`
4. `git push -u origin feat/new-onboarding`
5. 创建 PR，绑定 Issue、填写 checklist、附截图。

## 提交信息

```
<type>(scope?): <summary>

[optional body]

Refs: #issue-id
```

- type 取值：`feat`/`fix`/`docs`/`refactor`/`chore`.
- scope 可选，用于模块或项目名称，如 `feat(rcsb-pdb): add pipeline metrics`.

## 标签与版本

- 版本号格式 `vMAJOR.MINOR.PATCH`。
- 每次发布在 `update.md` 记录摘要，同时执行 `git tag vX.Y.Z && git push origin vX.Y.Z`。

## 常见命令速查

| 场景 | 命令 |
| --- | --- |
| 调整上游 | `git pull --rebase origin develop` |
| 撤销上一次提交 | `git reset --soft HEAD~1` |
| 变基清理 | `git rebase -i origin/develop` |
| 检查差异 | `git diff --stat origin/develop` |

> 所有文档更新同样遵循以上流程，确保文档与代码具备一致的审计链路。

