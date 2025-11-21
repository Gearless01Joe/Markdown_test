# 常见问题排查手册

## 使用说明

- 先确认问题等级（S0/S1/S2），并记录发生时间、影响范围。
- 依照「症状 → 诊断 → 处理 → 预防」流程填写，下次可直接引用。

## 1. API 文档缺失/生成失败

- **症状**：`mkdocs build` 提示 `FileNotFoundError` 或 `Broken reference`.
- **诊断**：
  1. 检查 `mkdocs.yml` 中是否新增路径。
  2. 运行 `python scripts/generate_mkdocstrings_md.py -v` 查看扫描日志。
- **处理**：补充路径、修复 docstring，重新执行脚本并提交。
- **预防**：在 PR 模板勾选「API 自动生成」项。

## 2. Scrapy 爬虫延迟/超时

- **症状**：任务堆积、`requests_per_minute` 降低。
- **诊断**：查看 `logs/spider.log` 中的重试率、Redis 队列深度。
- **处理**：调大并发/限速、检查代理池、按域名拆分任务。
- **预防**：使用健康检查脚本定时跑 `scrapy check`.

## 3. DataCleaner 入库失败

- **症状**：Pipeline 中断，日志出现 `persist_failed`。
- **诊断**：核对数据库连接、事务冲突、字段映射。
- **处理**：开启 `sqlalchemy.echo=true` 捕捉 SQL；必要时回滚。
- **预防**：上线前运行 `python scripts/data_cleaner_smoke.py`.

## 4. 部署后页面白屏

- **症状**：GitHub Pages/OSS 打开空白，控制台 404。
- **诊断**：确认 `mkdocs.yml` 中 `use_directory_urls`、`site_url` 配置；检查 `extra_javascript` 路径。
- **处理**：重新构建 `mkdocs build --clean` 并发布；若 CDN 缓存，执行刷新。
- **预防**：发布前在本地执行 `mkdocs serve -a 0.0.0.0:8000` 完整检查。

## 模板

```markdown
### <问题名称>

- 级别：S1
- 影响：x% 请求失败
- 症状：...
- 诊断步骤：
  1. ...
  2. ...
- 解决方案：...
- 后续行动：...
```

> 更多项目级别的排障记录，可在 `projects/<name>/troubleshooting.md` 中查看，并与本手册互相引用。*** End Patch}]}`

