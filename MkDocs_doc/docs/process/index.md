# 开发流程与协作规范

## 流程总览

```mermaid
flowchart LR
    idea[需求/问题] --> design[方案设计]
    design --> review[代码&文档评审]
    review --> ci[CI/CD 流水线]
    ci --> release[发布/部署]
    release --> retro[复盘 & 文档更新]
```

- **需求与方案**：所有需求在 Issue/PR 模板中注明背景、目标、验收标准。
- **评审**：代码与文档必须同时提交；文档缺失将被视为评审阻塞。
- **自动化**：CI 校验代码质量、测试、文档构建；CD 再部署到测试/生产环境。

## 模块入口

| 主题 | 文档 |
| --- | --- |
| Git 工作流 | [process/git.md](git.md) |
| 代码评审清单 | [process/code-review.md](code-review.md) |
| CI/CD 流水线 | [process/cicd.md](cicd.md) |

> 若流程出现例外（紧急修复、热补丁等），须在 PR 描述中说明，并在发布后补齐文档。

