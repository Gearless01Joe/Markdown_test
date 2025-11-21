# 编码规范与风格指南

## 目标

- 统一命名、注释、异常、日志与测试策略。
- 让 mkdocstrings 输出的 API 拥有一致的文档质量。
- 与 CI/CD、pre-commit 形成闭环，避免重复劳动。

## 模块拆分

| 主题 | 内容 | 关联文档 |
| --- | --- | --- |
| Python 风格基线 | 约定命名、异常、测试策略 | [Python 风格基线](../guide/best-practices.md) |
| Docstring 标准 | Google/NumPy 样例、常见片段 | [docstring 指南](../guide/mkdocstrings-comments.md) |
| 工具链集成 | pre-commit、Black、Flake8、MyPy | [工具链集成](tooling.md) |
| mkdocstrings | 工作流、语法、注释映射 | [工作流程](../guide/mkdocstrings-workflow.md)、[语法参考](../guide/mkdocstrings-syntax.md) |

## 执行方式

1. 新模块默认继承此处规则，特殊情况需在文档中声明并说明原因。
2. PR 审核单独检查「规范符合度」；如需破例请在描述中添加 `#skip-style` 并附理由。
3. `scripts/generate_mkdocstrings_md.py` 自动读取 docstring，请确保示例使用三反引号包裹，便于渲染。

!!! tip "建议的提交顺序"
    1. 运行 `pre-commit run --all-files`<br>
    2. `pytest` / 业务脚本自检<br>
    3. `mkdocs build` 验证内容结构<br>
    4. 提交并附带截图/链接

